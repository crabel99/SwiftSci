import copy,hashlib,json,struct,subprocess,sys
from pathlib import Path
root=Path('/Users/crabel/Documents/src/SwiftSci');run_dir=root/'Benchmarks/Runs/suite-neural-03';out=Path('/private/tmp/swiftsci-suite-neural/negative-workers');out.mkdir(exist_ok=True)
sys.path.insert(0,str(root/'Benchmarks/Tools'))
from neural_reference import reference
commands={'swiftsci':['/Users/crabel/Library/Caches/SwiftSci/standardized-benchmarks/derived/Build/Products/Release/SwiftSciBenchmarkWorker'],'pandas':[str(root/'Benchmarks/.venv-standardized/bin/python'),str(root/'Benchmarks/Python/standard_worker.py')]}
cases=['neural-cpu-learned-full','neural-cpu-rope-cached','neural-gpu-learned-cached','neural-gpu-rope-full']
records=[]
for case in cases:
 original=json.loads((run_dir/(case+'-swiftsci-0.request.json')).read_text())
 for variant in ('control','wrong-first-logit','wrong-last-logit','bad-token','float-token','bad-weight-shape','inexact-weight','changed-weight','future-token'):
  req=dict(original);p=json.loads(Path(req['input_path']).read_text())
  if variant.startswith('wrong-'):
   raw=Path(req['expected_path']).read_bytes();values=list(struct.unpack('<'+'d'*(len(raw)//8),raw));index=3 if variant=='wrong-first-logit' else 3+sum(map(len,p['tokens']))*7-1;values[index]+=.01
   raw=struct.pack('<'+'d'*len(values),*values);path=out/(case+'-'+variant+'.f64');path.write_bytes(raw);req.update(expected_path=str(path),expected_sha256=hashlib.sha256(raw).hexdigest())
  elif variant!='control':
   if variant=='bad-token':p['tokens'][0][0]=7
   elif variant=='float-token':p['tokens'][0][0]=1.0
   elif variant=='bad-weight-shape':p['weights']['lmHead.weight']['shape']=[8,7]
   elif variant=='inexact-weight':p['weights']['lmHead.weight']['values'][0]=.1
   elif variant=='changed-weight':p['weights']['lmHead.weight']['values']=[v+.125 for v in p['weights']['lmHead.weight']['values']]
   else:
    before=reference(p)
    for tokens in p['tokens']:tokens[-1]=(tokens[-1]+1)%7
    values=reference(p)
    for batch in range(2):
     start=3+batch*28;assert before[start:start+21]==values[start:start+21]
    assert before!=values
    raw=struct.pack('<'+'d'*len(values),*values);path=out/(case+'-'+variant+'.f64');path.write_bytes(raw);req.update(expected_path=str(path),expected_sha256=hashlib.sha256(raw).hexdigest())
   raw=(json.dumps(p)+'\n').encode();path=out/(case+'-'+variant+'.json');path.write_bytes(raw);req.update(input_path=str(path),input_sha256=hashlib.sha256(raw).hexdigest(),input_bytes=len(raw))
  for engine,command in commands.items():
   path=out/(case+'-'+variant+'-'+engine+'.request.json');path.write_text(json.dumps(req));response=path.with_suffix('.response.json')
   proc=subprocess.run(command+[str(path),str(response)],capture_output=True,text=True,timeout=120)
   r=json.loads(response.read_text());assert (r['status']=='passed')==(variant in ('control','future-token')),(case,variant,engine,r)
   records.append({'case':case,'variant':variant,'engine':engine,'status':r['status'],'exit_code':proc.returncode,'error':r.get('error')})
(out/'summary.json').write_text(json.dumps(records,indent=2)+'\n');print('PASS: 8 controls and 8 future-token cases passed; 56 wrong-input/output cases rejected')
