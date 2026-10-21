from pathlib import Path
import shutil,json
r=Path(__file__).resolve().parent;shutil.copytree(r/'inlined',r/'scoped')
p=r/'scoped/Sources/SwiftDataFrame/IO/CSVRecordIndex.swift';s=p.read_text();anchor='    func row(at index: Int) -> [CSVFieldOffset] {'
s=s.replace(anchor,'''    func withCompactFields<Result>(_ body: (CSVCompactRecordView) -> Result) -> Result? {
        guard case .compact(let values) = fields else { return nil }
        return values.withUnsafeBufferPointer { blocks in
            rowStarts.withUnsafeBufferPointer { starts in
                body(CSVCompactRecordView(blocks: blocks, rowStarts: starts))
            }
        }
    }

'''+anchor)
s+='''
internal struct CSVCompactRecordView: CSVRecordAccess {
    let blocks: UnsafeBufferPointer<[CompactCSVField]>
    let rowStarts: UnsafeBufferPointer<Int>

    @inline(__always)
    func field(row: Int, column: Int) -> CSVFieldOffset? {
        guard row < rowStarts.count - 1 else { return nil }
        let start = rowStarts[row]
        guard column < rowStarts[row + 1] - start else { return nil }
        let index = start + column
        return blocks[index >> 14][index & 16383].offset
    }
}
''';p.write_text(s)
p=r/'scoped/Sources/SwiftDataFrame/IO/CSVReader.swift';s=p.read_text();anchor='''        return buildIndexedColumn(buffer: buffer, records: records,
''';assert s.count(anchor)==1
s=s.replace(anchor,'''        if let column = records.withCompactFields({ view in
            buildIndexedColumn(buffer: buffer, records: view,
                startRowIdx: startRowIdx, dataRowsToRead: dataRowsToRead,
                colIndex: colIndex, name: name, options: options)
        }) { return column }
'''+anchor);p.write_text(s)
p=r/'variants.json';v=json.loads(p.read_text());v['scoped']={**v['inlined'],'path':str(r/'scoped')};p.write_text(json.dumps(v,indent=2)+'\n')
