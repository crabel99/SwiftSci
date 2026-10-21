from pathlib import Path
import subprocess,json,hashlib
import sys
r=Path(__file__).resolve().parent;v=sys.argv[1] if len(sys.argv)>1 else "borrowed"
sources=[r/v/'Sources/SwiftDataFrame/IO'/n for n in ['CSVRecordIndex.swift','SystemsCSVParser.swift']]+[r/'FlatBorrowChecks.swift']
cmd=['xcrun','swiftc','-O','-whole-module-optimization','-swift-version','6','-target','arm64-apple-macos14.0','-sanitize=address','-parse-as-library',*[str(p) for p in sources],'-o',str(r/(v+'-FlatBorrowChecks'))]
p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stderr
p=subprocess.run([cmd[-1]],capture_output=True,text=True);assert p.returncode==0,p.stderr
(r/(v+'-flat-checks.json')).write_text(json.dumps(dict(command=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}),indent=2)+'\n');print(p.stdout)
