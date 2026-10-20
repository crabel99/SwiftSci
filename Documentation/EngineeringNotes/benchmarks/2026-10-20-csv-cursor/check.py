from pathlib import Path
import subprocess,json,hashlib
R=Path(__file__).resolve().parent;records=[]
for v in ['baseline','active','cursor']:
 b=json.loads((R/'build'/v/'build.json').read_text())
 for name in ['Inspect','Semantics','ParserParity']:
  cmd=b['commands'][1][:];cmd[cmd.index(str(R/'ResourceProbe.swift'))]=str(R/(name+'.swift'));cmd[-1]=str(R/'build'/v/name)
  p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stderr
  args=[str(R/'fixtures/250000-4-True.csv')] if name=='Inspect' else []
  p=subprocess.run([cmd[-1],*args],capture_output=True,text=True);assert p.returncode==0,p.stderr
  records.append({'variant':v,'probe':name,'command':cmd,'stdout':p.stdout,'source_sha256':hashlib.sha256((R/(name+'.swift')).read_bytes()).hexdigest()});print(v,name,p.stdout.strip())
(R/'checks.json').write_text(json.dumps(records,indent=2)+'\n')

parity=[r['stdout'] for r in records if r['probe']=='ParserParity']
assert len(parity)==3 and len(set(parity))==1,parity
