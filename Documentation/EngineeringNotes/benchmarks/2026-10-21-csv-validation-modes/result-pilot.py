from pathlib import Path
import hashlib,json,subprocess,statistics as st,sys
R=Path(__file__).resolve().parent;E=Path('/private/tmp/swiftsci-csv-cpu-profile-20261021');sys.path.insert(0,'/private/tmp/swiftsci-csv-count-only-scan-20261021/Benchmarks/Tools')
from execution_policy import worker_environment,PRODUCTION_MODE
from runner import power_state
assert power_state()['source']=='AC'
engines=['before','result'];builds={}
for e in engines:
 d=E/'build/count-only' if e=='before' else R/'build'/e
 receipt=json.loads((d/'build.json').read_text());cmd=[str(R/'StreamProbe.swift') if a.endswith('/ResourceProbe.swift') else a for a in receipt['commands'][1]];cmd[cmd.index('-o')+1]=str(d/'StreamPilot')
 p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stderr
 builds[e]=dict(eager=str(d/'ResourceProbe'),stream=str(d/'StreamPilot'),stream_sha256=hashlib.sha256((d/'StreamPilot').read_bytes()).hexdigest(),link=cmd,receipt_sha256=hashlib.sha256((d/'build.json').read_bytes()).hexdigest())
# All linking completes before any measurement.
records=[]
orders=[engines if i%2==0 else list(reversed(engines)) for i in range(6)]
for case,scope in [('date-100000-1','stream'),('unique-shuffled','stream'),('Aotizhongxin','eager'),('energy-date-full','stream')]:
 path=R/(case+'.json') if case.startswith('date-') else E/'inputs'/(case+'.json')
 for rnd,order in enumerate(orders):
  for e in order:
   args=[str(path),'10000'] if scope=='stream' else [str(path),'known','fresh','1']
   p=subprocess.run([builds[e][scope],*args],capture_output=True,text=True,env=worker_environment(PRODUCTION_MODE),timeout=120);assert p.returncode==0,p.stderr;d=json.loads(p.stdout);assert d['validated'];sample=d.get('samples',[d])[0]
   records.append(dict(case=case,scope=scope,engine=e,round=rnd,result=d,cpu_ns=sample['total_cpu_ns'],elapsed_ns=sample['total_ns']))
 for e in engines:
  ds=[d for d in records if d['case']==case and d['engine']==e];print(case,e,round(st.median(d['cpu_ns'] for d in ds)/1e6,3),'CPUms',round(st.median(d['elapsed_ns'] for d in ds)/1e6,3),'wallms',flush=True)
(R/'result-pilot.json').write_text(json.dumps(dict(builds=builds,orders=orders,records=records),indent=2)+'\n');assert power_state()['source']=='AC'
