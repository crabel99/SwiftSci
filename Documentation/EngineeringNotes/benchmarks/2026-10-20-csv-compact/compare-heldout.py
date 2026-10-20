from pathlib import Path
import json,subprocess,hashlib,statistics,sys
R=Path(__file__).resolve().parent
sys.path.insert(0,'/private/tmp/swiftsci-csv-sort-20261017/Benchmarks/Tools')
from runner import power_state,verify_uninstrumented,environment
from execution_policy import worker_environment,PRODUCTION_MODE
P=Path('/Users/crabel/local-ai/spl/swiftsci/pr-resource-metrics-20261018/fixtures')
cases=[['csv',1000,4,str(R/'heldout-fixtures/1000-4-False.csv')],['csv-quoted',1000,4,str(R/'heldout-fixtures/1000-4-True.csv')],['csv-quoted',10000,4,str(R/'heldout-fixtures/10000-4-True.csv')],['csv-quoted',131071,7,str(R/'heldout-fixtures/131071-7-True.csv')],['csv-quoted',75001,13,str(R/'heldout-fixtures/75001-13-True.csv')]]
builds={v:json.loads((R/'build'/v/'build.json').read_text()) for v in ['baseline','compact']}
assert builds['baseline']['dependency_objects']==builds['compact']['dependency_objects']
assert builds['baseline']['harness_sha256']==builds['compact']['harness_sha256']
for v in builds:verify_uninstrumented(R/'build'/v/'ResourceProbe')
assert not (R/'heldout-workers.jsonl').exists()
power=power_state();assert power['source']=='AC',power
plan=dict(cases=cases,builds=builds,power=power,environment=environment(),fixtures={c[3]:hashlib.sha256(Path(c[3]).read_bytes()).hexdigest() for c in cases})
(R/'heldout-comparison-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
with (R/'heldout-workers.jsonl').open('w') as f:
 for ci,c in enumerate(cases):
  for phase,count in [('timing',5),('memory',3)]:
   for pair in range(count):
    for v in (['baseline','compact'] if (ci+pair)%2==0 else ['compact','baseline']):
     args=[c[0],str(c[1]),str(c[2]),'5',phase,c[3]]
     p=subprocess.run([str(R/'build'/v/'ResourceProbe'),*args],env=worker_environment(PRODUCTION_MODE),capture_output=True,text=True,timeout=120)
     assert p.returncode==0,(c,v,p.stderr)
     record=json.loads(p.stdout);assert record['validated'] and len(record['samples'])==(5 if phase=='timing' else 1)
     f.write(json.dumps(dict(case=c[:3],phase=phase,pair=pair,variant=v,**record))+'\n');f.flush()
  print(ci+1,len(cases),c[:3],flush=True)
end=power_state();assert end['source']=='AC';(R/'heldout-power-end.json').write_text(json.dumps(end,indent=2)+'\n')
