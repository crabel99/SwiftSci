from pathlib import Path
import hashlib,json,subprocess,time
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');P='/Users/crabel/Documents/src/SwiftSci/Benchmarks/.venv-standardized/bin/python'
assert not (R/'finish-status.json').exists(), "Restore the pinned inputs and choose a fresh run directory before rerunning"
start=time.time()
while not (R/'validation-modes-asan-summary.json').exists():
 if time.time()-start>600:raise RuntimeError('Sanitizer did not finish within ten minutes')
 time.sleep(1)
for l in ['validation-modes-release','validation-modes-debug','validation-modes-asan']:
 summary=json.loads((R/(l+'-summary.json')).read_text());assert summary['passedTests']==382 and summary['failedTests']==0 and summary['skippedTests']==0
 receipt=json.loads((R/(l+'-command.json')).read_text());assert all(hashlib.sha256((S/p).read_bytes()).hexdigest()==h for p,h in receipt['source_sha256'].items())
assert not subprocess.check_output(['git','status','--porcelain'],cwd=S)
phases=[('matched-sample',['python3',str(R/'sample-matched.py')]),('standardized-prepare',[P,'Benchmarks/Tools/bench.py','prepare','--profile','tabular-smoke']),('standardized-run',[P,'Benchmarks/Tools/bench.py','run','--profile','tabular-smoke','--mode','production-default','--engines','swiftsci,pandas','--swift-worker',str(R/'standard-worker/SwiftSciBenchmarkWorker'),'--python',P,'--output',str(R/'standardized')]),('standardized-audit',[P,'Benchmarks/Tools/bench.py','audit',str(R/'standardized')]),('eager',['python3',str(R/'run-final.py')]),('stream',['python3',str(R/'run-final-stream.py')]),('null',['python3',str(R/'run-final-null.py')])]
records=[]
for label,cmd in phases:
 print('Starting',label,flush=True);phase=dict(label=label,command=cmd,start=time.time());records.append(phase);(R/'finish-status.json').write_text(json.dumps(records,indent=2)+'\n')
 with (R/(label+'.log')).open('w') as log:p=subprocess.run(cmd,cwd=S,stdout=log,stderr=subprocess.STDOUT,timeout=900)
 phase.update(exit_code=p.returncode,elapsed_seconds=time.time()-phase['start']);(R/'finish-status.json').write_text(json.dumps(records,indent=2)+'\n');assert p.returncode==0,(label,(R/(label+'.log')).read_text()[-2000:]);print('Finished',label,flush=True)
assert len(list((R/'standardized').glob('*.response.json')))==190
print('All final validation and comparison phases completed',flush=True)
