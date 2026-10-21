from pathlib import Path
import json,statistics
r=Path(__file__).resolve().parent
for name in ['geometric-pilot','bounded-measurement','counted-measurement','counted64-measurement','final-measurement']:
 p=r/name/'workers.jsonl'
 if not p.exists():continue
 ds=[json.loads(x) for x in p.read_text().splitlines()];group={}
 for d in ds:
  k=(d['case'],d['mode'],d['engine']);group.setdefault(k,[]).append(d['samples'][0])
 rows=[]
 for case,mode,engine in group:
  ss=group[(case,mode,engine)];v={k:statistics.median(d[k] for d in ss) for k in ['total_cpu_ns','total_ns','process_peak_held_bytes','rss_held_delta_bytes','held_heap_delta_bytes']};v.update(case=case,mode=mode,engine=engine,workers=len(ss));rows.append(v)
 (r/name/'summary.json').write_text(json.dumps(dict(workers=len(ds),all_validated=all(d['validated'] for d in ds),medians=rows),indent=2)+'\n')
 print(name,len(ds))
 for a in rows:
  if a['engine']=='indexed':continue
  b=next(x for x in rows if(x['case'],x['mode'],x['engine'])==(a['case'],a['mode'],'indexed'))
  print(a['case'],a['mode'],f"CPU {b['total_cpu_ns']/1e6:.3f}->{a['total_cpu_ns']/1e6:.3f} ms ({(a['total_cpu_ns']/b['total_cpu_ns']-1)*100:+.1f}%)",f"peak {b['process_peak_held_bytes']/2**20:.2f}->{a['process_peak_held_bytes']/2**20:.2f} MiB")
