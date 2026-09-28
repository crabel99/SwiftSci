import hashlib,json,struct,subprocess,sys
from pathlib import Path
root=Path('/Users/LOCAL_USER/Documents/src/SwiftSci');out=Path('/private/tmp/swiftsci-suite-neural/rope-isolation');out.mkdir(exist_ok=True)
sys.path.insert(0,str(root/'Benchmarks/Tools'))
from neural_reference import reference
original=json.loads((root/'Benchmarks/Runs/suite-neural-01/neural-gpu-rope-cached-swiftsci-0.request.json').read_text())
base=json.loads(Path(original['input_path']).read_text());records=[]
for name,device,execution,tokens in [('gpu-cached-batch2','gpu','cached',base['tokens']),('gpu-cached-first-batch','gpu','cached',base['tokens'][:1]),('gpu-cached-second-batch','gpu','cached',base['tokens'][1:]),('cpu-cached-batch2','cpu','cached',base['tokens']),('gpu-full-batch2','gpu','full',base['tokens'])]:
 p=dict(base,device=device,execution=execution,tokens=tokens);raw=(json.dumps(p)+'\n').encode();path=out/(name+'.input.json');path.write_bytes(raw)
 gold=reference(p);binary=struct.pack('<'+'d'*len(gold),*gold);expected=out/(name+'.expected.f64');expected.write_bytes(binary)
 req=dict(original,input_path=str(path),input_sha256=hashlib.sha256(raw).hexdigest(),input_bytes=len(raw),rows=sum(map(len,tokens)),expected_path=str(expected),expected_sha256=hashlib.sha256(binary).hexdigest())
 for repeat in range(3):
  request=out/(name+f'-{repeat}.request.json');request.write_text(json.dumps(req));response=request.with_suffix('.response.json')
  proc=subprocess.run(['/Users/LOCAL_USER/Library/Caches/SwiftSci/standardized-benchmarks/derived/Build/Products/Release/SwiftSciBenchmarkWorker',str(request),str(response)],capture_output=True,text=True,timeout=120)
  r=json.loads(response.read_text());records.append(dict(name=name,repeat=repeat,status=r['status'],error=r.get('error'),exit_code=proc.returncode))
(out/'summary.json').write_text(json.dumps(records,indent=2)+'\n');print(json.dumps(records,indent=2))
