from pathlib import Path
import sys,json,subprocess,os
root=Path('/Users/crabel/Library/Caches/SwiftSci/retained-gpu-trial-20261007');out=Path('/Users/crabel/local-ai/spl/swiftsci/prediction-phases-20261007')
worker=Path('/Users/crabel/Library/Caches/SwiftSci/unified-memory-prototype/derived/Build/Products/Release/SwiftSciRetainedGPUTrial')
sys.path.insert(0,str(root/'Benchmarks/Tools'))
from profile_gpu_residency import owned_worker
from profile_prediction_phases import validate
from profile_imputed_latency import validate as latency_validate
from runner import verify_uninstrumented
verify_uninstrumented(worker)
env=dict(os.environ);env.pop('SWIFTSCI_RESIDENCY_DIR',None)
for slots in [1,2]:
 assert int(subprocess.check_output(['sysctl','-n','kern.memorystatus_vm_pressure_level']))==1
 stem=f'smoke-prediction-{slots}';command=[str(worker),'prediction-phases',str(slots),'64','2']
 (out/(stem+'-command.json')).write_text(json.dumps(command)+'\n')
 with (out/(stem+'.json')).open('w') as stdout,(out/(stem+'.stderr')).open('w') as stderr:
  with owned_worker(command,stdout=stdout,stderr=stderr,env=env) as p:assert p.wait(timeout=90)==0,stem
 validate(json.loads((out/(stem+'.json')).read_text()),slots,64,2);print('Passed',stem,flush=True)
for route in ['preprocessing','direct','pipeline']:
 for slots in [1,2]:
  assert int(subprocess.check_output(['sysctl','-n','kern.memorystatus_vm_pressure_level']))==1
  stem=f'smoke-{route}-{slots}';command=[str(worker),'imputed-latency',route,str(slots),'64','2']
  with (out/(stem+'.json')).open('w') as stdout,(out/(stem+'.stderr')).open('w') as stderr:
   with owned_worker(command,stdout=stdout,stderr=stderr,env=env) as p:assert p.wait(timeout=90)==0,stem
  record=json.loads((out/(stem+'.json')).read_text())
  hashes=latency_validate(record,route,slots,64,2)
  parent=json.loads((out.parent/'small-imputed-latency-20261007'/(stem+'.json')).read_text())
  assert hashes==latency_validate(parent,route,slots,64,2),'Hash compatibility failed'
  print('Passed parent hash parity',stem,flush=True)
