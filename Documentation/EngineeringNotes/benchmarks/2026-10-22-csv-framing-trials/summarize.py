from pathlib import Path
import json,statistics as st,re,collections
R=Path(__file__).resolve().parent
rows=[]
for file in ['pilot.json','derived-pilot.json']:
 records=json.loads((R/file).read_text())['records']
 # The early printed width labels omitted row count. Native worker input IDs
 # preserve the exact contracts and separate those cohorts here.
 keys=list(dict.fromkeys((r['result']['input'],r['mode'],r['policy'],r['engine']) for r in records))
 for case,mode,policy,engine in keys:
  ds=[r['result']['samples'][0] for r in records if (r['result']['input'],r['mode'],r['policy'],r['engine'])==(case,mode,policy,engine)]
  rows.append(dict(run=file,case=case,mode=mode,policy=policy,engine=engine,samples=len(ds),medians={k:st.median(d[k] for d in ds) for k in ['total_cpu_ns','total_ns','process_peak_held_bytes']}))
(R/'public-read-summary.json').write_text(json.dumps(rows,indent=2)+'\n')
allocs={}
for label in ['parent','consume','header','derived-count']:
 lines=(R/('allocation-full-'+label+'-events.txt')).read_text().splitlines();events=collections.Counter(line.split(' ',1)[0] for line in lines if re.match(r'^(ALLOC|FREE|VM_)',line));selected=[]
 for line in lines:
  if line.startswith('ALLOC ') and 'SystemsCSVParser.scan' in line:
   selected.append(dict(size=int(re.search(r'\[size=(\d+)\]',line)[1]),frames=[x.split(') ',1)[-1] for x in line.split(' | ') if '(AllocationProbe-' in x]))
 allocs[label]=dict(events=dict(events),scanner_calls=len(selected),scanner_bytes=sum(x['size'] for x in selected),scanner_allocations=selected)
(R/'allocation-full-summary.json').write_text(json.dumps(allocs,indent=2)+'\n')
print('public read workers',sum(r['samples'] for r in rows))
for e,d in allocs.items():print(e,d['scanner_calls'],d['scanner_bytes'])
