from pathlib import Path
import json,subprocess,time,hashlib
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');PY='/Users/crabel/Documents/src/SwiftSci/Benchmarks/.venv-standardized/bin/python'
assert (R/'builds-complete.json').exists()
head=json.loads((R/'builds-complete.json').read_text())['commit'];assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=S,text=True).strip()==head
assert not subprocess.check_output(['git','status','--porcelain'],cwd=S)
for label in ['selected-release','selected-debug','selected-asan']:
 d=json.loads((R/(label+'-summary.json')).read_text());assert (d['passedTests'],d['failedTests'],d['skippedTests'])==(394,0,0)
 rec=json.loads((R/(label+'-command.json')).read_text());assert all(hashlib.sha256((S/p).read_bytes()).hexdigest()==h for p,h in rec['source_sha256'].items())
phases=[('unicode',['python3',str(R/'run-unicode.py')]),('crossover',['python3',str(R/'run-crossover.py'),'crossover','1','cleanup','production','byte-only']),('setup',['python3',str(R/'run-setup.py'),'setup','2','cleanup','production','byte-only']),('standardized-prepare',[PY,'Benchmarks/Tools/bench.py','prepare','--profile','tabular-smoke']),('standardized-run',[PY,'Benchmarks/Tools/bench.py','run','--profile','tabular-smoke','--mode','production-default','--engines','swiftsci,pandas','--swift-worker',str(R/'standard-worker/SwiftSciBenchmarkWorker'),'--python',PY,'--output',str(R/'standardized')]),('standardized-audit',[PY,'Benchmarks/Tools/bench.py','audit',str(R/'standardized')]),('acceptance',['python3',str(R/'run-acceptance.py')]),('mode-controls',['python3',str(R/'run-mode-controls.py')]),('text-controls',['python3',str(R/'run-text-controls.py')]),('long-key-controls',['python3',str(R/'run-long-key-controls.py')])]
assert not (R/'qualification-status.json').exists();records=[]
for label,cmd in phases:
 print('Starting',label,flush=True);phase=dict(label=label,command=cmd,start=time.time());records.append(phase);(R/'qualification-status.json').write_text(json.dumps(records,indent=2)+'\n')
 with (R/(label+'.log')).open('w') as log:p=subprocess.run(cmd,cwd=S,stdout=log,stderr=subprocess.STDOUT,timeout=3600)
 phase.update(exit_code=p.returncode,elapsed_seconds=time.time()-phase['start']);(R/'qualification-status.json').write_text(json.dumps(records,indent=2)+'\n');assert p.returncode==0,(label,(R/(label+'.log')).read_text()[-2000:]);print('Finished',label,flush=True)
assert len(list((R/'standardized').glob('*.response.json')))==190
flags={label:json.loads((R/label/'review-flags.json').read_text()) for label in ['crossover','setup','acceptance','mode-controls','text-controls','long-key-controls']}
(R/'qualification-result.json').write_text(json.dumps(dict(commit=head,flags=flags,passed_review_limits=not any(flags.values()),scope='All builds and tests finished before timings; no source changes during measurements.'),indent=2)+'\n')
print('Qualification complete. Review flags:',{k:len(v) for k,v in flags.items()},flush=True)
