from pathlib import Path
import sys,json,subprocess
root=Path('/Users/crabel/Library/Caches/SwiftSci/retained-gpu-trial-20261007')
out=Path('/Users/crabel/local-ai/spl/swiftsci/gpu-consuming-minmax-20261007')
worker=Path('/Users/crabel/Library/Caches/SwiftSci/unified-memory-prototype/derived/Build/Products/Release/SwiftSciRetainedGPUTrial')
sys.path.insert(0,str(root/'Benchmarks/Tools'))
from profile_gpu_residency import owned_worker
from compare_gpu_pipeline_service import validate
from runner import verify_uninstrumented
verify_uninstrumented(worker)
name=sys.argv[1];hashes=None
for mode in ['copy','owned']:
 with (out/f'{name}-smoke-{mode}.json').open('w') as stdout,(out/f'{name}-smoke-{mode}.stderr').open('w') as stderr:
  with owned_worker([str(worker),'pipeline-service',mode,'fixed','64','3','8','minmax'],stdout=stdout,stderr=stderr) as p:
   assert p.wait(timeout=120)==0
 record=json.loads((out/f'{name}-smoke-{mode}.json').read_text());actual=validate(record,mode,'fixed',64,3,8,'minmax')
 if hashes is not None:assert hashes==actual
 hashes=actual
print('Smoke passed',flush=True)
cmd=[sys.executable,'Benchmarks/Tools/compare_gpu_pipeline_service.py','--worker',str(worker),'--output',str(out/name),'--scaler','minmax','--rounds','3']
(out/(name+'-command.json')).write_text(json.dumps(cmd,indent=2)+'\n')
with (out/(name+'.log')).open('w') as log:
 with owned_worker(cmd,cwd=root,stdout=log,stderr=subprocess.STDOUT) as process:
  assert process.wait(timeout=1200)==0
print(name+' continuous comparison passed',flush=True)
