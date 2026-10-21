from pathlib import Path
import subprocess,json,hashlib
r=Path(__file__).resolve().parent;v='scoped';d=r/'asan'/v;d.mkdir(parents=True,exist_ok=False)
b=json.loads((r/'build'/v/'build.json').read_text())
cmd=[s.replace(str(r/'build'/v),str(d)) for s in b['commands'][0]]+['-sanitize=address']
p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stderr
link=[s.replace(str(r/'build'/v),str(d)) for s in b['commands'][1]]+['-sanitize=address']
p=subprocess.run(link,capture_output=True,text=True);assert p.returncode==0,p.stderr
cases=json.loads((r/'diverse-cases.json').read_text())+[['csv',1000000,4,str(r/'fixtures/1000000-4-False.csv')]]
receipts=[]
for case in cases:
 run=[str(d/'ResourceProbe'),case[0],str(case[1]),str(case[2]),'1','memory',case[3]]
 p=subprocess.run(run,capture_output=True,text=True,timeout=180);assert p.returncode==0,p.stderr
 assert json.loads(p.stdout)['validated'] and not p.stderr,p.stderr
 receipts.append(dict(case=case,exit_code=p.returncode,result=json.loads(p.stdout),stderr=p.stderr));print('ASan',case[0],'PASS',flush=True)
(r/'sanitizer.json').write_text(json.dumps(dict(variant=v,commands=[cmd,link],production_build=b,receipts=receipts,binary_sha256=hashlib.sha256((d/'ResourceProbe').read_bytes()).hexdigest()),indent=2)+'\n')
