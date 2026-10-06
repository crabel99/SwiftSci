import json,os,sys,statistics,subprocess
from pathlib import Path
root=Path('/Users/crabel/Documents/src/SwiftSci');sys.path.insert(0,str(root/'Benchmarks/UnifiedMemoryPrototype'));import run as c
from mixed_device import check_memory_pressure
out=Path('/Users/crabel/local-ai/spl/swiftsci/cpu-async-cleanup-20261006');worker=c.CACHE/'derived/Build/Products/Release/SwiftSciCPUAsyncCleanupTrial';old=worker.with_name('SwiftSciCPUScopedWorkspaceTrial')
b=json.loads((out/'build.json').read_text());assert c.digest(worker)==b['binary_sha256'];old_build=json.loads(Path('/Users/crabel/local-ai/spl/swiftsci/cpu-scoped-workspace-20261006/build.json').read_text());assert c.digest(old)==old_build['binary_sha256']
env={k:v for k,v in os.environ.items() if k not in c.THREAD_OVERRIDES and not k.startswith('Malloc') and k not in ['CPU_WORKSPACE_REUSE','CPU_WORKSPACE_SIZING','CPU_VM_MAP','CPU_WARMUP_ONLY']}
assert 'AC Power' in subprocess.check_output(['pmset','-g','batt'],text=True)
checks=[]
for i in range(20):
 check_memory_pressure(out,{'phase':'ownership-check','round':i})
 r=c.invoke_admission([str(worker),'--planned-cpu-workspace-check'],env,out,{'phase':'async-cleanup-check','round':i},expected_job_count=None,timeout=30)
 assert r['final_reserved_bytes']==0
 checks.append(r);c.write(out/'checks.json',checks)
 print('Ownership checks passed',i+1,flush=True)
records=[]
for ri in range(2):
 for profile in ['cpu-small','cpu-same','cpu-sizes','cpu-growing']:
  arms=['scoped-close','async-close'];arms=arms[ri:]+arms[:ri]
  for arm in arms:
   context=dict(round=ri,profile=profile,arm=arm)
   before=check_memory_pressure(out,context)
   binary=old if arm=='scoped-close' else worker
   r=c.invoke_admission([str(binary),'--retained-memory',profile,'retain','12','sequence'],env|{'CPU_WORKSPACE_REUSE':'1','CPU_WORKSPACE_SIZING':'planned'},out,context,expected_job_count=None,timeout=60)
   after=check_memory_pressure(out,context)
   assert r['final_reserved_bytes']==0 and r['peak_reserved_bytes']==r['planned_bytes']==r['workspace']['owned_bytes']
   assert r['workspace']['allocations']==1 and r['workspace']['uses']==36
   r.update(context,memory_pressure_before=before,memory_pressure_after=after,binary_sha256=c.digest(binary))
   records.append(r);c.write(out/'samples.json',records)
   print(context,'peak MiB',round(r['records'][-1]['after_intervention']['peak_physical_footprint_bytes']/1048576,2),'fits ms',round(sum(j['fit_ns'] for j in r['records'][1:])/1e6,2),flush=True)
summary=[]
for profile in ['cpu-small','cpu-same','cpu-sizes','cpu-growing']:
 row={'profile':profile,'arms':{}}
 for arm in ['scoped-close','async-close']:
  group=[r for r in records if r['profile']==profile and r['arm']==arm]
  row['arms'][arm]={'peak_mib':statistics.median(r['records'][-1]['after_intervention']['peak_physical_footprint_bytes']/1048576 for r in group),'fit_ms':statistics.median(sum(j['fit_ns'] for j in r['records'][1:])/1e6 for r in group),'batch_ms':statistics.median(r['measured_batch_ns']/1e6 for r in group)}
 row['async_vs_scoped_fit_percent']=[]
 for ri in range(2):
  pair={r['arm']:r for r in records if r['profile']==profile and r['round']==ri}
  total=lambda k:sum(j['fit_ns'] for j in pair[k]['records'][1:])
  row['async_vs_scoped_fit_percent'].append((total('async-close')/total('scoped-close')-1)*100)
 summary.append(row)
c.write(out/'summary.json',dict(status='passed',workers=len(records),measured_fits=sum(r['fits'] for r in records),ownership_workers=len(checks),ownership_successful_fits=sum(r['explicit_fits'] for r in checks),summaries=summary,samples_sha256=c.digest(out/'samples.json'),checks_sha256=c.digest(out/'checks.json')))
print('All workers passed',flush=True)
