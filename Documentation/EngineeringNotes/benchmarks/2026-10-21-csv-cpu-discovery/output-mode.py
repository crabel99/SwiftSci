from pathlib import Path
import subprocess
s=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');p=s/'Sources/SwiftDataFrame/IO/SystemsCSVParser.swift'
t=subprocess.check_output(['git','show','8d901c15ad:Sources/SwiftDataFrame/IO/SystemsCSVParser.swift'],cwd=s,text=True)
a=t.index('    internal func countRecords(');b=t.index('    private enum ScanResult',a)
t=t[:a]+'''    /// Counts complete records with the same grammar, without allocating field coordinates.
    internal func countRecords(buffer: UnsafeBufferPointer<UInt8>, maximumRows: Int? = nil) throws -> Int {
        guard maximumRows != 0 else { return 0 }
        try Task.checkCancellation()
        switch scanRecords(buffer: buffer, range: buffer.indices, fieldType: PackedCSVField.self,
            maximumRows: maximumRows ?? Int.max, output: CSVCountOutput.self) {
        case .complete(let count): return count
        case .cancelled: throw CancellationError()
        case .widerOffsets: preconditionFailure("Record counting stores no offsets")
        }
    }

'''+t[b:]
t=t.replace('private enum ScanResult {\n        case batch(CSVRecordBatch)', 'private enum ScanResult<Value> {\n        case complete(Value)')
# Call sites select their output at compile time.
t=t.replace('guard case .batch(let batch)', 'guard case .complete(let batch)')
t=t.replace('fieldType: fieldType, maximumRows: nil)', 'fieldType: fieldType, maximumRows: nil, output: CSVIndexOutput.self)')
t=t.replace('fieldType: CompactCSVField.self, maximumRows: maximumRows)', 'fieldType: CompactCSVField.self, maximumRows: maximumRows, output: CSVIndexOutput.self)')
t=t.replace('fieldType: PackedCSVField.self, maximumRows: maximumRows)', 'fieldType: PackedCSVField.self, maximumRows: maximumRows, output: CSVIndexOutput.self)')
t=t.replace('case .batch(let batch): return batch', 'case .complete(let batch): return batch')
t=t.replace('private func scanRecords<Field: CSVIndexField>(', 'private func scanRecords<Field: CSVIndexField, Output: CSVScanOutput>(')
t=t.replace('maximumRows: Int?\n    ) -> ScanResult {\n        var fields', 'maximumRows: Int?, output: Output.Type\n    ) -> ScanResult<Output.Value> {\n        var fields')
t=t.replace('var fields = CSVFieldBlocks<Field>(byteCount: range.count)\n        var rowStarts = [0]\n        rowStarts.reserveCapacity(min(range.count / 16, maximumRows ?? 100_000, 100_000) + 1)', '''var fields = CSVFieldBlocks<Field>(byteCount: Output.keepsCoordinates ? range.count : 0)
        var rowStarts = [Int]()
        if Output.keepsCoordinates {
            rowStarts = [0]
            rowStarts.reserveCapacity(min(range.count / 16, maximumRows ?? 100_000, 100_000) + 1)
        }
        var rowCount = 0''')
t=t.replace('return .batch(CSVRecordBatch(\n                records: Field.recordIndex(blocks: fields, rowStarts: rowStarts), nextOffset: count))', 'return .complete(Output.finish(fields: fields, rowStarts: rowStarts, rowCount: rowCount, nextOffset: count))')
t=t.replace('''                    let len = index - fieldStart
                    guard index <= Field.maximumEndOffset else { return .widerOffsets }
                    fields.append(Field(
                        startOffset: fieldStart,
                        length: max(0, len),
                        escapedQuotesPresent: escapedQuotesFound
                    ))''', '''                    if Output.keepsCoordinates {
                        let len = index - fieldStart
                        guard index <= Field.maximumEndOffset else { return .widerOffsets }
                        fields.append(Field(startOffset: fieldStart, length: max(0, len),
                            escapedQuotesPresent: escapedQuotesFound))
                    }''')
t=t.replace('''                    let len = endPosition - fieldStart
                    guard endPosition <= Field.maximumEndOffset else { return .widerOffsets }
                    fields.append(Field(
                        startOffset: fieldStart,
                        length: max(0, len),
                        escapedQuotesPresent: escapedQuotesFound
                    ))

                    rowStarts.append(fields.count)
                    if let maximumRows, rowStarts.count - 1 == maximumRows {
                        return .batch(CSVRecordBatch(
                            records: Field.recordIndex(blocks: fields, rowStarts: rowStarts),
                            nextOffset: index + 1))
                    }''', '''                    if Output.keepsCoordinates {
                        let len = endPosition - fieldStart
                        guard endPosition <= Field.maximumEndOffset else { return .widerOffsets }
                        fields.append(Field(startOffset: fieldStart, length: max(0, len),
                            escapedQuotesPresent: escapedQuotesFound))
                        rowStarts.append(fields.count)
                    }
                    rowCount += 1
                    if let maximumRows, rowCount == maximumRows {
                        return .complete(Output.finish(fields: fields, rowStarts: rowStarts,
                            rowCount: rowCount, nextOffset: index + 1))
                    }''')
t=t.replace('''            guard count <= Field.maximumEndOffset else { return .widerOffsets }
            let len = count - fieldStart
            fields.append(Field(
                startOffset: fieldStart,
                length: max(0, len),
                escapedQuotesPresent: escapedQuotesFound
            ))
            rowStarts.append(fields.count)''', '''            if Output.keepsCoordinates {
                guard count <= Field.maximumEndOffset else { return .widerOffsets }
                let len = count - fieldStart
                fields.append(Field(startOffset: fieldStart, length: max(0, len),
                    escapedQuotesPresent: escapedQuotesFound))
                rowStarts.append(fields.count)
            }
            rowCount += 1''')
t=t.replace('fields.truncate(to: rowStarts.last!)', 'if Output.keepsCoordinates { fields.truncate(to: rowStarts.last!) }')
t=t.replace('return .batch(CSVRecordBatch(\n            records: Field.recordIndex(blocks: fields, rowStarts: rowStarts), nextOffset: count))', 'return .complete(Output.finish(fields: fields, rowStarts: rowStarts, rowCount: rowCount, nextOffset: count))')
i=t.index('// Buffers are borrowed')
t=t[:i]+'''// Output mode is fixed for each specialization. The cell loop keeps its local
// arrays for indexing; count-only specialization removes those arrays entirely.
private protocol CSVScanOutput {
    associatedtype Value
    static var keepsCoordinates: Bool { get }
    static func finish<Field: CSVIndexField>(
        fields: CSVFieldBlocks<Field>, rowStarts: [Int], rowCount: Int, nextOffset: Int
    ) -> Value
}

private enum CSVIndexOutput: CSVScanOutput {
    static var keepsCoordinates: Bool { true }
    @inline(__always)
    static func finish<Field: CSVIndexField>(
        fields: CSVFieldBlocks<Field>, rowStarts: [Int], rowCount: Int, nextOffset: Int
    ) -> CSVRecordBatch {
        CSVRecordBatch(records: Field.recordIndex(blocks: fields, rowStarts: rowStarts), nextOffset: nextOffset)
    }
}

private enum CSVCountOutput: CSVScanOutput {
    static var keepsCoordinates: Bool { false }
    @inline(__always)
    static func finish<Field: CSVIndexField>(
        fields: CSVFieldBlocks<Field>, rowStarts: [Int], rowCount: Int, nextOffset: Int
    ) -> Int { rowCount }
}

'''+t[i:]
assert '.batch(' not in t
p.write_text(t)
r=Path('/private/tmp/swiftsci-csv-cpu-profile-20261021');import shutil
shutil.copytree(r/'build/count-only',r/'build/sink-final-snapshot',dirs_exist_ok=True)
