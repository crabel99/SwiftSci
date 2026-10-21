import hashlib,json,shutil,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-eager-count-probe-20261021')
sys.path.insert(0,str(S/'Benchmarks/Tools'))
from runner import source_identity,environment,verify_uninstrumented,metal_build_record
assert not subprocess.check_output(['git','status','--porcelain'],cwd=S)
base=json.loads(Path('/Users/crabel/local-ai/spl/swiftsci/layer-activation-20261017/release-worker/SwiftSciBenchmarkWorker.build.json').read_text())
cmd=list(base['command']);cmd[1]='build';cmd[cmd.index('-scheme')+1]='SwiftSciBenchmarkWorker'
for flag in ['-enableCodeCoverage','-enableThreadSanitizer','-parallel-testing-enabled']:
 i=cmd.index(flag);del cmd[i:i+2]
identity=source_identity(S);start=time.time()
with (R/'standard-worker-build.log').open('w') as f:p=subprocess.run(cmd,cwd=S,stdout=f,stderr=subprocess.STDOUT,timeout=1200)
(R/'standard-worker-build-result.json').write_text(json.dumps(dict(command=cmd,source=identity,exit_code=p.returncode,elapsed_seconds=time.time()-start),indent=2)+'\n')
if p.returncode:print((R/'standard-worker-build.log').read_text()[-5000:]);raise SystemExit(p.returncode)
assert source_identity(S)==identity
b=Path('/Users/crabel/Library/Caches/SwiftSci/mixed-workloads-derived/Build/Products/Release/SwiftSciBenchmarkWorker');verify_uninstrumented(b)
D=R/'standard-worker';D.mkdir(exist_ok=False);shutil.copy2(b,D/b.name)
for bundle in b.parent.glob('*.bundle'):shutil.copytree(bundle,D/bundle.name)
for metal in b.parent.glob('*.metallib'):shutil.copy2(metal,D/metal.name)
receipt=dict(coverage_instrumentation='absent',source=identity,command=cmd,environment=environment(),binary_sha256=hashlib.sha256(b.read_bytes()).hexdigest(),metal=metal_build_record(D/b.name),scope='Uninstrumented Release standard benchmark worker at the eager-batch head.')
(D/(b.name+'.build.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(D/b.name,flush=True)
