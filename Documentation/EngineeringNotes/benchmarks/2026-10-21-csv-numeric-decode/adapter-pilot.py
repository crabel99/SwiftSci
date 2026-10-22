from pathlib import Path
import hashlib,json,subprocess,statistics as st,sys
R=Path(__file__).resolve().parent;E=Path('/private/tmp/swiftsci-csv-cpu-profile-20261021');C=Path('/private/tmp/swiftsci-csv-conversion-profile-20261021');sys.path.insert(0,'/private/tmp/swiftsci-csv-count-only-scan-20261021/Benchmarks/Tools')
from execution_policy import worker_environment,PRODUCTION_MODE
from runner import power_state
output=R/'adapter-pilot.json';assert not output.exists();assert power_state()['source']=='AC'
engines=['current','direct','inline','combined'];bins={};receipts={}
for label in engines:
 d=C/'build/production' if label=='current' else R/'build'/label;record=json.loads((d/'build.json').read_text());bins[label]={'eager':d/'ResourceProbe'}
 cmd=[str(R/'StreamProbe.swift') if a.endswith('/ResourceProbe.swift') else a for a in record['commands'][1]];b=R/(label+'-StreamPilot');cmd[cmd.index('-o')+1]=str(b)
 p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stderr;bins[label]['stream']=b;receipts[label]=dict(command=cmd,eager_sha256=hashlib.sha256(bins[label]['eager'].read_bytes()).hexdigest(),stream_sha256=hashlib.sha256(b.read_bytes()).hexdigest(),module_receipt_sha256=hashlib.sha256((d/'build.json').read_bytes()).hexdigest())
orders=[engines[i:]+engines[:i] for i in range(4)]+[list(reversed(engines[i:]+engines[:i])) for i in range(4)];records=[]
cases=[('wide',E/'inputs/Aotizhongxin.json','eager','known'),('numeric',C/'nullable-0.json','eager','infer'),('numeric-known',C/'nullable-0.json','eager','known'),('double',R/'PM25-35064.json','stream','known'),('string',R/'station-35064.json','stream','known'),('power',E/'inputs/energy-date-full.json','stream','known')]
for case,path,scope,mode in cases:
 for rnd,order in enumerate(orders):
  for label in order:
   args=[str(path),'10000'] if scope=='stream' else [str(path),mode,'fresh','1'];p=subprocess.run([str(bins[label][scope]),*args],capture_output=True,text=True,env=worker_environment(PRODUCTION_MODE));assert p.returncode==0,p.stderr;d=json.loads(p.stdout);assert d['validated'];sample=d.get('samples',[d])[0];records.append(dict(case=case,engine=label,round=rnd,scope=scope,mode=mode,result=d,cpu_ns=sample['total_cpu_ns'],elapsed_ns=sample['total_ns']))
 print(case,{e:{'cpu_ms':round(st.median(r['cpu_ns'] for r in records if r['case']==case and r['engine']==e)/1e6,3),'wall_ms':round(st.median(r['elapsed_ns'] for r in records if r['case']==case and r['engine']==e)/1e6,3)} for e in engines},flush=True)
output.write_text(json.dumps(dict(records=records,receipts=receipts,orders=orders),indent=2)+'\n');assert power_state()['source']=='AC'
