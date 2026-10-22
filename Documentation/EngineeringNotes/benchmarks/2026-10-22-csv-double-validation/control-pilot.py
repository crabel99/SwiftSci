from pathlib import Path
import json,hashlib,subprocess,statistics as st,sys
R=Path(__file__).resolve().parent;P=Path('/private/tmp/swiftsci-csv-batch-profile-20261022');E=Path('/private/tmp/swiftsci-csv-cpu-profile-20261021');A=Path('/private/tmp/swiftsci-csv-cell-profile-20261021');sys.path.insert(0,'/private/tmp/swiftsci-csv-count-only-scan-20261021/Benchmarks/Tools')
from execution_policy import worker_environment,PRODUCTION_MODE
from runner import power_state
assert not (R/'control-pilot.json').exists()
engines=['current','lean','closure'];bins={};receipts={}
for e in engines:
 d=P/'build/production' if e=='current' else R/'build'/e;record=json.loads((d/'build.json').read_text());b=R/(e+'-StreamControl');cmd=[str(R/'StreamProbe.swift') if a.endswith('/ResourceProbe.swift') else a for a in record['commands'][1]];cmd[cmd.index('-o')+1]=str(b);p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stderr;bins[e]={'eager':d/'ResourceProbe','stream':b};receipts[e]=dict(command=cmd,stream_sha256=hashlib.sha256(b.read_bytes()).hexdigest(),module_receipt_sha256=hashlib.sha256((d/'build.json').read_bytes()).hexdigest())
orders=[engines[i:]+engines[:i] for i in range(3)]+[list(reversed(engines[i:]+engines[:i])) for i in range(3)];records=[]
cases=[('date',A/'date-100000-1.json','stream','known'),('date-power',E/'inputs/energy-date-full.json','stream','known'),('string',A/'station-35064.json','stream','known'),('null-half',P/'nullable-50.json','eager','infer'),('null-half-known',P/'nullable-50.json','eager','known'),('late-bool',E/'inputs/late-bool.json','eager','infer'),('late-text',E/'inputs/late-text.json','eager','infer'),('wide-known',E/'inputs/Aotizhongxin.json','eager','known')]
for case,path,scope,mode in cases:
 for rnd,order in enumerate(orders):
  for e in order:
   assert power_state()['source']=='AC';args=[str(path),'10000'] if scope=='stream' else [str(path),mode,'fresh','1'];p=subprocess.run([str(bins[e][scope]),*args],capture_output=True,text=True,env=worker_environment(PRODUCTION_MODE),timeout=120);assert p.returncode==0,p.stderr;d=json.loads(p.stdout);assert d['validated'];s=d.get('samples',[d])[0];records.append(dict(case=case,scope=scope,mode=mode,engine=e,round=rnd,result=d,cpu_ns=s['total_cpu_ns']))
 print(case,{e:round(st.median(d['cpu_ns'] for d in records if d['case']==case and d['engine']==e)/1e6,3) for e in engines},flush=True)
(R/'control-pilot.json').write_text(json.dumps(dict(records=records,orders=orders,receipts=receipts),indent=2)+'\n')
