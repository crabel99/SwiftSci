from pathlib import Path
import csv,hashlib,json,statistics as st,struct,subprocess,sys
R=Path(__file__).resolve().parent;P=Path('/private/tmp/swiftsci-csv-batch-profile-20261022');O=Path('/private/tmp/swiftsci-csv-cpu-profile-20261021');sys.path.insert(0,'/private/tmp/swiftsci-csv-count-only-scan-20261021/Benchmarks/Tools')
from execution_policy import worker_environment,PRODUCTION_MODE
from runner import power_state
assert power_state()['source']=='AC';assert not (R/'minimization.json').exists()
bins={'original':O/'build/indexed/ResourceProbe','current':P/'build/production/ResourceProbe'};records=[];data=list(csv.reader((P/'nullable-0.csv').open()))
for count,indices in [(16384,[0,1]),(100000,[0,1]),(100000,[0]),(100000,[1])]:
 rows=[[row[j] for j in indices] for row in data[:count+1]];p=R/f'numeric-{count}-{len(indices)}-{indices[0]}.csv'
 with p.open('w') as f:csv.writer(f,lineterminator='\n').writerows(rows)
 hs=[hashlib.sha256() for _ in indices]
 for row in rows[1:]:
  for j,v in enumerate(row):hs[j].update(b'\1'+struct.pack('<d',float(v)))
 inp=dict(id=p.stem,path=str(p),rows=count,names=rows[0],types=[['Int64','Double'][i] for i in indices],integral=[i==0 for i in indices],hashes=[h.hexdigest() for h in hs],null_tokens=['','NA'],null_counts=[0]*len(indices),delimiter=',',max_rows=None,sha256=hashlib.sha256(p.read_bytes()).hexdigest());c=p.with_suffix('.json');c.write_text(json.dumps(inp,indent=2)+'\n')
 for mode in ['known','infer']:
  for rnd in range(6):
   for e in (list(bins) if rnd%2==0 else list(reversed(bins))):
    assert power_state()['source']=='AC'
    d=subprocess.run([str(bins[e]),str(c),mode,'fresh','1'],env=worker_environment(PRODUCTION_MODE),capture_output=True,text=True,timeout=120);assert d.returncode==0,d.stderr;v=json.loads(d.stdout);assert v['validated'];records.append(dict(case=p.stem,rows=count,indices=indices,mode=mode,round=rnd,engine=e,result=v))
  med={e:st.median(d['result']['samples'][0]['total_cpu_ns'] for d in records if (d['case'],d['mode'],d['engine'])==(p.stem,mode,e)) for e in bins};print(p.stem,mode,{e:round(v/1e6,3) for e,v in med.items()},'ratio',round(med['current']/med['original'],3),flush=True)
(R/'minimization.json').write_text(json.dumps(dict(records=records,binaries={e:dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for e,p in bins.items()}),indent=2)+'\n')
