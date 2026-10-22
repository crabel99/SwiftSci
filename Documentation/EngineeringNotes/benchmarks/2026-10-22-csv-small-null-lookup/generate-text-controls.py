from pathlib import Path
import csv,hashlib,json,struct,unicodedata
R=Path(__file__).resolve().parent;D=R/'text-inputs';D.mkdir(exist_ok=False)
default=['','NA','na','N/A','n/a','null','NULL','NaN','nan','None']
contracts=[]
for label,tokens in [('none',[]),('one',['NA']),('pair',['','NA']),('four',['','NA','é','K']),('default',default),('sixteen',['','NA','é','K','a"b']+[f'missing-{j}' for j in range(11)]),('seventeen',[f'missing-{j}' for j in range(17)]),('large',[f'missing-{j}' for j in range(2048)])]:
 for density in ([0,50] if label!='default' else [0,50,90]):
  p=D/f'{label}-nulls-{density}.csv';hs=[hashlib.sha256(),hashlib.sha256()];nulls=[0,0];norm={unicodedata.normalize('NFC',t) for t in tokens};n=32769
  with p.open('w') as f:
   w=csv.writer(f,lineterminator='\n');w.writerow(['id','text'])
   for i in range(n):
    value=f'reading-{i%257}'
    if i%13==0:value=f'site,{i%17}\nzone'
    if i%31==0:value='e\u0301'
    if i%37==0:value='K'
    if i%41==0:value='a"b'
    if i%43==0:value=''
    if tokens and (i*17)%100<density:value=' \t'+tokens[i%len(tokens)]+' \r\n'
    w.writerow([str(i),value]);hs[0].update(b'\1'+struct.pack('<d',float(i)))
    decoded=value.strip(' \t\r\n')
    if unicodedata.normalize('NFC',decoded) in norm:hs[1].update(b'\0');nulls[1]+=1
    else:
     raw=decoded.encode();hs[1].update(b'\1'+struct.pack('<I',len(raw))+raw)
  d=dict(id=p.stem,path=str(p),rows=n,names=['id','text'],types=['Int64','String'],hashes=[h.hexdigest() for h in hs],null_tokens=tokens,null_counts=nulls,integral=[True,False],delimiter=',',max_rows=None,source_sha256=hashlib.sha256(p.read_bytes()).hexdigest())
  q=p.with_suffix('.json');q.write_text(json.dumps(d,indent=2)+'\n');contracts.append(str(q))
(R/'text-contracts.json').write_text(json.dumps(contracts,indent=2)+'\n');print(len(contracts),'independent String controls')
