from pathlib import Path
import json,subprocess,hashlib
R=Path(__file__).resolve().parent;P=Path('/private/tmp/swiftsci-csv-local-builder-20261022/build/production');S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021')
rec=json.loads((P/'build.json').read_text());h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert all(h(S/p)==v for p,v in rec['sources'].items())
for name in ['PhaseProbe','LoopProfile']:
 source=R/(name+'.swift');binary=R/name
 cmd=[str(source) if a.endswith('/ResourceProbe.swift') else a for a in rec['commands'][1]];cmd[cmd.index('-o')+1]=str(binary)
 with (R/(name+'.build.log')).open('w') as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
 assert p.returncode==0,(R/(name+'.build.log')).read_text()[-5000:]
 (R/(name+'.build.json')).write_text(json.dumps(dict(command=cmd,harness_sha256=h(source),binary_sha256=h(binary),module_receipt_sha256=h(P/'build.json'),module_object_sha256=h(P/'SwiftDataFrame.o')),indent=2)+'\n');print(name,'built',flush=True)
