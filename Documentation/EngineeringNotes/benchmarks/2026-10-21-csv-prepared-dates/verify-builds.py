from pathlib import Path
import hashlib,io,json,subprocess,tarfile,sys
R=Path(__file__).resolve().parent
sys.path.insert(0,'/private/tmp/swiftsci-csv-ingestion-20261021/Benchmarks/Tools')
from runner import verify_uninstrumented
from execution_policy import worker_environment,PRODUCTION_MODE
heads={'baseline':'a5f6e78a751365ec360efdd4ae8f028db04b441b','candidate':subprocess.check_output(['git','rev-parse','85f240ef70'],cwd='/private/tmp/swiftsci-csv-ingestion-20261021',text=True).strip()};proof={}
for engine,head in heads.items():
 build=json.loads((R/'build'/engine/'build.json').read_text());source=Path(build['variant']['path'])
 archive=subprocess.check_output(['git','archive',head,'Sources/SwiftDataFrame'],cwd=source)
 with tarfile.open(fileobj=io.BytesIO(archive)) as tf:
  hashes={m.name:hashlib.sha256(tf.extractfile(m).read()).hexdigest() for m in tf.getmembers() if m.isfile() and m.name.endswith('.swift')}
 assert hashes==build['sources'],engine
 binary=R/'build'/engine/'ResourceProbe';assert hashlib.sha256(binary.read_bytes()).hexdigest()==build['binary_sha256'];verify_uninstrumented(binary)
 proof[engine]={'commit':head,'verified_swift_sources':len(hashes),'binary_sha256':build['binary_sha256'],'receipt_sha256':hashlib.sha256((R/'build'/engine/'build.json').read_bytes()).hexdigest()}
(R/'build-vcs-verification.json').write_text(json.dumps(proof,indent=2)+'\n')
D=R/'preflight-candidate-final';D.mkdir(exist_ok=True)
for case in sorted((R/'inputs').glob('*.json')):
 cmd=[str(R/'build/candidate/ResourceProbe'),str(case),'known','audit','1']
 p=subprocess.run(cmd,env=worker_environment(PRODUCTION_MODE),capture_output=True,text=True,timeout=300);assert p.returncode==0,p.stderr
 d=json.loads(p.stdout);assert d['validated'] and d['checks']['passed'];oracle=json.loads(case.read_text());assert [c['sha256'] for c in d['checks']['columns']]==oracle['hashes'];assert [c['nulls'] for c in d['checks']['columns']]==oracle['null_counts']
 (D/(case.stem+'.json')).write_text(json.dumps(d,indent=2)+'\n')
 print(case.stem,'final candidate PASS',flush=True)
(D/'summary.json').write_text(json.dumps({'workers':8,'failures':[],'build':proof['candidate']},indent=2)+'\n')
