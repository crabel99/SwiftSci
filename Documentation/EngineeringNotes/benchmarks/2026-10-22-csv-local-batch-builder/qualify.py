from pathlib import Path
import hashlib,json,subprocess,time
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021')
assert not (R/'qualify-status.json').exists()
start=time.monotonic()
while not (R/'local-builder-release-summary.json').exists():
 assert time.monotonic()-start<600,'Release result not available'
 command=R/'local-builder-release-command.json'
 if command.exists():assert json.loads(command.read_text())['exit_code']==0,'Release failed'
 time.sleep(5)
for config,label,flags in [('Debug','local-builder-debug',[]),('Release','local-builder-asan',['--address-sanitizer'])]:
 print('Starting',label,flush=True);p=subprocess.run(['python3',str(R/'verify.py'),config,'--label',label,*flags],cwd=R);assert p.returncode==0,label
for label in ['local-builder-release','local-builder-debug','local-builder-asan']:
 d=json.loads((R/(label+'-summary.json')).read_text());assert (d['passedTests'],d['failedTests'],d['skippedTests'])==(391,0,0)
 rec=json.loads((R/(label+'-command.json')).read_text());assert all(hashlib.sha256((S/p).read_bytes()).hexdigest()==h for p,h in rec['source_sha256'].items())
subprocess.run(['git','diff','--check'],cwd=S,check=True)
subprocess.run(['git','add','Sources/SwiftDataFrame/IO/CSVColumnConversion.swift','Tests/SwiftDataFrameTests/CSVBatchBuilderStateTests.swift'],cwd=S,check=True)
subprocess.run(['git','commit','-m','perf(csv): keep batch builder mutation local to workers','-m','Move the existing builder into a local value for each typed batch and restore it before rejection handling. Preserve array capacity, null counts, schema behavior, and native worker selection. Add lifecycle coverage for accumulation, draining, and rejection in integer and validated Double paths.'],cwd=S,check=True)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=S,text=True).strip();(R/'final-head.json').write_text(json.dumps(dict(commit=head,branch='codex/csv-local-batch-builder',parent='1c15702331ed68ea1bd214daf844d1c9d571dacd',comparison='680ac74b96ab6c6968d83a9511ebdce69d30093b'),indent=2)+'\n')
for phase in ['build-standard-worker.py','finish.py']:
 print('Starting',phase,flush=True);p=subprocess.run(['python3',str(R/phase)],cwd=R);assert p.returncode==0,phase
flags={label:json.loads((R/label/'review-flags.json').read_text()) for label in ['acceptance','mode-controls','text-controls','long-key-controls']}
(R/'qualify-status.json').write_text(json.dumps(dict(commit=head,flags=flags,passed_review_limits=not any(flags.values()),scope='Tests and build finish before timings start. No source or worker changes during accepted measurements.'),indent=2)+'\n');print('Qualification completed; review flags:',{k:len(v) for k,v in flags.items()},flush=True)
