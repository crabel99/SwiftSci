from pathlib import Path
import json,statistics,hashlib
R=Path(__file__).resolve().parent
es=[json.loads(l) for l in (R/'production-workers.jsonl').read_text().splitlines()];assert len(es)==80
med=statistics.median;rows=[]
lines=['# Single-pass CSV block trial','','The index construction and field lookups are included in CPU and elapsed time. Values include result release. CPU percentages use median paired ratios, while displayed times are medians of worker medians. Memory workers are separate and capture peak RSS before validation.','','| Input | CPU ms before → trial | Paired CPU change and ratio range | Elapsed ms before → trial | Peak RSS MiB before → trial | Held heap MiB before → trial |','| --- | ---: | ---: | ---: | ---: | ---: |']
for case in dict.fromkeys(tuple(e['case']) for e in es):
 groups={v:{ph:sorted([e for e in es if tuple(e['case'])==case and e['variant']==v and e['phase']==ph],key=lambda e:e['pair']) for ph in ['timing','memory']} for v in ['baseline','cursor']}
 stats={}
 for v,g in groups.items():
  assert len(g['timing'])==5 and len(g['memory'])==3
  stats[v]={k:med(med(s[k] for s in e['samples']) for e in g['timing']) for k in ['total_ns','total_cpu_ns']}
  stats[v].update({k:med(e['samples'][0][k] for e in g['memory']) for k in ['held_heap_delta_bytes','process_peak_held_bytes','heap_before_bytes','heap_after_release_bytes']})
 ratios=[med(s['total_cpu_ns'] for s in groups['cursor']['timing'][i]['samples'])/med(s['total_cpu_ns'] for s in groups['baseline']['timing'][i]['samples']) for i in range(5)]
 p={'median_ratio':med(ratios),'range':[min(ratios),max(ratios)]}
 rows.append(dict(case=case,statistics=stats,cpu_paired=p))
 a,b=stats['baseline'],stats['cursor']
 lines.append(f'| {case[0]}, {case[1]:,} × {case[2]} | {a["total_cpu_ns"]/1e6:.2f} → {b["total_cpu_ns"]/1e6:.2f} | {(p["median_ratio"]-1)*100:+.1f}%; {min(ratios):.3f}–{max(ratios):.3f} | {a["total_ns"]/1e6:.2f} → {b["total_ns"]/1e6:.2f} | {a["process_peak_held_bytes"]/2**20:.2f} → {b["process_peak_held_bytes"]/2**20:.2f} | {a["held_heap_delta_bytes"]/2**20:.2f} → {b["held_heap_delta_bytes"]/2**20:.2f} |')
(R/'production-summary.json').write_text(json.dumps({'workers':len(es),'timing_samples':250,'memory_samples':30,'validated':all(e['validated'] for e in es),'rows':rows,'records_sha256':hashlib.sha256((R/'production-workers.jsonl').read_bytes()).hexdigest()},indent=2)+'\n')
(R/'production-RESULTS.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines))
