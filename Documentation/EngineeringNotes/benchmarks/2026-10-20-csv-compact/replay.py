from pathlib import Path
import sys,subprocess,shutil,json
S=Path(__file__).resolve().parent;repo=Path(sys.argv[1]).resolve();D=Path(sys.argv[2]).resolve();D.mkdir(parents=True,exist_ok=False)
sha='546510bb7df19fc87a664bded5947c738011ee1d';variants=['baseline','active','compact','inlined','packed']
files=subprocess.check_output(['git','ls-tree','-r','--name-only',sha,'Sources/SwiftDataFrame'],cwd=repo,text=True).splitlines()
for v in variants:
 for name in files:
  p=D/v/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(subprocess.check_output(['git','show',sha+':'+name],cwd=repo))
 if v!='baseline':subprocess.run(['git','apply',str(S/(v+'.patch'))],cwd=D/v,check=True)
(D/'variants.json').write_text(json.dumps({v:dict(path=str(D/v),base_sha=sha,pr=None) for v in variants},indent=2)+'\n')
for name in ['build.py','run-pair.py','summarize-pair.py','check.py','check-inlined.py','check-packed.py','boundary.py','packed-boundary.py','range-check.py','packed-range-check.py','run-tests.py','run-packed-tests.py']:
 shutil.copy2(S/name,D/name)
for name in ['ResourceProbe.swift','Inspect.swift','Semantics.swift','ParserParity.swift','CompactChecks.swift','RangeChecks.swift']:shutil.copy2(S/name,D/name)
shutil.copytree(S/'tests',D/'tests')
for name,cases in [('fixtures',[(100000,4,True),(250000,4,True),(1000000,4,True),(1000000,2,True),(1000000,4,False)]),('heldout-fixtures',[(1000,4,False),(1000,4,True),(10000,4,True),(131071,7,True),(75001,13,True)])]:
 F=D/name;F.mkdir()
 for n,w,q in cases:
  with (F/f'{n}-{w}-{q}.csv').open('w') as f:
   f.write(','.join(f'c{j}' for j in range(w))+'\n')
   for i in range(n):
    values=[str((i*17+j*31)%1009)+'.5' for j in range(w)]
    if q:values=['"'+v+'"' for v in values]
    f.write(','.join(values)+'\n')
p=D/'run-pair.py';p.write_text(p.read_text().replace("Path('/Users/crabel/local-ai/spl/swiftsci/pr-resource-metrics-20261018/fixtures/02-pr39-csv-quoted-1000000-4.csv')","R/'fixtures/1000000-4-True.csv'"))
print(f'cd {str(D)!r}')
print('python3 build.py baseline active compact inlined packed')
print('python3 check.py && python3 check-inlined.py && python3 check-packed.py')
print('python3 boundary.py && python3 packed-boundary.py && python3 range-check.py && python3 packed-range-check.py')
print('python3 run-tests.py && python3 run-packed-tests.py')
for old,new,suites in [('baseline','compact',['primary','heldout']),('active','compact',['primary','heldout']),('baseline','inlined',['primary']),('baseline','packed',['primary','heldout']),('compact','packed',['heldout'])]:
 for suite in suites:
  name=f'{old}-{new}-{suite}'
  print(f'python3 run-pair.py {old} {new} {suite} {name} && python3 summarize-pair.py {name}')
