import json,os,sys,shutil,subprocess,plistlib
from pathlib import Path
root=Path('/Users/crabel/Documents/src/SwiftSci');sys.path.insert(0,str(root/'Benchmarks/UnifiedMemoryPrototype'))
import run as c
from mixed_device import check_memory_pressure
out=Path('/Users/crabel/local-ai/spl/swiftsci/cpu-retention-20261006');worker=c.CACHE/'derived/Build/Products/Release/SwiftSciCPURetentionProfile'
b=json.loads((out/'build.json').read_text());assert c.digest(worker)==b['binary_sha256']
copy=worker.with_name('SwiftSciCPURetentionVMProfile');shutil.copy2(worker,copy)
ent=out/'entitlements.plist';ent.write_bytes(plistlib.dumps({'com.apple.security.get-task-allow':True}))
subprocess.run(['codesign','--force','--sign','-','--entitlements',str(ent),str(copy)],check=True)
c.write(out/'vm-profile.json',dict(binary_sha256=c.digest(copy),original_binary_sha256=c.digest(worker),change='Disposable executable copy with get-task-allow for vmmap. Source identical. No global security settings changed.'))
env={k:v for k,v in os.environ.items() if k not in c.THREAD_OVERRIDES and k not in ['CPU_WARMUP_ONLY','CPU_VM_MAP']}
for warmup in ['both','cpu']:
 folder=out/('vm-'+warmup);folder.mkdir(exist_ok=False)
 ctx=dict(warmup=warmup,profile='cpu-sizes',instrumented=True)
 check_memory_pressure(out,ctx)
 r=c.invoke_admission([str(copy),'--retained-memory','cpu-sizes','retain','12','sequence'],env|{'CPU_WARMUP_ONLY':'1' if warmup=='cpu' else '0','CPU_VM_MAP':str(folder)},out,ctx,expected_job_count=None,timeout=90)
 check_memory_pressure(out,ctx);c.write(folder/'observations.json',r)
 print('VM maps complete',warmup,flush=True)
