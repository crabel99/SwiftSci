import json, hashlib, struct, subprocess
from pathlib import Path
root=Path('/Users/crabel/Documents/src/SwiftSci')
base=root/'Benchmarks/Runs/strategy-nist-decimal-01'
out=Path('/private/tmp/swiftsci-strategy/negative-workers');out.mkdir(exist_ok=True)
request=json.loads((base/'nist-norris-decimal-swiftsci-0.request.json').read_text())
commands={'swiftsci':['/Users/crabel/Library/Caches/SwiftSci/standardized-benchmarks/derived/Build/Products/Release/SwiftSciBenchmarkWorker'],'pandas':[str(root/'Benchmarks/.venv-standardized/bin/python'),str(root/'Benchmarks/Python/standard_worker.py')]}
results=[]
for variant in ['control','wrong-final-prediction','ragged','boolean','extra-field']:
 req=dict(request)
 if variant=='wrong-final-prediction':
  b=Path(req['expected_path']).read_bytes();v=list(struct.unpack('<'+'d'*(len(b)//8),b));v[-1]+=100
  b=struct.pack('<'+'d'*len(v),*v);path=out/(variant+'.f64');path.write_bytes(b);req.update(expected_path=str(path),expected_sha256=hashlib.sha256(b).hexdigest())
 elif variant!='control':
  data=json.loads(Path(req['input_path']).read_text())
  if variant=='ragged':data['features'][0].append(1)
  if variant=='boolean':data['features'][0][0]=True
  if variant=='extra-field':data['expected_values']=[0,1]
  b=(json.dumps(data)+'\n').encode();path=out/(variant+'.json');path.write_bytes(b);req.update(input_path=str(path),input_sha256=hashlib.sha256(b).hexdigest(),input_bytes=len(b))
 for engine,command in commands.items():
  p=out/(variant+'-'+engine+'.request.json');p.write_text(json.dumps(req));response=out/(variant+'-'+engine+'.response.json')
  run=subprocess.run(command+[str(p),str(response)],capture_output=True,text=True,timeout=120)
  result=json.loads(response.read_text());passed=result['status']=='passed'
  assert passed==(variant=='control'),(variant,engine,result)
  results.append(dict(variant=variant,engine=engine,exit_code=run.returncode,status=result['status'],error=result.get('error')))
(out/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
