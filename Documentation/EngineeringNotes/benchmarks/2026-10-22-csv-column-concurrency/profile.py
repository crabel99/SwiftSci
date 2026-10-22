from pathlib import Path
import json,subprocess,statistics,sys
R=Path(__file__).resolve().parent;E=Path('/private/tmp/swiftsci-csv-cpu-profile-20261021');C=Path('/private/tmp/swiftsci-csv-plan-profile-20261022');sys.path.insert(0,'/private/tmp/swiftsci-csv-count-only-scan-20261021/Benchmarks/Tools')
from execution_policy import worker_environment,PRODUCTION_MODE
records=[]
for case,path,mode in [('wide',E/'inputs/Aotizhongxin.json','known'),('numeric',C/'nullable-0.json','infer'),('energy',E/'inputs/energy-full.json','known')]:
 if not path.exists(): continue
 for rnd in range(12):
  p=subprocess.run([str(R/'build/profile/ResourceProbe'),str(path),mode,'fresh','1'],capture_output=True,text=True,env=worker_environment(PRODUCTION_MODE));assert p.returncode==0,p.stderr
  result=json.loads(p.stdout);assert result['validated'];phase=json.loads(p.stderr);assert phase['tag']=='CSV-CPU-20261022';records.append(dict(case=case,round=rnd,result=result,phase=phase))
 subset=[d for d in records if d['case']==case];print(case,{k:round(statistics.median(d['phase']['cpu_ns'][k] for d in subset)/1e6,3) for k in subset[0]['phase']['cpu_ns']},'calls',subset[0]['phase']['calls'],flush=True)
(R/'stage-profile.json').write_text(json.dumps(records,indent=2)+'\n')
