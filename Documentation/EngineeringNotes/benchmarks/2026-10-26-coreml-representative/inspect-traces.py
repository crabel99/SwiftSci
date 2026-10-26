"""Export and bind actual Core ML dispatches to the owned measurement interval."""
from pathlib import Path
import collections, hashlib, json, subprocess, xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parent
folder=ROOT/'traces'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def rows(path):
 ids={};columns=[]
 for _,element in E.iterparse(path,events=['end']):
  if element.tag=='schema':columns=[col.findtext('mnemonic') for col in element.findall('col')]
  if 'id' in element.attrib:
   ids[element.attrib['id']]=(element.text or element.get('fmt'),element.get('fmt'))
  if element.tag=='row':
   cells=[]
   for child in element:
    if 'ref' in child.attrib:value=ids[child.attrib['ref']]
    else:value=(child.text or child.get('fmt'),child.get('fmt'))
    cells.append(value)
   assert len(columns)==len(cells),(columns,cells)
   yield dict(zip(columns,cells))
   element.clear()
summary=[]
for name in ['wdbc-cpu','wdbc-neural','wine-cpu','wine-neural']:
 toc=folder/(name+'.toc.xml');data=E.parse(toc)
 target=data.find('./run/info/target/process');assert target.get('name')=='ProfileWorker' and target.get('return-exit-status')=='0'
 pid=int(target.get('pid'))
 table=data.find("./run/data/table[@schema='coreml-os-signpost']");assert table.get('target-pid')=='SINGLE'
 paths={}
 for key,schema in [('coreml','coreml-os-signpost'),('intervals','OSSignpostIntervals'),('ane','ane-hw-intervals')]:
  out=folder/(name+'.'+key+'.xml');paths[key]=out
  if not out.exists():
   subprocess.run(['xcrun','xctrace','export','--input',str(folder/(name+'.trace')),'--xpath',f'/trace-toc/run[@number="1"]/data/table[@schema="{schema}"]','--output',str(out)],check=True,timeout=120)
 intervals=[row for row in rows(paths['intervals']) if row['name'][0]=='CoreML measurement']
 assert len(intervals)==1
 interval=intervals[0];assert interval['subsystem'][0]=='org.swiftsci.benchmarks' and f'({pid})' in interval['process'][1]
 start=int(interval['start'][0]);end=start+int(interval['duration'][0])
 counts=collections.Counter();dispatches=collections.Counter();models=collections.Counter();first=[];last=collections.deque(maxlen=5)
 for row in rows(paths['coreml']):
  time=int(row['start'][0]);duration=int(row['duration'][0])
  if start<=time and time+duration<=end:
   event=row['event-label'][0];counts[event]+=1
   if row['event-type'][0]=='model-dispatch-event':
    dispatches[event]+=1;models[row['model-name'][0]]+=1
    sample=dict(start_ns=time,duration_ns=duration,event=event,model=row['model-name'][0])
    if len(first)<5:first.append(sample)
    last.append(sample)
 record=json.loads((folder/(name+'.json')).read_text());expected=sum(c['latency']['count'] for c in record['callers'])
 assert counts['Prediction']==expected,(name,counts['Prediction'],expected)
 assert dispatches['CPU']==expected and sum(dispatches.values())==expected,(name,dispatches,expected)
 item=dict(name=name,target_pid=pid,modelSHA256=record['modelSHA256'],measurement_start_ns=start,measurement_end_ns=end,
  completed_requests=expected,event_counts=dict(counts),dispatch_counts=dict(dispatches),models=dict(models),first_dispatches=first,last_dispatches=list(last),
  event_exports={key:dict(path=str(path),sha256=sha(path),size_bytes=path.stat().st_size) for key,path in paths.items()},
  toc_sha256=sha(toc),record_sha256=sha(folder/(name+'.json')),
  attribution='Positive CPU dispatch events for every completed request of the target process inside its measurement signpost. No other Core ML device dispatch is present in that interval. This does not establish Neural Engine support or activity for other artifacts.')
 summary.append(item)
 print(name,expected,dict(dispatches),flush=True)
(folder/'inspected-events.json').write_text(json.dumps(summary,indent=2)+'\n')
