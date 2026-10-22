from pathlib import Path
import json,shutil
R=Path(__file__).resolve().parent;B=Path('/private/tmp/swiftsci-csv-vector-mask-control-20261022');D=R/'batch-null-trial';shutil.copytree(B/'Sources/SwiftDataFrame',D/'Sources/SwiftDataFrame')
p=D/'Sources/SwiftDataFrame/IO/CSVColumnConversion.swift';s=p.read_text()
s=s.replace('    case string(CSVColumnAttempt<CSVStringDecoder>)','    case string(CSVColumnAttempt<CSVStringDecoder<Set<String>>>)\n    case stringWithSmallNullSet(CSVColumnAttempt<CSVStringDecoder<[String]>>)')
s=s.replace('        case .utf8:\n            return .string', '''        case .utf8:
            if !nullValues.isEmpty && nullValues.count <= 2 {
                return .stringWithSmallNullSet(CSVColumnAttempt(
                    decoder: CSVStringDecoder(nullValues: Array(nullValues)),
                    capacity: capacity, validates: false))
            }
            return .string''')
lines=s.splitlines(keepends=True);s=''.join(line+(line.replace('case .string(', 'case .stringWithSmallNullSet(') if 'case .string(let attempt):' in line else '') for line in lines)
s=s.replace('internal struct CSVStringDecoder: CSVValueDecoder {\n    let nullValues: Set<String>','internal struct CSVStringDecoder<Nulls: Collection>: CSVValueDecoder where Nulls.Element == String {\n    let nullValues: Nulls')
p.write_text(s)
v=json.loads((R/'variants.json').read_text());v['batch-null']={'path':str(D),'pr':None};(R/'variants.json').write_text(json.dumps(v,indent=2)+'\n')
s=(R/'bounded-pilot.py').read_text().replace("engines=['parent','linear-two','pair-two'];bins={'parent':P/'build/production/ResourceProbe',**{e:R/'build'/e/'ResourceProbe' for e in engines[1:]}}", "engines=['parent','row-null','batch-null'];bins={'parent':P/'build/production/ResourceProbe','row-null':R/'build/production/ResourceProbe','batch-null':R/'build/batch-null/ResourceProbe'}")
s=s.replace("root=S if e=='parent' else R/(e+'-trial')", "root=Path('/private/tmp/swiftsci-csv-vector-mask-control-20261022') if e=='parent' else (S if e=='row-null' else R/(e+'-trial'))")
s=s.replace("assert not (R/'bounded-pilot.json').exists();records=[]",'''selected=[];seen=set()
for case,path,mode in cases:
 name=case.removeprefix('all-string-')
 if case not in ['bike-hour','Aotizhongxin','energy','energy-date-full'] and not name.startswith(('none-nulls','pair-nulls','default-nulls','large-nulls')):continue
 inp=json.loads(path.read_text());key=(inp.get('sha256',inp.get('source_sha256')),tuple(inp['types']),tuple(sorted(inp['null_tokens'])),mode)
 if key not in seen:selected.append((case,path,mode));seen.add(key)
cases=selected
assert not (R/'batch-pilot.json').exists();records=[]''')
for name in ['bounded-pilot.json','bounded-pilot-plan.json','bounded-pilot-workers.jsonl']:s=s.replace(name,name.replace('bounded-','batch-'))
assert 'engines=[\'parent\',\'row-null\',\'batch-null\']' in s
(R/'batch-pilot.py').write_text(s)
