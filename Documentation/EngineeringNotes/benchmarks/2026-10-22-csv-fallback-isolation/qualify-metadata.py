from pathlib import Path
import json,subprocess,hashlib,shutil
R=Path(__file__).resolve().parent;P=Path('/private/tmp/swiftsci-csv-prefix-selection-20261022');S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021')
for config,label,flags in [('Debug','metadata-debug',[]),('Release','metadata-asan',['--address-sanitizer'])]:
 print('Starting',label,flush=True);subprocess.run(['python3',str(R/'verify.py'),config,'--label',label,*flags],check=True,cwd=R)
for label in ['metadata-release','metadata-debug','metadata-asan']:
 d=json.loads((R/(label+'-summary.json')).read_text());assert (d['passedTests'],d['failedTests'],d['skippedTests'])==(394,0,0)
 rec=json.loads((R/(label+'-command.json')).read_text());assert all(hashlib.sha256((S/p).read_bytes()).hexdigest()==h for p,h in rec['source_sha256'].items())
subprocess.run(['git','diff','--check'],cwd=S,check=True)
subprocess.run(['git','add','Sources/SwiftDataFrame/IO/CSVASCIIPrefixStringDecoder.swift','Tests/SwiftDataFrameTests/CSVASCIIPrefixStringDecoderTests.swift'],cwd=S,check=True)
subprocess.run(['git','commit','-m','perf(csv): reject oversized null sets before scanning bytes','-m','Read UTF-8 lengths only for native contiguous storage, admit two token traversals and a byte scan within the selected row budget, and keep foreign storage on the hashed path. Remove the byte-by-byte budget check after admission. Extend exact-boundary and bridged-String coverage.'],cwd=S,check=True)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=S,text=True).strip();(R/'metadata-head.json').write_text(json.dumps(dict(commit=head,parent='167d9a4e6f8cb923342dea3236721c8722015bf3',qualification='All394ReleaseDebugASantests pass. Whole-read resource qualification pending.'),indent=2)+'\n')
v=json.loads((R/'variants.json').read_text());D=R/'variants/scan-selected';shutil.copytree(S/'Sources/SwiftDataFrame',D/'Sources/SwiftDataFrame')
p=D/'Sources/SwiftDataFrame/IO/CSVASCIIPrefixStringDecoder.swift';p.write_bytes(subprocess.check_output(['git','show','167d9a4e6f:Sources/SwiftDataFrame/IO/CSVASCIIPrefixStringDecoder.swift'],cwd=S))
v['production']['path']=str(D);v['metadata']={'path':str(S),'pr':None};(R/'variants.json').write_text(json.dumps(v,indent=2)+'\n')
subprocess.run(['python3',str(R/'build.py'),'metadata'],check=True,cwd=R)
subprocess.run(['python3',str(R/'link-variant.py'),'metadata'],check=True,cwd=R)
rec=json.loads((R/'build/metadata/build.json').read_text());source=P/'StreamRepeatProbe.swift';cmd=[str(source) if a.endswith('/ResourceProbe.swift') else a for a in rec['commands'][1]];binary=R/'build/metadata/StreamRepeatProbe';cmd[cmd.index('-o')+1]=str(binary)
p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stderr
(binary.parent/'StreamRepeatProbe.build.json').write_text(json.dumps(dict(command=cmd,binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),harness_sha256=hashlib.sha256(source.read_bytes()).hexdigest()),indent=2)+'\n')
shutil.copy2(P/'build-standard-worker.py',R/'build-standard-worker.py');subprocess.run(['python3',str(R/'build-standard-worker.py')],check=True,cwd=R)
(R/'metadata-builds-complete.json').write_text(json.dumps(dict(commit=head),indent=2)+'\n');print('All metadata builds finished. Timing can start.',flush=True)
