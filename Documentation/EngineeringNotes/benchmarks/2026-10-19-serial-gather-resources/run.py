from pathlib import Path
import hashlib,json,statistics,subprocess,sys,time
R=Path(__file__).resolve().parent
sys.path.insert(0,'/private/tmp/swiftsci-csv-sort-20261017/Benchmarks/Tools')
from runner import power_state,environment,verify_uninstrumented
from execution_policy import worker_environment,PRODUCTION_MODE
cases=[['sort',4096,4,'random','numeric','asc'],['sort',1000000,4,'random','numeric','asc'],
 ['sort',250003,3,'ties','mixed','asc'],['sort',250003,8,'ties','mixed','asc'],
 ['sort',1000000,4,'random','mixed','asc'],['sort',250003,4,'nulls','mixed','desc'],
 ['gather',250003,3,'ties','mixed','asc'],['gather',250003,8,'ties','mixed','asc'],
 ['gather',1000000,4,'random','mixed','asc'],['sort',250003,4,'nulls','dates','asc'],
 ['gather',250003,4,'random','dates','asc'],['sort',4096,4,'random','mixed','asc']]
builds={v:json.loads((R/'build'/v/'build.json').read_text()) for v in ['baseline','candidate']}
assert builds['baseline']['dependency_objects']==builds['candidate']['dependency_objects']
assert builds['baseline']['harness_sha256']==builds['candidate']['harness_sha256']
for v,b in builds.items():
 binary=R/'build'/v/'ResourceProbe';verify_uninstrumented(binary)
 assert hashlib.sha256(binary.read_bytes()).hexdigest()==b['binary_sha256']
power=power_state();assert power['source']=='AC',power
env=worker_environment(PRODUCTION_MODE)
plan=dict(cases=cases,seed=0x912dd83562,timing_rounds=5,memory_rounds=3,samples=5,builds=builds,power=power,environment=environment())
(R/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
log=R/'processes.jsonl';assert not log.exists()
with log.open('w') as f:
 for i,case in enumerate(cases):
  for phase,rounds in [('timing',5),('memory',3)]:
   for pair in range(rounds):
    receipts=[]
    for variant in (['baseline','candidate'] if (pair+i)%2==0 else ['candidate','baseline']):
     args=[str(x) for x in case]+[str(plan['seed']),'5',phase]
     p=subprocess.run([str(R/'build'/variant/'ResourceProbe'),*args],env=env,capture_output=True,text=True,timeout=180)
     assert p.returncode==0,(case,variant,p.stderr)
     result=json.loads(p.stdout);assert result['validated']
     assert len(result['samples'])==(1 if phase=='memory' else 5)
     row=dict(case=case,phase=phase,pair=pair,variant=variant,**result)
     f.write(json.dumps(row)+'\n');f.flush();receipts.append(row)
    assert receipts[0]['index_sha']==receipts[1]['index_sha']
  print(i+1,len(cases),case,flush=True)
end=power_state();assert end['source']=='AC';(R/'power-end.json').write_text(json.dumps(end,indent=2)+'\n')
