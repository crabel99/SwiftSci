from pathlib import Path
T=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021/Tests/SwiftDataFrameTests')
(T/'CSVASCIIPrefixStringDecoderTests.swift').write_text('''import Foundation
import Testing
@testable import SwiftDataFrame

@Suite("CSV bounded ASCII String null keys")
struct CSVASCIIPrefixStringDecoderTests {
    @Test("Preparation uses the selected row budget and rejects unsuitable sets")
    func eligibility() {
        let tokens: Set<String> = ["", "NA", "null"]
        #expect(CSVASCIIPrefixStringDecoder(nullValues: tokens, selectedRowCount: 8) == nil)
        #expect(CSVASCIIPrefixStringDecoder(nullValues: tokens, selectedRowCount: 9) != nil)
        #expect(CSVASCIIPrefixStringDecoder(nullValues: tokens, selectedRowCount: 10) != nil)
        let rejected: [Set<String>] = [[], ["NA"], ["", "NA"], ["", "NA", "é"]]
        for values in rejected {
            #expect(CSVASCIIPrefixStringDecoder(nullValues: values, selectedRowCount: 1_000) == nil)
        }
        let long: Set<String> = ["", "NA", String(repeating: "x", count: 10_000)]
        #expect(CSVASCIIPrefixStringDecoder(nullValues: long, selectedRowCount: 64) == nil)
        var saturated = Set<String>()
        for byte in UInt8(0)...UInt8(127) { saturated.insert(String(UnicodeScalar(byte))) }
        #expect(CSVASCIIPrefixStringDecoder(nullValues: saturated, selectedRowCount: 256) == nil)
    }

    @Test("Prepared keys own values and preserve parsed String membership")
    func ownedMembership() throws {
        let expected: Set<String> = ["", "K", "NA", "?", "@", "\\u{7f}"]
        var tokens = expected
        let decoder = try #require(CSVASCIIPrefixStringDecoder(nullValues: tokens, selectedRowCount: 128))
        tokens.removeAll()
        tokens.insert("replacement")
        let strings: [String] = ["", " \\tNA\\r\\n", "na", "é", "e\\u{301}", "K", "K", "?", "@", "\\u{7f}", "\\0", "\\\"a\\\"\\\"b\\\"", "汉字"]
        var inputs: [[UInt8]] = strings.map { (value: String) -> [UInt8] in Array(value.utf8) }
        inputs.append([0xff])
        inputs.append([34, 0xff, 34])
        inputs.append([34, 0xff, 34, 34, 34])
        for bytes in inputs {
            bytes.withUnsafeBufferPointer { buffer in
                let field = CSVFieldOffset(startOffset: 0, length: bytes.count, escapedQuotesPresent: bytes.contains(34))
                let text = VectorizedByteParsers.parseString(buffer: buffer, offset: field)
                switch decoder.decode(buffer: buffer, offset: field) {
                case .missing: #expect(expected.contains(text))
                case .value(let value):
                    #expect(!expected.contains(text))
                    #expect(value == text)
                case .invalid: Issue.record("String conversion unexpectedly rejected a field")
                }
            }
        }
    }
}
''')
(T/'CSVASCIIPrefixStringReadTests.swift').write_text('''import Foundation
import Testing
@testable import SwiftDataFrame

@Suite("CSV prepared String read parity")
struct CSVASCIIPrefixStringReadTests {
    @Test("Eager and streamed chunks agree across decoder-selection boundaries")
    func publicReads() async throws {
        let fixture: [String] = ["value", "NA", "", "K", "K", "é", "e\\u{301}", "a\\\"b", "汉字"]
        let values: [String] = (0..<64).map { (index: Int) -> String in fixture[index % fixture.count] }
        let lines: [String] = values.enumerated().map { pair -> String in
            let escaped: String = pair.element.replacingOccurrences(of: "\\\"", with: "\\\"\\\"")
            return "\\(pair.offset),\\\" \\t\\(escaped) \\r\\n\\\"\\n"
        }
        let url = FileManager.default.temporaryDirectory.appendingPathComponent("csv-prepared-nulls-\\(UUID().uuidString).csv")
        defer { try? FileManager.default.removeItem(at: url) }
        try Data(("id,text\\n" + lines.joined()).utf8).write(to: url)
        let tokens: Set<String> = ["", "K", "NA"]
        let expected: [String?] = values.map { (value: String) -> String? in tokens.contains(value) ? nil : value }
        for mode in [CSVColumnConversionMode.parallel, .serial] {
            var options = CSVReadOptions()
            options.nullValues = tokens
            options.columnConversionMode = mode
            options.columnTypeOverrides = ["id": .int64, "text": .utf8]
            let frame = try await DataFrame(csv: url, options: options)
            #expect(frame[column: "text", as: String.self]?.values == expected)
            for size in [3, 63] {
                var actual: [String?] = []
                for try await chunk in DataFrame.readCSVStream(contentsOf: url, chunkSize: size, options: options) {
                    let column = try #require(chunk[column: "text", as: String.self])
                    actual.append(contentsOf: column.values)
                }
                #expect(actual == expected)
            }
        }
    }
}
''')
p=T/'CSVStringNullTests.swift';s=p.read_text().replace('["é", "K"], CSVReadOptions','["é", "K"], ["é", "K", "NA"], CSVReadOptions');p.write_text(s)
