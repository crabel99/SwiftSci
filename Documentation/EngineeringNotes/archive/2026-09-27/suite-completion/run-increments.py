import subprocess,json
from pathlib import Path
root=Path('/Users/LOCAL_USER/Documents/src/SwiftSci');out=Path('/private/tmp/swiftsci-suite-finish');python=str(root/'Benchmarks/.venv-standardized/bin/python');worker='/Users/LOCAL_USER/Library/Caches/SwiftSci/standardized-benchmarks/derived/Build/Products/Release/SwiftSciBenchmarkWorker'
for profile,name in [('vision-conformance','finish-vision-01'),('boundary-conformance','finish-boundary-01')]:
 for mode,args in [('prepare',['prepare','--profile',profile]),('run',['run','--profile',profile,'--engines','swiftsci,pandas','--swift-worker',worker,'--python',python,'--output',str(root/'Benchmarks/Runs'/name)]),('audit',['audit',str(root/'Benchmarks/Runs'/name)])]:
  with (out/(name+'-'+mode+'.log')).open('w') as log:
   code=subprocess.run([python,str(root/'Benchmarks/Tools/bench.py'),*args],cwd=root,stdout=log,stderr=subprocess.STDOUT).returncode
  print(profile,mode,code,flush=True)
  if mode=='prepare':assert code==0
