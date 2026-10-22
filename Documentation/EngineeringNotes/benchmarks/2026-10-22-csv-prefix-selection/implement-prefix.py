from pathlib import Path
S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021')
p=S/'Sources/SwiftDataFrame/IO/CSVColumnConversion.swift';s=p.read_text();s=s.replace('conversion(type: candidates[next], capacity: 1)','conversion(type: candidates[next], selectedRowCount: 1)')
a=s.index('    func conversion(type:');b=s.index('\n}\n',a)
part=s[a:b].replace('capacity: Int','selectedRowCount: Int').replace('capacity: capacity','capacity: selectedRowCount')
part=part.replace('            return .string(CSVColumnAttempt', '''            if let decoder = CSVASCIIPrefixStringDecoder(nullValues: nullValues, selectedRowCount: selectedRowCount) {
                return .stringWithASCIIPrefix(CSVColumnAttempt(
                    decoder: decoder, capacity: selectedRowCount, validates: false))
            }
            return .string(CSVColumnAttempt''')
s=s[:a]+part+s[b:]
s=s.replace('    case stringWithSmallNullSet(CSVColumnAttempt<CSVSmallStringDecoder>)','    case stringWithSmallNullSet(CSVColumnAttempt<CSVSmallStringDecoder>)\n    case stringWithASCIIPrefix(CSVColumnAttempt<CSVASCIIPrefixStringDecoder>)')
s=s.replace('        case .stringWithSmallNullSet(let attempt): attempt.append(buffer, records, startRow, rowCount, column, sourceOffset: sourceOffset)','        case .stringWithSmallNullSet(let attempt): attempt.append(buffer, records, startRow, rowCount, column, sourceOffset: sourceOffset)\n        case .stringWithASCIIPrefix(let attempt): attempt.append(buffer, records, startRow, rowCount, column, sourceOffset: sourceOffset)')
s=s.replace('        case .stringWithSmallNullSet(let attempt): attempt.rejectedField','        case .stringWithSmallNullSet(let attempt): attempt.rejectedField\n        case .stringWithASCIIPrefix(let attempt): attempt.rejectedField')
s=s.replace('        case .stringWithSmallNullSet(let attempt): attempt.column(named: name)','        case .stringWithSmallNullSet(let attempt): attempt.column(named: name)\n        case .stringWithASCIIPrefix(let attempt): attempt.column(named: name)')
p.write_text(s)
p=S/'Sources/SwiftDataFrame/IO/CSVEagerReader.swift';s=p.read_text().replace('capacity: initial.capacity','selectedRowCount: initial.totalRows').replace('let capacity: Int','let totalRows: Int').replace('let capacity = rows +','let totalRows = rows +').replace('capacity: capacity','selectedRowCount: totalRows').replace('Initial(plans: plans, selectedRowCount: totalRows','Initial(plans: plans, totalRows: totalRows');p.write_text(s)
p=S/'Sources/SwiftDataFrame/IO/CSVReader.swift';s=p.read_text().replace('capacity: dataRowsToRead','selectedRowCount: dataRowsToRead');p.write_text(s)
p=S/'Sources/SwiftDataFrame/IO/CSVASCIIPrefixStringDecoder.swift';p.write_text('''import Foundation

/// Rejects impossible ASCII starts before retaining the original String equality check.
internal struct CSVASCIIPrefixStringDecoder: CSVValueDecoder, Sendable {
    private let nullValues: Set<String>
    private let lowStarts: UInt64
    private let highStarts: UInt64

    init?(nullValues: Set<String>, selectedRowCount: Int) {
        guard nullValues.count > 2, nullValues.count <= selectedRowCount else { return nil }
        // Bound token visits plus inspected bytes by the work selected for this attempt.
        var remaining = selectedRowCount - nullValues.count
        var low: UInt64 = 0
        var high: UInt64 = 0
        for token in nullValues {
            var first = true
            for byte in token.utf8 {
                guard remaining > 0, byte < 128 else { return nil }
                remaining -= 1
                if first {
                    if byte < 64 { low |= UInt64(1) << byte }
                    else { high |= UInt64(1) << (byte - 64) }
                    first = false
                }
            }
        }
        guard low != UInt64.max || high != UInt64.max else { return nil }
        self.nullValues = nullValues
        lowStarts = low
        highStarts = high
    }

    @inline(__always)
    func decode(buffer: UnsafeBufferPointer<UInt8>, offset: CSVFieldOffset) -> CSVDecodedValue<String> {
        let text = VectorizedByteParsers.parseString(buffer: buffer, offset: offset)
        if let first = text.utf8.first, first < 128 {
            let mask = first < 64 ? lowStarts : highStarts
            if mask & (UInt64(1) << (first & 63)) == 0 { return .value(text) }
        }
        // Empty and non-ASCII-leading strings retain canonical String equality.
        return nullValues.contains(text) ? .missing : .value(text)
    }
}
''')
