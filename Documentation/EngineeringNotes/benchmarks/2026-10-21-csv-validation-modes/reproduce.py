from pathlib import Path
import hashlib,json,statistics as st,subprocess,sys
R=Path(__file__).resolve().parent;E=Path('/private/tmp/swiftsci-csv-cpu-profile-20261021');S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');sys.path.insert(0,str(S/'Benchmarks/Tools'))
from execution_policy import worker_environment,PRODUCTION_MODE
from runner import power_state
assert power_state()['source']=='AC'
records=[]
for case,scope in [('unique-shuffled','stream'),('Aotizhongxin','eager')]:
 for rnd in range(6):
  for engine in (['indexed','count-only'] if rnd%2==0 else ['count-only','indexed']):
   b=E/('aux' if scope=='stream' else 'build')/engine/('StreamProbe' if scope=='stream' else 'ResourceProbe')
   args=[str(E/'inputs'/(case+'.json')),'10000'] if scope=='stream' else [str(E/'inputs'/(case+'.json')),'known','fresh','1']
   p=subprocess.run([str(b),*args],env=worker_environment(PRODUCTION_MODE),capture_output=True,text=True,timeout=60);assert p.returncode==0,p.stderr
   d=json.loads(p.stdout);assert d['validated'];sample=d.get('samples',[d])[0]
   records.append(dict(case=case,scope=scope,engine=engine,round=rnd,binary_sha256=hashlib.sha256(b.read_bytes()).hexdigest(),cpu_ns=sample['total_cpu_ns'],result=d))
verdict=[]
for case in ['unique-shuffled','Aotizhongxin']:
 m={e:st.median(r['cpu_ns'] for r in records if r['case']==case and r['engine']==e) for e in ['indexed','count-only']}
 ratio=m['count-only']/m['indexed'];verdict.append(dict(case=case,medians=m,cpu_ratio=ratio,passes=ratio<=1.10));print(case,{k:round(v/1e6,3) for k,v in m.items()},'ratio',round(ratio,3),'PASS' if ratio<=1.1 else 'RED',flush=True)
(R/'repro.json').write_text(json.dumps(dict(records=records,verdict=verdict),indent=2)+'\n')
raise SystemExit(0 if all(v['passes'] for v in verdict) else 1)
