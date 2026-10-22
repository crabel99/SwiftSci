from pathlib import Path
import json,csv,hashlib,struct
R=Path(__file__).resolve().parent;T=Path('/private/tmp/swiftsci-csv-number-loop-20261022');E=Path('/private/tmp/swiftsci-csv-cpu-profile-20261021/inputs');(R/'inputs').mkdir(exist_ok=True)
contracts=[T/'text-inputs/all-string-default-nulls-0.json',T/'Aotizhongxin-default.json',E/'energy.json'];plan=[]
for source in contracts:
 d=json.loads(source.read_text())
 if d['id']=='energy':d['id']='energy-default';d['null_tokens']=['','NA','na','N/A','n/a','null','NULL','NaN','nan','None']
 columns=[i for i,t in enumerate(d['types']) if t=='String'];hashes={i:hashlib.sha256() for i in columns};n=0
 assert hashlib.sha256(Path(d['path']).read_bytes()).hexdigest()==d.get('source_sha256',d.get('sha256'))
 with Path(d['path']).open(newline='',encoding='utf-8',errors='strict') as f:
  reader=csv.reader(f,delimiter=d['delimiter']);assert next(reader)==d['names']
  for row in reader:
   if not row:continue
   n+=1
   for i,h in hashes.items():
    raw=row[i].strip(' \t\r\n').encode();h.update(b'\x01'+struct.pack('<I',len(raw))+raw)
 assert n==d['rows'];d['raw_string_hashes']={d['names'][i]:h.hexdigest() for i,h in hashes.items()}
 out=R/'inputs'/(d['id']+'.json');content=json.dumps(d,indent=2)+'\n'
 if out.exists():assert out.read_text()==content
 else:out.write_text(content)
 plan.append(str(out))
content=json.dumps(plan,indent=2)+'\n';out=R/'contracts.json'
if out.exists():assert out.read_text()==content
else:out.write_text(content)
for density in [0,50]:
 source=Path('/private/tmp/swiftsci-csv-null-dispatch-20261022/long-key-inputs')/f'pair-unicode-nulls-{density}.json';d=json.loads(source.read_text());d['null_tokens'].append('_unused_ascii_null_token_for_hashed_fallback_');d['id']=f'three-unicode-nulls-{density}'
 assert b'_unused_ascii_null_token_for_hashed_fallback_' not in Path(d['path']).read_bytes()
 out=R/'inputs'/(d['id']+'.json');content=json.dumps(d,indent=2)+'\n'
 if out.exists():assert out.read_text()==content
 else:out.write_text(content)
