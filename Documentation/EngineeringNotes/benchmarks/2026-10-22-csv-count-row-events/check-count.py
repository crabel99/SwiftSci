from pathlib import Path
import subprocess,json,hashlib
R=Path(__file__).resolve().parent
for label,source in [('before',Path('/private/tmp/swiftsci-csv-numeric-decode-control-20261022')),('production',Path('/private/tmp/swiftsci-csv-count-only-scan-20261021'))]:
 files=[source/'Sources/SwiftDataFrame/IO'/p for p in ['SystemsCSVParser.swift','CSVRecordIndex.swift']]+[R/'CountParity.swift'];cmd=['xcrun','swiftc','-swift-version','6','-O','-parse-as-library',*[str(p) for p in files],'-o',str(R/('CountParity-'+label))]
 p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stderr
 p=subprocess.run([str(R/('CountParity-'+label))],capture_output=True,text=True);assert p.returncode==0,p.stderr
 (R/('count-parity-'+label+'.json')).write_text(json.dumps(dict(command=cmd,sources={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},result=json.loads(p.stdout)),indent=2)+'\n');print(label,p.stdout.strip(),flush=True)
