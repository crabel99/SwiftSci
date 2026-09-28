import json,subprocess
from pathlib import Path
root=Path('/Users/LOCAL_USER/Documents/src/SwiftSci');out=Path('/private/tmp/swiftsci-suite-neural');python=str(root/'Benchmarks/.venv-standardized/bin/python');bench=str(root/'Benchmarks/Tools/bench.py');worker='/Users/LOCAL_USER/Library/Caches/SwiftSci/standardized-benchmarks/derived/Build/Products/Release/SwiftSciBenchmarkWorker'
records=[]
for profile,name,expected in [('neural-conformance','suite-neural-02',1),('neural-loader-conformance','suite-neural-loader-02',1),('neural-cpu-conformance','suite-neural-cpu-01',0),('smoke','suite-neural-smoke-01',0)]:
 args=[python,bench,'run','--profile',profile,'--engines','swiftsci,pandas','--swift-worker',worker,'--python',python,'--output',str(root/'Benchmarks/Runs'/name)]
 with (out/(name+'.log')).open('w') as log:code=subprocess.run(args,cwd=root,stdout=log,stderr=subprocess.STDOUT).returncode
 records.append({'run':name,'operation':'run','exit_code':code});assert code==expected,(name,code)
 with (out/(name+'-audit.log')).open('w') as log:code=subprocess.run([python,bench,'audit',str(root/'Benchmarks/Runs'/name)],cwd=root,stdout=log,stderr=subprocess.STDOUT).returncode
 records.append({'run':name,'operation':'audit','exit_code':code});assert code==expected,(name,'audit',code)
(out/'validation-exits.json').write_text(json.dumps(records,indent=2)+'\n')
with (out/'negative-workers.log').open('w') as log:
 code=subprocess.run([python,str(out/'check-workers.py')],cwd=root,stdout=log,stderr=subprocess.STDOUT).returncode
assert code==0,'negative worker checks failed'
print('Validation finished: diagnostic failures retained; CPU and smoke certificates passed; negative controls passed.')
