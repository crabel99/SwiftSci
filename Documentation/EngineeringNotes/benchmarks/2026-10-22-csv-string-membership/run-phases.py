from pathlib import Path
import json,subprocess,hashlib,statistics as st,sys
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');sys.path.insert(0,str(S/'Benchmarks/Tools'))
from execution_policy import worker_environment,PRODUCTION_MODE
from runner import environment,power_state,verify_uninstrumented
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();binary=R/'PhaseProbe';verify_uninstrumented(binary)
rec=json.loads((R/'source-state.json').read_text());assert all(h(S/p)==v for p,v in rec['sources'].items())
D=R/sys.argv[1];D.mkdir(exist_ok=False);reps=int(sys.argv[2]);contracts=[Path(p) for p in json.loads((R/'contracts.json').read_text())]
orders=[contracts[i:]+contracts[:i] for i in range(len(contracts))];orders += [list(reversed(o)) for o in orders];orders=(orders*((reps+5)//6))[:reps]
plan=dict(binary=str(binary),binary_sha256=h(binary),controller_sha256=h(Path(__file__)),contracts={str(p):h(p) for p in contracts},orders=[[str(p) for p in order] for order in orders],environment=environment(),scope='Serial diagnostic replay. Native CPU scheduling and hash randomization unchanged. Whole public read measured before replay. No builds or profiling during these measurements.')
(D/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');records=[]
for rnd,order in enumerate(orders):
 for contract in order:
  assert power_state()['source']=='AC';inp=json.loads(contract.read_text());assert h(Path(inp['path']))==inp.get('source_sha256',inp.get('sha256'))
  with Path(inp['path']).open('rb') as f:
   while f.read(1024*1024):pass
  p=subprocess.run(['PhaseProbe',str(contract)],executable=str(binary),env=worker_environment(PRODUCTION_MODE),capture_output=True,text=True,timeout=240)
  (D/(inp['id']+f'-{rnd}.stderr')).write_text(p.stderr);assert p.returncode==0,p.stderr
  d=json.loads(p.stdout);assert d['validated'] and all(a['validated'] for a in d['phases']);d['worker_round']=rnd;records.append(d)
  (D/(inp['id']+f'-{rnd}.json')).write_text(json.dumps(d,indent=2)+'\n');print(rnd,inp['id'],len(d['phases']),'validated phases',flush=True)
summary=[]
for case in sorted({d['input'] for d in records}):
 rs=[d for d in records if d['input']==case]
 for column in sorted({p['column'] for d in rs for p in d['phases']}):
  for mode in ['copy','match','parse','parse-match']:
   medians=[{k:st.median(p[k] for p in d['phases'] if p['column']==column and p['mode']==mode) for k in ['total_cpu_ns','total_ns','held_heap_delta_bytes','held_rss_delta_bytes']} for d in rs]
   summary.append(dict(case=case,column=column,mode=mode,workers=len(rs),medians={k:st.median(m[k] for m in medians) for k in medians[0]},worker_medians=medians))
(D/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
full=[dict(case=c,workers=len([d for d in records if d['input']==c]),medians={k:st.median(d['full_read'][k] for d in records if d['input']==c) for k in ['total_cpu_ns','total_ns','peak_bytes']}) for c in sorted({d['input'] for d in records})]
(D/'full-read-summary.json').write_text(json.dumps(full,indent=2)+'\n');print(len(records),'public reads and',sum(len(d['phases']) for d in records),'phases validated',flush=True)
for case in sorted({d['case'] for d in summary}):
 print(case,{m:round(sum(d['medians']['total_cpu_ns'] for d in summary if d['case']==case and d['mode']==m)/1e6,3) for m in ['copy','match','parse','parse-match']},flush=True)
