from pathlib import Path
import json,subprocess,shutil
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');P=Path('/private/tmp/swiftsci-csv-loop-profile-20261022')
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=S,text=True).strip()=='46a9b9bf951918cd2eb281dadf554efb30c7b0a0'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=S)
for f in ['build.py','ResourceProbe.swift','StreamProbe.swift','GrammarProbe.swift','link-probes.py','verify.py','build-standard-worker.py','summarize-pilot.py']:shutil.copy2(P/f,R/f)
linear='''internal enum CSVStringNulls {
    case linear([String])
    case hashed(Set<String>)

    init(_ values: Set<String>) {
        self = values.count <= 16 ? .linear(Array(values)) : .hashed(values)
    }

    @inline(__always)
    func contains(_ value: String) -> Bool {
        switch self {
        case .linear(let values): values.contains(value)
        case .hashed(let values): values.contains(value)
        }
    }
}

'''
pair='''internal enum CSVStringNulls {
    case none
    case one(String)
    case two(String, String)
    case linear([String])
    case hashed(Set<String>)

    init(_ values: Set<String>) {
        switch values.count {
        case 0: self = .none
        case 1: self = .one(values.first!)
        case 2:
            let strings = values.sorted()
            self = .two(strings[0], strings[1])
        case 3...16: self = .linear(Array(values))
        default: self = .hashed(values)
        }
    }

    @inline(__always)
    func contains(_ value: String) -> Bool {
        switch self {
        case .none: false
        case .one(let first): value == first
        case .two(let first, let second): value == first || value == second
        case .linear(let values): values.contains(value)
        case .hashed(let values): values.contains(value)
        }
    }
}

'''
v={}
for label in ['lazy-null','linear-null','pair-null']:
 d=R/(label+'-trial');shutil.copytree(S/'Sources/SwiftDataFrame',d/'Sources/SwiftDataFrame');v[label]={'path':str(d),'pr':None}
 p=d/'Sources/SwiftDataFrame/IO/CSVColumnConversion.swift';s=p.read_text()
 if label=='lazy-null':
  assert s.count('        let nulls = CSVNullMatcher(nullValues)')==1
  s=s.replace('        let nulls = CSVNullMatcher(nullValues)\n','')
  s=s.replace('Decoder(nulls: nulls','Decoder(nulls: CSVNullMatcher(nullValues)')
 else:
  needle='internal struct CSVStringDecoder: CSVValueDecoder {\n    let nullValues: Set<String>'
  assert needle in s
  s=s.replace(needle,(linear if label=='linear-null' else pair)+'internal struct CSVStringDecoder: CSVValueDecoder {\n    let nullValues: CSVStringNulls\n\n    init(nullValues: Set<String>) {\n        self.nullValues = CSVStringNulls(nullValues)\n    }')
 p.write_text(s)
(R/'variants.json').write_text(json.dumps(v,indent=2)+'\n')
print('Prepared three single-factor scratch trials. Production source unchanged.')
