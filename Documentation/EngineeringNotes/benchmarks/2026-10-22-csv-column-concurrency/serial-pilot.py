from pathlib import Path
import hashlib,json,statistics as st,subprocess,sys
R=Path(__file__).resolve().parent;E=Path('/private/tmp/swiftsci-csv-cpu-profile-20261021');C=Path('/private/tmp/swiftsci-csv-plan-profile-20261022');sys.path.insert(0,'/private/tmp/swiftsci-csv-count-only-scan-20261021/Benchmarks/Tools')
from execution_policy import worker_environment,PRODUCTION_MODE
from runner import power_state
assert power_state()['source']=='AC'
engines=['current','quartet','serial']
binaries={'current':C/'build/production/ResourceProbe',**{e:R/'build'/e/'ResourceProbe' for e in engines[1:]}}
assert not (R/'serial-pilot.json').exists()
orders=[engines[i:]+engines[:i] for i in range(len(engines))]+[list(reversed(engines[i:]+engines[:i])) for i in range(len(engines))]
cases=[('wide',E/'inputs/Aotizhongxin.json','known'),('numeric',C/'nullable-0.json','infer'),('null-half',C/'nullable-50.json','infer'),('bike-hour',E/'inputs/bike-hour.json','known'),('energy',E/'inputs/energy.json','known'),('energy-infer',E/'inputs/energy.json','infer'),('late-bool',E/'inputs/late-bool.json','infer'),('late-text',E/'inputs/late-text.json','infer')]
cases += [(Path(p).stem,Path(p),'known') for p in json.loads((R/'width-contracts.json').read_text())]
cases += [('wide-wanliu',E/'inputs/Wanliu.json','known'),('energy-date',E/'inputs/energy-date-full.json','known')]
records=[]
for case,path,mode in cases:
 assert path.exists(),path
 inp=json.loads(path.read_text());assert hashlib.sha256(Path(inp['path']).read_bytes()).hexdigest()==inp.get('sha256',inp.get('source_sha256'))
 for rnd,order in enumerate(orders):
  for e in order:
   assert power_state()['source']=='AC'
   p=subprocess.run([str(binaries[e]),str(path),mode,'fresh','1'],env=worker_environment(PRODUCTION_MODE),capture_output=True,text=True,timeout=120);assert p.returncode==0,p.stderr;d=json.loads(p.stdout);assert d['validated'];records.append(dict(case=case,round=rnd,engine=e,result=d))
 print(case,{e:round(st.median(r['result']['samples'][0]['total_cpu_ns'] for r in records if r['case']==case and r['engine']==e)/1e6,3) for e in engines},flush=True)
 (R/'serial-pilot-progress.json').write_text(json.dumps(dict(records=records),indent=2)+'\n')
(R/'serial-pilot.json').write_text(json.dumps(dict(records=records,orders=orders,binaries={e:dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for e,p in binaries.items()}),indent=2)+'\n')
