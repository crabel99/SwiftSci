import Foundation

// Caller usage comes first. Existing readers keep their current calls.
//
// let eager = plan.conversion(type: .utf8, capacity: selectedRowCount)
// let chunk = plan.conversion(type: .utf8, capacity: records.count)
// let retryProbe = plan.conversion(type: candidate, capacity: 1)

internal struct CSVColumnPlan {
    let candidates: [ColumnDType]
    private let validates: Bool
    private let nullValues: Set<String>
    private let dateFormat: String?

    // Existing initializer and candidate advancement remain unchanged.

    /// Creates one concrete attempt for the exact row work represented by
    /// `capacity`. String strategy selection does not escape this boundary.
    func conversion(type: ColumnDType, capacity: Int) -> CSVColumnConversion {
        switch type {
        case .int32, .int64:
            // TODO: Construct CSVNullMatcher here, where it is consumed.
            fatalError("not implemented")
        case .float32, .float64:
            // TODO: Construct CSVNullMatcher here, where it is consumed.
            fatalError("not implemented")
        case .boolean:
            // TODO: Preserve the existing Boolean decoder without CSVNullMatcher.
            fatalError("not implemented")
        case .date32:
            // TODO: Construct CSVNullMatcher here, where it is consumed.
            fatalError("not implemented")
        case .utf8:
            return stringConversion(capacity: capacity)
        }
    }

    /// Selection preserves the original empty, one-token, two-token, and
    /// general hashed decoders. Count gates the single budgeted ASCII scan.
    private func stringConversion(capacity: Int) -> CSVColumnConversion {
        // TODO:
        // 1. Empty token set -> CSVStringDecoder.
        // 2. CSVSmallStringDecoder succeeds -> one/two-token enum case.
        // 3. nullValues.count > capacity -> CSVStringDecoder.
        // 4. Initialize CSVASCIIPrefixStringDecoder with byteBudget: capacity.
        //    It scans token bytes once and succeeds within that budget.
        // 5. Otherwise -> CSVStringDecoder.
        fatalError("not implemented")
    }
}

/// Dispatches decoder choice once per attempt. Append paths contain no
/// fallback strategy flag.
internal enum CSVColumnConversion {
    case integer(CSVColumnAttempt<CSVIntegerDecoder>)
    case double(CSVColumnAttempt<CSVDoubleDecoder>)
    case boolean(CSVColumnAttempt<CSVBooleanDecoder>)
    case date(CSVColumnAttempt<CSVDateDecoder>)
    case string(CSVColumnAttempt<CSVStringDecoder>)
    case stringWithSmallNullSet(CSVColumnAttempt<CSVSmallStringDecoder>)
    case stringWithASCIIPrefix(CSVColumnAttempt<CSVASCIIPrefixStringDecoder>)

    // Existing append, appendIndexed, rejectedField, and column methods add
    // direct switch arms for stringWithASCIIPrefix. Their signatures stay put.
}

/// A prepared String decoder whose token set is known to be fully ASCII.
/// Possible matches and non-ASCII values still use Set equality.
internal struct CSVASCIIPrefixStringDecoder: CSVValueDecoder, Sendable {
    private let nullValues: Set<String>
    private let leadingBytes: CSVASCIILeadingByteSet

    /// Returns nil if any token is non-ASCII or the single token scan would
    /// visit more bytes than `byteBudget`. The caller first checks token count.
    init?(nullValues: Set<String>, byteBudget: Int) {
        // TODO: Start remaining bytes at byteBudget. Iterate each token's UTF-8
        // view once. Before consuming a byte, fail if the budget is exhausted;
        // fail on a non-ASCII byte; otherwise decrement the budget and record
        // only the token's first byte. After the scan, fail if both masks are
        // .max because the screen cannot reject an ASCII prefix. Do not
        // allocate a byte array or call utf8.count in a separate pass.
        fatalError("not implemented")
    }

    @inline(__always)
    func decode(
        buffer: UnsafeBufferPointer<UInt8>,
        offset: CSVFieldOffset
    ) -> CSVDecodedValue<String> {
        // TODO: Parse with the existing String parser. Reject only an ASCII
        // leading byte absent from leadingBytes. Use Set equality otherwise.
        fatalError("not implemented")
    }
}

/// Private representation for membership of the 128 ASCII leading bytes.
/// Its exact storage is an implementation choice hidden from row callers.
private struct CSVASCIILeadingByteSet: Sendable {
    private let low: UInt64
    private let high: UInt64

    init(low: UInt64, high: UInt64) {
        // TODO: Store the completed masks from the decoder's budgeted scan.
        fatalError("not implemented")
    }

    @inline(__always)
    func contains(_ byte: UInt8) -> Bool {
        fatalError("not implemented")
    }
}
