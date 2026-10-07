from pathlib import Path
import json,subprocess,sys
root=Path('/Users/crabel/Library/Caches/SwiftSci/retained-gpu-trial-20261007')
out=Path('/Users/crabel/local-ai/spl/swiftsci/gpu-consuming-scaler-20261007');out.mkdir(exist_ok=True)
name=sys.argv[1]
cmd=json.loads(Path('/Users/crabel/local-ai/spl/swiftsci/retained-gpu-trial-20261007/final-release-command.json').read_text())
cmd = [arg for arg in cmd if not arg.startswith('-only-testing:')]
cmd += ['-only-testing:' + target for target in ['SwiftDataFrameTests','SwiftStatsTests','SwiftPreprocessingTests','SwiftMLTests','SwiftClusterTests','SwiftOptimizeTests','SwiftExplainTests','SwiftNLPTests','SwiftSciBenchmarkSupportTests']]
if name.startswith('red'):
 cmd = [arg for arg in cmd if not arg.startswith('-only-testing:')] + ['-only-testing:SwiftPreprocessingTests/ConsumingScalerTests']
cmd[cmd.index('-resultBundlePath')+1]=str(out/(name+'.xcresult'))
(out/(name+'-command.json')).write_text(json.dumps(cmd,indent=2)+'\n')
sys.path.insert(0,'/Users/crabel/Library/Caches/SwiftSci/prepared-memory-integration-20261006-qualification/Benchmarks/UnifiedMemoryPrototype')
from processes import run_process
with (out/(name+'.log')).open('w') as log:
 result=run_process(cmd,cwd=root,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
print('exit',result.returncode)
if result.returncode:
 print('\n'.join(x[:800] for x in (out/(name+'.log')).read_text().splitlines() if 'error:' in x or 'recorded an issue' in x))
else:
 data=subprocess.check_output(['xcrun','xcresulttool','get','test-results','summary','--path',str(out/(name+'.xcresult'))])
 (out/(name+'-summary.json')).write_bytes(data)
 summary=json.loads(data);print({k:summary[k] for k in ['result','passedTests','failedTests','skippedTests']})
sys.exit(result.returncode)
