from pathlib import Path
import json
r=Path(__file__).resolve().parent;d=r/'flat-fixtures';d.mkdir(exist_ok=False);cases=[]
for n,w in [(5000,4),(100000,4),(1000000,2),(131071,7),(75001,13)]:
 p=d/f'{n}-{w}.csv'
 with p.open('w') as f:
  f.write(','.join(f'c{j}' for j in range(w))+'\n')
  for i in range(n):f.write(','.join(str((i*17+j*31)%1009)+'.5' for j in range(w))+'\n')
 cases.append(['csv',n,w,str(p)])
(r/'flat-cases.json').write_text(json.dumps(cases,indent=2)+'\n')
