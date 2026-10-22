from pathlib import Path
import csv,hashlib,json,struct,unicodedata
R=Path(__file__).resolve().parent;D=R/'long-key-inputs';D.mkdir(exist_ok=False);contracts=[]
first='missing-measurement-token-with-owned-String-storage';second='second-measurement-token-with-owned-String-storage'
for label,tokens in [('one-long',[first]),('pair-long',[first,second]),('pair-unicode',[first+'-é',second+'-K']),('three-long',[first,second,first+'-third'])]:
 for density in [0,50]:
  path=D/f'{label}-nulls-{density}.csv';n=32769;width=4;hashes=[hashlib.sha256() for _ in range(width)];nulls=[0]*width;norm={unicodedata.normalize('NFC',t) for t in tokens}
  with path.open('w') as f:
   writer=csv.writer(f,lineterminator='\n');writer.writerow([f'text-{i}' for i in range(width)])
   for row in range(n):
    values=[]
    for col in range(width):
     index=row*width+col;v=f'observation-with-owned-String-storage-{index%257},station-"{col}"\nzone-汉字'
     if index%100<density:v=' \t'+unicodedata.normalize('NFD',tokens[index%len(tokens)])+' \r\n'
     values.append(v);decoded=v.strip(' \t\r\n')
     if unicodedata.normalize('NFC',decoded) in norm:hashes[col].update(b'\0');nulls[col]+=1
     else:
      raw=decoded.encode();hashes[col].update(b'\1'+struct.pack('<I',len(raw))+raw)
    writer.writerow(values)
  data=dict(id=path.stem,path=str(path),rows=n,names=[f'text-{i}' for i in range(width)],types=['String']*width,hashes=[h.hexdigest() for h in hashes],null_tokens=tokens,null_counts=nulls,integral=[False]*width,delimiter=',',max_rows=None,source_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
  contract=path.with_suffix('.json');contract.write_text(json.dumps(data,indent=2)+'\n');contracts.append(str(contract))
(R/'long-key-contracts.json').write_text(json.dumps(contracts,indent=2)+'\n')
s=(R/'run-text-controls.py').read_text().replace("R/'text-contracts.json'","R/'long-key-contracts.json'").replace('assert len(cases)==32','assert len(cases)==8').replace("D=R/'text-controls'","D=R/'long-key-controls'")
(R/'run-long-key-controls.py').write_text(s)
p=R/'finish.py';s=p.read_text().replace("('text-controls',['python3',str(R/'run-text-controls.py')])","('text-controls',['python3',str(R/'run-text-controls.py')]),('long-key-controls',['python3',str(R/'run-long-key-controls.py')])");p.write_text(s)
print(len(contracts),'long-key contracts prepared')
