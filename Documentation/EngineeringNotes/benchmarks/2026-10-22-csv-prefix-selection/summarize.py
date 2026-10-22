from pathlib import Path
import json,statistics as st
R=Path(__file__).resolve().parent
rows=[]
for label in ['acceptance','mode-controls','text-controls','long-key-controls','crossover','setup','preflight-screen','steady-boundaries']:
 p=R/label/'summary.json'
 if not p.exists():continue
 data=json.loads(p.read_text());pairs=[]
 for a in data:
  engine=a['engine'];base='parent-'+engine if engine in ['parallel','serial'] else 'cleanup' if engine in ['production','byte-only','preflight'] else None
  if not base:continue
  key={k:a[k] for k in ['scope','case','mode','policy'] if k in a}
  b=next(b for b in data if b['engine']==base and all(b.get(k)==v for k,v in key.items()))
  mem=next(k for k in ['process_peak_held_bytes','peak_after_bytes'] if k in a['medians'])
  rec=dict(stage=label,engine=engine,**key,cpu_before_ms=b['medians']['total_cpu_ns']/1e6,cpu_after_ms=a['medians']['total_cpu_ns']/1e6,cpu_change_percent=100*(a['medians']['total_cpu_ns']/b['medians']['total_cpu_ns']-1),elapsed_before_ms=b['medians']['total_ns']/1e6,elapsed_after_ms=a['medians']['total_ns']/1e6,peak_before_mib=b['medians'][mem]/2**20,peak_after_mib=a['medians'][mem]/2**20)
  pairs.append(rec);rows.append(rec)
 lines=['# '+label.replace('-',' ')+' results','','CPU is process user-plus-system time. Peak RSS is a whole-process high-water mark. Elapsed time is separate.','','| Scope / case | Policy / candidate | CPU before ms | CPU after ms | Change | Elapsed before / after ms | Peak before / after MiB |','|---|---|---:|---:|---:|---:|---:|']
 for a in pairs:lines.append(f"| {a.get('scope','eager')} / {a['case']} | {a.get('policy',a.get('mode',''))} {a['engine']} | {a['cpu_before_ms']:.3f} | {a['cpu_after_ms']:.3f} | {a['cpu_change_percent']:+.1f}% | {a['elapsed_before_ms']:.3f} / {a['elapsed_after_ms']:.3f} | {a['peak_before_mib']:.2f} / {a['peak_after_mib']:.2f} |")
 (R/(label+'.md')).write_text('\n'.join(lines)+'\n')
(R/'comparison-summary.json').write_text(json.dumps(rows,indent=2)+'\n')
print({stage:sum(a['stage']==stage for a in rows) for stage in sorted(set(a['stage'] for a in rows))})
