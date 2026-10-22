from pathlib import Path
import hashlib,json,subprocess,statistics as st,sys,time
R=Path(__file__).resolve().parent;P=Path('/private/tmp/swiftsci-csv-batch-profile-20261022');E=Path('/private/tmp/swiftsci-csv-cpu-profile-20261021');sys.path.insert(0,'/private/tmp/swiftsci-csv-count-only-scan-20261021/Benchmarks/Tools')
from execution_policy import worker_environment,PRODUCTION_MODE
from runner import power_state,verify_uninstrumented
assert not (R/'finalist-pilot.json').exists();start=time.time()
while not (R/'build/closure/build.json').exists():
 assert time.time()-start<300
 time.sleep(1)
engines=['current','concrete','lean','closure'];bins={};receipts={}
for e in engines:
 d=P/'build/production' if e=='current' else (E/'build/indexed' if e=='original' else R/'build'/e);record=json.loads((d/'build.json').read_text());b=d/'ResourceProbe';assert hashlib.sha256(b.read_bytes()).hexdigest()==record['binary_sha256'];verify_uninstrumented(b);bins[e]=b;receipts[e]=record
orders=[engines[i:]+engines[:i] for i in range(4)]+[list(reversed(engines[i:]+engines[:i])) for i in range(4)];records=[];signatures={}
cases=[('numeric',P/'nullable-0.json','infer'),('double',R/'numeric-100000-1-1.json','infer'),('numeric-known',P/'nullable-0.json','known'),('null-heavy',P/'nullable-90.json','infer'),('wide',E/'inputs/Aotizhongxin.json','infer'),('power',E/'inputs/energy.json','infer')]
for case,path,mode in cases:
 inp=json.loads(path.read_text());assert hashlib.sha256(Path(inp['path']).read_bytes()).hexdigest()==inp.get('sha256',inp.get('source_sha256'))
 for rnd,order in enumerate(orders):
  for e in order:
   assert power_state()['source']=='AC'
   p=subprocess.run([str(bins[e]),str(path),mode,'fresh','1'],capture_output=True,text=True,env=worker_environment(PRODUCTION_MODE),timeout=120);assert p.returncode==0,p.stderr;d=json.loads(p.stdout);assert d['validated'];sig=d['checks']['columns']
   if case in signatures:assert signatures[case]==sig
   signatures[case]=sig;s=d['samples'][0];records.append(dict(case=case,engine=e,round=rnd,mode=mode,result=d,cpu_ns=s['total_cpu_ns'],elapsed_ns=s['total_ns']))
 print(case,{e:{'cpu_ms':round(st.median(d['cpu_ns'] for d in records if d['case']==case and d['engine']==e)/1e6,3),'wall_ms':round(st.median(d['elapsed_ns'] for d in records if d['case']==case and d['engine']==e)/1e6,3)} for e in engines},flush=True)
(R/'finalist-pilot.json').write_text(json.dumps(dict(records=records,receipts=receipts,orders=orders),indent=2)+'\n')
