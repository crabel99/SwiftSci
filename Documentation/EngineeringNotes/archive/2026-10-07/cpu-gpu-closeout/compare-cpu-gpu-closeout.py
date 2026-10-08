from pathlib import Path
import subprocess,sys,json,os,hashlib,statistics
root=Path('/Users/LOCAL_USER/Library/Caches/SwiftSci/retained-gpu-trial-20261007')
out=Path('/Users/LOCAL_USER/local-ai/spl/swiftsci/cpu-gpu-closeout-20261007')
controllers=out/'comparison-controllers';controllers.mkdir(exist_ok=True)
for name in ['compare_gpu_device_reuse.py','compare_gpu_pipeline_service.py','compare_gpu_budget_workflow.py','profile_gpu_residency.py']:
 (controllers/name).write_bytes(subprocess.check_output(['git','show','main:Benchmarks/Tools/'+name],cwd=root))
sys.path[:0]=[str(controllers),str(root/'Benchmarks/Tools')]
from compare_gpu_device_reuse import compare_records
from compare_gpu_pipeline_service import IMPUTER_CASES,validate
from profile_gpu_residency import owned_worker
from runner import verify_uninstrumented
from contracts import require,write_json
products=Path('/Users/LOCAL_USER/Library/Caches/SwiftSci/unified-memory-prototype/derived/Build/Products/Release')
workers={'baseline':products/'SwiftSciRetainedGPUTrial-closeout-reference','candidate':products/'SwiftSciPreparedMemoryQualification'}
digests={k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in workers.items()}
require(digests['baseline']=='fa97a6195dd9cd150435938826a3204fc90771faaa6caa9cae7ed5aa22952211','Preserved trial differs')
for p in workers.values():verify_uninstrumented(p)
result=out/'comparison';result.mkdir(exist_ok=False)
write_json(result/'provenance.json',{'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'binary_sha256':digests,'worker_sources':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (out/'qualification-sources').glob('*.swift')},'cases':IMPUTER_CASES,'rounds':3,'baseline':'5fa86f9f75 measured trial executable','candidate':'production-only extraction with public workflow copied unchanged and unused trial helpers removed','timing':'Full admitted request windows; fitting, warmup and final cleanup excluded. Not a claim of equivalence for untested workflows.'})
pairs=[];summaries=[];references={};parameters={};env=dict(os.environ);env.pop('SWIFTSCI_RESIDENCY_DIR',None)
for iteration in range(3):
 cases=list(IMPUTER_CASES);cases=cases if iteration%2==0 else list(reversed(cases))
 for ci,case in enumerate(cases):
  schedule,rows,columns,requests=IMPUTER_CASES[case]
  for si,storage in enumerate(['copy','owned'] if iteration%2==0 else ['owned','copy']):
   records={}
   for name in (['baseline','candidate'] if (iteration+ci+si)%2==0 else ['candidate','baseline']):
    require(int(subprocess.check_output(['sysctl','-n','kern.memorystatus_vm_pressure_level'],text=True))==1,'Elevated memory pressure')
    stem=f'{iteration}-{case}-{storage}-{name}'
    cmd=[str(workers[name]),'pipeline-service',storage,schedule,str(rows),str(columns),str(requests),'imputer-minmax']
    write_json(result/(stem+'-command.json'),cmd)
    with (result/(stem+'.json')).open('w') as stdout,(result/(stem+'.stderr')).open('w') as stderr:
     with owned_worker(cmd,stdout=stdout,stderr=stderr,env=env) as child:require(child.wait(timeout=180)==0,'Worker failed '+stem)
    record=json.loads((result/(stem+'.json')).read_text());hashes=validate(record,storage,schedule,rows,columns,requests,'imputer-minmax')
    require(case not in references or references[case]==hashes,'Outputs differ across ownership or rounds')
    require(case not in parameters or parameters[case]==record['parameters_sha256'],'Fitted parameters differ')
    references[case]=hashes;parameters[case]=record['parameters_sha256'];records[name]=record
    summaries.append({'round':iteration,'case':case,'storage':storage,'binary':name,'requests_per_second':record['requests_per_second'],'elapsed_ms':record['elapsed_ms'],'measured_rss_mib':record['measured']['rss_bytes']/1024**2})
    write_json(result/'summary.json',summaries);print('Passed',stem,flush=True)
   pairs.append({'round':iteration,'case':case,'storage':storage,**compare_records(records['baseline'],records['candidate'],storage,case)})
   write_json(result/'paired.json',pairs)
print('Passed 48 public pipeline workers',flush=True)
