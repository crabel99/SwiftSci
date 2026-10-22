from pathlib import Path
import json,shutil
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-control-20261021');T=R/'explicit-trial';shutil.copytree(S/'Sources/SwiftDataFrame',T/'Sources/SwiftDataFrame',dirs_exist_ok=True)
p=T/'Sources/SwiftDataFrame/IO/CSVColumnConversion.swift';t=p.read_text();needle='    func decode(buffer: UnsafeBufferPointer<UInt8>, offset: CSVFieldOffset) -> CSVDecodedValue<Value>\n'
assert needle in t;t=t.replace(needle,needle+'    func decodeValue(buffer: UnsafeBufferPointer<UInt8>, offset: CSVFieldOffset) -> Value?\n')
needle='internal final class CSVColumnAttempt<Decoder: CSVValueDecoder> {'
extra='''internal extension CSVValueDecoder {
    func decodeValue(buffer: UnsafeBufferPointer<UInt8>, offset: CSVFieldOffset) -> Value? {
        switch decode(buffer: buffer, offset: offset) {
        case .value(let value): value
        case .missing, .invalid: nil
        }
    }
}

''';assert needle in t;t=t.replace(needle,extra+needle)
needle='''    ) -> CSVFieldOffset? {
        for row in startRow..<(startRow + rowCount) {'''
extra='''    ) -> CSVFieldOffset? {
        if !validates {
            for row in startRow..<(startRow + rowCount) {
                let value = records.field(row: row, column: column).flatMap {
                    decoder.decodeValue(buffer: buffer, offset: $0)
                }
                values.append(value)
            }
            return nil
        }
        for row in startRow..<(startRow + rowCount) {''';assert needle in t;t=t.replace(needle,extra)
t=t.replace('''            case .invalid:
                if validates { return field }
                values.append(nil)''','''            case .invalid: return field''')
a=t.index('internal struct CSVDateDecoder: CSVValueDecoder {');t=t[:a]+t[a:].replace('''    @inline(__always)
    func decode(''','''    @inline(__always)
    func decodeValue(buffer: UnsafeBufferPointer<UInt8>, offset: CSVFieldOffset) -> Date? {
        if nulls.contains(buffer: buffer, offset: offset) { return nil }
        return parser.parse(buffer: buffer, offset: offset)
    }

    @inline(__always)
    func decode(''',1)
p.write_text(t)
v=json.loads((R/'variants.json').read_text());v['explicit']={'path':str(T),'pr':None};(R/'variants.json').write_text(json.dumps(v,indent=2)+'\n')
s=(R/'result-pilot.py').read_text().replace("engines=['before','result']","engines=['before','explicit']").replace("R/'result-pilot.json'","R/'explicit-pilot.json'");(R/'explicit-pilot.py').write_text(s)
s=(R/'null-pilot.py').read_text().replace("'optional'","'explicit'").replace('optional','explicit');(R/'explicit-null-pilot.py').write_text(s)
