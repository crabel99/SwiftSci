from pathlib import Path
import json,subprocess,time,hashlib
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');P=Path('/private/tmp/swiftsci-csv-prefix-selection-20261022');PY='/Users/crabel/Documents/src/SwiftSci/Benchmarks/.venv-standardized/bin/python'
assert (R/'metadata-builds-complete.json').exists();head=json.loads((R/'metadata-head.json').read_text())['commit'];assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=S,text=True).strip()==head;assert not subprocess.check_output(['git','status','--porcelain'],cwd=S)
for label in ['metadata-release','metadata-debug','metadata-asan']:
 d=json.loads((R/(label+'-summary.json')).read_text());assert (d['passedTests'],d['failedTests'],d['skippedTests'])==(394,0,0)
 rec=json.loads((R/(label+'-command.json')).read_text());assert all(hashlib.sha256((S/p).read_bytes()).hexdigest()==h for p,h in rec['source_sha256'].items())
s=(P/'run-unicode.py').read_text().replace("['production']","['metadata']").replace("R/'unicode-semantics'","R/'metadata-unicode'");(R/'metadata-unicode.py').write_text(s)
phases=[('metadata-unicode',['python3',str(R/'metadata-unicode.py')]),('metadata-boundary-correctness',['python3',str(R/'metadata-correctness.py')]),('metadata-calibration',['python3',str(R/'metadata-calibration.py')]),('standardized-prepare',[PY,'Benchmarks/Tools/bench.py','prepare','--profile','tabular-smoke']),('standardized-run',[PY,'Benchmarks/Tools/bench.py','run','--profile','tabular-smoke','--mode','production-default','--engines','swiftsci,pandas','--swift-worker',str(R/'standard-worker/SwiftSciBenchmarkWorker'),'--python',PY,'--output',str(R/'standardized')]),('standardized-audit',[PY,'Benchmarks/Tools/bench.py','audit',str(R/'standardized')]),('acceptance',['python3',str(R/'run-acceptance.py')]),('mode-controls',['python3',str(R/'run-mode-controls.py')]),('text-controls',['python3',str(R/'run-text-controls.py')]),('long-key-controls',['python3',str(R/'run-long-key-controls.py')])]
records=[];assert not (R/'metadata-qualification-status.json').exists()
for label,cmd in phases:
 print('Starting',label,flush=True);r=dict(label=label,command=cmd,start=time.time());records.append(r);(R/'metadata-qualification-status.json').write_text(json.dumps(records,indent=2)+'\n')
 with (R/(label+'.log')).open('w') as log:p=subprocess.run(cmd,cwd=S,stdout=log,stderr=subprocess.STDOUT,timeout=3600)
 r.update(exit_code=p.returncode,elapsed_seconds=time.time()-r['start']);(R/'metadata-qualification-status.json').write_text(json.dumps(records,indent=2)+'\n');assert p.returncode==0,(label,(R/(label+'.log')).read_text()[-2000:]);print('Finished',label,flush=True)
assert len(list((R/'standardized').glob('*.response.json')))==190
flags={k:json.loads((R/k/'review-flags.json').read_text()) for k in ['metadata-calibration','acceptance','mode-controls','text-controls','long-key-controls']}
(R/'metadata-qualification-result.json').write_text(json.dumps(dict(commit=head,flags=flags,passed_review_limits=not any(flags.values()),scope='Tests and builds complete before timing. Native hashing for all production acceptance. Historical flags retained, no tolerance changes, identical-binary gate required.'),indent=2)+'\n');print('Metadata qualification completed. Flags:',{k:len(v) for k,v in flags.items()},flush=True)
