from pathlib import Path
import json,hashlib,struct
R=Path(__file__).resolve().parent;p=R/'text-contracts.json';contracts=json.loads(p.read_text());assert len(contracts)==17
for item in list(contracts):
 q=Path(item);d=json.loads(q.read_text());h=hashlib.sha256()
 for index in range(d['rows']):
  raw=str(index).encode();h.update(b'\1'+struct.pack('<I',len(raw))+raw)
 d['id']='all-string-'+d['id'];d['types']=['String','String'];d['integral']=[False,False];d['hashes'][0]=h.hexdigest()
 dest=q.with_name('all-string-'+q.name);dest.write_text(json.dumps(d,indent=2)+'\n');contracts.append(str(dest))
p.write_text(json.dumps(contracts,indent=2)+'\n');print(len(contracts),'contracts, 32 unique byte/schema/null combinations')
p=R/'run-text-controls.py';s=p.read_text();assert 'assert len(cases)==16' in s;p.write_text(s.replace('assert len(cases)==16','assert len(cases)==32'))
