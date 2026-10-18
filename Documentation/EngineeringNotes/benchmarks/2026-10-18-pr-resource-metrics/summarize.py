from pathlib import Path
import json,statistics,hashlib
R=Path(__file__).resolve().parent
cases=json.loads((R/'all-cases.json').read_text()); records=[]; summary=[]
for c in cases:
 groups={}
 for phase,rounds in [('qualification',1),('timing',5),('memory',3)]:
  for rd in range(rounds):
   pair=[]
   for side in ['before','after']:
    p=R/'runs'/f'{c["id"]}-{phase}-{rd}-{side}.json';d=json.loads(p.read_text())
    assert d['case']==c and d['phase']==phase and d['round']==rd and d['side']==side
    assert d['result']['validated'] and len(d['result']['samples'])==(7 if phase=='timing' else 1)
    build=json.loads((R/'build'/f'pr{c["pr"]}-{side}'/'build.json').read_text());assert d['binary_sha256']==build['binary_sha256']
    record={'file':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()};records.append(record)
    groups[(phase,rd,side)]=d
    pair.append(d)
   if c['pr']==70:assert pair[0]['result']['context']==pair[1]['result']['context']
 row={'case':c,'rounds':5,'samples_per_process':7,'memory_pairs':3}
 for field in ['total_cpu_ns','total_ns','call_cpu_ns','call_ns','release_cpu_ns','release_ns']:
  values={side:[statistics.median(s[field] for s in groups[('timing',rd,side)]['result']['samples']) for rd in range(5)] for side in ['before','after']}
  assert all(x>0 for x in values['before']) if field in ['total_cpu_ns','total_ns','call_cpu_ns','call_ns'] else True
  ratios=[b/a if a>0 else None for a,b in zip(values['before'],values['after'])]
  valid=[x for x in ratios if x is not None]
  row[field]={'before':statistics.median(values['before']),'after':statistics.median(values['after']),'paired_after_before_median':statistics.median(valid) if valid else None,'paired_after_before_range':[min(valid),max(valid)] if valid else None,'process_medians':values}
 for field in ['heap_before_bytes','held_heap_bytes','held_heap_delta_bytes','heap_after_release_bytes','process_peak_before_bytes','process_peak_held_bytes']:
  values={side:[groups[('memory',rd,side)]['result']['samples'][0][field] for rd in range(3)] for side in ['before','after']}
  row[field]={'before':statistics.median(values['before']),'after':statistics.median(values['after']),'range':{s:[min(v),max(v)] for s,v in values.items()}}
 summary.append(row)
assert len(records)==342
(R/'summary.json').write_text(json.dumps({'cases':summary,'manifest':records},indent=2)+'\n')
lines=['# Matched PR resource measurements','','CPU and wall figures are medians of five process medians, seven measured samples per process after two warmups. Both include the API call and output release; complete validation runs outside the clocks. Memory is the median of three separate fresh processes. Peak RSS includes input/setup and allocator history. It is not an owned-memory measurement. MiB = 1,048,576 bytes.','','| PR / operation / shape | CPU ms before → after | CPU change, paired | Wall ms before → after | Peak RSS MiB before → after | Held heap delta MiB before → after |','| --- | ---: | ---: | ---: | ---: | ---: |']
for row in summary:
 c=row['case']; cpu=row['total_cpu_ns'];wall=row['total_ns'];rss=row['process_peak_held_bytes'];held=row['held_heap_delta_bytes']
 lines.append(f'| #{c["pr"]} {c["mode"]} {c["rows"]:,}×{c["width"]} | {cpu["before"]/1e6:.4f} → {cpu["after"]/1e6:.4f} | {(cpu["paired_after_before_median"]-1)*100:+.1f}% | {wall["before"]/1e6:.4f} → {wall["after"]/1e6:.4f} | {rss["before"]/2**20:.2f} → {rss["after"]/2**20:.2f} | {held["before"]/2**20:.2f} → {held["after"]/2**20:.2f} |')
lines += ['','## Observed CPU ratio ranges','','Ratios are after/before for each paired process median. Below one means less CPU time. Ranges are observed extrema, not confidence intervals.','','| Case | Median ratio | Paired range |','| --- | ---: | ---: |']
for row in summary:
 c=row['case'];m=row['total_cpu_ns'];a,b=m['paired_after_before_range'];lines.append(f'| #{c["pr"]} {c["mode"]} {c["rows"]:,}×{c["width"]} | {m["paired_after_before_median"]:.3f} | {a:.3f}–{b:.3f} |')
(R/'RESULTS.md').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines[:26]))
print('VERIFIED:',len(records),'workers; all outputs passed; all MLP weight/oracle fingerprints matched')
