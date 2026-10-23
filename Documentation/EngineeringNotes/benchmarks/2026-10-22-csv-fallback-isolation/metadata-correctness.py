from pathlib import Path
import json,subprocess,hashlib,sys
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');sys.path.insert(0,str(S/'Benchmarks/Tools'))
from execution_policy import worker_environment,PRODUCTION_MODE
D=R/'metadata-boundary-correctness';D.mkdir(exist_ok=False);rs=[]
with (D/'workers.jsonl').open('x') as out:
 for path in map(Path,json.loads((R/'metadata-boundary-contracts.json').read_text())):
  inp=json.loads(path.read_text());assert hashlib.sha256(Path(inp['path']).read_bytes()).hexdigest()==inp['source_sha256']
  for scope in ['eager','stream']:
   for policy in ['parallel','serial']:
    b=R/'build/metadata'/('ResourceProbe' if scope=='eager' else 'StreamProbe');args=[str(path),'known','fresh','1',policy] if scope=='eager' else [str(path),str(inp['rows']),policy]
    p=subprocess.run([str(b),*args],env=worker_environment(PRODUCTION_MODE),capture_output=True,text=True,timeout=120);assert p.returncode==0,p.stderr
    d=json.loads(p.stdout);assert d['validated'];d.update(case=path.stem,scope=scope,policy=policy);rs.append(d);out.write(json.dumps(d)+'\n');out.flush()
assert len(rs)==480
(D/'summary.json').write_text(json.dumps(dict(validated_workers=len(rs),contracts=120,scope='Correctness only; no performance decision from these one-observation workers.'),indent=2)+'\n');print(len(rs),'native output workers validated',flush=True)
