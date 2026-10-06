import json,os,sys,statistics,subprocess
from pathlib import Path
root=Path('/Users/crabel/Documents/src/SwiftSci');sys.path.insert(0,str(root/'Benchmarks/UnifiedMemoryPrototype'));import run as c
from mixed_device import check_memory_pressure
out=Path('/Users/crabel/local-ai/spl/swiftsci/cpu-planned-workspace-20261006');worker=c.CACHE/'derived/Build/Products/Release/SwiftSciCPUPlannedWorkspaceTrial'
b=json.loads((out/'build.json').read_text());assert c.digest(worker)==b['binary_sha256']
env={k:v for k,v in os.environ.items() if k not in c.THREAD_OVERRIDES and not k.startswith('Malloc') and k not in ['CPU_WORKSPACE_REUSE','CPU_WORKSPACE_SIZING','CPU_VM_MAP','CPU_WARMUP_ONLY']}
assert 'AC Power' in subprocess.check_output(['pmset','-g','batt'],text=True)
check=c.invoke_admission([str(worker),'--planned-cpu-workspace-check'],env,out,{'phase':'planned-workspace-check'},expected_job_count=None,timeout=30);c.write(out/'checks.json',check)
records=[]
for ri in range(4):
 for profile in ['cpu-small','cpu-same','cpu-sizes','cpu-growing']:
  for arm in (['arrays','fixed','adaptive','planned'][ri:]+['arrays','fixed','adaptive','planned'][:ri]):
   context=dict(round=ri,profile=profile,arm=arm)
   before=check_memory_pressure(out,context)
   r=c.invoke_admission([str(worker),'--retained-memory',profile,'retain','12','sequence'],env|{'CPU_WORKSPACE_REUSE':'0' if arm=='arrays' else '1','CPU_WORKSPACE_SIZING':arm},out,context,expected_job_count=None,timeout=60)
   after=check_memory_pressure(out,context)
   if arm=='planned':
    assert r['final_reserved_bytes']==0 and r['peak_reserved_bytes']==r['planned_bytes']==r['workspace']['owned_bytes']
    assert r['workspace']['allocations']==1 and all(j['workspace_reserved_bytes']==r['planned_bytes'] for j in r['records'][1:])
   r.update(context,memory_pressure_before=before,memory_pressure_after=after)
   records.append(r);c.write(out/'samples.json',records)
   mem=r['records'][-1]['after_intervention'];ready=r['records'][0]['memory']
   print(context,'growth MiB',round((mem['physical_footprint_bytes']-ready['physical_footprint_bytes'])/1048576,3),'fit ms',round(sum(j['fit_ns'] for j in r['records'][1:])/1e6,2),flush=True)
summary=[]
for profile in ['cpu-small','cpu-same','cpu-sizes','cpu-growing']:
 for arm in ['arrays','fixed','adaptive','planned']:
  group=[r for r in records if r['profile']==profile and r['arm']==arm]
  row=dict(profile=profile,arm=arm,workers=len(group),setup_ms=[r['workspace_setup_ns']/1e6 for r in group],complete_batch_ms=[r['measured_batch_ns']/1e6 for r in group],workspace_owned_bytes=[r['workspace']['owned_bytes'] for r in group],workspace_allocations=[r['workspace']['allocations'] for r in group],fit_sum_ms=[sum(j['fit_ns'] for j in r['records'][1:])/1e6 for r in group],steady_fit_sum_ms=[sum(j['fit_ns'] for j in r['records'][4:])/1e6 for r in group])
  for key in ['physical_footprint_bytes','malloc_bytes_in_use','peak_physical_footprint_bytes']:
   row[key]=dict(warmed=statistics.median(r['warmed'][key] for r in group),inputs_ready=statistics.median(r['records'][0]['memory'][key] for r in group),end=statistics.median(r['records'][-1]['after_intervention'][key] for r in group),inputs_dropped=statistics.median(r['after_inputs_dropped'][key] for r in group),workspace_dropped=statistics.median(r['after_workspace_dropped'][key] for r in group),growth=statistics.median(r['records'][-1]['after_intervention'][key]-r['records'][0]['memory'][key] for r in group))
  summary.append(row)
c.write(out/'summary.json',dict(status='passed',workers=len(records),measured_fits=sum(r['fits'] for r in records),summaries=summary,samples_sha256=c.digest(out/'samples.json')))
print('All workers passed',flush=True)
