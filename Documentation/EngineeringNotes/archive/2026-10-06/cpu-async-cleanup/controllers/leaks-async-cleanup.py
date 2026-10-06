import json,os,sys,shutil,subprocess,plistlib
from pathlib import Path
root=Path('/Users/crabel/Documents/src/SwiftSci');sys.path.insert(0,str(root/'Benchmarks/UnifiedMemoryPrototype'));import run as c
from processes import run_process
from mixed_device import check_memory_pressure
out=Path('/Users/crabel/local-ai/spl/swiftsci/cpu-async-cleanup-20261006');worker=c.CACHE/'derived/Build/Products/Release/SwiftSciCPUAsyncCleanupTrial'
b=json.loads((out/'build.json').read_text());assert c.digest(worker)==b['binary_sha256']
copy=worker.with_name('SwiftSciCPUAsyncCleanupLeakProbe');shutil.copy2(worker,copy)
ent=out/'entitlements.plist';ent.write_bytes(plistlib.dumps({'com.apple.security.get-task-allow':True}));subprocess.run(['codesign','--force','--sign','-','--entitlements',str(ent),str(copy)],check=True)
env={k:v for k,v in os.environ.items() if k not in c.THREAD_OVERRIDES and not k.startswith('Malloc')};env.update(CPU_WORKSPACE_REUSE='1',CPU_WORKSPACE_SIZING='planned',MallocStackLogging='1')
summaries=[]
for label,args in [('overlap',['--planned-cpu-workspace-check']),('growing',['--retained-memory','cpu-growing','retain','12','sequence'])]:
 check_memory_pressure(out,{'phase':label+'-leaks-before'})
 with (out/(label+'-leaks.log')).open('w') as log:
  r=run_process(['/usr/bin/leaks','--atExit','--',str(copy),*args],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=90)
 check_memory_pressure(out,{'phase':label+'-leaks-after'})
 text=(out/(label+'-leaks.log')).read_text();record=next(json.loads(l) for l in text.splitlines() if l.startswith('{'));assert r.returncode==0 and record['status']=='passed' and record['final_reserved_bytes']==0;assert '0 leaks for 0 total leaked bytes.' in text
 summaries.append(dict(status='passed',case=label,leaks=0,leaked_bytes=0,record=record,binary_sha256=c.digest(copy),scope='Separate stack-logged worker, process-exit leak graph. Not a timing sample.'))
 print('Leak scan passed',label,flush=True)
c.write(out/'leaks-summary.json',summaries)
