from pathlib import Path
import sys,json,statistics,hashlib
R=Path(sys.argv[1]);plan=json.loads((R/'plan.json').read_text());old=plan['reference'];new=plan['candidate']
es=[json.loads(l) for l in (R/'workers.jsonl').read_text().splitlines()];med=statistics.median;rows=[]
lines=['# Paired resource comparison','',f'Reference: `{old}`. Candidate: `{new}`. CPU and elapsed time include CSV read and output release. Memory workers are separate.','', '| Input | Paired CPU change | CPU ratio range | Peak RSS MiB, reference → candidate | Held heap MiB, reference → candidate |','| --- | ---: | ---: | ---: | ---: |']
for case in dict.fromkeys(tuple(e['case']) for e in es):
 groups={v:sorted([e for e in es if tuple(e['case'])==case and e['variant']==v and e['phase']=='timing'],key=lambda e:e['pair']) for v in [old,new]}
 ratios=[med(s['total_cpu_ns'] for s in groups[new][i]['samples'])/med(s['total_cpu_ns'] for s in groups[old][i]['samples']) for i in range(5)]
 stats={}
 for v in [old,new]:
  stats[v]={k:med(med(s[k] for s in e['samples']) for e in groups[v]) for k in ['total_ns','total_cpu_ns']}
  for k in ['held_heap_delta_bytes','process_peak_held_bytes']:
   stats[v][k]=med(e['samples'][0][k] for e in es if tuple(e['case'])==case and e['variant']==v and e['phase']=='memory')
 pair=dict(median_ratio=med(ratios),range=[min(ratios),max(ratios)])
 rows.append(dict(case=case,statistics=stats,cpu_paired=pair))
 a,b=stats[old],stats[new]
 lines.append(f'| {case[0]} {case[1]:,} × {case[2]} | {(med(ratios)-1)*100:+.1f}% | {min(ratios):.3f}–{max(ratios):.3f} | {a["process_peak_held_bytes"]/2**20:.2f} → {b["process_peak_held_bytes"]/2**20:.2f} | {a["held_heap_delta_bytes"]/2**20:.2f} → {b["held_heap_delta_bytes"]/2**20:.2f} |')
(R/'summary.json').write_text(json.dumps(dict(rows=rows,records_sha256=hashlib.sha256((R/'workers.jsonl').read_bytes()).hexdigest()),indent=2)+'\n')
(R/'RESULTS.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines))
