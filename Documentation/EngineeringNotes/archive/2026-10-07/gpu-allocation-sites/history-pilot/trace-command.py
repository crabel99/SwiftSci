from pathlib import Path
import hashlib,json,os,signal,subprocess,sys
root=Path('/Users/crabel/Library/Caches/SwiftSci/retained-gpu-trial-20261007')
out=Path('/Users/crabel/local-ai/spl/swiftsci/gpu-allocation-sites-20261007/history-pilot')
out.mkdir(parents=True,exist_ok=False)
(out/'stacks').mkdir()
sys.path.insert(0,str(root/'Benchmarks/Tools'))
from profile_gpu_residency import owned_worker,wait_stopped
from compare_gpu_budget_workflow import validate
worker=Path('/Users/crabel/Library/Caches/SwiftSci/unified-memory-prototype/derived/Build/Products/Release/SwiftSciRetainedGPUTrial')
assert int(subprocess.check_output(['sysctl','-n','kern.memorystatus_vm_pressure_level'],text=True))==1
changes={'SWIFTSCI_RESIDENCY_DIR':str(out),'MallocStackLogging':'full','MallocStackLoggingDirectory':str(out/'stacks')}
command=[str(worker),'budget-workflow','logical','65535','65','256','8']
(out/'provenance.json').write_text(json.dumps({'binary_sha256':hashlib.sha256(worker.read_bytes()).hexdigest(),'command':command,'environment_override':changes,'head':subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip(),'diagnostic':'Stack logging perturbs allocations and timing; do not compare throughput'},indent=2)+'\n')
with (out/'worker.stdout').open('w') as stdout,(out/'worker.stderr').open('w') as stderr:
 with owned_worker(command,stdout=stdout,stderr=stderr,env=dict(os.environ,**changes)) as process:
  for stage in ['before-burst','after-cache-clear','after-pressure-relief']:
   wait_stopped(process,out/(stage+'.json'))
   if stage=='after-cache-clear':
    tools=[('history-peak',['/usr/bin/malloc_history',str(process.pid),'-callTree','-highWaterMark','-invert','-ignoreThreads','-noContent']),('history-live',['/usr/bin/malloc_history',str(process.pid),'-allBySize']),('vmmap',['/usr/bin/vmmap','-summary','-wide',str(process.pid)])]
    for name,cmd in tools:
     with (out/(name+'.txt')).open('w') as log:
      result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=60)
     print(name,result.returncode,flush=True)
   os.kill(process.pid,signal.SIGCONT)
  assert process.wait(timeout=120)==0
record=json.loads((out/'worker.stdout').read_text())
validate(record,'logical',65535,65,256,8)
print('Validated 8 requests',flush=True)
