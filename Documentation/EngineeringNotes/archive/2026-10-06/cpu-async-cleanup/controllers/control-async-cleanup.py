import json,os,sys,statistics
from pathlib import Path
root=Path('/Users/crabel/Documents/src/SwiftSci');sys.path.insert(0,str(root/'Benchmarks/UnifiedMemoryPrototype'));import run as c
from mixed_device import check_memory_pressure
out=Path('/Users/crabel/local-ai/spl/swiftsci/cpu-async-cleanup-20261006');env={k:v for k,v in os.environ.items() if k not in c.THREAD_OVERRIDES and not k.startswith('Malloc') and k not in ['CPU_WORKSPACE_REUSE','CPU_WORKSPACE_SIZING','CPU_VM_MAP','CPU_WARMUP_ONLY']}
workers={name:c.CACHE/'derived/Build/Products/Release'/binary for name,binary in [('prior','SwiftSciCPUScopedWorkspaceTrial'),('new','SwiftSciCPUAsyncCleanupTrial')]}
records=json.loads((out/'memory-controls.json').read_text()) if (out/'memory-controls.json').exists() else [];arms=[('prior',False),('new',False),('prior',True),('new',True)]
for ri in range(4):
 for name,reuse in arms[ri:]+arms[:ri]:
  context=dict(phase='largest-first-control',round=ri,binary=name,reuse=reuse)
  if any(r['round']==ri and r['binary']==name and r['reuse']==reuse for r in records): continue
  before=check_memory_pressure(out,context)
  record=c.invoke_admission([str(workers[name]),'--retained-memory','cpu-sizes','retain','12','sequence'],env|{'CPU_WORKSPACE_REUSE':'1' if reuse else '0','CPU_WORKSPACE_SIZING':'planned'},out,context,expected_job_count=None,timeout=60)
  after=check_memory_pressure(out,context)
  record.update(context,memory_pressure_before=before,memory_pressure_after=after,binary_sha256=c.digest(workers[name]));records.append(record);c.write(out/'memory-controls.json',records)
  print(name,reuse,'input MiB',round(record['records'][0]['memory']['physical_footprint_bytes']/1048576,2),'peak',round(record['records'][-1]['after_intervention']['peak_physical_footprint_bytes']/1048576,2),flush=True)
summary=[]
for name,reuse in arms:
 group=[r for r in records if r['binary']==name and r['reuse']==reuse]
 vals=lambda fn:[fn(r) for r in group]
 summary.append(dict(binary=name,reuse=reuse,inputs_mib=vals(lambda r:r['records'][0]['memory']['physical_footprint_bytes']/1048576),peak_mib=vals(lambda r:r['records'][-1]['after_intervention']['peak_physical_footprint_bytes']/1048576),fit_growth_mib=vals(lambda r:(r['records'][-1]['after_intervention']['physical_footprint_bytes']-r['records'][0]['memory']['physical_footprint_bytes'])/1048576),end_live_malloc_mib=vals(lambda r:r['after_workspace_dropped']['malloc_bytes_in_use']/1048576)))
c.write(out/'memory-control-summary.json',dict(status='passed',workers=len(records),measured_fits=sum(r['fits'] for r in records),samples_sha256=c.digest(out/'memory-controls.json'),summaries=summary))
