from pathlib import Path
import json,hashlib,struct,csv
r=Path('/private/tmp/swiftsci-csv-eager-checks-20261021')
p=r/'ResourceProbe.swift';t=p.read_text().replace('        case "Date":','''        case "Bool":
            let c = df[column: name, as: Bool.self]!
            for i in 0..<df.shape.rows { d.append(c[i]) { $0.integer(UInt8($1 ? 1 : 0)) } }
        case "Date":''').replace('["String":.utf8,"Double":.float64,"Int64":.int64,"Date":.date32]', '["String":.utf8,"Double":.float64,"Int64":.int64,"Date":.date32,"Bool":.boolean]');p.write_text(t)
for name,token,end,typ in [('late-bool','1','true','Bool'),('late-text','009007199254740993','offline','String')]:
 p=r/'inputs'/(name+'.csv');p.write_text('value\n'+(token+'\n')*100_000+end+'\n')
 h=hashlib.sha256()
 with p.open() as f:
  for row in list(csv.reader(f))[1:]:
   x=row[0];h.update(b'\1')
   if typ=='String':
    b=x.encode();h.update(struct.pack('<I',len(b)));h.update(b)
   else:h.update(b'\1')
 d=dict(id=name,path=str(p),delimiter=',',rows=100001,names=['value'],types=[typ],hashes=[h.hexdigest()],null_tokens=['','NA'],integral=[False],null_counts=[0],sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 (r/'inputs'/(name+'.json')).write_text(json.dumps(d,indent=2)+'\n')
