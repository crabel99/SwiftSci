from pathlib import Path
import csv,hashlib,json,struct,subprocess,sys,statistics as st
R=Path(__file__).resolve().parent;E=Path('/private/tmp/swiftsci-csv-cpu-profile-20261021');C=Path('/private/tmp/swiftsci-csv-conversion-profile-20261021');sys.path.insert(0,'/private/tmp/swiftsci-csv-count-only-scan-20261021/Benchmarks/Tools')
from execution_policy import worker_environment,PRODUCTION_MODE
src=json.loads((E/'inputs/Aotizhongxin.json').read_text());rows=list(csv.reader(Path(src['path']).open()))[1:];result=[]
for name in ['No','PM2.5','wd','station']:
 j=src['names'].index(name);typ=src['types'][j]
 for n in [10000,len(rows)]:
  selected=[r[j] for r in rows[:n]];label=f'{name.replace(".","")}-{n}';p=R/(label+'.csv')
  with p.open('w') as f:csv.writer(f,lineterminator='\n').writerows([[name],*[[s] for s in selected]])
  h=hashlib.sha256();nulls=0
  for raw in selected:
   value=raw.strip()
   if value in src['null_tokens']:h.update(b'\0');nulls+=1;continue
   h.update(b'\1')
   if typ=='String':b=value.encode();h.update(struct.pack('<I',len(b)));h.update(b)
   else:h.update(struct.pack('<d',float(value)))
  inp=dict(id=label,path=str(p),rows=len(selected),names=[name],types=[typ],hashes=[h.hexdigest()],integral=[src['integral'][j]],null_tokens=src['null_tokens'],null_counts=[nulls],delimiter=',',max_rows=None,source_sha256=hashlib.sha256(p.read_bytes()).hexdigest());contract=p.with_suffix('.json');contract.write_text(json.dumps(inp,indent=2)+'\n')
  for scope in ['eager','stream']:
   vals={e:[] for e in ['original','current']}
   for rnd in range(6):
    for e in (list(vals) if rnd%2==0 else list(reversed(vals))):
     binary=(E/'build/indexed/ResourceProbe' if e=='original' else C/'build/production/ResourceProbe') if scope=='eager' else (E/'aux/indexed/StreamProbe' if e=='original' else C/'build/production/StreamProbe')
     args=[str(contract),'known','fresh','1'] if scope=='eager' else [str(contract),'10000'];run=subprocess.run([str(binary),*args],env=worker_environment(PRODUCTION_MODE),capture_output=True,text=True);assert run.returncode==0,run.stderr;d=json.loads(run.stdout);assert d['validated'],d;vals[e].append(d)
   med={e:st.median(d.get('samples',[d])[0]['total_cpu_ns'] for d in ds) for e,ds in vals.items()};ratio=med['current']/med['original'];result.append(dict(case=label,scope=scope,workers=vals,medians=med,cpu_ratio=ratio));print(label,typ,scope,{e:round(v/1e6,3) for e,v in med.items()},round(ratio,3),flush=True)
(R/'minimization.json').write_text(json.dumps(result,indent=2)+'\n')
