import Foundation

// DESIGN ONLY. Bodies are intentionally unimplemented. Existing module types are
// referenced rather than reproduced. This file is not a buildable replacement.
// Module ownership stays in Sources/SwiftDataFrame/IO/CSVColumnConversion.swift.

// MARK: Reader-facing factory

extension CSVColumnPlan {
    /// Replaces conversion(type:capacity:), without changing public read options.
    /// selectedRowCount is exact for this attempt, including every eager batch.
    /// The same value reserves the builder. Retry probes pass one.
    func conversion(type: ColumnDType, selectedRowCount: Int) -> CSVColumnConversion {
        // TODO: Construct CSVNullMatcher only in Integer, Double, and Date cases.
        // TODO: Boolean keeps its original Set<String>.
        // TODO: UTF-8 constructs CSVStringDecoder(nullValues:selectedRowCount:)
        // and returns .string(CSVColumnAttempt(decoder: ..., capacity:
        // selectedRowCount, validates: false)).
        fatalError("not implemented")
    }
}

/// Replaces the current enum. Removes stringWithSmallNullSet rather than adding
/// one conversion case for every String lookup algorithm.
internal enum CSVColumnConversion {
    case integer(CSVColumnAttempt<CSVIntegerDecoder>)
    case double(CSVColumnAttempt<CSVDoubleDecoder>)
    case boolean(CSVColumnAttempt<CSVBooleanDecoder>)
    case date(CSVColumnAttempt<CSVDateDecoder>)
    case string(CSVColumnAttempt<CSVStringDecoder>)

    func append<Records: CSVRecordAccess>(
        buffer: UnsafeBufferPointer<UInt8>, records: Records,
        startRow: Int, rowCount: Int, column: Int, sourceOffset: Int = 0
    ) {
        // TODO: Existing enum dispatch. String calls attempt.append, exactly as
        // the generic scalar types do. Double keeps attempt.appendDouble.
        fatalError("not implemented")
    }

    // Existing appendIndexed, rejectedField, rejected, and column methods keep
    // their behavior with the removed small-String case deleted from switches.
}

// MARK: Batch contract, replacing the current scalar-only protocol

internal protocol CSVValueDecoder {
    associatedtype Value: SupportedType

    /// Invoked once by the attempt for one column batch. Returns its first
    /// invalid field, or nil. The builder belongs to the caller throughout.
    func appendRows<Records: CSVRecordAccess>(
        _ buffer: UnsafeBufferPointer<UInt8>, _ records: Records,
        _ startRow: Int, _ rowCount: Int, _ column: Int,
        validates: Bool, into values: inout CSVColumnBuilder<Value>
    ) -> CSVFieldOffset?
}

/// Existing scalar decoding contract. Integer, Double, Boolean, and Date change
/// their conformance spelling to this protocol; their scalar methods stay put.
internal protocol CSVCellDecoder: CSVValueDecoder {
    func decode(buffer: UnsafeBufferPointer<UInt8>, offset: CSVFieldOffset) -> CSVDecodedValue<Value>
    func decodeValue(buffer: UnsafeBufferPointer<UInt8>, offset: CSVFieldOffset) -> Value?
}

internal extension CSVCellDecoder {
    func decodeValue(buffer: UnsafeBufferPointer<UInt8>, offset: CSVFieldOffset) -> Value? {
        // TODO: Existing classified-result-to-optional default.
        fatalError("not implemented")
    }

    func appendRows<Records: CSVRecordAccess>(
        _ buffer: UnsafeBufferPointer<UInt8>, _ records: Records,
        _ startRow: Int, _ rowCount: Int, _ column: Int,
        validates: Bool, into values: inout CSVColumnBuilder<Value>
    ) -> CSVFieldOffset? {
        // TODO: Call appendCellRows with Self as the static decoder type.
        fatalError("not implemented")
    }
}

/// Owns the existing generic appendRows loops, moved out of CSVColumnAttempt.
/// Selects validation once before its loop. No String-mode branch is inside it.
private func appendCellRows<Decoder: CSVCellDecoder, Records: CSVRecordAccess>(
    _ buffer: UnsafeBufferPointer<UInt8>, _ records: Records,
    _ startRow: Int, _ rowCount: Int, _ column: Int,
    decoder: Decoder, validates: Bool,
    into values: inout CSVColumnBuilder<Decoder.Value>
) -> CSVFieldOffset? {
    // TODO: Preserve current absent-field behavior and first-invalid return.
    // TODO: Nonvalidating loop calls Decoder.decodeValue. Validating loop calls
    // Decoder.decode. Specialization must be inspected in generated code.
    fatalError("not implemented")
}

// MARK: Stable String policy and concrete inner-loop algorithms

/// One immutable mode for the attempt's entire lifetime. It has no scalar
/// decode method, so generic scalar code cannot accidentally switch per row.
internal struct CSVStringDecoder: CSVValueDecoder {
    typealias Value = String

    private enum Mode {
        case hashed(CSVHashedStringDecoder)
        case tiny(CSVSmallStringDecoder)
        case prefix(CSVPrefixStringDecoder)
    }
    private let mode: Mode

    init(nullValues: Set<String>, selectedRowCount: Int) {
        // TODO: Empty -> original hashed decoder. One or two tokens -> original
        // tiny decoder. Larger sets -> attempt bounded ASCII preparation.
        // TODO: Success stores prefix; failure stores hashed, never partial masks.
        fatalError("not implemented")
    }

    func appendRows<Records: CSVRecordAccess>(
        _ buffer: UnsafeBufferPointer<UInt8>, _ records: Records,
        _ startRow: Int, _ rowCount: Int, _ column: Int,
        validates: Bool, into values: inout CSVColumnBuilder<String>
    ) -> CSVFieldOffset? {
        // TODO: Switch mode ONCE here. Each case invokes appendCellRows using
        // its concrete associated decoder and validates: false. UTF-8 attempts
        // never reject. Do not capture a decoder in a stored lookup closure.
        // .hashed -> appendCellRows<CSVHashedStringDecoder, Records>
        // .tiny   -> appendCellRows<CSVSmallStringDecoder, Records>
        // .prefix -> appendCellRows<CSVPrefixStringDecoder, Records>
        fatalError("not implemented")
    }
}

/// Renames the original CSVStringDecoder and preserves its scalar algorithm.
internal struct CSVHashedStringDecoder: CSVCellDecoder {
    typealias Value = String
    let nullValues: Set<String>

    func decode(buffer: UnsafeBufferPointer<UInt8>, offset: CSVFieldOffset) -> CSVDecodedValue<String> {
        // TODO: Original parseString, followed by nullValues.contains(text).
        // No empty-set optimization and no mode or prefix guard on this path.
        fatalError("not implemented")
    }
}

/// Existing stored first/second token representation and scalar equality logic.
internal struct CSVSmallStringDecoder: CSVCellDecoder, Sendable {
    typealias Value = String
    private let first: String
    private let second: String?

    init?(nullValues: Set<String>) {
        // TODO: Preserve the original one-or-two-token acceptance exactly.
        fatalError("not implemented")
    }

    func decode(buffer: UnsafeBufferPointer<UInt8>, offset: CSVFieldOffset) -> CSVDecodedValue<String> {
        // TODO: Original parseString and first == text || second == text.
        fatalError("not implemented")
    }
}

/// The initializer is the only producer of masks. Success certifies that every
/// token is ASCII, the token-plus-byte traversal fit its budget, and at least
/// one ASCII start can be excluded.
private struct CSVASCIINullPrefixes {
    private let lowStarts: UInt64
    private let highStarts: UInt64

    init?(nullValues: Set<String>, selectedRowCount: Int) {
        // TODO: Immediately fail if nullValues.count > selectedRowCount.
        // TODO: Start budget at selectedRowCount. Charge one per visited token
        // and per UTF-8 byte; check before subtracting, avoiding overflow.
        // TODO: Fail only when the next charge exceeds remaining budget, or a
        // byte is >= 128. An exact final zero budget is success. Build masks during
        // this same traversal. Empty tokens set no bits and still cost a visit.
        // TODO: If both masks are .max, fail because rejection is impossible.
        // Publish masks only after the entire set passes.
        fatalError("not implemented")
    }

    /// True only for an ASCII first byte absent from all prepared token starts.
    /// Empty and non-ASCII-leading Strings return false and use Set equality.
    func excludes(_ text: String) -> Bool {
        fatalError("not implemented")
    }
}

private struct CSVPrefixStringDecoder: CSVCellDecoder {
    typealias Value = String
    let nullValues: Set<String>
    let prefixes: CSVASCIINullPrefixes

    func decode(buffer: UnsafeBufferPointer<UInt8>, offset: CSVFieldOffset) -> CSVDecodedValue<String> {
        // TODO: Existing parseString first. Return .value only for a certified
        // negative prefix, otherwise use the original nullValues.contains(text).
        // No lookup-mode or preparation-eligibility test occurs here.
        fatalError("not implemented")
    }
}

// MARK: Attempt integration, existing class members omitted

extension CSVColumnAttempt {
    func append<Records: CSVRecordAccess>(
        _ buffer: UnsafeBufferPointer<UInt8>, _ records: Records,
        _ startRow: Int, _ rowCount: Int, _ column: Int, sourceOffset: Int
    ) {
        // TODO: Preserve rejected guard, swap of class builder into local
        // batchValues, and swap back. Replace Self.appendRows(...) with:
        // decoder.appendRows(buffer, records, startRow, rowCount, column,
        //     validates: validates, into: &batchValues)
        // TODO: Preserve reject(field, sourceOffset:) after the swap.
        // This is one generic witness call per batch if not specialized. It is
        // never a stored function call per cell. Delete the old static row loop.
        fatalError("not implemented")
    }
}
