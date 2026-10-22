from pathlib import Path
import json,subprocess,hashlib
R=Path(__file__).resolve().parent;P=Path('/private/tmp/swiftsci-csv-wide-profile-20261022');S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021')
production=json.loads((P/'build/production/build.json').read_text());base=production['commands'][0];common=base[2:base.index('-parse-as-library')]
assert '-O' in common and '-whole-module-optimization' in common
variants={'parent':S,**{e:R/(e+'-trial') for e in ['consume','header','derived-count']}}
for label,source in variants.items():
 files=[source/'Sources/SwiftDataFrame/IO'/f for f in ['SystemsCSVParser.swift','CSVRecordIndex.swift']]+[R/'ScanProbe.swift'];binary=R/('ScanProbe-wmo-'+label);cmd=['xcrun','swiftc',*common,'-parse-as-library',*[str(p) for p in files],'-o',str(binary)]
 p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stderr
 (R/('scan-wmo-'+label+'-build.json')).write_text(json.dumps(dict(command=cmd,production_compiler_options=common,sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest()),indent=2)+'\n');print(label,'matched scanner built',flush=True)
