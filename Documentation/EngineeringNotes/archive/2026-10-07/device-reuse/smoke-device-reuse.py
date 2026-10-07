from pathlib import Path
import sys,json,subprocess,os
root=Path('/Users/crabel/Library/Caches/SwiftSci/retained-gpu-trial-20261007');out=Path('/Users/crabel/local-ai/spl/swiftsci/device-reuse-20261007')
worker=Path('/Users/crabel/Library/Caches/SwiftSci/unified-memory-prototype/derived/Build/Products/Release/SwiftSciRetainedGPUTrial')
sys.path.insert(0,str(root/'Benchmarks/Tools'))
from profile_gpu_residency import owned_worker
from profile_prediction_phases import validate
from runner import verify_uninstrumented
verify_uninstrumented(worker)
env=dict(os.environ);env.pop('SWIFTSCI_RESIDENCY_DIR',None)
for slots in [1,2]:
 assert int(subprocess.check_output(['sysctl','-n','kern.memorystatus_vm_pressure_level']))==1
 stem=f'smoke-{slots}';command=[str(worker),'prediction-phases',str(slots),'64','2']
 (out/(stem+'-command.json')).write_text(json.dumps(command)+'\n')
 with (out/(stem+'.json')).open('w') as stdout,(out/(stem+'.stderr')).open('w') as stderr:
  with owned_worker(command,stdout=stdout,stderr=stderr,env=env) as p:assert p.wait(timeout=90)==0,stem
 hashes=validate(json.loads((out/(stem+'.json')).read_text()),slots,64,2)
 previous=json.loads((out.parent/'prediction-phases-20261007'/f'smoke-prediction-{slots}.json').read_text())
 assert hashes=={b['pair']:b['output_sha256'] for b in previous['blocks']}
 print('Passed smoke and historical parity',stem,flush=True)
