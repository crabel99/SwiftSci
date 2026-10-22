from pathlib import Path
s=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');p=s/'Sources/SwiftDataFrame/IO/SystemsCSVParser.swift';t=p.read_text();i=t.index('    private enum ScanResult')
t=t[:i]+'''    internal func countRecords(buffer: UnsafeBufferPointer<UInt8>, maximumRows: Int? = nil) throws -> Int {
        var rows = 0
        var offset = 0
        while offset < buffer.count && maximumRows.map({ rows < $0 }) != false {
            let bytes = UnsafeBufferPointer(rebasing: buffer[offset...])
            let remaining = maximumRows.map { $0 - rows } ?? 16_384
            let batch = try scanBatch(buffer: bytes, maximumRows: min(16_384, remaining))
            guard !batch.records.isEmpty else { break }
            rows += batch.records.count
            offset += batch.nextOffset
        }
        return rows
    }

'''+t[i:];p.write_text(t)
p=s/'Sources/SwiftDataFrame/IO/CSVEagerReader.swift';t=p.read_text();a=t.index('    private static func countRows(');b=t.index('    private struct Initial',a);t=t[:a]+t[b:];t=t.replace('countRows(source: remainder, parser: parser, maximum: remaining)', 'parser.countRecords(buffer: remainder, maximumRows: remaining)');p.write_text(t)
(s/'Tests/SwiftDataFrameTests/CSVRecordCountTests.swift').write_text('''import Foundation
import Testing
@testable import SwiftDataFrame

@Suite("CSV count-only grammar parity")
struct CSVRecordCountTests {
    @Test("Count matches record discovery for quotes and permissive EOF",
          arguments: ["", "a,b", "a,b,", "a,b\\n", "\\n\\n", "\\"a\\nb\\",c\\r\\nlast,", "\\"unterminated,tail", "a,\\"b\\"\\"c\\"\\n"])
    func records(_ text: String) throws {
        try compare(Array(text.utf8), delimiter: 44, quote: 34)
    }

    @Test("Count shares custom delimiter and quote precedence", arguments: [UInt8(44), 59, 10, 34, 0, 255])
    func generated(_ delimiter: UInt8) throws {
        for quote: UInt8 in [34, 39, 10, 44, 0] {
            var seed: UInt64 = 81_471
            let alphabet: [UInt8] = [65, 10, 13, 34, delimiter, quote]
            for length in 0..<256 {
                var bytes = [UInt8]()
                for _ in 0..<(length % 37) {
                    seed = seed &* 6_364_136_223_846_793_005 &+ 1
                    bytes.append(alphabet[Int(seed >> 32) % alphabet.count])
                }
                try compare(bytes, delimiter: delimiter, quote: quote)
            }
        }
    }

    @Test("Count crosses search windows and preserves row limits", arguments: [65_535, 65_536, 65_537])
    func longField(_ length: Int) throws {
        let text = "\\"" + String(repeating: "x", count: length) + "\\ninside\\",tail\\r\\nnext,row\\n"
        try compare(Array(text.utf8), delimiter: 44, quote: 34)
    }

    @Test("Record counting checks cancellation")
    func cancellation() async throws {
        let bytes = Array("a,b\\n1,2\\n".utf8)
        let task = Task {
            withUnsafeCurrentTask { $0?.cancel() }
            return try bytes.withUnsafeBufferPointer {
                try SystemsCSVParser().countRecords(buffer: $0)
            }
        }
        do {
            _ = try await task.value
            Issue.record("Cancelled counting completed")
        } catch is CancellationError {} catch {
            Issue.record("Unexpected error: \\(error)")
        }
    }

    private func compare(_ bytes: [UInt8], delimiter: UInt8, quote: UInt8) throws {
        try bytes.withUnsafeBufferPointer { buffer in
            let parser = SystemsCSVParser(delimiterByte: delimiter, quoteByte: quote)
            let expected = parser.parseIndex(buffer: buffer, minimumParallelBytes: .max).count
            #expect(try parser.countRecords(buffer: buffer) == expected)
            for limit in [0, 1, 2, 100] {
                #expect(try parser.countRecords(buffer: buffer, maximumRows: limit) == min(expected, limit))
            }
        }
    }
}
''')
r=Path('/private/tmp/swiftsci-csv-cpu-profile-20261021');v=Path('/private/tmp/swiftsci-csv-eager-checks-20261021/verify-counted.py').read_text().replace('/private/tmp/swiftsci-csv-eager-count-probe-20261021',str(s));(r/'verify.py').write_text(v)
