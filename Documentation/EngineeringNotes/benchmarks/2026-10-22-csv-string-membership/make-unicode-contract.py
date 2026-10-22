from pathlib import Path
import csv,hashlib,json,struct,unicodedata
R=Path(__file__).resolve().parent;D=R/'unicode';D.mkdir(exist_ok=False)
tokens=['','NA','na','N/A','n/a','null','NULL','NaN','nan','None','K','A','e','\x00','!','?','Z','\x7f']
nulls=set(tokens);digests=[hashlib.sha256() for _ in range(3)];counts=[0,0,0];rows=0
path=D/'all-scalars.csv'
def consume(values):
 global rows
 rows+=1
 for i,value in enumerate(values):
  value=value.strip(' \t\r\n')
  if unicodedata.normalize('NFC',value) in nulls:digests[i].update(b'\x00');counts[i]+=1
  else:
   raw=value.encode();digests[i].update(b'\x01'+struct.pack('<I',len(raw))+raw)
with path.open('w',encoding='utf-8',newline='') as f:
 w=csv.writer(f,lineterminator='\n',quoting=csv.QUOTE_ALL);w.writerow(['scalar','excluded-ASCII-prefix','included-ASCII-prefix'])
 for n in range(0x110000):
  if 0xd800<=n<=0xdfff:continue
  scalar=chr(n);values=[scalar,'X'+scalar,'N'+scalar];w.writerow(values);consume(values)
 # Multi-scalar normalization, long Strings and token prefixes share the same input.
 for value in ['K','K','é','e\u0301','Å','A\u030a','N\u0303','X\u0301','NA','NaN','null','None','K'+'\u0301'*16,'X'+'\u0301'*16,'a"b',' NA \r\n','value'*40]:
  values=[value,'X'+value,'N'+value];w.writerow(values);consume(values)
d=dict(id='all-unicode-scalars',path=str(path),rows=rows,names=['scalar','excluded-ASCII-prefix','included-ASCII-prefix'],types=['String']*3,hashes=[h.hexdigest() for h in digests],null_tokens=tokens,null_counts=counts,integral=[False]*3,delimiter=',',max_rows=None,source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),expected_scope='Every Unicode scalar and two ASCII-prefixed variants, plus multi-scalar normalization, escaped quotes and long Strings. Independent Python CSV and NFC membership expectation. This is semantic coverage, not a performance dataset.',unicode_reference_version=unicodedata.unidata_version)
(D/'all-scalars.json').write_text(json.dumps(d,indent=2)+'\n');print(rows,'rows;',rows*3,'independently hashed String cells',flush=True)
