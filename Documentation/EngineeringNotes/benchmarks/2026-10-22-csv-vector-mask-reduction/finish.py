from pathlib import Path
import hashlib,json,subprocess,time
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');P='/Users/crabel/Documents/src/SwiftSci/Benchmarks/.venv-standardized/bin/python'
assert not (R/'finish-status.json').exists()
for label in ['vector-mask-release','vector-mask-debug','vector-mask-asan']:
 d=json.loads((R/(label+'-summary.json')).read_text());assert d['passedTests']==385 and d['failedTests']==0 and d['skippedTests']==0
 receipt=json.loads((R/(label+'-command.json')).read_text());assert all(hashlib.sha256((S/p).read_bytes()).hexdigest()==h for p,h in receipt['source_sha256'].items())
assert not subprocess.check_output(['git','status','--porcelain'],cwd=S)
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=S,text=True).strip()=='46a9b9bf951918cd2eb281dadf554efb30c7b0a0'
assert (R/'standard-worker/SwiftSciBenchmarkWorker').exists()
phases=[('standardized-prepare',[P,'Benchmarks/Tools/bench.py','prepare','--profile','tabular-smoke']),('standardized-run',[P,'Benchmarks/Tools/bench.py','run','--profile','tabular-smoke','--mode','production-default','--engines','swiftsci,pandas','--swift-worker',str(R/'standard-worker/SwiftSciBenchmarkWorker'),'--python',P,'--output',str(R/'standardized')]),('standardized-audit',[P,'Benchmarks/Tools/bench.py','audit',str(R/'standardized')]),('acceptance',['python3',str(R/'run-acceptance.py')]),('mode-controls',['python3',str(R/'run-mode-controls.py')])]
records=[]
for label,cmd in phases:
 print('Starting',label,flush=True);phase=dict(label=label,command=cmd,start=time.time());records.append(phase);(R/'finish-status.json').write_text(json.dumps(records,indent=2)+'\n')
 with (R/(label+'.log')).open('w') as log:p=subprocess.run(cmd,cwd=S,stdout=log,stderr=subprocess.STDOUT,timeout=1200)
 phase.update(exit_code=p.returncode,elapsed_seconds=time.time()-phase['start']);(R/'finish-status.json').write_text(json.dumps(records,indent=2)+'\n');assert p.returncode==0,(label,(R/(label+'.log')).read_text()[-1500:]);print('Finished',label,flush=True)
assert len(list((R/'standardized').glob('*.response.json')))==190
print('All final phases completed',flush=True)
