from pathlib import Path
import sys,json,subprocess
root=Path('/Users/LOCAL_USER/Library/Caches/SwiftSci/retained-gpu-trial-20261007')
out=Path('/Users/LOCAL_USER/local-ai/spl/swiftsci/cpu-gpu-closeout-20261007')
sys.path.insert(0,str(root/'Benchmarks/Tools'))
from runner import source_identity,verify_uninstrumented,metal_build_record,environment
from contracts import digest,write_json
worker=Path('/Users/LOCAL_USER/Library/Caches/SwiftSci/unified-memory-prototype/derived/Build/Products/Release/SwiftSciBenchmarkWorker')
verify_uninstrumented(worker)
write_json(Path(str(worker)+'.build.json'),dict(schema_version=1,source=source_identity(root),command=json.loads((out/'Release-command.json').read_text()),binary_sha256=digest(worker.read_bytes()),coverage_instrumentation='absent',metal=metal_build_record(worker),log=str(out/'Release.log'),snapshot=str(root),environment=environment()))
cmd=[sys.executable,'Benchmarks/Tools/acceptance.py','--tier','cpu','--check-baseline','--swift-worker',str(worker),'--python',sys.executable,'--output',str(out/'cpu-acceptance')]
(out/'cpu-acceptance-command.json').write_text(json.dumps(cmd,indent=2)+'\n')
with (out/'cpu-acceptance.log').open('w') as log:r=subprocess.run(cmd,cwd=root,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
print('policy exit',r.returncode);print((out/'cpu-acceptance.log').read_text()[-1800:]);sys.exit(r.returncode)
