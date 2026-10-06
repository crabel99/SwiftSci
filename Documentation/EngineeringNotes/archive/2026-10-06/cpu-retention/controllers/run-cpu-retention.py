import json,os,sys,statistics,time,subprocess
from pathlib import Path
root=Path('/Users/crabel/Documents/src/SwiftSci');sys.path.insert(0,str(root/'Benchmarks/UnifiedMemoryPrototype'))
import run as c
from mixed_device import check_memory_pressure
out=Path('/Users/crabel/local-ai/spl/swiftsci/cpu-retention-20261006');worker=c.CACHE/'derived/Build/Products/Release/SwiftSciCPURetentionProfile'
b=json.loads((out/'build.json').read_text());assert c.digest(worker)==b['binary_sha256']
env={k:v for k,v in os.environ.items() if k not in c.THREAD_OVERRIDES and k not in ['CPU_WARMUP_ONLY','CPU_VM_MAP']}
assert 'AC Power' in subprocess.check_output(['pmset','-g','batt'],text=True)
records=[]
for round_index in range(3):
 for profile in ['cpu-same','cpu-sizes']:
  for warmup in (['both','cpu'] if round_index%2==0 else ['cpu','both']):
   ctx=dict(round=round_index,profile=profile,warmup=warmup)
   before=check_memory_pressure(out,ctx)
   start=time.monotonic();r=c.invoke_admission([str(worker),'--retained-memory',profile,'retain','12','sequence'],env|{'CPU_WARMUP_ONLY':'1' if warmup=='cpu' else '0'},out,ctx,expected_job_count=None,timeout=60)
   after=check_memory_pressure(out,ctx);r.update(ctx,memory_pressure_before=before,memory_pressure_after=after,wall_seconds=time.monotonic()-start);records.append(r);c.write(out/'samples.json',records)
   ready=r['records'][0]['memory'];last=r['records'][-1]['after_intervention']
   print(ctx,'growth MiB',round((last['physical_footprint_bytes']-ready['physical_footprint_bytes'])/1048576,3),'live KiB',round((last['malloc_bytes_in_use']-ready['malloc_bytes_in_use'])/1024,3),flush=True)
summary=[]
for profile in ['cpu-same','cpu-sizes']:
 for warmup in ['both','cpu']:
  group=[r for r in records if r['profile']==profile and r['warmup']==warmup]
  def change(r,cycle,key):return r['records'][cycle*3]['after_intervention'][key]-r['records'][0]['memory'][key]
  summary.append(dict(profile=profile,warmup=warmup,cycle_physical_growth_bytes=[statistics.median(change(r,i,'physical_footprint_bytes') for r in group) for i in range(1,13)],cycle_malloc_live_growth_bytes=[statistics.median(change(r,i,'malloc_bytes_in_use') for r in group) for i in range(1,13)],input_release_live_bytes=statistics.median(r['records'][-1]['after_intervention']['malloc_bytes_in_use']-r['after_inputs_dropped']['malloc_bytes_in_use'] for r in group),late_growth_range_bytes=[min(change(r,12,'physical_footprint_bytes')-change(r,6,'physical_footprint_bytes') for r in group),max(change(r,12,'physical_footprint_bytes')-change(r,6,'physical_footprint_bytes') for r in group)]))
c.write(out/'summary.json',dict(workers=len(records),measured_fits=sum(r['fits'] for r in records),summaries=summary,samples_sha256=c.digest(out/'samples.json')))
print(json.dumps(summary,indent=2))
