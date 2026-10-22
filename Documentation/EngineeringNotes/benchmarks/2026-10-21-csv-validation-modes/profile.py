from pathlib import Path
import json,subprocess,sys,hashlib,statistics as st
R=Path(__file__).resolve().parent;E=Path('/private/tmp/swiftsci-csv-cpu-profile-20261021');sys.path.insert(0,'/private/tmp/swiftsci-csv-count-only-scan-20261021/Benchmarks/Tools')
from execution_policy import worker_environment,PRODUCTION_MODE
for label in ['original','current']:
 d=R/'build'/label;receipt=json.loads((d/'build.json').read_text());cmd=[str(R/'StreamProbe.swift') if a==str(R/'ResourceProbe.swift') else a for a in receipt['commands'][1]];cmd[cmd.index('-o')+1]=str(d/'StreamProbe')
 p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stderr
 (d/'stream-build.json').write_text(json.dumps(dict(command=cmd,binary_sha256=hashlib.sha256((d/'StreamProbe').read_bytes()).hexdigest()),indent=2)+'\n')
records=[]
for case in ['date-100000-1','unique-shuffled','Aotizhongxin','energy-date-full']:
 path=R/(case+'.json') if case.startswith('date-') else E/'inputs'/(case+'.json')
 for rnd in range(6):
  for label in (['original','current'] if rnd%2==0 else ['current','original']):
   p=subprocess.run([str(R/'build'/label/'StreamProbe'),str(path),'10000'],capture_output=True,text=True,env=worker_environment(PRODUCTION_MODE));assert p.returncode==0,p.stderr
   d=json.loads(p.stdout);assert d['validated'];phases=[json.loads(l) for l in p.stderr.splitlines()];assert len(phases)==2 and all(d['tag']=='CSV-CONVERSION-20261021' for d in phases)
   records.append(dict(case=case,engine=label,round=rnd,result=d,phases=phases))
 for label in ['original','current']:
  subset=[d for d in records if d['case']==case and d['engine']==label];print(case,label,{k:round(st.median(d['phases'][0]['cpu_ns'][k] for d in subset)/1e6,3) for k in subset[0]['phases'][0]['cpu_ns']},flush=True)
(R/'stage-profile.json').write_text(json.dumps(records,indent=2)+'\n')
