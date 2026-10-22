from pathlib import Path
s=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021')
p=s/'Sources/SwiftDataFrame/IO/CSVColumnConversion.swift';t=p.read_text();i=t.index('    func conversion(type:')
t=t[:i]+'''    /// A rejected original token can disprove later candidates, but cannot admit new ones.
    func nextCandidate(after index: Int, buffer: UnsafeBufferPointer<UInt8>, rejectedField: CSVFieldOffset) -> Int {
        let record = CSVRecordIndex(fields: [PackedCSVField(startOffset: rejectedField.startOffset,
            length: rejectedField.length, escapedQuotesPresent: rejectedField.escapedQuotesPresent)], rowStarts: [0, 1])
        var next = index + 1
        while candidates[next] != .utf8 {
            let probe = conversion(type: candidates[next], capacity: 1)
            probe.appendIndexed(buffer: buffer, records: record, startRow: 0, rowCount: 1, column: 0)
            if !probe.rejected { return next }
            next += 1
        }
        return next
    }

'''+t[i:]
t=t.replace('rowCount: Int, column: Int\n    ) {\n        switch self', 'rowCount: Int, column: Int, sourceOffset: Int = 0\n    ) {\n        switch self',1)
for name in ['integer','double','boolean','date','string']:
 t=t.replace(f'case .{name}(let attempt): attempt.append(buffer, records, startRow, rowCount, column)',f'case .{name}(let attempt): attempt.append(buffer, records, startRow, rowCount, column, sourceOffset: sourceOffset)')
t=t.replace('startRow: Int, rowCount: Int, column: Int\n    ) {','startRow: Int, rowCount: Int, column: Int, sourceOffset: Int = 0\n    ) {',1)
t=t.replace('rowCount: rowCount, column: column)\n', 'rowCount: rowCount, column: column, sourceOffset: sourceOffset)\n')
i=t.index('    var rejected: Bool {')
t=t[:i]+'''    var rejectedField: CSVFieldOffset? {
        switch self {
        case .integer(let attempt): attempt.rejectedField
        case .double(let attempt): attempt.rejectedField
        case .boolean(let attempt): attempt.rejectedField
        case .date(let attempt): attempt.rejectedField
        case .string(let attempt): attempt.rejectedField
        }
    }

'''+t[i:]
t=t.replace('    private(set) var rejected = false','    private(set) var rejectedField: CSVFieldOffset?\n    var rejected: Bool { rejectedField != nil }')
t=t.replace('_ startRow: Int, _ rowCount: Int, _ column: Int\n    ) {','_ startRow: Int, _ rowCount: Int, _ column: Int, sourceOffset: Int\n    ) {',1)
t=t.replace('''        if !Self.appendRows(buffer, records, startRow, rowCount, column,
            decoder: decoder, validates: validates, into: &values) {
            rejected = true
            values = CSVColumnBuilder(capacity: 0)
        }''','''        if let field = Self.appendRows(buffer, records, startRow, rowCount, column,
            decoder: decoder, validates: validates, into: &values) {
            rejectedField = CSVFieldOffset(startOffset: sourceOffset + field.startOffset,
                length: field.length, escapedQuotesPresent: field.escapedQuotesPresent)
            values = CSVColumnBuilder(capacity: 0)
        }''')
t=t.replace(') -> Bool {\n        for row in startRow',') -> CSVFieldOffset? {\n        for row in startRow').replace('if validates { return false }','if validates { return field }').replace('        return true\n    }\n\n    func column(named','        return nil\n    }\n\n    func column(named')
p.write_text(t)
p=s/'Sources/SwiftDataFrame/IO/CSVEagerReader.swift';t=p.read_text().replace('append(buffer: bytes, records: batch.records, attempts: attempts, columns: active)', 'append(buffer: bytes, records: batch.records, attempts: attempts, columns: active, sourceOffset: offset)')
t=t.replace('''                if attempt.rejected {
                    candidate[column] += 1''','''                if let field = attempt.rejectedField {
                    candidate[column] = plans[column].nextCandidate(after: candidate[column],
                        buffer: source, rejectedField: field)''')
t=t.replace('columns: [Int], rowCount: Int? = nil', 'columns: [Int], rowCount: Int? = nil, sourceOffset: Int = 0').replace('startRow: 0, rowCount: count, column: column)', 'startRow: 0, rowCount: count, column: column, sourceOffset: sourceOffset)')
p.write_text(t)
p=s/'Sources/SwiftDataFrame/IO/CSVReader.swift';t=p.read_text();a=t.index('        for type in plan.candidates {');b=t.index('\n    }',a)
t=t[:a]+'''        var candidate = 0
        while true {
            let conversion = plan.conversion(type: plan.candidates[candidate], capacity: dataRowsToRead)
            conversion.append(buffer: buffer, records: records, startRow: startRowIdx,
                rowCount: dataRowsToRead, column: colIndex)
            guard let field = conversion.rejectedField else { return conversion.column(named: name) }
            candidate = plan.nextCandidate(after: candidate, buffer: buffer, rejectedField: field)
        }'''+t[b:];p.write_text(t)
