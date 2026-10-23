from pathlib import Path
import json,hashlib,subprocess,sys
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');sys.path.insert(0,str(S/'Benchmarks/Tools'))
from execution_policy import worker_environment,PRODUCTION_MODE
D=R/'metadata-unicode';D.mkdir(exist_ok=False);contract=Path('/private/tmp/swiftsci-csv-string-cost-20261022/unicode/all-scalars.json');inp=json.loads(contract.read_text());assert hashlib.sha256(Path(inp['path']).read_bytes()).hexdigest()==inp['source_sha256']
results=[]
for engine in ['metadata']:
 binary=R/'build'/engine/'ResourceProbe'
 for policy in ['parallel','serial']:
  cmd=[str(binary),str(contract),'known','fresh','1',policy];p=subprocess.run(cmd,capture_output=True,text=True,env=worker_environment(PRODUCTION_MODE),timeout=180)
  (D/(engine+'-'+policy+'.stderr')).write_text(p.stderr);assert p.returncode==0,p.stderr
  d=json.loads(p.stdout);assert d['validated'];assert [c['nulls'] for c in d['checks']['columns']]==inp['null_counts'];(D/(engine+'-'+policy+'.json')).write_text(json.dumps(d,indent=2)+'\n')
  results.append(dict(engine=engine,policy=policy,validated=True,command=cmd,binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),cells=inp['rows']*3));print(engine,policy,inp['rows']*3,'String cells validated',flush=True)
(D/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
