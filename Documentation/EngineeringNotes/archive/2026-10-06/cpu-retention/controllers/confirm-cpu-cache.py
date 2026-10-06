import os,sys,json,subprocess
from pathlib import Path
root=Path('/Users/crabel/Documents/src/SwiftSci');sys.path.insert(0,str(root/'Benchmarks/UnifiedMemoryPrototype'));import run as c
from mixed_device import check_memory_pressure
from processes import run_process
p=Path('/Users/crabel/local-ai/spl/swiftsci/cpu-retention-20261006');env={k:v for k,v in os.environ.items() if k not in c.THREAD_OVERRIDES};env.update(CPU_WARMUP_ONLY='1',MallocLargeCache='0')
w=c.CACHE/'derived/Build/Products/Release/SwiftSciCPURetentionProfile';v=w.with_name('SwiftSciCPURetentionVMProfile')
records=[json.loads((p/'large-cache-control.json').read_text())]
for i in [1,2]:
 check_memory_pressure(p,{'case':'cache-control','round':i})
 r=c.invoke_admission([str(w),'--retained-memory','cpu-sizes','retain','12','sequence'],env,p,{'case':'cache-control','round':i},expected_job_count=None,timeout=60)
 check_memory_pressure(p,{'case':'cache-control-after','round':i});records.append(r);c.write(p/'cache-control-samples.json',records)
 print('control',i,'growth MiB',(r['records'][-1]['after_intervention']['physical_footprint_bytes']-r['records'][0]['memory']['physical_footprint_bytes'])/1048576,flush=True)
folder=p/'vm-cache-disabled';folder.mkdir(exist_ok=False)
check_memory_pressure(p,{'case':'cache-control-vm'})
r=c.invoke_admission([str(v),'--retained-memory','cpu-sizes','retain','12','sequence'],env|{'CPU_VM_MAP':str(folder)},p,{'case':'cache-control-vm'},expected_job_count=None,timeout=90)
check_memory_pressure(p,{'case':'cache-control-vm-after'});c.write(folder/'observations.json',r)
print('VM cache disabled complete',flush=True)
# Leak scanner is a separate default-allocator worker, not a timing sample.
env.pop('MallocLargeCache');env['MallocStackLogging']='1'
check_memory_pressure(p,{'case':'cpu-leaks'})
with (p/'leaks.log').open('w') as log:
 r=run_process(['/usr/bin/leaks','--atExit','--',str(v),'--retained-memory','cpu-sizes','retain','12','sequence'],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=90)
check_memory_pressure(p,{'case':'cpu-leaks-after'})
c.write(p/'leaks-result.json',dict(returncode=r.returncode,scope='Separate default-allocator worker with MallocStackLogging and leaks at process exit. Not an intermediate ownership proof or a timing sample.'))
print('leaks exit',r.returncode,flush=True)
