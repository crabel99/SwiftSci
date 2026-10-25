"""Reuse the native fixed-register loop with background workers and ordinary coordination."""
import json,os,signal,subprocess,time,sys,hashlib,platform
from pathlib import Path
q=Path(sys.argv[1]);q.mkdir()
(q/'anchors.json').write_text(json.dumps(dict(start_unix_ns=time.time_ns(),start_monotonic_ns=time.monotonic_ns()),indent=2)+'\n')
probe=Path(__file__).resolve().parent/'native-probe/fixed-work-mach-aligned'
(q/'provenance.json').write_text(json.dumps(dict(python=sys.executable,python_version=sys.version,platform=platform.platform(),probe=str(probe),probe_sha256=hashlib.sha256(probe.read_bytes()).hexdigest(),driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2)+'\n')
expected=json.loads((probe.parent/'sha256.json').read_text())[probe.name]
if hashlib.sha256(probe.read_bytes()).hexdigest()!=expected:raise ValueError('Native probe changed')
def interrupted(signum,frame):raise KeyboardInterrupt
signal.signal(signal.SIGTERM,interrupted)
owned=[];records=[]
for phase,callers in enumerate([1,4,1,4]):
    jobs=[]
    try:
        for slot in range(callers):
            out=(q/f'rate-probe-{phase}-{slot}.jsonl').open('w')
            err=(q/f'rate-probe-{phase}-{slot}.stderr').open('w')
            p=subprocess.Popen(['/usr/sbin/taskpolicy','-c','background',str(probe),'200000000'],stdout=out,stderr=err,start_new_session=True)
            jobs.append((p,out,err));owned.append(p.pid)
        for p,out,err in jobs:
            p.wait(timeout=60)
            if p.returncode:raise RuntimeError('Native rate probe failed')
    finally:
        for p,out,err in jobs:
            if p.poll() is None:os.killpg(p.pid,signal.SIGKILL);p.wait()
            out.close();err.close()
    for slot in range(callers):
        for row in map(json.loads,(q/f'rate-probe-{phase}-{slot}.jsonl').read_text().splitlines()):
            records.append(dict(phase=phase,callers=callers,slot=slot,**row))
summary=dict(samples=len(records),checksum_count=len({r['value'] for r in records}),
    all_p_user_zero=all(r['p_user_ns']==0 for r in records),
    cpu_ms_min=min(r['sdk_cpu_ns'] for r in records)/1e6,cpu_ms_max=max(r['sdk_cpu_ns'] for r in records)/1e6,
    effective_cycles_per_cpu_ns_min=min(r['cycles']/r['sdk_cpu_ns'] for r in records),
    effective_cycles_per_cpu_ns_max=max(r['cycles']/r['sdk_cpu_ns'] for r in records),
    sdk_vs_getrusage_max_fraction=max(abs(r['rusage_ns']/r['sdk_cpu_ns']-1) for r in records),
    maximum_clock_disagreement_fraction=max(max(r[k] for k in ['sdk_cpu_ns','rusage_ns','clock_cpu_ns'])/min(r[k] for k in ['sdk_cpu_ns','rusage_ns','clock_cpu_ns'])-1 for r in records),
    owned_pids=owned)
(q/'rate-probe-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
(q/'end-anchors.json').write_text(json.dumps(dict(end_unix_ns=time.time_ns(),end_monotonic_ns=time.monotonic_ns()),indent=2)+'\n')
print(json.dumps(summary,indent=2))
if summary['samples']!=240 or summary['checksum_count']!=1 or not summary['all_p_user_zero']:
    raise ValueError('Native workload failed checksum, completeness, or E-core placement')
