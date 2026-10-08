from pathlib import Path
import sys,subprocess,os,json
root=Path('/Users/LOCAL_USER/Library/Caches/SwiftSci/retained-gpu-trial-20261007');out=Path('/Users/LOCAL_USER/local-ai/spl/swiftsci/cpu-gpu-closeout-20261007')
sys.path[:0]=[str(out/'comparison-controllers'),str(root/'Benchmarks/Tools')]
from compare_gpu_pipeline_service import IMPUTER_CASES,validate
from profile_gpu_residency import owned_worker
from contracts import require,write_json
worker=Path('/Users/LOCAL_USER/Library/Caches/SwiftSci/unified-memory-prototype/derived/Build/Products/Release/SwiftSciPreparedMemoryQualification')
folder=out/'source-integrity';folder.mkdir(exist_ok=False);results=[]
for case,(schedule,rows,columns,_) in IMPUTER_CASES.items():
 for storage in ['copy','owned']:
  require(int(subprocess.check_output(['sysctl','-n','kern.memorystatus_vm_pressure_level'],text=True))==1,'Memory pressure')
  cmd=[str(worker),'pipeline-service',storage,schedule,str(rows),str(columns),'8','imputer-minmax','verify-source']
  stem=case+'-'+storage
  with (folder/(stem+'.json')).open('w') as stdout,(folder/(stem+'.stderr')).open('w') as stderr:
   with owned_worker(cmd,stdout=stdout,stderr=stderr) as p:require(p.wait(timeout=180)==0,'Source worker failed')
  record=json.loads((folder/(stem+'.json')).read_text());validate(record,storage,schedule,rows,columns,8,'imputer-minmax',True)
  results.append({'case':case,'storage':storage,'requests':8,'source_checks':record['source_checks']})
write_json(folder/'validation.json',{'workers':len(results),'requests':sum(r['requests'] for r in results),'source_checks':sum(r['source_checks'] for r in results),'results':results})
print('Passed',len(results),'source-integrity workers')
