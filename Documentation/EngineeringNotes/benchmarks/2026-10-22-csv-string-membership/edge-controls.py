from pathlib import Path
import json,subprocess,hashlib,statistics as st,sys
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');sys.path.insert(0,str(S/'Benchmarks/Tools'))
from execution_policy import worker_environment,PRODUCTION_MODE
from runner import power_state,environment,verify_uninstrumented
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();D=R/'edge-controls';D.mkdir(exist_ok=False)
roots={'production':Path('/private/tmp/swiftsci-csv-local-builder-20261022/build/production'),'ascii-prefix':R/'build/ascii-prefix'}
for root in roots.values():verify_uninstrumented(root/'ResourceProbe')
engines=[(e,policy,phase) for e in roots for policy in ['parallel','serial'] for phase in ['fresh','timing']]
orders=[engines[i:]+engines[:i] for i in range(len(engines))];orders += [list(reversed(o)) for o in orders];orders*=2
T=Path('/private/tmp/swiftsci-csv-number-loop-20261022/text-inputs');cases=[T/'all-string-default-nulls-90.json',T/'all-string-none-nulls-0.json']
(D/'plan.json').write_text(json.dumps(dict(binaries={e:dict(path=str(root/'ResourceProbe'),sha256=h(root/'ResourceProbe')) for e,root in roots.items()},cases=[str(p) for p in cases],orders=orders,environment=environment(),controller_sha256=h(Path(__file__)),scope='Diagnostic repeat of high-null and empty-set CPU costs. Fresh reads and steady reads are separate. Steady worker has two warmups and five recorded complete reads; all reads independently validated. Same native scheduling/hash randomization; explicit matched policy; common argv[0]; builds and profiling stopped.'),indent=2)+'\n')
records=[]
with (D/'workers.jsonl').open('x') as out:
 for path in cases:
  inp=json.loads(path.read_text());assert h(Path(inp['path']))==inp['source_sha256']
  for rnd,order in enumerate(orders):
   assert power_state()['source']=='AC'
   for engine,policy,phase in order:
    cmd=['ResourceProbe',str(path),'known',phase,'5' if phase=='timing' else '1',policy]
    p=subprocess.run(cmd,executable=str(roots[engine]/'ResourceProbe'),env=worker_environment(PRODUCTION_MODE),capture_output=True,text=True,timeout=120);assert p.returncode==0,p.stderr
    d=json.loads(p.stdout);assert d['validated'];assert [a['nulls'] for a in d['checks']['columns']]==inp['null_counts'];d.update(case=path.stem,engine=engine,policy=policy,round=rnd);records.append(d);out.write(json.dumps(d)+'\n');out.flush()
  print(path.stem,'completed',flush=True)
summary=[]
for path in cases:
 for engine,policy,phase in engines:
  rs=[d for d in records if (d['case'],d['engine'],d['policy'],d['phase'])==(path.stem,engine,policy,phase)]
  medians=[{k:st.median(s[k] for s in d['samples']) for k in ['total_cpu_ns','total_ns','process_peak_held_bytes']} for d in rs]
  summary.append(dict(case=path.stem,engine=engine,policy=policy,phase=phase,workers=len(rs),recorded_reads=sum(len(d['samples']) for d in rs),medians={k:st.median(m[k] for m in medians) for k in medians[0]}))
(D/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');flags=[]
for a in summary:
 if a['engine']!='ascii-prefix':continue
 b=next(b for b in summary if b['engine']=='production' and all(a[k]==b[k] for k in ['case','policy','phase']))
 cpu=(a['medians']['total_cpu_ns']/b['medians']['total_cpu_ns']-1)*100
 if cpu>10:flags.append(dict(candidate=a,parent=b,reason='CPU review limit'))
 if a['medians']['process_peak_held_bytes']>b['medians']['process_peak_held_bytes']*1.05+8*2**20:flags.append(dict(candidate=a,parent=b,reason='Memory review limit'))
 print(a['case'],a['policy'],a['phase'],round(b['medians']['total_cpu_ns']/1e6,3),'to',round(a['medians']['total_cpu_ns']/1e6,3),f'{cpu:+.1f}%',flush=True)
(D/'review-flags.json').write_text(json.dumps(flags,indent=2)+'\n');print(len(records),'validated workers;',len(flags),'review flags',flush=True)
