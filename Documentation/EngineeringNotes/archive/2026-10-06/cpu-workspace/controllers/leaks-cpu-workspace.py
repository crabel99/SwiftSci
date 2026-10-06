import json,os,sys,shutil,subprocess,plistlib
from pathlib import Path
root=Path('/Users/crabel/Documents/src/SwiftSci');sys.path.insert(0,str(root/'Benchmarks/UnifiedMemoryPrototype'));import run as c
from processes import run_process
from mixed_device import check_memory_pressure
out=Path('/Users/crabel/local-ai/spl/swiftsci/cpu-workspace-20261006/adaptive');worker=c.CACHE/'derived/Build/Products/Release/SwiftSciCPUAdaptiveWorkspaceTrial'
b=json.loads((out/'build.json').read_text());assert c.digest(worker)==b['binary_sha256']
copy=worker.with_name('SwiftSciCPUAdaptiveWorkspaceLeakProbe');shutil.copy2(worker,copy)
ent=out/'entitlements.plist';ent.write_bytes(plistlib.dumps({'com.apple.security.get-task-allow':True}));subprocess.run(['codesign','--force','--sign','-','--entitlements',str(ent),str(copy)],check=True)
env={k:v for k,v in os.environ.items() if k not in c.THREAD_OVERRIDES and not k.startswith('Malloc')};env.update(CPU_WORKSPACE_REUSE='1',CPU_WORKSPACE_SIZING='adaptive',MallocStackLogging='1')
check_memory_pressure(out,{'phase':'leaks-before'})
with (out/'leaks.log').open('w') as log:
 r=run_process(['/usr/bin/leaks','--atExit','--',str(copy),'--retained-memory','cpu-growing','retain','12','sequence'],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=90)
check_memory_pressure(out,{'phase':'leaks-after'})
text=(out/'leaks.log').read_text();record=next(json.loads(l) for l in text.splitlines() if l.startswith('{'));assert r.returncode==0 and record['status']=='passed';assert '0 leaks for 0 total leaked bytes.' in text
c.write(out/'leaks-summary.json',dict(status='passed',leaks=0,leaked_bytes=0,measured_fits=record['fits'],workspace=record['workspace'],binary_sha256=c.digest(copy),scope='Separate stack-logged adaptive workspace worker, increasing-size sequence, process-exit leak graph. Not a timing sample.'))
print('Leak scan passed',record['workspace'],flush=True)
