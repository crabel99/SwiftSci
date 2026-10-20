from pathlib import Path
import sys,subprocess,shutil,json
S=Path(__file__).resolve().parent
repo=Path(sys.argv[1]).resolve();D=Path(sys.argv[2]).resolve()
assert not D.exists(), 'Use a new output directory'
D.mkdir(parents=True)
sha='546510bb7df19fc87a664bded5947c738011ee1d'
files=subprocess.check_output(['git','ls-tree','-r','--name-only',sha,'Sources/SwiftDataFrame'],cwd=repo,text=True).splitlines()
for v in ['baseline','active','cursor','specialized']:
 for name in files:
  p=D/v/name;p.parent.mkdir(parents=True,exist_ok=True)
  p.write_bytes(subprocess.check_output(['git','show',sha+':'+name],cwd=repo))
 if v!='baseline':subprocess.run(['git','apply',str(S/(v+'.patch'))],cwd=D/v,check=True)
(D/'variants.json').write_text(json.dumps({v:dict(path=str(D/v),base_sha=sha,pr=None) for v in ['baseline','active','cursor','specialized']},indent=2)+'\n')
for p in S.glob('*.py'):
 if p.name not in ['replay.py','package.py','audit.py','prepare.py','prepare-specialized.py']:
  shutil.copy2(p,D/p.name)
for p in S.glob('*.swift'):shutil.copy2(p,D/p.name)
F=D/'fixtures';F.mkdir()
for n,w,q in [(100000,4,True),(250000,4,True),(1000000,4,True),(1000000,2,True),(1000000,4,False)]:
 with (F/f'{n}-{w}-{q}.csv').open('w') as f:
  f.write(','.join(f'c{j}' for j in range(w))+'\n')
  for i in range(n):
   values=[str((i*17+j*31)%1009)+'.5' for j in range(w)]
   if q:values=['"'+v+'"' for v in values]
   f.write(','.join(values)+'\n')
for p in D.glob('compare*.py'):
 p.write_text(p.read_text().replace("str(P/'02-pr39-csv-quoted-1000000-4.csv')","str(R/'fixtures/1000000-4-True.csv')"))
H=D/'heldout-fixtures';H.mkdir()
for n,w,q in [(1000,4,False),(1000,4,True),(10000,4,True),(131071,7,True),(75001,13,True)]:
 with (H/f'{n}-{w}-{q}.csv').open('w') as f:
  f.write(','.join(f'c{j}' for j in range(w))+'\n')
  for i in range(n):
   values=[str((i*17+j*31)%1009)+'.5' for j in range(w)]
   if q:values=['"'+v+'"' for v in values]
   f.write(','.join(values)+'\n')
shutil.copytree(S/'tests',D/'tests')
for name in ['lookup.py','index.py']:
 p=D/name;p.write_text(p.read_text().replace("Path('/Users/crabel/local-ai/spl/swiftsci/pr-resource-metrics-20261018/fixtures/02-pr39-csv-quoted-1000000-4.csv')","R/'fixtures/1000000-4-True.csv'"))
print(f'cd {str(D)!r}')
print('python3 build.py baseline active cursor specialized')
print('python3 check.py && python3 check-specialized.py && python3 run-tests.py')
print('python3 lookup.py && python3 index.py')
for suffix in ['', '-heldout', '-specialized', '-specialized-heldout', '-production', '-production-heldout']:
 print(f'python3 compare{suffix}.py && python3 summarize{suffix}.py')
