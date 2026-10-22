from pathlib import Path
p=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021/Sources/SwiftDataFrame/IO/SystemsCSVParser.swift');t=p.read_text()
a=t.index('    internal func countRecords(');b=t.index('    private enum ScanResult',a)
t=t[:a]+'''    /// Counts complete records with the same grammar, without allocating field coordinates.
    internal func countRecords(buffer: UnsafeBufferPointer<UInt8>, maximumRows: Int? = nil) throws -> Int {
        guard maximumRows != 0 else { return 0 }
        try Task.checkCancellation()
        var sink = CSVCountSink()
        switch walkRecords(buffer: buffer, range: buffer.indices,
            maximumRows: maximumRows ?? Int.max, sink: &sink) {
        case .finished: return sink.rowCount
        case .cancelled: throw CancellationError()
        case .widerOffsets: preconditionFailure("Record counting stores no offsets")
        }
    }

'''+t[b:]
a=t.index('    private func scanRecords<Field: CSVIndexField>(');start=t.index('        let count = range.upperBound',a);end=t.index('\n}\n\n// Buffers are borrowed',start)
body=t[start:end]
# Remove the scanRecords function's final closing brace, preserving its grammar body.
assert body.endswith('\n    }\n');body=body[:-len('\n    }\n')]
body=body.replace('''return .batch(CSVRecordBatch(
                records: Field.recordIndex(blocks: fields, rowStarts: rowStarts), nextOffset: count))''', 'return .finished(count)')
body=body.replace('''                    let len = index - fieldStart
                    guard index <= Field.maximumEndOffset else { return .widerOffsets }
                    fields.append(Field(
                        startOffset: fieldStart,
                        length: max(0, len),
                        escapedQuotesPresent: escapedQuotesFound
                    ))''', '''                    guard sink.appendField(start: fieldStart, end: index,
                        escaped: escapedQuotesFound) else { return .widerOffsets }''')
body=body.replace('''                    let len = endPosition - fieldStart
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
                    }''', '''                    guard sink.appendField(start: fieldStart, end: endPosition,
                        escaped: escapedQuotesFound) else { return .widerOffsets }
                    sink.finishRow()
                    if let maximumRows, sink.rowCount == maximumRows {
                        return .finished(index + 1)
                    }''')
body=body.replace('''            guard count <= Field.maximumEndOffset else { return .widerOffsets }
            let len = count - fieldStart
            fields.append(Field(
                startOffset: fieldStart,
                length: max(0, len),
                escapedQuotesPresent: escapedQuotesFound
            ))
            rowStarts.append(fields.count)''', '''            guard sink.appendField(start: fieldStart, end: count,
                escaped: escapedQuotesFound) else { return .widerOffsets }
            sink.finishRow()''')
body=body.replace('fields.truncate(to: rowStarts.last!)','sink.discardIncompleteRow()')
body=body.replace('''        return .batch(CSVRecordBatch(
            records: Field.recordIndex(blocks: fields, rowStarts: rowStarts), nextOffset: count))''','''        return .finished(count)''')
assert all(x not in body for x in ['Field.','fields.','rowStarts'])
replacement='''    private func scanRecords<Field: CSVIndexField>(
        buffer: UnsafeBufferPointer<UInt8>, range: Range<Int>, fieldType: Field.Type,
        maximumRows: Int?
    ) -> ScanResult {
        var sink = CSVIndexSink<Field>(byteCount: range.count, maximumRows: maximumRows)
        switch walkRecords(buffer: buffer, range: range, maximumRows: maximumRows, sink: &sink) {
        case .finished(let nextOffset):
            return .batch(CSVRecordBatch(records: sink.records, nextOffset: nextOffset))
        case .widerOffsets: return .widerOffsets
        case .cancelled: return .cancelled
        }
    }

    private enum WalkResult {
        case finished(Int)
        case widerOffsets
        case cancelled
    }

    private func walkRecords<Sink: CSVScanSink>(
        buffer: UnsafeBufferPointer<UInt8>, range: Range<Int>, maximumRows: Int?, sink: inout Sink
    ) -> WalkResult {
'''+body+'''
    }
'''
t=t[:a]+replacement+t[end:]
i=t.index('// Buffers are borrowed')
t=t[:i]+'''// Concrete sinks share one grammar. Count specialization discards field events;
// index specialization retains offsets with the existing width and EOF rules.
private protocol CSVScanSink {
    var rowCount: Int { get }
    mutating func appendField(start: Int, end: Int, escaped: Bool) -> Bool
    mutating func finishRow()
    mutating func discardIncompleteRow()
}

private struct CSVCountSink: CSVScanSink {
    private(set) var rowCount = 0
    @inline(__always) mutating func appendField(start: Int, end: Int, escaped: Bool) -> Bool { true }
    @inline(__always) mutating func finishRow() { rowCount += 1 }
    @inline(__always) mutating func discardIncompleteRow() {}
}

private struct CSVIndexSink<Field: CSVIndexField>: CSVScanSink {
    private var fields: CSVFieldBlocks<Field>
    private var rowStarts: [Int] = [0]

    init(byteCount: Int, maximumRows: Int?) {
        fields = CSVFieldBlocks(byteCount: byteCount)
        rowStarts.reserveCapacity(min(byteCount / 16, maximumRows ?? 100_000, 100_000) + 1)
    }

    var rowCount: Int { rowStarts.count - 1 }
    var records: CSVRecordIndex { Field.recordIndex(blocks: fields, rowStarts: rowStarts) }

    @inline(__always)
    mutating func appendField(start: Int, end: Int, escaped: Bool) -> Bool {
        guard end <= Field.maximumEndOffset else { return false }
        fields.append(Field(startOffset: start, length: max(0, end - start), escapedQuotesPresent: escaped))
        return true
    }

    @inline(__always) mutating func finishRow() { rowStarts.append(fields.count) }
    @inline(__always) mutating func discardIncompleteRow() { fields.truncate(to: rowStarts.last!) }
}

'''+t[i:];p.write_text(t)
