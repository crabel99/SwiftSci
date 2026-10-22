from pathlib import Path
import json,shutil,subprocess
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');P=Path('/private/tmp/swiftsci-csv-batch-profile-20261022')
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=S,text=True).strip()=='277d1792d34e280a50744bd7419848d1c16b8655'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=S)
for name in ['build.py','ResourceProbe.swift','StreamProbe.swift','GrammarProbe.swift']:(R/name).write_bytes((P/name).read_bytes())
variants={}
for label in ['append','plan','batch']:
 T=R/(label+'-trial');assert not T.exists();shutil.copytree(S/'Sources/SwiftDataFrame',T/'Sources/SwiftDataFrame');variants[label]={'path':str(T),'pr':None}
p=R/'append-trial/Sources/SwiftDataFrame/IO/CSVColumnConversion.swift';s=p.read_text();old='''    func decode(buffer: UnsafeBufferPointer<UInt8>, offset: CSVFieldOffset) -> CSVDecodedValue<Value>''';new=old+'''
    func appendDecoded(buffer: UnsafeBufferPointer<UInt8>, offset: CSVFieldOffset,
        into values: inout CSVColumnBuilder<Value>) -> Bool''';assert old in s;s=s.replace(old,new)
old='''internal extension CSVValueDecoder {
''';new=old+'''    func appendDecoded(buffer: UnsafeBufferPointer<UInt8>, offset: CSVFieldOffset,
        into values: inout CSVColumnBuilder<Value>) -> Bool {
        switch decode(buffer: buffer, offset: offset) {
        case .value(let value): values.append(value)
        case .missing: values.append(nil)
        case .invalid: return false
        }
        return true
    }

''';assert old in s;s=s.replace(old,new)
old='''            switch decoder.decode(buffer: buffer, offset: field) {
            case .value(let value): values.append(value)
            case .missing: values.append(nil)
            case .invalid: return field
            }''';new='''            if !decoder.appendDecoded(buffer: buffer, offset: field, into: &values) { return field }''';assert old in s;s=s.replace(old,new)
for name,typ,parser,cast in [('CSVIntegerDecoder','Int64','parseInt','Int64(value)'),('CSVDoubleDecoder','Double','parseDouble','value')]:
 a=s.index('internal struct '+name+':');b=s.index('    @inline(__always)',a)
 method=f'''    @inline(__always)
    func appendDecoded(buffer: UnsafeBufferPointer<UInt8>, offset: CSVFieldOffset,
        into values: inout CSVColumnBuilder<{typ}>) -> Bool {{
        if !nulls.canSkipNumericMatch && nulls.contains(buffer: buffer, offset: offset) {{
            values.append(nil)
            return true
        }}
        if let value = VectorizedByteParsers.{parser}(buffer: buffer, offset: offset) {{
            values.append({cast})
            return true
        }}
        if nulls.canSkipNumericMatch && nulls.contains(buffer: buffer, offset: offset) {{
            values.append(nil)
            return true
        }}
        guard let value = {typ}.parse(from: VectorizedByteParsers.parseString(buffer: buffer, offset: offset)) else {{ return false }}
        values.append(value)
        return true
    }}

''';s=s[:b]+method+s[b:]
p.write_text(s)
p=R/'plan-trial/Sources/SwiftDataFrame/IO/CSVEagerReader.swift';s=p.read_text();old='''        let plans = headers.enumerated().map { column, name in
            CSVColumnPlan(buffer: source, records: batch.records, startRow: 0,
                rowCount: rows, column: column, name: name, options: options)
        }''';new='''        let plans = batch.records.withFlatFields { view in
            makePlans(source: source, records: view, rows: rows, headers: headers, options: options)
        } ?? batch.records.withCompactFields { view in
            makePlans(source: source, records: view, rows: rows, headers: headers, options: options)
        } ?? makePlans(source: source, records: batch.records, rows: rows, headers: headers, options: options)''';assert old in s;s=s.replace(old,new)
anchor='''    private static func append(
''';helper='''    private static func makePlans<Records: CSVRecordAccess>(
        source: UnsafeBufferPointer<UInt8>, records: Records, rows: Int,
        headers: [String], options: CSVReadOptions
    ) -> [CSVColumnPlan] {
        headers.enumerated().map { column, name in
            CSVColumnPlan(buffer: source, records: records, startRow: 0,
                rowCount: rows, column: column, name: name, options: options)
        }
    }

''';assert anchor in s;p.write_text(s.replace(anchor,helper+anchor))
p=R/'batch-trial/Sources/SwiftDataFrame/IO/CSVEagerReader.swift';s=p.read_text();assert 'batchRows = 16_384' in s;p.write_text(s.replace('batchRows = 16_384','batchRows = 65_536'))
(R/'variants.json').write_text(json.dumps(variants,indent=2)+'\n')
