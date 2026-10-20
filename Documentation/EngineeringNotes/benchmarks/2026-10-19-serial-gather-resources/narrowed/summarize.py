from pathlib import Path
import json,statistics,hashlib
R=Path(__file__).resolve().parent
plan=json.loads((R/'plan.json').read_text());events=[json.loads(l) for l in (R/'processes.jsonl').read_text().splitlines()]
assert len(events)==len(plan['cases'])*16
med=statistics.median;rows=[]
for case in plan['cases']:
 grouped={v:{phase:sorted([e for e in events if e['case']==case and e['variant']==v and e['phase']==phase],key=lambda e:e['pair']) for phase in ['timing','memory']} for v in ['baseline','candidate']}
 stats={}
 for v,g in grouped.items():
  assert len(g['timing'])==5 and len(g['memory'])==3
  stats[v]={}
  for metric in ['total_ns','total_cpu_ns','call_ns','release_ns']:
   stats[v][metric]=med(med(s[metric] for s in e['samples']) for e in g['timing'])
  for metric in ['held_heap_delta_bytes','heap_before_bytes','heap_after_release_bytes','process_peak_before_bytes','process_peak_held_bytes']:
   stats[v][metric]=med(e['samples'][0][metric] for e in g['memory'])
 paired={}
 for metric in ['total_ns','total_cpu_ns']:
  ratios=[med(s[metric] for s in grouped['candidate']['timing'][i]['samples'])/med(s[metric] for s in grouped['baseline']['timing'][i]['samples']) for i in range(5)]
  paired[metric]={'median_ratio':med(ratios),'range':[min(ratios),max(ratios)]}
 rows.append(dict(case=case,statistics=stats,paired=paired))
summary=dict(processes=len(events),measured_timing_samples=len(plan['cases'])*50,memory_samples=len(plan['cases'])*6,validated=all(e['validated'] for e in events),rows=rows,records_sha256=hashlib.sha256((R/'processes.jsonl').read_bytes()).hexdigest())
(R/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
lines=['# Serial gather resource results','','All values include the API call and result release. CPU change is the median of five paired ratios. Ranges are observed paired ratios, not confidence intervals. RSS includes process setup and input construction. Heap delta measures live malloc storage while the output is held.','','| Operation and source | CPU ms before → after | CPU change | CPU ratio range | Elapsed ms before → after | Peak RSS MiB before → after | Held heap MiB before → after |','| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
for row in rows:
 a,b=(row['statistics'][v] for v in ['baseline','candidate']);p=row['paired']['total_cpu_ns'];c=row['case']
 lines.append(f'| {c[0]}, {c[1]:,} × {c[2]}, {c[4]}, {c[3]}, {c[5]} | {a["total_cpu_ns"]/1e6:.3f} → {b["total_cpu_ns"]/1e6:.3f} | {(p["median_ratio"]-1)*100:+.1f}% | {p["range"][0]:.3f}–{p["range"][1]:.3f} | {a["total_ns"]/1e6:.3f} → {b["total_ns"]/1e6:.3f} | {a["process_peak_held_bytes"]/2**20:.2f} → {b["process_peak_held_bytes"]/2**20:.2f} | {a["held_heap_delta_bytes"]/2**20:.2f} → {b["held_heap_delta_bytes"]/2**20:.2f} |')
(R/'RESULTS.md').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines))
