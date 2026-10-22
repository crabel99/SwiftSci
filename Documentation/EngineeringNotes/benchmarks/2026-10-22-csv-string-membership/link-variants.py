from pathlib import Path
import subprocess,json,hashlib,sys
R=Path(__file__).resolve().parent
for label in sys.argv[1:]:
 D=R/'build'/label;rec=json.loads((D/'build.json').read_text());cmd=[str(R/'StreamProbe.swift') if a.endswith('/ResourceProbe.swift') else a for a in rec['commands'][1]];binary=D/'StreamProbe';cmd[cmd.index('-o')+1]=str(binary)
 p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stderr
 (D/'StreamProbe.build.json').write_text(json.dumps(dict(command=cmd,binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),harness_sha256=hashlib.sha256((R/'StreamProbe.swift').read_bytes()).hexdigest()),indent=2)+'\n')
 print(label,'streaming probe linked',flush=True)
