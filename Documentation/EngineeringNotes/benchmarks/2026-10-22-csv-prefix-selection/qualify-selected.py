from pathlib import Path
import hashlib,json,subprocess,time,shutil
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021')
start=time.monotonic()
while not (R/'selected-release-summary.json').exists():
 assert time.monotonic()-start<900
 c=R/'selected-release-command.json'
 if c.exists():assert json.loads(c.read_text())['exit_code']==0
 time.sleep(3)
for config,label,flags in [('Debug','selected-debug',[]),('Release','selected-asan',['--address-sanitizer'])]:
 print('Starting',label,flush=True)
 subprocess.run(['python3',str(R/'verify.py'),config,'--label',label,*flags],cwd=R,check=True)
for label in ['selected-release','selected-debug','selected-asan']:
 d=json.loads((R/(label+'-summary.json')).read_text());assert (d['passedTests'],d['failedTests'],d['skippedTests'])==(394,0,0)
 rec=json.loads((R/(label+'-command.json')).read_text());assert all(hashlib.sha256((S/p).read_bytes()).hexdigest()==h for p,h in rec['source_sha256'].items())
subprocess.run(['git','diff','--check'],cwd=S,check=True)
files=['Sources/SwiftDataFrame/IO/CSVASCIIPrefixStringDecoder.swift','Sources/SwiftDataFrame/IO/CSVColumnConversion.swift','Sources/SwiftDataFrame/IO/CSVEagerReader.swift','Sources/SwiftDataFrame/IO/CSVReader.swift','Tests/SwiftDataFrameTests/CSVASCIIPrefixStringDecoderTests.swift','Tests/SwiftDataFrameTests/CSVASCIIPrefixStringReadTests.swift','Tests/SwiftDataFrameTests/CSVStringNullTests.swift']
subprocess.run(['git','add',*files],cwd=S,check=True)
subprocess.run(['git','commit','-m','perf(csv): select bounded ASCII null-prefix decoding per column','-m','Prepare the negative prefix filter only when token and byte visits fit within the selected row count. Keep tiny sets and hashed fallback unchanged, preserve canonical String equality, and select one concrete decoder for each attempt. Cover preparation boundaries and eager/streamed native values.'],cwd=S,check=True)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=S,text=True).strip();(R/'final-head.json').write_text(json.dumps(dict(commit=head,parent=json.loads((R/'cleanup-head.json').read_text())['head'],qualification='Semantic suites passed; resource qualification pending.'),indent=2)+'\n')
D=R/'variants/byte-only';shutil.copytree(S/'Sources/SwiftDataFrame',D/'Sources/SwiftDataFrame')
p=D/'Sources/SwiftDataFrame/IO/CSVASCIIPrefixStringDecoder.swift';p.write_text(p.read_text().replace('var remaining = selectedRowCount - nullValues.count','var remaining = selectedRowCount'))
v=json.loads((R/'variants.json').read_text());v['byte-only']={'path':str(D),'pr':None};(R/'variants.json').write_text(json.dumps(v,indent=2)+'\n')
for cmd in [['python3',str(R/'build.py'),'production','byte-only'],*[[ 'python3',str(R/'link-variant.py'),v] for v in ['production','cleanup','byte-only']],['python3',str(R/'build-standard-worker.py')]]:
 print('Starting',cmd[-1],flush=True);subprocess.run(cmd,cwd=R,check=True)
(R/'builds-complete.json').write_text(json.dumps(dict(commit=head,completed=time.time()),indent=2)+'\n')
print('All builds and semantic suites complete. Ready for isolated resource measurements.',flush=True)
