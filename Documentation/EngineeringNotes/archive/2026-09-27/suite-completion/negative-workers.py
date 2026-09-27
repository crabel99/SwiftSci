import copy,hashlib,json,struct,subprocess
from pathlib import Path
root=Path('/Users/crabel/Documents/src/SwiftSci');out=Path('/private/tmp/swiftsci-suite-finish/negative-workers');out.mkdir(exist_ok=True)
commands={'swiftsci':['/Users/crabel/Library/Caches/SwiftSci/standardized-benchmarks/derived/Build/Products/Release/SwiftSciBenchmarkWorker'],'pandas':[str(root/'Benchmarks/.venv-standardized/bin/python'),str(root/'Benchmarks/Python/standard_worker.py')]}
cases=[('finish-vision-01','vision-cpu-rgb-odd-identity'),('finish-vision-01','vision-cpu-rgb-up-asymmetric'),('finish-boundary-01','boundary-cpu-float64-narrow'),('finish-boundary-01','boundary-gpu-float32-wide'),('finish-acceptance-02/boundary-sweep','sweep-gpu-float32-128x8-prepared'),('finish-acceptance-02/boundary-sweep','sweep-cpu-float64-128x64-conversion')]
records=[]
for run,case in cases:
 original=json.loads((root/'Benchmarks/Runs'/run/(case+'-swiftsci-0.request.json')).read_text())
 for variant in ['control','wrong-first','wrong-middle','wrong-last','embedded-answer','bad-device','bad-shape']:
  request=copy.deepcopy(original)
  if variant.startswith('wrong-'):
   raw=Path(request['expected_path']).read_bytes();values=list(struct.unpack('<'+'d'*(len(raw)//8),raw))
   i=0 if variant=='wrong-first' else len(values)//2 if variant=='wrong-middle' else len(values)-1
   values[i]+=1;raw=struct.pack('<'+'d'*len(values),*values);path=out/(case+'-'+variant+'.f64');path.write_bytes(raw)
   request.update(expected_path=str(path),expected_sha256=hashlib.sha256(raw).hexdigest())
  elif variant!='control':
   p=json.loads(Path(request['input_path']).read_text())
   if variant=='embedded-answer':p['expected_values']=[1]
   elif variant=='bad-device':p['device']='auto'
   elif p['operation']=='vision-letterbox-cpu':p['width']=0
   elif p['operation']=='dataframe-model':p['features'][0].pop()
   else:p['columns']=7
   raw=(json.dumps(p)+'\n').encode();path=out/(case+'-'+variant+'.json');path.write_bytes(raw)
   request.update(input_path=str(path),input_sha256=hashlib.sha256(raw).hexdigest(),input_bytes=len(raw))
  for engine,command in commands.items():
   path=out/(case+'-'+variant+'-'+engine+'.request.json');path.write_text(json.dumps(request));response=path.with_suffix('.response.json')
   proc=subprocess.run(command+[str(path),str(response)],capture_output=True,text=True,timeout=120)
   result=json.loads(response.read_text());assert result['case_key']==request['case_key']
   assert result['status']==('passed' if variant=='control' else 'failed'),(case,variant,engine,result)
   assert proc.returncode==(0 if variant=='control' else 1),(case,variant,engine,proc.returncode)
   if variant!='control':assert result.get('error') and not result['samples']
   records.append(dict(case=case,variant=variant,engine=engine,status=result['status'],error=result.get('error')))
(out/'summary.json').write_text(json.dumps(records,indent=2)+'\n')
print('Verified 12 unchanged controls and 72 rejected malformed inputs or wrong answers.')
