from pathlib import Path
import hashlib,json,subprocess,sys
R=Path(__file__).resolve().parent;sys.path.insert(0,'/private/tmp/swiftsci-csv-ingestion-20261021/Benchmarks/Tools')
from execution_policy import worker_environment,PRODUCTION_MODE
P='/Users/crabel/Documents/src/SwiftSci/Benchmarks/.venv-standardized/bin/python'
cases=['bike-day','bike-hour','unique','unique-shuffled','energy','Aotizhongxin','Wanliu','energy-date-full']
engines=['baseline','candidate','pandas','polars','duckdb'];D=R/'preflight';D.mkdir(exist_ok=True);failures=[]
for case in cases:
 oracle=json.loads((R/'inputs'/(case+'.json')).read_text())
 for engine in engines:
  target=D/(case+'-'+engine+'.json')
  args=[str(R/'build'/engine/'ResourceProbe'),str(R/'inputs'/(case+'.json')),'known','audit','1'] if engine in ['baseline','candidate'] else [P,str(R/'python-probe.py'),engine,str(R/'inputs'/(case+'.json'))]
  p=subprocess.run(args,env=worker_environment(PRODUCTION_MODE),capture_output=True,text=True,timeout=300)
  (D/(case+'-'+engine+'.stderr')).write_text(p.stderr)
  if p.returncode:failures.append([case,engine,p.stderr[-600:]]);print(case,engine,'ERROR',flush=True);continue
  data=json.loads(p.stdout);target.write_text(json.dumps(data,indent=2)+'\n')
  ok=data['validated'] and data['checks']['passed'] and [c['sha256'] for c in data['checks']['columns']]==oracle['hashes'] and [c['nulls'] for c in data['checks']['columns']]==oracle['null_counts']
  if not ok:failures.append([case,engine,data['checks']])
  print(case,engine,'PASS' if ok else 'FAIL',flush=True)
(R/'preflight-summary.json').write_text(json.dumps(dict(cases=cases,engines=engines,workers=len(cases)*len(engines),failures=failures),indent=2)+'\n')
assert not failures,failures
