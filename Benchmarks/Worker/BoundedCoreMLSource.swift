import Foundation
import SwiftSciBenchmarkSupport
import SwiftDataFrame
import SwiftML

// The timing source reads one column-major binary batch at a time. Fixture conversion
// happens before timing; decoded held-out columns are not captured by this actor.
actor BoundedCoreMLSource {
    private let file: FileHandle
    private let names: [String]
    private let rows: Int
    private let batches: Int
    private(set) var loaded = 0
    private(set) var consumed = 0
    private(set) var maximumOutstanding = 0
    private(set) var sampledResidentBytes: UInt64 = 0
    private(set) var hashes: [String] = []
    private(set) var firstResultSeconds: Double = 0
    private let start: ContinuousClock.Instant
    private let delayMilliseconds: Int

    init(url: URL, names: [String], rows: Int, batches: Int, delayMilliseconds: Int) throws {
        file = try FileHandle(forReadingFrom: url)
        self.names = names
        self.rows = rows
        self.batches = batches
        self.delayMilliseconds = delayMilliseconds
        start = .now
    }

    func load(_ sequence: Int) throws -> PreparedNumericBatch? {
        try Task.checkCancellation()
        guard sequence == loaded else { throw BenchmarkFailure("Source order changed") }
        if sequence == batches { return nil }
        let bytes = rows * names.count * 8
        guard let data = try file.read(upToCount: bytes), data.count == bytes else {
            throw BenchmarkFailure("Truncated bounded input")
        }
        let columns: [[Double]] = data.withUnsafeBytes { buffer in
            (0..<names.count).map { c in
                (0..<rows).map { r in
                    let bits = buffer.loadUnaligned(fromByteOffset: (c * rows + r) * 8, as: UInt64.self)
                    return Double(bitPattern: UInt64(littleEndian: bits))
                }
            }
        }
        loaded += 1
        maximumOutstanding = max(maximumOutstanding, loaded - consumed)
        sampledResidentBytes = max(sampledResidentBytes, try residentBytes())
        return try PreparedNumericBatch(columnNames: names, columns: columns)
    }

    func consume(_ sequence: Int, prediction: CoreMLPrediction) async throws {
        guard sequence == consumed, prediction.values.originalRowIndices == Array(0..<rows) else {
            throw BenchmarkFailure("Output order or local row identity changed")
        }
        if consumed == 0 { firstResultSeconds = elapsedSeconds(since: start) }
        if delayMilliseconds > 0 { try await Task.sleep(for: .milliseconds(delayMilliseconds)) }
        hashes.append(try coreMLResultHash(prediction.values))
        consumed += 1
        sampledResidentBytes = max(sampledResidentBytes, try residentBytes())
        guard sampledResidentBytes < 1_073_741_824 else { throw BenchmarkFailure("Bounded workflow RSS cutoff") }
    }

    func close() throws { try file.close() }
}

func writeBoundedCoreMLSource(_ raw: FusionRawFixture, rows: Int, batches: Int, to url: URL) throws {
    var bytes = Data()
    for batch in 0..<batches {
        for column in raw.heldOutColumns {
            for row in 0..<rows {
                let source = (batch * rows + row) % column.count
                var bits = column[source].bitPattern.littleEndian
                withUnsafeBytes(of: &bits) { bytes.append(contentsOf: $0) }
            }
        }
    }
    try bytes.write(to: url)
}
