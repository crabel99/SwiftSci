from pathlib import Path
import json,subprocess,sys
root=Path('/Users/crabel/Library/Caches/SwiftSci/retained-gpu-trial-20261007')
out=Path('/Users/crabel/local-ai/spl/swiftsci/gpu-consuming-scaler-20261007')
worker=Path('/Users/crabel/Library/Caches/SwiftSci/unified-memory-prototype/derived/Build/Products/Release/SwiftSciRetainedGPUTrial')
sys.path.insert(0,str(root/'Benchmarks/Tools'))
from profile_gpu_residency import owned_worker
sys.path.insert(0,"/Users/crabel/Library/Caches/SwiftSci/prepared-memory-integration-20261006-qualification/Benchmarks/UnifiedMemoryPrototype")
from processes import run_process
with (out/'owned-check.stdout').open('w') as stdout,(out/'owned-check.stderr').open('w') as stderr:
 with owned_worker([str(worker),'owned-transform-check'],stdout=stdout,stderr=stderr) as p:
  code=p.wait(timeout=120)
assert code==0
print((out/'owned-check.stdout').read_text(),flush=True)
with (out/'controller-tests.log').open('w') as log:
 p=run_process([sys.executable,'-m','unittest','discover','-s','Benchmarks/Tests','-p','test_gpu_*.py'],cwd=root,stdout=log,stderr=subprocess.STDOUT,timeout=120)
assert p.returncode==0
print('Controller tests passed',flush=True)
cmd=[sys.executable,'Benchmarks/Tools/compare_gpu_memory_reuse.py','--worker',str(worker),'--output',str(out/'comparison'),'--rounds','2','--bursts','32','--storage','copy','owned']
(out/'comparison-command.json').write_text(json.dumps(cmd,indent=2)+'\n')
with (out/'comparison.log').open('w') as log:
 p=run_process(cmd,cwd=root,stdout=log,stderr=subprocess.STDOUT,timeout=1200)
assert p.returncode==0
print('Matched comparison passed',flush=True)
cmd=[sys.executable,'Benchmarks/Tools/compare_gpu_budget_workflow.py','--worker',str(worker),'--output',str(out/'original-mode'),'--rows','65535','65536','--columns','65','--limits-mib','256','--rounds','1','--requests','8']
(out/'original-mode-command.json').write_text(json.dumps(cmd,indent=2)+'\n')
with (out/'original-mode.log').open('w') as log:
 p=run_process(cmd,cwd=root,stdout=log,stderr=subprocess.STDOUT,timeout=180)
assert p.returncode==0
print('Original mode passed',flush=True)
