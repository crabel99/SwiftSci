from pathlib import Path
import json,shutil,subprocess
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');C=Path('/private/tmp/swiftsci-csv-conversion-profile-20261021')
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=S,text=True).strip()=='a5856aa40f8de2bbcc3653976419202a41222190'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=S)
for name in ['build.py','ResourceProbe.swift','StreamProbe.swift','GrammarProbe.swift']:(R/name).write_bytes((C/name).read_bytes())
variants={}
for name in ['local','direct','serial']:
 T=R/(name+'-trial');assert not T.exists();shutil.copytree(S/'Sources/SwiftDataFrame',T/'Sources/SwiftDataFrame');variants[name]={'path':str(T),'pr':None}
p=R/'local-trial/Sources/SwiftDataFrame/IO/CSVColumnConversion.swift';t=p.read_text();old='''        if let field = Self.appendRows(buffer, records, startRow, rowCount, column,
            decoder: decoder, validates: validates, into: &values) {
            rejectedField = CSVFieldOffset(startOffset: sourceOffset + field.startOffset,
                length: field.length, escapedQuotesPresent: field.escapedQuotesPresent)
            values = CSVColumnBuilder(capacity: 0)
        }
''';new='''        var local = CSVColumnBuilder<Decoder.Value>(capacity: 0)
        swap(&values, &local)
        if let field = Self.appendRows(buffer, records, startRow, rowCount, column,
            decoder: decoder, validates: validates, into: &local) {
            rejectedField = CSVFieldOffset(startOffset: sourceOffset + field.startOffset,
                length: field.length, escapedQuotesPresent: field.escapedQuotesPresent)
        } else {
            values = local
        }
''';assert old in t;p.write_text(t.replace(old,new))
p=R/'direct-trial/Sources/SwiftDataFrame/IO/CSVColumnConversion.swift';t=p.read_text()
for decoder,typ,parse in [('CSVIntegerDecoder','Int64','parseInt'),('CSVDoubleDecoder','Double','parseDouble')]:
 a=t.index('internal struct '+decoder+':');b=t.index('    @inline(__always)',a)
 code=f'''    @inline(__always)
    func decodeValue(buffer: UnsafeBufferPointer<UInt8>, offset: CSVFieldOffset) -> {typ}? {{
        if !nulls.canSkipNumericMatch && nulls.contains(buffer: buffer, offset: offset) {{ return nil }}
        if let value = VectorizedByteParsers.{parse}(buffer: buffer, offset: offset) {{ return {typ}(value) }}
        if nulls.canSkipNumericMatch && nulls.contains(buffer: buffer, offset: offset) {{ return nil }}
        return {typ}.parse(from: VectorizedByteParsers.parseString(buffer: buffer, offset: offset))
    }}

''';t=t[:b]+code+t[b:]
p.write_text(t)
p=R/'serial-trial/Sources/SwiftDataFrame/IO/CSVReader.swift';t=p.read_text().replace('DispatchQueue.concurrentPerform(iterations: headers.count) { column in','for column in headers.indices {');p.write_text(t)
p=R/'serial-trial/Sources/SwiftDataFrame/IO/CSVEagerReader.swift';t=p.read_text().replace('DispatchQueue.concurrentPerform(iterations: columns.count) { index in','for index in columns.indices {');p.write_text(t)
(R/'variants.json').write_text(json.dumps(variants,indent=2)+'\n')
