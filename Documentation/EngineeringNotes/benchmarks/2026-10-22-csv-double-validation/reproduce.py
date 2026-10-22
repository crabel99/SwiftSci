from pathlib import Path
import hashlib,json,statistics as st,subprocess,sys
R=Path(__file__).resolve().parent;E=Path('/private/tmp/swiftsci-csv-cpu-profile-20261021');C=Path('/private/tmp/swiftsci-csv-batch-profile-20261022');S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');sys.path.insert(0,str(S/'Benchmarks/Tools'))
from execution_policy import worker_environment,PRODUCTION_MODE
from runner import power_state
assert power_state()['source']=='AC'
binaries={'original':E/'build/indexed/ResourceProbe','current':C/'build/production/ResourceProbe'}
assert not (R/'repro.json').exists()
records=[]
for case,path,mode in [('wide',E/'inputs/Aotizhongxin.json','known'),('numeric',C/'nullable-0.json','infer')]:
 for rnd in range(6):
  for e in (list(binaries) if rnd%2==0 else list(reversed(binaries))):
   p=subprocess.run([str(binaries[e]),str(path),mode,'fresh','1'],env=worker_environment(PRODUCTION_MODE),capture_output=True,text=True);assert p.returncode==0,p.stderr;d=json.loads(p.stdout);assert d['validated'];records.append(dict(case=case,round=rnd,engine=e,result=d))
 ratios={}
 for e in binaries:ratios[e]=st.median(r['result']['samples'][0]['total_cpu_ns'] for r in records if r['case']==case and r['engine']==e)
 ratio=ratios['current']/ratios['original'];print(case,{e:round(v/1e6,3) for e,v in ratios.items()},round(ratio,3),'RED' if ratio>1.10 else 'PASS',flush=True)
(R/'repro.json').write_text(json.dumps(dict(records=records,binaries={e:dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for e,p in binaries.items()}),indent=2)+'\n')
med=lambda case,e:st.median(r['result']['samples'][0]['total_cpu_ns'] for r in records if r['case']==case and r['engine']==e)
raise SystemExit(1 if any(med(c,'current')/med(c,'original')>1.10 for c in ['wide','numeric']) else 0)
