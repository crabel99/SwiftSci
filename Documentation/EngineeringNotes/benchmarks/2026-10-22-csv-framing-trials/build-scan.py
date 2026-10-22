from pathlib import Path
import json,subprocess,hashlib,sys
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021')
variants={'parent':S,**{e:R/(e+'-trial') for e in ['consume','header','derived-count']}}
for label in sys.argv[1:]:
 source=variants[label]
 files=[source/'Sources/SwiftDataFrame/IO'/f for f in ['SystemsCSVParser.swift','CSVRecordIndex.swift']]+[R/'ScanProbe.swift'];binary=R/('ScanProbe-'+label);cmd=['xcrun','swiftc','-swift-version','6','-O','-parse-as-library',*[str(p) for p in files],'-o',str(binary)]
 p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stderr
 (R/('scan-'+label+'-build.json')).write_text(json.dumps(dict(command=cmd,sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest()),indent=2)+'\n');print(label,'scanner built',flush=True)
