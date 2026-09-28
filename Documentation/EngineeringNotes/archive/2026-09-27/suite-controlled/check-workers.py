import json, hashlib, struct, subprocess
from pathlib import Path
root=Path('/Users/LOCAL_USER/Documents/src/SwiftSci');base=root/'Benchmarks/Runs/suite-controlled-01';out=Path('/private/tmp/swiftsci-suite-stage3/negative-workers');out.mkdir(exist_ok=True)
commands={'swiftsci':['/Users/LOCAL_USER/Library/Caches/SwiftSci/standardized-benchmarks/derived/Build/Products/Release/SwiftSciBenchmarkWorker'],'pandas':[str(root/'Benchmarks/.venv-standardized/bin/python'),str(root/'Benchmarks/Python/standard_worker.py')]}
results=[]
for case in ['controlled-kalman-scalar','controlled-kmeans-one-mean','controlled-cosine-distinct','controlled-kernel-interaction']:
 request=json.loads((base/(case+'-swiftsci-0.request.json')).read_text())
 for variant in ['control','wrong-output','malformed-input','leaked-answer']:
  req=dict(request)
  if variant=='wrong-output':
   b=Path(req['expected_path']).read_bytes();v=list(struct.unpack('<'+'d'*(len(b)//8),b))
   if 'kernel' in case: v[1]+=1;v[2]-=1 # Preserve additivity while making both contributions wrong.
   elif 'cosine' in case: v[0]=999 # Correct scores do not excuse a wrong result identity.
   else:v[-1]+=1 # Includes final predicted covariance or inertia.
   b=struct.pack('<'+'d'*len(v),*v);path=out/(case+'-'+variant+'.f64');path.write_bytes(b);req.update(expected_path=str(path),expected_sha256=hashlib.sha256(b).hexdigest())
  elif variant in ['malformed-input','leaked-answer']:
   data=json.loads(Path(req['input_path']).read_text())
   if variant=='leaked-answer':data['expected']=[0]
   elif 'kalman' in case:data['measurement_noise'][0][0]=-1
   elif 'kmeans' in case:data['n_clusters']=2
   elif 'cosine' in case:data['query']=[0]*len(data['query'])
   else:data['model']['weights'].append(1)
   b=(json.dumps(data)+'\n').encode();path=out/(case+'-'+variant+'.json');path.write_bytes(b);req.update(input_path=str(path),input_sha256=hashlib.sha256(b).hexdigest(),input_bytes=len(b))
  for engine,command in commands.items():
   p=out/(case+'-'+variant+'-'+engine+'.request.json');p.write_text(json.dumps(req));response=p.with_suffix('.response.json')
   run=subprocess.run(command+[str(p),str(response)],capture_output=True,text=True,timeout=120);result=json.loads(response.read_text());assert (result['status']=='passed')==(variant=='control'),result
   results.append(dict(case=case,variant=variant,engine=engine,exit_code=run.returncode,status=result['status'],error=result.get('error')))
(out/'summary.json').write_text(json.dumps(results,indent=2)+'\n');print('PASS: 8 controls and 24 intentional failures behaved correctly')
