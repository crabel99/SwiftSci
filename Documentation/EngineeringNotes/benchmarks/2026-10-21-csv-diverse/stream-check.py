from pathlib import Path
import subprocess,json,hashlib
r=Path(__file__).resolve().parent;records=[]
for v in ['baseline','packed','direct']:
 b=json.loads((r/'build'/v/'build.json').read_text());cmd=b['commands'][1][:]
 cmd[cmd.index(str(r/'ResourceProbe.swift'))]=str(r/'StreamChecks.swift');cmd[-1]=str(r/'build'/v/'StreamChecks')
 p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stderr
 p=subprocess.run([cmd[-1],str(r/'diverse-cases.json')],capture_output=True,text=True,timeout=120);assert p.returncode==0,p.stderr
 records.append(dict(variant=v,command=cmd,stdout=p.stdout,exit_code=p.returncode,source_sha256=hashlib.sha256((r/'StreamChecks.swift').read_bytes()).hexdigest()))
 print(v,p.stdout.strip(),flush=True)
(r/'stream-checks.json').write_text(json.dumps(records,indent=2)+'\n')
