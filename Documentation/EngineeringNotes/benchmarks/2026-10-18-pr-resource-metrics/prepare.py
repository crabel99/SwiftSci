"""Prepare an isolated replay directory from the recorded Git revisions."""
from pathlib import Path
import argparse,hashlib,io,json,shutil,subprocess,tarfile
p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
S=Path(__file__).resolve().parent;R=a.output.resolve();R.mkdir(parents=True,exist_ok=False)
for name in ['PLAN.md','ResourceProbe.swift','MLPProbe.swift','inspect-csv.swift','build.py','build-mlp.py','run.py','summarize.py','revisions.json']:
 shutil.copy2(S/name,R/name)
variants=json.loads((S/'revisions.json').read_text())
for label,v in variants.items():
 d=R/'sources'/label;d.mkdir(parents=True)
 data=subprocess.check_output(['git','archive',v['sha'],'Sources/','Package.swift','Package.resolved'],cwd=a.repo)
 with tarfile.open(fileobj=io.BytesIO(data)) as archive:archive.extractall(d,filter='data')
 v['path']=str(d)
(R/'variants.json').write_text(json.dumps(variants,indent=2)+'\n')
F=R/'fixtures';F.mkdir()
cases=[]
for mode,n,w in [('csv',100000,4),('csv',1000000,4),('csv-quoted',1000000,4),('gather',100000,4),('gather',1000000,4),('gather',100000,32)]:cases.append(dict(pr=39,mode=mode,rows=n,width=w))
for mode,n,w in [('target',100000,8),('target',1000000,8),('matrix',100000,8),('matrix',8192,128)]:cases.append(dict(pr=45,mode=mode,rows=n,width=w))
for n,w in [(16384,128),(512,2048),(4096,8)]:cases.append(dict(pr=82,mode='compact-matrix',rows=n,width=w))
for i,c in enumerate(cases):
 c['id']=f'{i:02d}-pr{c["pr"]}-{c["mode"]}-{c["rows"]}-{c["width"]}'
 if c['mode'].startswith('csv'):
  path=F/(c['id']+'.csv')
  with path.open('w') as f:
   f.write(','.join(f'c{j}' for j in range(c['width']))+'\n')
   for row in range(c['rows']):
    values=[str((row*17+j*31)%1009)+'.5' for j in range(c['width'])]
    if c['mode']=='csv-quoted':values=['"'+v+'"' for v in values]
    f.write(','.join(values)+'\n')
  c['file']=str(path);c['file_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
(R/'cases.json').write_text(json.dumps(cases,indent=2)+'\n')
print('Prepared',R)
