from pathlib import Path
import json,shutil
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');v=json.loads((R/'variants.json').read_text())
for old,label in [('linear-null','linear-two'),('pair-null','pair-two')]:
 d=R/(label+'-trial');shutil.copytree(S/'Sources/SwiftDataFrame',d/'Sources/SwiftDataFrame');v[label]={'path':str(d),'pr':None}
 p=d/'Sources/SwiftDataFrame/IO/CSVColumnConversion.swift';text=(R/(old+'-trial')/'Sources/SwiftDataFrame/IO/CSVColumnConversion.swift').read_text()
 if label=='linear-two':text=text.replace('values.count <= 16','values.count <= 2')
 else:
  text=text.replace('    case linear([String])\n','').replace('        case .linear(let values): values.contains(value)\n','')
  a=text.index('    init(_ values: Set<String>) {',text.index('internal enum CSVStringNulls'))
  b=text.index('    @inline(__always)',a)
  text=text[:a]+'''    init(_ values: Set<String>) {
        guard values.count <= 2 else {
            self = .hashed(values)
            return
        }
        var iterator = values.makeIterator()
        guard let first = iterator.next() else {
            self = .none
            return
        }
        if let second = iterator.next() { self = .two(first, second) }
        else { self = .one(first) }
    }

'''+text[b:]
 p.write_text(text)
(R/'variants.json').write_text(json.dumps(v,indent=2)+'\n')
s=(R/'pilot.py').read_text().replace("engines=['parent','lazy-null','linear-null','pair-null']", "engines=['parent','linear-two','pair-two']")
s=s.replace("orders=[engines[i:]+engines[:i] for i in range(len(engines))]", "orders=[engines[i:]+engines[:i] for i in range(len(engines))]+[list(reversed(engines[i:]+engines[:i])) for i in range(len(engines))]")
for name in ['pilot.json','pilot-plan.json','pilot-workers.jsonl']:s=s.replace("R/'"+name+"'", "R/'bounded-"+name+"'")
(R/'bounded-pilot.py').write_text(s)
