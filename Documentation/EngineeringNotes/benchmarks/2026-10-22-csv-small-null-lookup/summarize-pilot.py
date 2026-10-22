from pathlib import Path
import json,statistics as st
R=Path(__file__).resolve().parent;records=json.loads((R/'pilot.json').read_text())['records'];summary=[]
for key in dict.fromkeys((r['result']['input'],r['mode'],r['policy'],r['engine']) for r in records):
 ds=[r['result']['samples'][0] for r in records if (r['result']['input'],r['mode'],r['policy'],r['engine'])==key]
 summary.append(dict(case=key[0],mode=key[1],policy=key[2],engine=key[3],samples=len(ds),medians={k:st.median(d[k] for d in ds) for k in ['total_cpu_ns','total_ns','process_peak_held_bytes']}))
(R/'pilot-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
for a in summary:
 if a['engine']=='parent':continue
 b=next(b for b in summary if b['engine']=='parent' and (b['case'],b['mode'],b['policy'])==(a['case'],a['mode'],a['policy']))
 a['cpu_ratio']=a['medians']['total_cpu_ns']/b['medians']['total_cpu_ns'];a['wall_ratio']=a['medians']['total_ns']/b['medians']['total_ns']
 if a['cpu_ratio']>1.05:print('CPU review',a['case'],a['policy'],a['engine'],round(a['cpu_ratio'],3))
print('Energy CPU ratios',[(a['mode'],a['policy'],a['engine'],round(a['cpu_ratio'],3)) for a in summary if a['engine']!='parent' and a['case']=='energy'])
(R/'pilot-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
