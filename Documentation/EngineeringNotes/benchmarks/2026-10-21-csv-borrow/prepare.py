from pathlib import Path
import shutil,json
r=Path(__file__).resolve().parent;old=Path('/private/tmp/swiftsci-csv-diverse-20261021')
for v,src in [('baseline','baseline'),('packed','packed'),('borrowed','packed')]:shutil.copytree(old/src,r/v)
for name in ['build.py','ResourceProbe.swift','run-pair.py','summarize-pair.py','Semantics.swift','ParserParity.swift','Inspect.swift','StreamChecks.swift','CompactChecks.swift','RangeChecks.swift','make-diverse.py']:
 shutil.copy2(old/name,r/name)
for name in ['fixtures','heldout-fixtures','diverse-fixtures']:(r/name).symlink_to((old/name).resolve(),target_is_directory=True)
shutil.copy2(old/'diverse-cases.json',r/'diverse-cases.json')
for name in ['check.py','smoke.py','stream-check.py']:
 s=(old/name).read_text().replace("['baseline','packed','direct']","['baseline','packed','borrowed']")
 (r/name).write_text(s)
for name in ['boundary.py','range-check.py','run-tests.py']:
 s=(old/name).read_text().replace("R/'direct/","R/'borrowed/").replace("['direct']","['borrowed']")
 (r/name).write_text(s)
(r/'variants.json').write_text(json.dumps({v:dict(path=str(r/v),base_sha='546510bb7df19fc87a664bded5947c738011ee1d',pr=None) for v in ['baseline','packed','borrowed']},indent=2)+'\n')
p=r/'borrowed/Sources/SwiftDataFrame/IO/CSVRecordIndex.swift';s=p.read_text().replace('internal struct CSVRecordIndex: Sendable {','internal struct CSVRecordIndex: Sendable, CSVRecordAccess {')
anchor='    func row(at index: Int) -> [CSVFieldOffset] {'
method='''    func withFlatFields<Result>(_ body: (CSVFlatRecordView) -> Result) -> Result? {
        guard case .flat(let values) = fields else { return nil }
        return values.withUnsafeBufferPointer { fields in
            rowStarts.withUnsafeBufferPointer { starts in
                body(CSVFlatRecordView(fields: fields, rowStarts: starts))
            }
        }
    }

'''
assert s.count(anchor)==1;s=s.replace(anchor,method+anchor)
s+='''
internal protocol CSVRecordAccess {
    func field(row: Int, column: Int) -> CSVFieldOffset?
}

internal struct CSVFlatRecordView: CSVRecordAccess {
    let fields: UnsafeBufferPointer<PackedCSVField>
    let rowStarts: UnsafeBufferPointer<Int>

    func field(row: Int, column: Int) -> CSVFieldOffset? {
        guard row < rowStarts.count - 1 else { return nil }
        let start = rowStarts[row]
        guard column < rowStarts[row + 1] - start else { return nil }
        return fields[start + column].offset
    }
}
''';p.write_text(s)
p=r/'borrowed/Sources/SwiftDataFrame/IO/CSVReader.swift';s=p.read_text();start=s.index('    internal static func buildColumn(');end=s.index('        let nullMatcher',start);header=s[start:end]
wrapper=header+'''        if let column = records.withFlatFields({ view in
            buildIndexedColumn(buffer: buffer, records: view,
                startRowIdx: startRowIdx, dataRowsToRead: dataRowsToRead,
                colIndex: colIndex, name: name, options: options)
        }) { return column }
        return buildIndexedColumn(buffer: buffer, records: records,
            startRowIdx: startRowIdx, dataRowsToRead: dataRowsToRead,
            colIndex: colIndex, name: name, options: options)
    }

'''
new=header.replace('internal static func buildColumn(','private static func buildIndexedColumn<Records: CSVRecordAccess>(').replace('records: CSVRecordIndex','records: Records')
p.write_text(s[:start]+wrapper+new+s[end:])
