from pathlib import Path
import sys,subprocess,json,plistlib
root=Path('/Users/LOCAL_USER/Library/Caches/SwiftSci/retained-gpu-trial-20261007');out=Path('/Users/LOCAL_USER/local-ai/spl/swiftsci/cpu-gpu-closeout-20261007')
sys.path.insert(0,'/Users/LOCAL_USER/Library/Caches/SwiftSci/prepared-memory-integration-20261006-qualification/Benchmarks/UnifiedMemoryPrototype')
from processes import run_process
cmd=json.loads((out/'Debug-command.json').read_text());cmd[1]='build-for-testing'
i=cmd.index('-resultBundlePath');del cmd[i:i+2]
with (out/'Debug-build-retry.log').open('w') as log:r=run_process(cmd,cwd=root,stdout=log,stderr=subprocess.STDOUT,timeout=900)
(out/'Debug-build-retry-command.json').write_text(json.dumps(cmd,indent=2)+'\n')
print('build exit',r.returncode,flush=True)
if r.returncode:sys.exit(r.returncode)
products=Path(cmd[cmd.index('-derivedDataPath')+1])/'Build/Products'
manifest=next(products.glob('SwiftSci-Package*.xctestrun'))
data=plistlib.loads(manifest.read_bytes())
assert all('/Debug/' in t['TestBundlePath'] for c in data['TestConfigurations'] for t in c['TestTargets'])
(out/'Debug.xctestrun').write_bytes(manifest.read_bytes())
cmd=['xcodebuild','test-without-building','-xctestrun',str(manifest),'-destination','platform=macOS,arch=arm64','-parallel-testing-enabled','NO','-resultBundlePath',str(out/'Debug-retry.xcresult')]
(out/'Debug-test-retry-command.json').write_text(json.dumps(cmd,indent=2)+'\n')
with (out/'Debug-test-retry.log').open('w') as log:r=run_process(cmd,cwd=root,stdout=log,stderr=subprocess.STDOUT,timeout=900)
print('test exit',r.returncode,flush=True)
p=subprocess.run(['xcrun','xcresulttool','get','test-results','summary','--path',str(out/'Debug-retry.xcresult')],capture_output=True)
if p.returncode==0:
 (out/'Debug-summary.json').write_bytes(p.stdout);d=json.loads(p.stdout);print({k:d.get(k) for k in ['result','passedTests','failedTests','skippedTests']})
sys.exit(r.returncode)
