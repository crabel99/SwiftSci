import json,hashlib,struct,subprocess,sys
from pathlib import Path
root=Path('/Users/crabel/Documents/src/SwiftSci');base=root/'Benchmarks/Runs/suite-classification-01';out=Path('/private/tmp/swiftsci-suite-classification/negative-workers');out.mkdir(exist_ok=True)
sys.path.insert(0,str(root/'Benchmarks/Tools'))
from build_supervised_fixtures import reference
import mpmath as mp
mp.mp.dps=80
commands={'swiftsci':['/Users/crabel/Library/Caches/SwiftSci/standardized-benchmarks/derived/Build/Products/Release/SwiftSciBenchmarkWorker'],'pandas':[str(root/'Benchmarks/.venv-standardized/bin/python'),str(root/'Benchmarks/Python/standard_worker.py')]}
results=[]
for epochs in (0,1,32):
 case=f'wdbc-supervised-logistic-cpu-epochs{epochs}'
 request=json.loads((base/(case+'-swiftsci-0.request.json')).read_text())
 for variant in ['control','wrong-probability','wrong-label','wrong-score','bad-training','single-class','leaked-answer','heldout-labels']:
  req=dict(request);p=json.loads(Path(req['input_path']).read_text());n=len(p['features']);width=len(p['feature_names'])
  if variant.startswith('wrong-'):
   b=Path(req['expected_path']).read_bytes();v=list(struct.unpack('<'+'d'*(len(b)//8),b))
   index={'wrong-probability':3*width+2*n,'wrong-label':3*width+3*n,'wrong-score':len(v)-1}[variant]
   v[index]=1-v[index] if variant=='wrong-label' else v[index]+.25
   b=struct.pack('<'+'d'*len(v),*v);path=out/(case+'-'+variant+'.f64');path.write_bytes(b);req.update(expected_path=str(path),expected_sha256=hashlib.sha256(b).hexdigest())
  elif variant!='control':
   if variant=='bad-training':p['training']['learning_rate']=.1
   elif variant=='single-class':
    for i in p['splits']['test']:p['targets'][i]=0
   elif variant=='leaked-answer':p['training']['expected_weights']=[0]
   else:
    original=reference(p)
    for k in ('validation','test'):
     for i in p['splits'][k]:p['targets'][i]=1-p['targets'][i]
    values=reference(p);assert original[:-44]==values[:-44]
    b=struct.pack('<'+'d'*len(values),*map(float,values));path=out/(case+'-'+variant+'.f64');path.write_bytes(b);req.update(expected_path=str(path),expected_sha256=hashlib.sha256(b).hexdigest())
   b=(json.dumps(p)+'\n').encode();path=out/(case+'-'+variant+'.json');path.write_bytes(b);req.update(input_path=str(path),input_sha256=hashlib.sha256(b).hexdigest(),input_bytes=len(b))
  for engine,command in commands.items():
   path=out/(case+'-'+variant+'-'+engine+'.request.json');path.write_text(json.dumps(req));response=path.with_suffix('.response.json')
   run=subprocess.run(command+[str(path),str(response)],capture_output=True,text=True,timeout=120);r=json.loads(response.read_text())
   assert (r['status']=='passed')==(variant in ('control','heldout-labels')),(case,variant,engine,r)
   results.append(dict(case=case,variant=variant,engine=engine,exit_code=run.returncode,status=r['status'],error=r.get('error')))
(out/'summary.json').write_text(json.dumps(results,indent=2)+'\n');print('PASS: 6 controls, 6 held-out label changes, and 36 intentional failures behaved correctly')
