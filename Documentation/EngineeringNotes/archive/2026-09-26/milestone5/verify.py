import subprocess,json,sys
from pathlib import Path
root=Path('/Users/crabel/Documents/src/SwiftSci')
python=str(root/'Benchmarks/.venv-standardized/bin/python')
bench=[python,str(root/'Benchmarks/Tools/bench.py')]
worker=str(Path.home()/'Library/Caches/SwiftSci/standardized-benchmarks/derived/Build/Products/Release/SwiftSciBenchmarkWorker')
results={}
with Path('/private/tmp/swiftsci-milestone5/verification.log').open('w') as log:
 for profile,name in [('public-smoke','milestone5-smoke-01'),('public-data','milestone5-production-01'),('smoke','milestone5-baseline-01'),('migration-smoke','milestone5-migration-01'),('certification','milestone5-nist-01')]:
  out=root/'Benchmarks/Runs'/name
  if profile!='public-smoke':
   subprocess.run(bench+['prepare','--profile',profile],cwd=root,stdout=log,stderr=subprocess.STDOUT,check=True)
   subprocess.run(bench+['run','--profile',profile,'--engines','swiftsci,pandas','--swift-worker',worker,'--python',python,'--output',str(out)],cwd=root,stdout=log,stderr=subprocess.STDOUT,check=True)
  subprocess.run(bench+['audit',str(out)],cwd=root,stdout=log,stderr=subprocess.STDOUT,check=True)
  r=json.loads((out/'run.json').read_text());samples=[s for e in r['events'] for s in e['result']['samples']]
  results[profile]=dict(status=r['status'],processes=len(r['events']),samples=len(samples),unresolved=sum(not s.get('timing_resolved',True) for s in samples),maximum_error=max(s['maximum_absolute_error'] for s in samples),run=name)
  print(profile,results[profile],flush=True)
  Path('/private/tmp/swiftsci-milestone5/results.json').write_text(json.dumps(results,indent=2)+'\n')
