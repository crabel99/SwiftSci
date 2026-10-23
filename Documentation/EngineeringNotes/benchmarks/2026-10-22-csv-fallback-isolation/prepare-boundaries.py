from pathlib import Path
import csv,json,hashlib,struct,unicodedata,shutil
R=Path(__file__).resolve().parent;D=R/'metadata-boundary-inputs';D.mkdir(exist_ok=False);contracts=[]
for count in [3,10,64]:
 for family in ['short','long']:
  tokens=['']+[('missing-' if family=='short' else 'missing-measurement-with-an-owned-long-ASCII-token-')+str(i) for i in range(count-1)]
  byte_work=sum(len(t.encode()) for t in tokens);combined_work=count+byte_work
  row_counts=sorted({max(1,n) for b in [byte_work,combined_work,2*count+byte_work] for n in [b-1,b,b+1]}|{combined_work*4})
  for rows in row_counts:
   for density in [0,90]:
    name=f'{family}-keys-{count}-rows-{rows}-nulls-{density}';path=D/(name+'.csv');digests=[hashlib.sha256(),hashlib.sha256()];null_counts=[0,0];nulls=set(tokens)
    with path.open('w',newline='',encoding='utf-8') as f:
     w=csv.writer(f,quoting=csv.QUOTE_ALL,lineterminator='\n');w.writerow(['text-0','text-1'])
     for i in range(rows):
      ordinary=['ordinary-value-'+str(i),'é','e\u0301','汉字','a"b','first\nsecond','K','K']
      values=[tokens[(i+j)%count] if (i*3+j)%10<density//10 else ordinary[(i+j)%len(ordinary)] for j in range(2)];w.writerow(values)
      for j,value in enumerate(values):
       value=value.strip(' \t\r\n')
       if unicodedata.normalize('NFC',value) in nulls:digests[j].update(b'\0');null_counts[j]+=1
       else:
        b=value.encode();digests[j].update(b'\1'+struct.pack('<I',len(b))+b)
    d=dict(id=name,path=str(path),rows=rows,names=['text-0','text-1'],types=['String','String'],hashes=[h.hexdigest() for h in digests],null_tokens=tokens,null_counts=null_counts,integral=[False,False],delimiter=',',max_rows=None,source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),preparation=dict(tokens=count,bytes=byte_work,combined=combined_work,expected_combined=rows>=combined_work,expected_byte_only=rows>=byte_work))
    p=D/(name+'.json');p.write_text(json.dumps(d,indent=2)+'\n');contracts.append(str(p))
(R/'metadata-boundary-contracts.json').write_text(json.dumps(contracts,indent=2)+'\n')
