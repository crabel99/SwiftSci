from pathlib import Path
import json,statistics as st
R=Path(__file__).resolve().parent;reports={}
for name,keys,count in [('final-measurement',['total_cpu_ns','total_ns','process_peak_held_bytes','rss_held_delta_bytes','held_heap_delta_bytes'],162),('final-stream-measurement',['total_cpu_ns','total_ns','peak_after_bytes','rss_after_bytes','heap_after_bytes'],108)]:
 ds=[json.loads(l) for l in (R/name/'workers.jsonl').read_text().splitlines()];assert len(ds)==count and all(d['validated'] for d in ds)
 groups={}
 signatures={}
 for d in ds:
  if 'checks' not in d:continue
  key=(d['case'],d.get('mode'));signature=d['checks']['columns']
  if key in signatures:assert signatures[key]==signature,(key,'native output differs between engines')
  signatures[key]=signature
 for d in ds:groups.setdefault((d['case'],d.get('mode'),d['engine']),[]).append(d.get('samples',[d])[0])
 rows=[]
 for (case,mode,engine),ss in groups.items():
  assert len(ss)==6;v={k:st.median(s[k] for s in ss) for k in keys};v.update(case=case,engine=engine,workers=6)
  if mode is not None:v['mode']=mode
  rows.append(v)
 summary=dict(workers=len(ds),all_validated=True,medians=rows);reports[name]=summary;(R/name/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
null=json.loads((R/'final-null-measurement.json').read_text());assert len(null['records'])==90
assert all(d['result']['validated'] for d in null['records'])
signatures={}
for d in null['records']:
 key=(d['null_percent'],d['mode']);signature=d['result']['checks']['columns']
 if key in signatures:assert signatures[key]==signature,(key,'native output differs between engines')
 signatures[key]=signature
rows=[]
for pct,mode in [(0,'infer'),(50,'infer'),(50,'known'),(90,'infer'),(90,'known')]:
 for e in ['original','before','production']:
  ss=[d['result']['samples'][0] for d in null['records'] if (d['null_percent'],d['mode'],d['engine'])==(pct,mode,e)];assert len(ss)==6
  rows.append(dict(null_percent=pct,mode=mode,engine=e,workers=6,**{k:st.median(d[k] for d in ss) for k in ['total_cpu_ns','total_ns','process_peak_held_bytes']}))
(R/'final-null-summary.json').write_text(json.dumps(dict(workers=90,all_validated=True,medians=rows),indent=2)+'\n')
comparisons=[]
for name,report in reports.items():
 for a in report['medians']:
  if a['engine']!='production':continue
  for control in ['indexed','before']:
   b=next(r for r in report['medians'] if (r['case'],r.get('mode'),r['engine'])==(a['case'],a.get('mode'),control));ratio=a['total_cpu_ns']/b['total_cpu_ns'];comparisons.append(dict(scope=name,case=a['case'],mode=a.get('mode'),control=control,cpu_ratio=ratio,cpu_review_required=ratio>1.10))
for a in rows:
 if a['engine']!='production':continue
 for control in ['original','before']:
  b=next(r for r in rows if (r['null_percent'],r['mode'],r['engine'])==(a['null_percent'],a['mode'],control));ratio=a['total_cpu_ns']/b['total_cpu_ns'];comparisons.append(dict(scope='null',case=str(a['null_percent']),mode=a['mode'],control=control,cpu_ratio=ratio,cpu_review_required=ratio>1.10))
verdict=dict(validated_resource_workers=360,comparisons=comparisons,new_cpu_regressions_above_review_limit=[d for d in comparisons if d['control']=='before' and d['cpu_review_required']],default_promotion_blockers=[d for d in comparisons if d['control'] in ['indexed','original'] and d['cpu_review_required']])
(R/'gate-verdict.json').write_text(json.dumps(verdict,indent=2)+'\n')
for name,report in reports.items():
 print(name)
 for a in report['medians']:
  if a['engine']!='production':continue
  refs={r['engine']:r for r in report['medians'] if r['case']==a['case'] and r.get('mode')==a.get('mode')}
  print(a['case'],a.get('mode',''), {e:round(v['total_cpu_ns']/1e6,3) for e,v in refs.items()},'new vs before',round((a['total_cpu_ns']/refs['before']['total_cpu_ns']-1)*100,1),'%')
print('New CPU review cases',len(verdict['new_cpu_regressions_above_review_limit']),'Original-reader blockers',len(verdict['default_promotion_blockers']))
