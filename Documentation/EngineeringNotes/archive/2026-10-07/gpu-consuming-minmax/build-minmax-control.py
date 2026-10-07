from pathlib import Path
import subprocess,json,sys,shutil,hashlib
root=Path('/Users/crabel/Library/Caches/SwiftSci/retained-gpu-trial-20261007');out=Path('/Users/crabel/local-ai/spl/swiftsci/gpu-consuming-minmax-20261007')
assert 'Passed 24 workers' in (out/'candidate.log').read_text()
p=root/'Sources/SwiftPreprocessing/Core/MinMaxScaler.swift';candidate=p.read_bytes()
assert candidate==(out/'MinMaxScaler-candidate.swift').read_bytes()
cmd=json.loads((out/'final-release-command.json').read_text());cmd=[x for x in cmd if not x.startswith('-only-testing:')]
cmd+=['-only-testing:SwiftPreprocessingTests/CompactScalerTests']
cmd[cmd.index('-resultBundlePath')+1]=str(out/'control-release.xcresult')
(out/'control-release-command.json').write_text(json.dumps(cmd,indent=2)+'\n')
sys.path.insert(0,'/Users/crabel/Library/Caches/SwiftSci/prepared-memory-integration-20261006-qualification/Benchmarks/UnifiedMemoryPrototype')
from processes import run_process
try:
 p.write_bytes(subprocess.check_output(['git','-C',str(root),'show','4c6d91b263bd16cd776eb315f6e1cafd44b6abab:Sources/SwiftPreprocessing/Core/MinMaxScaler.swift']))
 with (out/'control-release.log').open('w') as log:r=run_process(cmd,cwd=root,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
 assert r.returncode==0
 data=subprocess.check_output(['xcrun','xcresulttool','get','test-results','summary','--path',str(out/'control-release.xcresult')]);(out/'control-release-summary.json').write_bytes(data)
 worker=Path('/Users/crabel/Library/Caches/SwiftSci/unified-memory-prototype/derived/Build/Products/Release/SwiftSciRetainedGPUTrial')
 shutil.copy2(worker,worker.with_name('SwiftSciRetainedGPUTrial-minmax-baseline'))
 print('Control built and tested',hashlib.sha256(worker.read_bytes()).hexdigest(),flush=True)
finally:p.write_bytes(candidate)
