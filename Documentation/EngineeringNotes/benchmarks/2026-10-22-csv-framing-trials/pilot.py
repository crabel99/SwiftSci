from pathlib import Path
import hashlib,json,subprocess,statistics as st,sys
R=Path(__file__).resolve().parent;P=Path('/private/tmp/swiftsci-csv-wide-profile-20261022');E=Path('/private/tmp/swiftsci-csv-cpu-profile-20261021');sys.path.insert(0,'/private/tmp/swiftsci-csv-count-only-scan-20261021/Benchmarks/Tools')
from execution_policy import worker_environment,PRODUCTION_MODE
from runner import power_state
engines=['parent','consume','header'];bins={'parent':P/'build/production/ResourceProbe',**{e:R/'build'/e/'ResourceProbe' for e in engines[1:]}}
orders=[engines[i:]+engines[:i] for i in range(3)]+[list(reversed(engines[i:]+engines[:i])) for i in range(3)]
cases=[(c,E/'inputs'/(c+'.json'),m) for c,m in [('bike-day','known'),('bike-hour','known'),('unique-shuffled','known'),('Aotizhongxin','known'),('Wanliu','known'),('energy','known'),('energy','infer'),('energy-date-full','known'),('late-bool','infer'),('late-text','infer')]]
cases += [(f'width{n}',P/'width-inputs'/f'width-{n}-rows-{r}.json','known') for n,r in [(1,257),(18,257),(64,257),(4,32769),(18,32769),(64,32769)]]
assert not (R/'pilot.json').exists();records=[]
for case,path,mode in cases:
 inp=json.loads(path.read_text());assert hashlib.sha256(Path(inp['path']).read_bytes()).hexdigest()==inp.get('sha256',inp.get('source_sha256'))
 for policy in ['parallel','serial']:
  for rnd,order in enumerate(orders):
   assert power_state()['source']=='AC'
   for e in order:
    p=subprocess.run([str(bins[e]),str(path),mode,'fresh','1',policy],env=worker_environment(PRODUCTION_MODE),capture_output=True,text=True,timeout=120);assert p.returncode==0,p.stderr;d=json.loads(p.stdout);assert d['validated'];records.append(dict(case=case,mode=mode,policy=policy,engine=e,round=rnd,result=d))
  print(case,mode,policy,{e:round(st.median(d['result']['samples'][0]['total_cpu_ns'] for d in records if (d['case'],d['mode'],d['policy'],d['engine'])==(case,mode,policy,e))/1e6,3) for e in engines},flush=True)
(R/'pilot.json').write_text(json.dumps(dict(records=records,orders=orders,binaries={e:{'path':str(b),'sha256':hashlib.sha256(b.read_bytes()).hexdigest()} for e,b in bins.items()}),indent=2)+'\n')
