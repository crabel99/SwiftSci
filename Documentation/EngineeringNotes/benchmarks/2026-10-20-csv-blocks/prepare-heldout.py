from pathlib import Path
R=Path(__file__).resolve().parent
D=R/'heldout-fixtures';D.mkdir(exist_ok=True)
for n,w,q in [(1000,4,False),(1000,4,True),(10000,4,True),(131071,7,True),(75001,13,True)]:
 p=D/f'{n}-{w}-{q}.csv'
 with p.open('w') as f:
  f.write(','.join(f'c{i}' for i in range(w))+'\n')
  for i in range(n):
   fields=[str((i*17+j*31)%1009)+'.5' for j in range(w)]
   if q:fields=['"'+v+'"' for v in fields]
   f.write(','.join(fields)+'\n')
# Fixed held-out cases declared before inspecting active-block measurements.
s=(R/'compare-active.py').read_text()
a=s.index('cases=');b=s.index('\nbuilds=',a)
s=s[:a]+'''cases=[['csv',1000,4,str(R/'heldout-fixtures/1000-4-False.csv')],['csv-quoted',1000,4,str(R/'heldout-fixtures/1000-4-True.csv')],['csv-quoted',10000,4,str(R/'heldout-fixtures/10000-4-True.csv')],['csv-quoted',131071,7,str(R/'heldout-fixtures/131071-7-True.csv')],['csv-quoted',75001,13,str(R/'heldout-fixtures/75001-13-True.csv')]]'''+s[b:]
for f in ['comparison-plan.json','workers.jsonl','power-end.json']:
 s=s.replace('active-'+f,'heldout-'+f)
(R/'compare-heldout.py').write_text(s)
s=(R/'summarize-active.py').read_text()
for f in ['workers.jsonl','summary.json','RESULTS.md']:
 s=s.replace('active-'+f,'heldout-'+f)
(R/'summarize-heldout.py').write_text(s)
print('Declared five held-out cases')
