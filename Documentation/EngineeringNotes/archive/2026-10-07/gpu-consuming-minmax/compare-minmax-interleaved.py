from pathlib import Path
import json,sys,hashlib,subprocess,os,statistics
root=Path('/Users/crabel/Library/Caches/SwiftSci/retained-gpu-trial-20261007');out=Path('/Users/crabel/local-ai/spl/swiftsci/gpu-consuming-minmax-20261007');dest=out/'interleaved'
workers={v:Path('/Users/crabel/Library/Caches/SwiftSci/unified-memory-prototype/derived/Build/Products/Release/SwiftSciRetainedGPUTrial-minmax-'+v) for v in ['baseline','candidate']}
sys.path.insert(0,str(root/'Benchmarks/Tools'))
from compare_gpu_pipeline_service import validate,CASES
from profile_gpu_residency import owned_worker
from runner import verify_uninstrumented
for w in workers.values():verify_uninstrumented(w)
assert hashlib.sha256(workers['candidate'].read_bytes()).hexdigest()==json.loads((out/'candidate/provenance.json').read_text())['binary_sha256']
dest.mkdir(exist_ok=False)
def save(name,value):(dest/name).write_text(json.dumps(value,indent=2)+'\n')
save('provenance.json',{'workers':{v:{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for v,p in workers.items()},'source_provenance':{v:json.loads((out/v/'provenance.json').read_text()) for v in workers},'baseline_build':'../control-release-command.json','candidate_build':'../final-release-command.json','cases':list(CASES),'rounds':3,'ordering':'Alternate baseline and candidate for each case and ownership mode. Reverse case, mode, and version order on middle round. Serial fresh processes.'})
summary=[]
env=dict(os.environ);env.pop('SWIFTSCI_RESIDENCY_DIR',None)
for iteration in range(3):
 for case in (list(CASES) if iteration%2==0 else list(reversed(CASES))):
  schedule,rows,columns,count=CASES[case]
  reference=json.loads((out/'baseline'/f'0-{case}-copy.json').read_text())
  hashes=tuple(x['outputSHA256'] for x in reference['requests'])
  for storage in (['copy','owned'] if iteration%2==0 else ['owned','copy']):
   for version in (['baseline','candidate'] if iteration%2==0 else ['candidate','baseline']):
    assert int(subprocess.check_output(['sysctl','-n','kern.memorystatus_vm_pressure_level'],text=True))==1
    stem=f'{iteration}-{case}-{storage}-{version}'
    cmd=[str(workers[version]),'pipeline-service',storage,schedule,str(rows),str(columns),str(count),'minmax']
    save(stem+'-command.json',cmd)
    load=os.getloadavg()
    with (dest/(stem+'.json')).open('w') as stdout,(dest/(stem+'.stderr')).open('w') as stderr:
     with owned_worker(cmd,stdout=stdout,stderr=stderr,env=env) as process:assert process.wait(timeout=180)==0
    record=json.loads((dest/(stem+'.json')).read_text());assert validate(record,storage,schedule,rows,columns,count,'minmax')==hashes
    summary.append({'round':iteration,'case':case,'storage':storage,'version':version,'host_load_before':load,'elapsed_ms':record['elapsed_ms'],'requests_per_second':record['requests_per_second'],'measured_rss_mib':record['measured']['rss_bytes']/1024**2,'peak_rss_mib':record['measured']['peak_rss_bytes']/1024**2})
    save('summary.json',summary);print('Passed',stem,flush=True)
print('Passed 48 interleaved workers',flush=True)
