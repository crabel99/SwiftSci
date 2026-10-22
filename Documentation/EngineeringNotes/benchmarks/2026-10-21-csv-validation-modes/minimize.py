from pathlib import Path
import csv,datetime as dt,hashlib,json,struct,subprocess,sys,statistics as st
R=Path(__file__).resolve().parent;E=Path('/private/tmp/swiftsci-csv-cpu-profile-20261021');S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');sys.path.insert(0,str(S/'Benchmarks/Tools'))
from execution_policy import worker_environment,PRODUCTION_MODE
source=json.loads((E/'inputs/unique-shuffled.json').read_text());rows=list(csv.reader(Path(source['path']).open()))[1:];results=[]
for n,colcount in [(100000,1),(10000,1),(1000,1),(10000,2)]:
 selected=[r[:colcount] for r in rows[:n]];p=R/f'date-{n}-{colcount}.csv'
 with p.open('w') as f:csv.writer(f,lineterminator='\n').writerows([source['names'][:colcount],*selected])
 hashes=[]
 for j in range(colcount):
  h=hashlib.sha256()
  for r in selected:
   v=(dt.datetime.combine(dt.date.fromisoformat(r[j]),dt.time(),dt.timezone.utc).timestamp() if j==0 else float(r[j]));h.update(b'\x01'+struct.pack('<d',v))
  hashes.append(h.hexdigest())
 inp=dict(source,id=p.stem,path=str(p),rows=n,names=source['names'][:colcount],types=source['types'][:colcount],integral=source['integral'][:colcount],hashes=hashes,null_counts=[0]*colcount,source_sha256=hashlib.sha256(p.read_bytes()).hexdigest());c=p.with_suffix('.json');c.write_text(json.dumps(inp,indent=2)+'\n')
 values={e:[] for e in ['indexed','count-only']}
 for rnd in range(6):
  for e in (list(values) if rnd%2==0 else list(reversed(values))):
   run=subprocess.run([str(E/'aux'/e/'StreamProbe'),str(c),'10000'],env=worker_environment(PRODUCTION_MODE),capture_output=True,text=True);assert run.returncode==0,run.stderr;d=json.loads(run.stdout);assert d['validated'];values[e].append(d)
 med={e:st.median(d['total_cpu_ns'] for d in ds) for e,ds in values.items()};ratio=med['count-only']/med['indexed'];results.append(dict(rows=n,columns=colcount,workers=values,medians=med,cpu_ratio=ratio));print(n,colcount,{k:round(v/1e6,3) for k,v in med.items()},round(ratio,3),flush=True)
(R/'minimization.json').write_text(json.dumps(results,indent=2)+'\n')
