from pathlib import Path
import sys,json,subprocess
root=Path('/Users/crabel/Library/Caches/SwiftSci/retained-gpu-trial-20261007')
out=Path('/Users/crabel/local-ai/spl/swiftsci/gpu-consuming-pipeline-20261007')
worker=Path('/Users/crabel/Library/Caches/SwiftSci/unified-memory-prototype/derived/Build/Products/Release/SwiftSciRetainedGPUTrial')
sys.path.insert(0,str(root/'Benchmarks/Tools'))
from profile_gpu_residency import owned_worker
from compare_gpu_pipeline_service import validate
sys.path.insert(0,'/Users/crabel/Library/Caches/SwiftSci/prepared-memory-integration-20261006-qualification/Benchmarks/UnifiedMemoryPrototype')
from processes import run_process
hashes=None
for mode in ['copy','owned']:
 with (out/f'sustained-smoke-{mode}.json').open('w') as stdout,(out/f'sustained-smoke-{mode}.stderr').open('w') as stderr:
  with owned_worker([str(worker),'pipeline-service',mode,'fixed','64','3','8'],stdout=stdout,stderr=stderr) as p:
   assert p.wait(timeout=120)==0
 record=json.loads((out/f'sustained-smoke-{mode}.json').read_text());actual=validate(record,mode,'fixed',64,3,8)
 if hashes is not None:assert hashes==actual
 hashes=actual
print('Smoke passed',flush=True)
cmd=[sys.executable,'Benchmarks/Tools/compare_gpu_pipeline_service.py','--worker',str(worker),'--output',str(out/'sustained-comparison'),'--rounds','3']
(out/'sustained-comparison-command.json').write_text(json.dumps(cmd,indent=2)+'\n')
with (out/'sustained-comparison.log').open('w') as log:
 result=run_process(cmd,cwd=root,stdout=log,stderr=subprocess.STDOUT,timeout=1200)
assert result.returncode==0
print('Continuous pipeline comparison passed',flush=True)
