from pathlib import Path
import sys,json,subprocess,hashlib
root=Path('/Users/crabel/Library/Caches/SwiftSci/retained-gpu-trial-20261007');out=Path('/Users/crabel/local-ai/spl/swiftsci/imputed-regression-20261007/source-verification');out.mkdir(exist_ok=False)
worker=Path('/Users/crabel/Library/Caches/SwiftSci/unified-memory-prototype/derived/Build/Products/Release/SwiftSciRetainedGPUTrial')
sys.path.insert(0,str(root/'Benchmarks/Tools'))
from runner import verify_uninstrumented
from profile_gpu_residency import owned_worker
from compare_gpu_pipeline_service import validate,IMPUTER_CASES
verify_uninstrumented(worker)
results=[]
for case,(schedule,rows,columns,_) in IMPUTER_CASES.items():
 expected=None
 for storage in ['copy','owned']:
  assert int(subprocess.check_output(['sysctl','-n','kern.memorystatus_vm_pressure_level']))==1
  stem=f'{case}-{storage}'
  command=[str(worker),'pipeline-service',storage,schedule,str(rows),str(columns),'8','imputer-minmax','verify-source']
  (out/(stem+'-command.json')).write_text(json.dumps(command,indent=2)+'\n')
  with (out/(stem+'.json')).open('w') as stdout,(out/(stem+'.stderr')).open('w') as stderr:
   with owned_worker(command,stdout=stdout,stderr=stderr) as p:assert p.wait(timeout=120)==0,stem
  record=json.loads((out/(stem+'.json')).read_text());digest=validate(record,storage,schedule,rows,columns,8,'imputer-minmax',verify_source=True)
  if expected is not None:assert digest==expected
  expected=digest
  results.append({'case':case,'storage':storage,'source_checks':record['source_checks'],'requests':8})
  print('Passed',stem,flush=True)
(out/'validation.json').write_text(json.dumps({'binary_sha256':hashlib.sha256(worker.read_bytes()).hexdigest(),'complete':True,'results':results},indent=2)+'\n')
print('All source integrity, predictions, consumed addresses and lifecycle checks pass.')
