from pathlib import Path
import csv,hashlib,json,struct,subprocess,sys,statistics as st
R=Path(__file__).resolve().parent;E=Path('/private/tmp/swiftsci-csv-cell-profile-20261021');O=Path('/private/tmp/swiftsci-csv-eager-checks-20261021');sys.path.insert(0,'/private/tmp/swiftsci-csv-count-only-scan-20261021/Benchmarks/Tools')
from execution_policy import worker_environment,PRODUCTION_MODE
from runner import power_state
assert power_state()['source']=='AC'
engines=['original','before','production'];bins={'original':O/'build/indexed/ResourceProbe','before':E/'build/production/ResourceProbe','production':R/'build/production/ResourceProbe'}
output=R/'final-null-measurement.json';assert not output.exists(), 'Choose a fresh output path; never overwrite a prior measurement'
records=[]
# The eager phase already verifies all source and binary receipts. Recheck binary hashes here.
plan=json.loads((R/'final-measurement/plan.json').read_text())
for e,p in bins.items():
 label='indexed' if e=='original' else e
 assert hashlib.sha256(p.read_bytes()).hexdigest()==plan['builds'][label]['binary_sha256']
orders=[engines[i:]+engines[:i] for i in range(3)]+[list(reversed(engines[i:]+engines[:i])) for i in range(3)]
for pct in [0,50,90]:
 rows=[];hashes=[hashlib.sha256(),hashlib.sha256()];nulls=[0,0]
 for i in range(100000):
  row=[]
  for j in range(2):
   missing=(i*37+j*17)%100<pct
   if missing: row.append('NA');hashes[j].update(b'\0');nulls[j]+=1
   else:
    value=i%137+42 if j==0 else (i%137+42)/8;row.append(str(value));hashes[j].update(b'\1'+struct.pack('<d',float(value)))
  rows.append(row)
 p=R/f'nullable-{pct}.csv'
 with p.open('w') as f:csv.writer(f,lineterminator='\n').writerows([['integer','double'],*rows])
 inp=dict(id=p.stem,path=str(p),rows=len(rows),names=['integer','double'],types=['Int64','Double'],integral=[True,False],hashes=[h.hexdigest() for h in hashes],null_tokens=['','NA'],null_counts=nulls,delimiter=',',max_rows=None,source_sha256=hashlib.sha256(p.read_bytes()).hexdigest());c=p.with_suffix('.json');c.write_text(json.dumps(inp,indent=2)+'\n')
 for mode in (['infer'] if pct==0 else ['infer','known']):
  for rnd,order in enumerate(orders):
   for e in order:
    assert power_state()['source']=='AC'
    p=subprocess.run([str(bins[e]),str(c),mode,'fresh','1'],capture_output=True,text=True,env=worker_environment(PRODUCTION_MODE),timeout=120);assert p.returncode==0,p.stderr;d=json.loads(p.stdout);assert d['validated'];records.append(dict(null_percent=pct,mode=mode,round=rnd,engine=e,result=d))
  print(pct,mode,{e:round(st.median(d['result']['samples'][0]['total_cpu_ns'] for d in records if d['null_percent']==pct and d['mode']==mode and d['engine']==e)/1e6,3) for e in engines},flush=True)
output.write_text(json.dumps(dict(records=records,orders=orders,binaries={e:dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for e,p in bins.items()}),indent=2)+'\n')
