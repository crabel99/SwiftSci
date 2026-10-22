from pathlib import Path
import json,shutil,subprocess
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');P=Path('/private/tmp/swiftsci-csv-cell-profile-20261021')
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=S,text=True).strip()=='5375f261c28c5cb1ee94f6c0892ba6d830e4312a'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=S)
for name in ['build.py','ResourceProbe.swift','StreamProbe.swift','GrammarProbe.swift']:(R/name).write_bytes((P/name).read_bytes())
variants={}
for label in ['count','batch','view']:
 T=R/(label+'-trial');assert not T.exists();shutil.copytree(S/'Sources/SwiftDataFrame',T/'Sources/SwiftDataFrame');variants[label]={'path':str(T),'pr':None}
p=R/'count-trial/Sources/SwiftDataFrame/IO/SystemsCSVParser.swift';s=p.read_text();old='''        var scanner = CSVStructuralScanner(bytes: buffer.baseAddress!, range: range,
            delimiter: delimiterByte, quote: quoteByte)
        var searchLimit = maximumRows == nil ? count : range.lowerBound + min(65_536, range.count)
''';new='''        var scanner = CSVStructuralScanner(bytes: buffer.baseAddress!, range: range,
            delimiter: Output.keepsCoordinates ? delimiterByte : lfByte, quote: quoteByte)
        var searchLimit = maximumRows == nil ? count : range.lowerBound + min(65_536, range.count)
''';assert old in s;s=s.replace(old,new)
old='''        // Handle trailing line without newline
        if fieldStart < count {''';new='''        // Count-only scanning skips delimiter events. Preserve the unfinished
        // trailing-empty-field behavior without visiting earlier delimiters.
        if !Output.keepsCoordinates && !insideQuotes && delimiterByte != quoteByte
            && buffer[count - 1] == delimiterByte { fieldStart = count }
        // Handle trailing line without newline
        if fieldStart < count {''';assert old in s;s=s.replace(old,new);p.write_text(s)
p=R/'batch-trial/Sources/SwiftDataFrame/IO/CSVEagerReader.swift';s=p.read_text();assert 'batchRows = 16_384' in s;p.write_text(s.replace('batchRows = 16_384','batchRows = 65_536'))
p=R/'view-trial/Sources/SwiftDataFrame/IO/CSVEagerReader.swift';s=p.read_text();old='''        let input = BatchInput(buffer: buffer, attempts: attempts)
''';new='''        if records.withFlatFields({ view in
            appendView(buffer: buffer, records: view, attempts: attempts, columns: columns,
                rowCount: rowCount ?? records.count, sourceOffset: sourceOffset)
            return true
        }) == true { return }
        if records.withCompactFields({ view in
            appendView(buffer: buffer, records: view, attempts: attempts, columns: columns,
                rowCount: rowCount ?? records.count, sourceOffset: sourceOffset)
            return true
        }) == true { return }
        appendView(buffer: buffer, records: records, attempts: attempts, columns: columns,
            rowCount: rowCount ?? records.count, sourceOffset: sourceOffset)
    }

    private static func appendView<Records: CSVRecordAccess>(
        buffer: UnsafeBufferPointer<UInt8>, records: Records,
        attempts: [CSVColumnConversion?], columns: [Int], rowCount: Int, sourceOffset: Int
    ) {
        let input = BatchInput(buffer: buffer, attempts: attempts, records: records)
''';assert old in s;s=s.replace(old,new).replace('let count = rowCount ?? records.count','let count = rowCount').replace('input.attempts[column]?.appendIndexed(buffer: input.buffer, records: records,','input.attempts[column]?.append(buffer: input.buffer, records: input.records,').replace('private struct BatchInput: @unchecked Sendable {','private struct BatchInput<Records: CSVRecordAccess>: @unchecked Sendable {').replace('        let attempts: [CSVColumnConversion?]\n    }\n}', '        let attempts: [CSVColumnConversion?]\n        let records: Records\n    }\n}')
p.write_text(s)
(R/'variants.json').write_text(json.dumps(variants,indent=2)+'\n')
