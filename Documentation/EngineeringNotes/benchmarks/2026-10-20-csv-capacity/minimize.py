from pathlib import Path
import subprocess,json
R=Path(__file__).resolve().parent;F=R/'fixtures';F.mkdir(exist_ok=True)
binary='/Users/crabel/local-ai/spl/swiftsci/pr-resource-metrics-20261018/build/pr39-after/inspect-csv'
cases=[(n,4,True) for n in [1000,10000,100000,250000,500000]]+[(1000000,w,q) for w,q in [(1,True),(2,True),(4,False)]]
results=[]
for n,w,quoted in cases:
 p=F/f'{n}-{w}-{quoted}.csv'
 with p.open('w') as f:
  f.write(','.join(f'c{j}' for j in range(w))+'\n')
  for i in range(n):
   vals=[str((i*17+j*31)%1009)+'.5' for j in range(w)]
   if quoted:vals=['"'+v+'"' for v in vals]
   f.write(','.join(vals)+'\n')
 columns=json.loads(subprocess.check_output([binary,str(p)],text=True))
 ratio=max(c['capacity']/c['count'] for c in columns)
 results.append(dict(n=n,width=w,quoted=quoted,columns=columns,ratio=ratio));print(n,w,quoted,round(ratio,4),flush=True)
(R/'minimization.json').write_text(json.dumps(results,indent=2)+'\n')
