from pathlib import Path
import shutil,json
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');variants=json.loads((R/'variants.json').read_text());base=(S/'Sources/SwiftDataFrame/IO/CSVColumnConversion.swift').read_text()
for label in ['lean','closure']:
 T=R/(label+'-trial');assert not T.exists();shutil.copytree(S/'Sources/SwiftDataFrame',T/'Sources/SwiftDataFrame');s=base
 s=s.replace('case .double(let attempt): attempt.append(buffer, records, startRow, rowCount, column, sourceOffset: sourceOffset)','case .double(let attempt): attempt.appendDouble(buffer, records, startRow, rowCount, column, sourceOffset: sourceOffset)')
 a=s.index('    func append<Records: CSVRecordAccess>(',s.index('internal final class CSVColumnAttempt'));b=s.index('    // Borrow the builder',a);wrapper=s[a:b]
 a=s.index('    private static func appendRows<Records:');b=s.index('    func column(named name:',a);helper=s[a:b]
 if label=='lean':
  w=wrapper.replace('func append<Records:', 'func appendDouble<Records:').replace('    ) {\n','    ) where Decoder == CSVDoubleDecoder {\n',1).replace('        guard !rejected else { return }','''        guard validates else {
            append(buffer, records, startRow, rowCount, column, sourceOffset: sourceOffset)
            return
        }
        guard !rejected else { return }''').replace('Self.appendRows(buffer, records, startRow, rowCount, column,\n            decoder: decoder, validates: validates, into: &values)','appendValidatedDoubles(buffer, records, startRow, rowCount, column,\n            decoder: decoder, into: &values)')
  i=s.index('    // Borrow the builder');s=s[:i]+w+s[i:]
  h=helper.replace('    private static func appendRows<Records:','private func appendValidatedDoubles<Records:').replace('decoder: Decoder, validates: Bool, into values: inout CSVColumnBuilder<Decoder.Value>','decoder: CSVDoubleDecoder, into values: inout CSVColumnBuilder<Double>')
  i=h.index('        // Choose the validation contract');j=h.index('        for row in startRow..<(startRow + rowCount) {',h.index('            return nil\n        }',i));h=h[:i]+h[j:];s+='\n'+h
 else:
  oldcall='''Self.appendRows(buffer, records, startRow, rowCount, column,
            decoder: decoder, validates: validates, into: &values)'''
  newcall='''appendCSVRows(buffer, records, startRow, rowCount, column,
            validates: validates, into: &values,
            decodeValue: { decoder.decodeValue(buffer: buffer, offset: $0) },
            decode: { decoder.decode(buffer: buffer, offset: $0) })'''
  w=wrapper.replace('func append<Records:', 'func appendDouble<Records:').replace('    ) {\n','    ) where Decoder == CSVDoubleDecoder {\n',1).replace(oldcall,newcall)
  s=s.replace(oldcall,newcall);i=s.index('    // Borrow the builder');j=s.index('    func column(named name:',i);s=s[:i]+w+s[j:]
  h=helper.replace('    private static func appendRows<Records: CSVRecordAccess>(', '@inline(__always)\nprivate func appendCSVRows<Records: CSVRecordAccess, Value: SupportedType>(').replace('        decoder: Decoder, validates: Bool, into values: inout CSVColumnBuilder<Decoder.Value>','''        validates: Bool, into values: inout CSVColumnBuilder<Value>,
        decodeValue: (CSVFieldOffset) -> Value?, decode: (CSVFieldOffset) -> CSVDecodedValue<Value>''').replace('decoder.decodeValue(buffer: buffer, offset: $0)','decodeValue($0)').replace('decoder.decode(buffer: buffer, offset: field)','decode(field)');s+='\n'+h
 (T/'Sources/SwiftDataFrame/IO/CSVColumnConversion.swift').write_text(s);variants[label]={'path':str(T),'pr':None}
(R/'variants.json').write_text(json.dumps(variants,indent=2)+'\n')
