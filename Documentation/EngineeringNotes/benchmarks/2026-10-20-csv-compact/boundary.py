from pathlib import Path
import json,subprocess,hashlib
R=Path(__file__).resolve().parent
sources=[R/'compact/Sources/SwiftDataFrame/IO'/n for n in ['CSVRecordIndex.swift','SystemsCSVParser.swift']]
cmd=['xcrun','swiftc','-O','-whole-module-optimization','-swift-version','6','-target','arm64-apple-macos14.0','-parse-as-library',*[str(p) for p in sources],str(R/'CompactChecks.swift'),'-o',str(R/'CompactChecks')]
p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stderr
p=subprocess.run([str(R/'CompactChecks')],capture_output=True,text=True);assert p.returncode==0,p.stderr
(R/'boundary-checks.json').write_text(json.dumps(dict(command=cmd,exit_code=p.returncode,stdout=p.stdout,source_hashes={str(s):hashlib.sha256(s.read_bytes()).hexdigest() for s in [*sources,R/'CompactChecks.swift']},binary_sha256=hashlib.sha256((R/'CompactChecks').read_bytes()).hexdigest()),indent=2)+'\n')
print(p.stdout)
