from pathlib import Path
import json,subprocess,hashlib,statistics,sys
R=Path(__file__).resolve().parent
sys.path.insert(0,'/private/tmp/swiftsci-csv-sort-20261017/Benchmarks/Tools')
from runner import power_state,verify_uninstrumented,environment
from execution_policy import worker_environment,PRODUCTION_MODE
P=Path('/Users/crabel/local-ai/spl/swiftsci/pr-resource-metrics-20261018/fixtures')
cases=[['csv-quoted',100000,4,str(R/'fixtures/100000-4-True.csv')],['csv-quoted',250000,4,str(R/'fixtures/250000-4-True.csv')],['csv-quoted',1000000,4,str(P/'02-pr39-csv-quoted-1000000-4.csv')],['csv-quoted',1000000,2,str(R/'fixtures/1000000-2-True.csv')],['csv',1000000,4,str(R/'fixtures/1000000-4-False.csv')]]
builds={v:json.loads((R/'build'/v/'build.json').read_text()) for v in ['active','compact']}
assert builds['active']['dependency_objects']==builds['compact']['dependency_objects']
assert builds['active']['harness_sha256']==builds['compact']['harness_sha256']
for v in builds:verify_uninstrumented(R/'build'/v/'ResourceProbe')
assert not (R/'compact-active-reference-workers.jsonl').exists()
power=power_state();assert power['source']=='AC',power
plan=dict(cases=cases,builds=builds,power=power,environment=environment(),fixtures={c[3]:hashlib.sha256(Path(c[3]).read_bytes()).hexdigest() for c in cases})
(R/'compact-active-reference-comparison-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
with (R/'compact-active-reference-workers.jsonl').open('w') as f:
 for ci,c in enumerate(cases):
  for phase,count in [('timing',5),('memory',3)]:
   for pair in range(count):
    for v in (['active','compact'] if (ci+pair)%2==0 else ['compact','active']):
     args=[c[0],str(c[1]),str(c[2]),'5',phase,c[3]]
     p=subprocess.run([str(R/'build'/v/'ResourceProbe'),*args],env=worker_environment(PRODUCTION_MODE),capture_output=True,text=True,timeout=120)
     assert p.returncode==0,(c,v,p.stderr)
     record=json.loads(p.stdout);assert record['validated'] and len(record['samples'])==(5 if phase=='timing' else 1)
     f.write(json.dumps(dict(case=c[:3],phase=phase,pair=pair,variant=v,**record))+'\n');f.flush()
  print(ci+1,len(cases),c[:3],flush=True)
end=power_state();assert end['source']=='AC';(R/'compact-active-reference-power-end.json').write_text(json.dumps(end,indent=2)+'\n')
