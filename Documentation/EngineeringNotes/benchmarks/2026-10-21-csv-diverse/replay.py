from pathlib import Path
import sys,subprocess,shutil,json,hashlib
s=Path(__file__).resolve().parent;repo=Path(sys.argv[1]).resolve();d=Path(sys.argv[2]).resolve();d.mkdir(parents=True,exist_ok=False)
sha='546510bb7df19fc87a664bded5947c738011ee1d';variants=['baseline','packed','direct']
files=subprocess.check_output(['git','ls-tree','-r','--name-only',sha,'Sources/SwiftDataFrame'],cwd=repo,text=True).splitlines()
for v in variants:
 for name in files:
  p=d/v/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(subprocess.check_output(['git','show',sha+':'+name],cwd=repo))
 if v!='baseline':subprocess.run(['git','apply',str(s/(v+'.patch'))],cwd=d/v,check=True)
(d/'variants.json').write_text(json.dumps({v:dict(path=str(d/v),base_sha=sha,pr=None) for v in variants},indent=2)+'\n')
for name in ['build.py','run-pair.py','summarize-pair.py','check.py','boundary.py','range-check.py','run-tests.py','make-diverse.py','smoke.py','stream-check.py']:
 shutil.copy2(s/name,d/name)
for name in ['ResourceProbe.swift','Inspect.swift','Semantics.swift','ParserParity.swift','CompactChecks.swift','RangeChecks.swift','StreamChecks.swift']:shutil.copy2(s/name,d/name)
shutil.copytree(s/'tests',d/'tests')
identity=json.loads((s/'replay-identities.json').read_text())
for path in identity['fixtures']:
 if path.startswith('diverse-fixtures/'):continue
 p=d/path;p.parent.mkdir(parents=True,exist_ok=True)
 parts=p.stem.split('-');n,w=int(parts[0]),int(parts[1]);q=parts[2]=='True'
 with p.open('w') as out:
  out.write(','.join(f'c{j}' for j in range(w))+'\n')
  for i in range(n):
   values=[str((i*17+j*31)%1009)+'.5' for j in range(w)]
   if q:values=['"'+v+'"' for v in values]
   out.write(','.join(values)+'\n')
subprocess.run([sys.executable,str(d/'make-diverse.py')],check=True)
p=d/'run-pair.py';old="Path('/Users/crabel/local-ai/spl/swiftsci/pr-resource-metrics-20261018/fixtures/02-pr39-csv-quoted-1000000-4.csv')";text=p.read_text();assert text.count(old)==1;p.write_text(text.replace(old,"R/'fixtures/1000000-4-True.csv'"))
identity=json.loads((s/'replay-identities.json').read_text());h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for v,sources in identity['sources'].items():
 for path,digest in sources.items():assert h(d/v/path)==digest
for path,digest in identity['fixtures'].items():assert h(d/path)==digest
(d/'replay-verification.json').write_text(json.dumps(dict(source_and_fixture_hashes_match=True,base_sha=sha),indent=2)+'\n')
print(f'cd {str(d)!r}')
print('python3 build.py baseline packed direct')
print('python3 check.py && python3 smoke.py && python3 stream-check.py')
print('python3 boundary.py && python3 range-check.py && python3 run-tests.py')
for a,b,suite in [('baseline','direct','primary'),('packed','direct','primary'),('baseline','packed','diverse'),('baseline','packed','primary')]:
 name=f'{a}-{b}-{suite}';print(f'python3 run-pair.py {a} {b} {suite} {name} && python3 summarize-pair.py {name}')
