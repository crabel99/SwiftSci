from pathlib import Path
import subprocess,hashlib,json
R=Path(__file__).resolve().parent;D=R/'build/production';receipt=json.loads((D/'build.json').read_text())
for label in ['GrammarProbe','StreamProbe']:
 cmd=[str(R/(label+'.swift')) if a.endswith('/ResourceProbe.swift') else a for a in receipt['commands'][1]];binary=D/label;cmd[cmd.index('-o')+1]=str(binary)
 if label=='GrammarProbe':cmd.remove('-parse-as-library')
 p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stderr
 (D/(label+'.build.json')).write_text(json.dumps(dict(command=cmd,binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),harness_sha256=hashlib.sha256((R/(label+'.swift')).read_bytes()).hexdigest(),module_receipt_sha256=hashlib.sha256((D/'build.json').read_bytes()).hexdigest()),indent=2)+'\n')
p=subprocess.run([str(D/'GrammarProbe')],capture_output=True,text=True);assert p.returncode==0,p.stderr
assert p.stdout.strip()=='30720 e144dd63a50a7717083714de1d9e1817990a23fe5f247bbe1d5c3d49e31c6a33'
(R/'grammar-result.json').write_text(json.dumps(dict(exit_code=p.returncode,output=p.stdout.strip()),indent=2)+'\n');print(p.stdout.strip())
