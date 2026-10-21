from pathlib import Path
import csv,json,hashlib
r=Path(__file__).resolve().parent;d=r/'diverse-fixtures';d.mkdir(exist_ok=False)
cases=[]
for kind,n,width in [('mixed',20000,4),('missing',250000,8),('text',2048,2),('dates',2048,2)]:
 p=d/(kind+'.csv')
 with p.open('w',newline='') as f:
  w=csv.writer(f,quoting=csv.QUOTE_ALL,lineterminator='\n');w.writerow(['c'+str(j) for j in range(width)])
  for i in range(n):
   if kind=='mixed':
    row=[str(i-10000),str((i*17)%1009+.5),'true' if i%2==0 else 'false','station-'+str(i%97)]
    for j in range(width):
     if (i+j)%11==0:row[j]='NA'
    if i%37==0:row=row[:-1]
   elif kind=='missing':row=['NA' if (i+j)%11==0 else str((i*17+j*31)%1009+.5) for j in range(width)]
   elif kind=='text':row=[str(i),'prefix, "quoted"\n'+('abcdefgh'*1024)+'-'+str(i)]
   else:row=[str(i),'2026-01-'+str(i%28+1).zfill(2)]
   w.writerow(row)
 for schema in ['infer','known']:cases.append([kind+'-'+schema,n,width,str(p)])
(r/'diverse-cases.json').write_text(json.dumps(cases,indent=2)+'\n')
(r/'diverse-fixtures.json').write_text(json.dumps({str(p):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in d.iterdir()},indent=2)+'\n')
