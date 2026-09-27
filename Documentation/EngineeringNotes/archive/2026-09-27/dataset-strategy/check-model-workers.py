import json, hashlib, struct, subprocess
from pathlib import Path
root=Path('/Users/crabel/Documents/src/SwiftSci');base=root/'Benchmarks/Runs/strategy-models-01';out=Path('/private/tmp/swiftsci-strategy/model-negative-workers');out.mkdir(exist_ok=True)
commands={'swiftsci':['/Users/crabel/Library/Caches/SwiftSci/standardized-benchmarks/derived/Build/Products/Release/SwiftSciBenchmarkWorker'],'pandas':[str(root/'Benchmarks/.venv-standardized/bin/python'),str(root/'Benchmarks/Python/standard_worker.py')]}
results=[]
for case in ['pca-oblique-k2','multinomial-nb-noncontiguous']:
 request=json.loads((base/(case+'-swiftsci-0.request.json')).read_text())
 for variant in ['control','wrong-output','malformed-input']:
  req=dict(request)
  if variant=='wrong-output':
   b=Path(req['expected_path']).read_bytes();v=list(struct.unpack('<'+'d'*(len(b)//8),b))
   if case.startswith('pca'):
    # Negate only cross-Gram. Training/query self-Grams and component projectors stay valid.
    v[-12:]=[-x for x in v[-12:]]
   else:v[-1]=1
   b=struct.pack('<'+'d'*len(v),*v);path=out/(case+'-'+variant+'.f64');path.write_bytes(b);req.update(expected_path=str(path),expected_sha256=hashlib.sha256(b).hexdigest())
  elif variant=='malformed-input':
   data=json.loads(Path(req['input_path']).read_text())
   if case.startswith('pca'):data['query'][0].append(1)
   else:data['features'][0][0]=-1
   b=(json.dumps(data)+'\n').encode();path=out/(case+'-'+variant+'.json');path.write_bytes(b);req.update(input_path=str(path),input_sha256=hashlib.sha256(b).hexdigest(),input_bytes=len(b))
  for engine,command in commands.items():
   p=out/(case+'-'+variant+'-'+engine+'.request.json');p.write_text(json.dumps(req));response=p.with_suffix('.response.json')
   run=subprocess.run(command+[str(p),str(response)],capture_output=True,text=True,timeout=120);result=json.loads(response.read_text());assert (result['status']=='passed')==(variant=='control'),result
   results.append(dict(case=case,variant=variant,engine=engine,exit_code=run.returncode,status=result['status'],error=result.get('error')))
(out/'summary.json').write_text(json.dumps(results,indent=2)+'\n');print('PASS: 4 controls and 8 intentional failures behaved correctly')
