import copy,json,hashlib,struct,subprocess,sys
from pathlib import Path
root=Path('/Users/LOCAL_USER/Documents/src/SwiftSci');base=root/'Benchmarks/Runs/suite-supervised-01';out=Path('/private/tmp/swiftsci-suite-stage4/negative-workers');out.mkdir(exist_ok=True)
sys.path.insert(0,str(root/'Benchmarks/Tools'))
from build_supervised_fixtures import reference
import mpmath as mp
mp.mp.dps=80
commands={'swiftsci':['/Users/LOCAL_USER/Library/Caches/SwiftSci/standardized-benchmarks/derived/Build/Products/Release/SwiftSciBenchmarkWorker'],'pandas':[str(root/'Benchmarks/.venv-standardized/bin/python'),str(root/'Benchmarks/Python/standard_worker.py')]}
results=[]
for case in ['wine-red-supervised-scale','wine-red-supervised-ols-cpu','wdbc-supervised-scale']:
 request=json.loads((base/(case+'-swiftsci-0.request.json')).read_text())
 for variant in ['control','wrong-output','overlap','duplicate-feature','leaked-answer','heldout-perturbation']:
  req=dict(request);p=json.loads(Path(req['input_path']).read_text())
  if variant=='wrong-output':
   b=Path(req['expected_path']).read_bytes();v=list(struct.unpack('<'+'d'*(len(b)//8),b));v[-1]+=1
   b=struct.pack('<'+'d'*len(v),*v);path=out/(case+'-'+variant+'.f64');path.write_bytes(b);req.update(expected_path=str(path),expected_sha256=hashlib.sha256(b).hexdigest())
  elif variant!='control':
   if variant=='leaked-answer':p['expected']=[1]
   elif variant=='overlap':p['splits']['test'][0]=p['splits']['train'][0]
   elif variant=='duplicate-feature':p['features'][p['splits']['test'][0]]=p['features'][p['splits']['train'][0]].copy()
   else:
    original=reference(p)
    for name in ('validation','test'):
     for i in p['splits'][name]:p['features'][i]=[v+1000 for v in p['features'][i]];p['targets'][i]+=10000
    values=reference(p);width=len(p['feature_names']);ntrain=len(p['splits']['train'])
    prefix=2*width+ntrain*width if p['operation']=='supervised-scale' else 3*width+1+ntrain
    assert original[:prefix]==values[:prefix]
    b=struct.pack('<'+'d'*len(values),*map(float,values));path=out/(case+'-'+variant+'.f64');path.write_bytes(b);req.update(expected_path=str(path),expected_sha256=hashlib.sha256(b).hexdigest())
   b=(json.dumps(p)+'\n').encode();path=out/(case+'-'+variant+'.json');path.write_bytes(b);req.update(input_path=str(path),input_sha256=hashlib.sha256(b).hexdigest(),input_bytes=len(b))
  for engine,command in commands.items():
   path=out/(case+'-'+variant+'-'+engine+'.request.json');path.write_text(json.dumps(req));response=path.with_suffix('.response.json')
   run=subprocess.run(command+[str(path),str(response)],capture_output=True,text=True,timeout=120);r=json.loads(response.read_text())
   assert (r['status']=='passed')==(variant in ('control','heldout-perturbation')),(case,variant,engine,r)
   results.append(dict(case=case,variant=variant,engine=engine,exit_code=run.returncode,status=r['status'],error=r.get('error')))
(out/'summary.json').write_text(json.dumps(results,indent=2)+'\n');print('PASS: 6 controls, 6 held-out perturbations, and 24 intentional failures behaved correctly')
