from pathlib import Path
import json,statistics
R=Path(__file__).resolve().parent
reports={}
for name,keys in [('final-measurement',['total_cpu_ns','total_ns','process_peak_held_bytes','rss_held_delta_bytes','held_heap_delta_bytes']),('final-stream-measurement',['total_cpu_ns','total_ns','peak_after_bytes','rss_after_bytes','heap_after_bytes'])]:
 ds=[json.loads(l) for l in (R/name/'workers.jsonl').read_text().splitlines()]
 assert len(ds)==(162 if name=='final-measurement' else 90)
 assert all(d['validated'] for d in ds)
 groups={}
 for d in ds:groups.setdefault((d['case'],d.get('mode'),d['engine']),[]).append(d.get('samples',[d])[0])
 rows=[]
 for (case,mode,engine),ss in groups.items():
  assert len(ss)==6
  d={k:statistics.median(s[k] for s in ss) for k in keys};d.update(case=case,engine=engine,workers=len(ss))
  if mode is not None:d['mode']=mode
  rows.append(d)
 report=dict(workers=len(ds),all_validated=True,medians=rows)
 (R/name/'summary.json').write_text(json.dumps(report,indent=2)+'\n');reports[name]=report
checks=[]
for name,report in reports.items():
 for a in report['medians']:
  if a['engine']!='count-only':continue
  for control in ['indexed','counted']:
   b=next(v for v in report['medians'] if v['engine']==control and v['case']==a['case'] and v.get('mode')==a.get('mode'))
   ratio=a['total_cpu_ns']/b['total_cpu_ns']
   checks.append(dict(scope='stream' if 'stream' in name else 'eager',case=a['case'],mode=a.get('mode'),control=control,cpu_ratio=ratio,review_limit=1.10,cpu_review_required=ratio>1.10))
verdict=dict(all_native_workers_validated=True,eager_workers=162,stream_workers=90,cpu_comparisons=checks,ready_for_default_promotion=not any(c['cpu_review_required'] for c in checks),interpretation='Late-type pruning clears the former late-Boolean CPU review limit. Eager Beijing and broader inherited streaming regressions still block replacing the original reader. No failures or resource regressions are waived.')
(R/'gate-verdict.json').write_text(json.dumps(verdict,indent=2)+'\n')
print('252 validated workers. Default promotion:',verdict['ready_for_default_promotion'])
