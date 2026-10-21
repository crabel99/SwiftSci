from pathlib import Path
import csv,datetime,hashlib,itertools,json,random,shutil,struct
R=Path(__file__).resolve().parent;I=R/'inputs';I.mkdir(exist_ok=True);D=R/'data';D.mkdir(exist_ok=True)
old=Path('/private/tmp/swiftsci-csv-matched-20261021')
for name in ['energy','energy-date-full','beijing-Aotizhongxin','beijing-Wanliu']:
 p=old/'inputs'/(name+'.json')
 if p.exists():shutil.copy2(p,I/p.name)
source=(old/'ResourceProbe.swift').read_text().replace('let max_rows: Int?', 'let max_rows: Int?\n    let date_formats: [String: String]?')
source=source.replace('if input.id.hasPrefix("energy-date-") && mode == "known" {\n            options.columnDateFormats = ["Date": "d/M/yyyy"]\n        }','if mode == "known" { options.columnDateFormats = input.date_formats ?? (input.id.hasPrefix("energy-date-") ? ["Date": "d/M/yyyy"] : [:]) }')
(R/'ResourceProbe.swift').write_text(source)
shutil.copy2(old/'build.py',R/'build.py')
(R/'variants.json').write_text(json.dumps({'baseline':{'path':'/private/tmp/swiftsci-csv-date-format-20261021','pr':None},'candidate':{'path':'/private/tmp/swiftsci-csv-ingestion-20261021','pr':None}},indent=2))
def oracle(name,path,date_name,fmt,foundation_fmt,double_names):
 with path.open(newline='') as f:
  reader=csv.DictReader(f);names=reader.fieldnames;hashes=[hashlib.sha256() for _ in names];rows=0
  types=['Date' if n==date_name else 'Double' if n in double_names else 'Int64' for n in names]
  for row in reader:
   for j,(n,k) in enumerate(zip(names,types)):
    v=row[n]
    if k=='Date':value=datetime.datetime.strptime(v,fmt).replace(tzinfo=datetime.timezone.utc).timestamp()
    else:value=float(v) if k=='Double' else float(int(v))
    hashes[j].update(b'\1'+struct.pack('<d',value))
   rows+=1
 case=dict(id=name,path=str(path),rows=rows,names=names,types=types,hashes=[h.hexdigest() for h in hashes],null_tokens=['','NA'],null_counts=[0]*len(names),integral=[k=='Int64' for k in types],delimiter=',',date_formats={date_name:foundation_fmt},max_rows=None,source_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
 (I/(name+'.json')).write_text(json.dumps(case,indent=2)+'\n')
for n in ['day','hour']:
 oracle('bike-'+n,R/'reference'/(n+'.csv'),'dteday','%Y-%m-%d','yyyy-MM-dd',{'temp','atemp','hum','windspeed'})
# Distinct dates and their deterministic permutation are diagnostic controls, not reference data.
for kind,seed in [('unique',None),('unique-shuffled',81471)]:
 indices=list(range(100_000))
 if seed is not None:random.Random(seed).shuffle(indices)
 p=D/(kind+'.csv')
 with p.open('w',newline='') as f:
  w=csv.writer(f);w.writerow(['date','value'])
  for i in indices:w.writerow([(datetime.date(1970,1,1)+datetime.timedelta(days=i)).isoformat(),i])
 oracle(kind,p,'date','%Y-%m-%d','yyyy-MM-dd',set())
print('Prepared cases:',[p.stem for p in I.glob('*.json')])
