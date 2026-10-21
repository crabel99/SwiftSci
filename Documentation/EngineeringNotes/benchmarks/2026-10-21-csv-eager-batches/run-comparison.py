from pathlib import Path
import hashlib,json,subprocess,sys,time
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-scoped-simd-20261021');sys.path.insert(0,str(S/'Benchmarks/Tools'))
from execution_policy import worker_environment,PRODUCTION_MODE,policy
from runner import environment,power_state,verify_uninstrumented
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
cases=[('bike-day','known'),('bike-hour','known'),('unique-shuffled','known'),('Aotizhongxin','known'),('energy','known'),('energy','infer'),('energy-date-full','known'),('late-bool','infer'),('late-text','infer')]
engines=['indexed','eager'];builds={}
for label in engines:
 d=R/'build'/label;record=json.loads((d/'build.json').read_text());assert h(d/'ResourceProbe')==record['binary_sha256'];verify_uninstrumented(d/'ResourceProbe')
 source=Path(record['variant']['path']);assert not subprocess.check_output(['git','status','--porcelain'],cwd=source)
 for rel,digest in record['sources'].items():assert h(source/rel)==digest
 builds[label]={'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip(),'binary_sha256':record['binary_sha256'],'build_receipt_sha256':h(d/'build.json')}
inputs={case:json.loads((R/'inputs'/(case+'.json')).read_text()) for case,mode in cases}
for d in inputs.values():assert h(Path(d['path']))==d.get('sha256',d.get('source_sha256'))
D=R/'bounded-measurement';D.mkdir(exist_ok=False);power=power_state();assert power['source']=='AC',power
plan=dict(builds=builds,inputs=inputs,cases=cases,engines=engines,rounds=6,orders=[engines,engines[::-1]]*3,power_start=power,environment=environment(),policy=policy(PRODUCTION_MODE),controller_sha256=h(Path(__file__)),harness_sha256=h(R/'ResourceProbe.swift'),criteria={'correctness':'Every worker validates every native value/null/type/order; failure invalidates timing.','cpu':'Review median CPU increases greater than10percent on any case; no weighted aggregate hides regressions.','memory':'Compare full eager peak and held RSS, not streaming against materialization. Review increases above5percent+8MiB.','scope':'Fresh processes, warm OS input, CPU backend with native parallelism, AC, no concurrent task builds/tests, no outlier trimming; no energy/allocation-count claim.'})
(D/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
with (D/'workers.jsonl').open('x') as out:
 for case,mode in cases:
  for rnd,order in enumerate(plan['orders']):
   power=power_state();assert power['source']=='AC',power
   with Path(inputs[case]['path']).open('rb') as f:
    while f.read(1024*1024):pass
   for label in order:
    p=subprocess.run([str(R/'build'/label/'ResourceProbe'),str(R/'inputs'/(case+'.json')),mode,'fresh','1'],env=worker_environment(PRODUCTION_MODE),capture_output=True,text=True,timeout=120)
    (D/(case+'-'+mode+'-'+str(rnd)+'-'+label+'.stderr')).write_text(p.stderr)
    if p.returncode:
     out.write(json.dumps(dict(case=case,mode=mode,engine=label,round=rnd,failed=True,exit_code=p.returncode,stderr=p.stderr))+'\n');out.flush();raise RuntimeError(p.stderr)
    d=json.loads(p.stdout);assert d['validated'],d
    assert [x['nulls'] for x in d['checks']['columns']]==inputs[case]['null_counts']
    d.update(case=case,engine=label,mode=mode,round=rnd,power=power)
    out.write(json.dumps(d)+'\n');out.flush();s=d['samples'][0]
    print(case,mode,rnd,label,round(s['total_cpu_ns']/1e6,3),'CPUms',round(s['process_peak_held_bytes']/2**20,3),'peakMiB',flush=True)
end=power_state();assert end['source']=='AC';(D/'power-end.json').write_text(json.dumps(end,indent=2)+'\n');print('Complete108validatedworkers',flush=True)
