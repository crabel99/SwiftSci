from pathlib import Path
import csv,hashlib,json,struct
R=Path(__file__).resolve().parent;D=R/'width-inputs';D.mkdir()
contracts=[]
for n in [257,32769]:
 for width in [1,2,4,8,18,64]:
  label=f'width-{width}-rows-{n}';p=D/(label+'.csv');names=[f'c{j}' for j in range(width)];types=[['Int64','Double','String'][j%3] for j in range(width)];hs=[hashlib.sha256() for j in range(width)];nulls=[0]*width
  with p.open('w') as f:
   w=csv.writer(f,lineterminator='\n');w.writerow(names)
   for i in range(n):
    row=[]
    for j,t in enumerate(types):
     missing=(i*17+j*11)%19==0
     if missing:raw='NA';hs[j].update(b'\0');nulls[j]+=1
     else:
      hs[j].update(b'\1')
      if t=='Int64':raw=str(i*13+j);hs[j].update(struct.pack('<d',float(raw)))
      elif t=='Double':raw=f'{(i*7+j)%1009}.125';hs[j].update(struct.pack('<d',float(raw)))
      else:
       raw=f'site-{j}-{i%113}'+('\nquoted,field' if i%23==0 else '');b=raw.encode();hs[j].update(struct.pack('<I',len(b))+b)
     row.append(raw)
    w.writerow(row)
  c=dict(id=label,path=str(p),rows=n,names=names,types=types,integral=[t=='Int64' for t in types],hashes=[h.hexdigest() for h in hs],null_tokens=['','NA'],null_counts=nulls,delimiter=',',max_rows=None,source_sha256=hashlib.sha256(p.read_bytes()).hexdigest());dest=p.with_suffix('.json');dest.write_text(json.dumps(c,indent=2)+'\n');contracts.append(str(dest))
(R/'width-contracts.json').write_text(json.dumps(contracts,indent=2)+'\n')
