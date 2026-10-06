import json,sys,subprocess
from pathlib import Path
root=Path('/Users/crabel/Documents/src/SwiftSci');sys.path.insert(0,str(root/'Benchmarks/UnifiedMemoryPrototype'));from processes import run_process
out=Path('/Users/crabel/local-ai/spl/swiftsci/cpu-async-cleanup-20261006');source=Path((out/'source.txt').read_text().strip());records=[]
for mode,flags in [('release',[]),('address',['-sanitize=address']),('thread',['-sanitize=thread'])]:
 binary=out/('stress-'+mode);command=['xcrun','swiftc','-O','-parse-as-library',*flags,str(source/'Sources/SwiftML/Core/CPUWorkspaceTrial.swift'),'/private/tmp/AsyncCloseStress.swift','-o',str(binary)]
 r=run_process(command,text=True,capture_output=True,timeout=90);(out/('stress-'+mode+'-build.log')).write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr
 r=run_process([str(binary)],text=True,capture_output=True,timeout=30);(out/('stress-'+mode+'.log')).write_text(r.stdout+r.stderr)
 assert r.returncode==0,(mode,r.stdout,r.stderr)
 record=json.loads(r.stdout);assert record['status']=='passed' and 'WARNING: ThreadSanitizer' not in r.stderr and 'ERROR: AddressSanitizer' not in r.stderr
 records.append(dict(mode=mode,command=command,result=record));(out/'sanitizers.json').write_text(json.dumps(records,indent=2)+'\n');print(mode,record,flush=True)
