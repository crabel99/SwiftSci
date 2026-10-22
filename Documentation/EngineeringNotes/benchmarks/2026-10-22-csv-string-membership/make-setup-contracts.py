from pathlib import Path
import csv,json,hashlib,struct,unicodedata
R=Path(__file__).resolve().parent;D=R/'setup-inputs';D.mkdir(exist_ok=False)
base=json.loads(Path('/private/tmp/swiftsci-csv-number-loop-20261022/text-inputs/all-string-large-nulls-0.json').read_text())
with Path(base['path']).open(newline='',encoding='utf-8') as f:
 reader=csv.reader(f);header=next(reader);values=[next(reader) for _ in range(257)]
contracts=[]
for count in [8,257]:
 path=D/f'rows-{count}.csv'
 with path.open('w',newline='',encoding='utf-8') as f:
  w=csv.writer(f,quoting=csv.QUOTE_ALL,lineterminator='\n');w.writerow(header);w.writerows(values[:count])
 for size in [0,10,2048,32768]:
  tokens=[] if size==0 else (['','NA','na','N/A','n/a','null','NULL','NaN','nan','None'] if size==10 else [f'missing-{i}' for i in range(size)])
  nulls={unicodedata.normalize('NFC',s) for s in tokens};digests=[hashlib.sha256() for _ in header];counts=[0 for _ in header]
  for row in values[:count]:
   for j,s in enumerate(row):
    s=s.strip(' \t\r\n')
    if unicodedata.normalize('NFC',s) in nulls:digests[j].update(b'\0');counts[j]+=1
    else:
     b=s.encode();digests[j].update(b'\1'+struct.pack('<I',len(b))+b)
  d=dict(id=f'setup-{count}-{size}',path=str(path),rows=count,names=header,types=['String']*len(header),hashes=[h.hexdigest() for h in digests],null_tokens=tokens,null_counts=counts,integral=[False]*len(header),delimiter=',',max_rows=None,source_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
  p=D/(d['id']+'.json');p.write_text(json.dumps(d,indent=2)+'\n');contracts.append(str(p))
(R/'setup-contracts.json').write_text(json.dumps(contracts,indent=2)+'\n')
s=(R/'screen.py').read_text();s=s.replace("D=R/label;D.mkdir(exist_ok=False)","cases=[('eager',Path(p).stem,Path(p)) for p in json.loads((R/'setup-contracts.json').read_text())]\nD=R/label;D.mkdir(exist_ok=False)")
(R/'setup-controls.py').write_text(s)
print('Prepared eight small-file and large-token-set setup contracts.')
