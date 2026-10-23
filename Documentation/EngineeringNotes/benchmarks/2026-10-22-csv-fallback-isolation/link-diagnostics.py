from pathlib import Path
import json,subprocess,hashlib
R=Path(__file__).resolve().parent;P=Path('/private/tmp/swiftsci-csv-prefix-selection-20261022')
for e in ['diagnostic-cleanup','diagnostic-selected','diagnostic-preflight','no-preparation']:
 D=R/'build'/e;rec=json.loads((D/'build.json').read_text());name='StreamRepeatProbe' if e=='no-preparation' else 'PreparationProbe'
 source=(P if name=='StreamRepeatProbe' else R)/(name+'.swift')
 cmd=[str(source) if a.endswith('/ResourceProbe.swift') else a for a in rec['commands'][1]];cmd[cmd.index('-o')+1]=str(D/name)
 p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stderr
 (D/(name+'.build.json')).write_text(json.dumps(dict(command=cmd,binary_sha256=hashlib.sha256((D/name).read_bytes()).hexdigest(),harness_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),module_receipt_sha256=hashlib.sha256((D/'build.json').read_bytes()).hexdigest()),indent=2)+'\n')
cmd=['xcrun','swiftc','-O',str(R/'HashFingerprint.swift'),'-o',str(R/'HashFingerprint')];subprocess.run(cmd,check=True)
(R/'HashFingerprint.build.json').write_text(json.dumps(dict(command=cmd,binary_sha256=hashlib.sha256((R/'HashFingerprint').read_bytes()).hexdigest()),indent=2)+'\n')
print('All diagnostic binaries built; no production source changes.',flush=True)
