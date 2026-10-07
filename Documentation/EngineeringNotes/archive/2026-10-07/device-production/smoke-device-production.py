from pathlib import Path
import sys,json,subprocess
root=Path('/Users/crabel/Library/Caches/SwiftSci/retained-gpu-trial-20261007');out=Path('/Users/crabel/local-ai/spl/swiftsci/device-production-20261007')
worker=Path('/Users/crabel/Library/Caches/SwiftSci/unified-memory-prototype/derived/Build/Products/Release/SwiftSciRetainedGPUTrial')
sys.path.insert(0,str(root/'Benchmarks/Tools'))
from runner import verify_uninstrumented
from profile_gpu_residency import owned_worker
from compare_gpu_pipeline_service import validate
verify_uninstrumented(worker)
for scaler,schedule,rows,columns in [('standard','fixed',64,3),('minmax','fixed',64,3),('imputer-minmax','fixed',64,3),('imputer-minmax','mixed',65536,65)]:
 expected=None
 for storage in ['copy','owned']:
  assert int(subprocess.check_output(['sysctl','-n','kern.memorystatus_vm_pressure_level']))==1
  stem=f'smoke-{scaler}-{schedule}-{storage}'
  command=[str(worker),'pipeline-service',storage,schedule,str(rows),str(columns),'4',scaler]
  (out/(stem+'-command.json')).write_text(json.dumps(command,indent=2)+'\n')
  with (out/(stem+'.json')).open('w') as stdout,(out/(stem+'.stderr')).open('w') as stderr:
   with owned_worker(command,stdout=stdout,stderr=stderr) as p:assert p.wait(timeout=120)==0,stem
  record=json.loads((out/(stem+'.json')).read_text());digest=validate(record,storage,schedule,rows,columns,4,scaler)
  parent=json.loads((out.parent/'imputed-regression-20261007'/(stem+'.json')).read_text())
  assert digest==validate(parent,storage,schedule,rows,columns,4,scaler), 'Parent pipeline hash mismatch'
  assert set(record['requests'][0])==set(parent['requests'][0]), 'Request JSON schema changed'
  if expected is not None:assert digest==expected
  expected=digest
  print('Passed',stem,flush=True)
print('All smoke predictions and cleanup checks pass.')
