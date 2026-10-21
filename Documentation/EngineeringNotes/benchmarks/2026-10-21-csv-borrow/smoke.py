from pathlib import Path
import json,subprocess,hashlib
r=Path(__file__).resolve().parent
records=[]
for v in list(json.loads((r/'variants.json').read_text())):
 for c in json.loads((r/'diverse-cases.json').read_text()):
  cmd=[str(r/'build'/v/'ResourceProbe'),c[0],str(c[1]),str(c[2]),'1','memory',c[3]]
  p=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
  record={'variant':v,'case':c,'command':cmd,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
  records.append(record)
  (r/'smoke.json').write_text(json.dumps(records,indent=2)+'\n')
  assert p.returncode==0,p.stderr
  assert json.loads(p.stdout)['validated']
  print(v,c[0],'PASS',flush=True)
