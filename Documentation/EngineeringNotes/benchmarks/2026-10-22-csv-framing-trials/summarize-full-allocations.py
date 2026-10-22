from pathlib import Path
import re,json,collections
R=Path(__file__).resolve().parent;report={}
for label in ['parent','consume','header']:
 lines=(R/('allocation-full-'+label+'-events.txt')).read_text().splitlines();counts=collections.Counter();allocs=[]
 for line in lines:
  if (m:=re.match(r'([A-Z_]+) .*?\[size=(\d+)\]:',line)):
   tag,size=m.group(1),int(m.group(2));counts[tag]+=1
   if tag=='ALLOC' and 'SystemsCSVParser.scan' in line:
    frames=[x.split(') ',1)[-1] for x in line.split(' | ') if '(AllocationProbe-' in x]
    allocs.append(dict(size=size,frames=frames))
 report[label]=dict(events=dict(counts),scanner_allocations=allocs,scanner_calls=len(allocs),scanner_bytes=sum(a['size'] for a in allocs))
 print(label,dict(counts),'scanner allocs',len(allocs),'bytes',report[label]['scanner_bytes'])
 print('sizes',dict(collections.Counter(a['size'] for a in allocs)))
 print('stderr', (R/('allocation-full-'+label+'.stderr')).read_text()[:800])
(R/'allocation-full-summary.json').write_text(json.dumps(report,indent=2)+'\n')
