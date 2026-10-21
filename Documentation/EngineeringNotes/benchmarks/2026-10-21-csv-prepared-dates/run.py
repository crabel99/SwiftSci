from pathlib import Path
import hashlib,json,subprocess,sys,time
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-ingestion-20261021');sys.path.insert(0,str(S/'Benchmarks/Tools'))
from execution_policy import worker_environment,PRODUCTION_MODE,policy
from runner import environment,power_state,verify_uninstrumented
P='/Users/crabel/Documents/src/SwiftSci/Benchmarks/.venv-standardized/bin/python';h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pre=json.loads((R/'preflight-summary.json').read_text());assert pre['workers']==40 and not pre['failures']
assert not json.loads((R/'preflight-candidate-final/summary.json').read_text())['failures']
builds=json.loads((R/'build-vcs-verification.json').read_text())
for engine in ['baseline','candidate']:
 b=R/'build'/engine/'ResourceProbe';assert h(b)==builds[engine]['binary_sha256'];verify_uninstrumented(b)
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=json.loads((R/'build'/engine/'build.json').read_text())['variant']['path'],text=True).strip()==builds[engine]['commit']
cases=pre['cases'];engines=pre['engines'];orders=[engines[i:]+engines[:i] for i in range(3)];orders += [list(reversed(x)) for x in orders.copy()]
for a in engines:
 for b in engines:
  if a!=b:assert sum(order.index(a)<order.index(b) for order in orders)==3
inputs={c:json.loads((R/'inputs'/(c+'.json')).read_text()) for c in cases}
for d in inputs.values():assert h(Path(d['path']))==d.get('sha256',d.get('source_sha256'))
state=power_state();assert state['source']=='AC',state
D=R/'measurement';D.mkdir(exist_ok=False)
criteria={'correctness':'All output hashes, types and null counts must pass; all worker failures retained.','dates':'Distinct-date candidate CPU must improve in every paired round, with no result cache.','controls':'Review any median CPU regression above10percent in text/numeric controls; do not silently waive it.','memory':'Review any candidate median held RSS growth above baseline by5percent plus8MiB. RSS not allocation count.','scope':'These review thresholds were recorded before timing. No universal weighted score, no full application-capacity claim.'}
plan={'builds':builds,'cases':cases,'engines':engines,'orders':orders,'rounds':6,'reads_per_fresh_process':1,'inputs':inputs,'criteria':criteria,'power_start':state,'environment':environment(),'execution_policy':policy(PRODUCTION_MODE),'controller_sha256':h(Path(__file__)),'python_worker_sha256':h(R/'python-probe.py'),'native_harness_sha256':h(R/'ResourceProbe.swift'),'scope':'One eager materialized public read and release, validation excluded, memory before validation. OSinput pre-read outside each round. CPU backend/native parallelism. No concurrent builds/tests by this task; unrelated user workflows continue.'}
(D/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
with (D/'workers.jsonl').open('x') as out:
 for case in cases:
  for rnd,order in enumerate(orders):
   power=power_state();assert power['source']=='AC',power
   with Path(inputs[case]['path']).open('rb') as f:
    while f.read(1024*1024):pass
   for position,engine in enumerate(order):
    cmd=[str(R/'build'/engine/'ResourceProbe'),str(R/'inputs'/(case+'.json')),'known','fresh','1'] if engine in builds else [P,str(R/'python-probe.py'),engine,str(R/'inputs'/(case+'.json'))]
    started=time.time();p=subprocess.run(cmd,env=worker_environment(PRODUCTION_MODE),capture_output=True,text=True,timeout=300)
    (D/(case+'-'+str(rnd)+'-'+engine+'.stderr')).write_text(p.stderr)
    if p.returncode:
     out.write(json.dumps({'case':case,'round':rnd,'engine':engine,'failed':True,'exit_code':p.returncode,'stderr':p.stderr})+'\n');out.flush();raise RuntimeError((case,engine,p.stderr[-800:]))
    d=json.loads(p.stdout);assert d['validated'] and d['checks']['passed'],d
    assert [c['sha256'] for c in d['checks']['columns']]==inputs[case]['hashes']
    assert [c['nulls'] for c in d['checks']['columns']]==inputs[case]['null_counts']
    assert len(d['samples'])==1
    d.update(case=case,engine=engine,round=rnd,position=position,power=power,process_seconds=time.time()-started)
    out.write(json.dumps(d)+'\n');out.flush()
    sample=d['samples'][0];print(case,rnd,engine,round(sample['total_cpu_ns']/1e6,3),'CPUms',round(sample['total_ns']/1e6,3),'elapsedms',flush=True)
end=power_state();assert end['source']=='AC';(D/'power-end.json').write_text(json.dumps(end,indent=2)+'\n')
print('Complete240validatedworkers',flush=True)
