from pathlib import Path
import json,subprocess,hashlib
R=Path(__file__).resolve().parent
for label in ['candidate','scoped']:
 d=R/'build'/label
 receipt=json.loads((d/'build.json').read_text())
 cmd=[str(R/'StreamProbe.swift') if arg==str(R/'ResourceProbe.swift') else arg for arg in receipt['commands'][1]]
 cmd[cmd.index('-o')+1]=str(d/'StreamProbe')
 with (d/'stream-link.log').open('w') as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
 if p.returncode:print((d/'stream-link.log').read_text()[-2000:]);raise SystemExit(p.returncode)
 (d/'stream-build.json').write_text(json.dumps({'command':cmd,'binary_sha256':hashlib.sha256((d/'StreamProbe').read_bytes()).hexdigest(),'harness_sha256':hashlib.sha256((R/'StreamProbe.swift').read_bytes()).hexdigest(),'module_receipt_sha256':hashlib.sha256((d/'build.json').read_bytes()).hexdigest()},indent=2)+'\n')
 print(label,'stream probe linked',flush=True)
