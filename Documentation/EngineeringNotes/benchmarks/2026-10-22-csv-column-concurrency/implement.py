from pathlib import Path
S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021')
p=S/'Sources/SwiftDataFrame/IO/CSVReadOptions.swift';s=p.read_text();s=s.replace('''    /// Maximum number of rows to read (nil = unlimited).''','''    /// How eager and streamed reads schedule column conversion.
    /// The default converts columns in parallel using the system scheduler.
    /// Serial conversion can reduce CPU work at the cost of longer elapsed time.
    /// This choice does not change type inference, row batches, or output values.
    public var columnConversionMode: CSVColumnConversionMode = .parallel
    /// Maximum number of rows to read (nil = unlimited).''')
s+='''
/// Scheduling choices for converting CSV fields into native columns.
/// Both modes complete conversion before releasing the batch's borrowed bytes.
public enum CSVColumnConversionMode: Sendable {
    /// Convert independent columns with the system's native parallelism.
    case parallel
    /// Convert columns sequentially on the calling thread, without dispatching workers.
    /// This does not constrain other work in the process or set a thread affinity.
    case serial

    internal func forEachColumn(count: Int, _ body: @Sendable (Int) -> Void) {
        switch self {
        case .parallel:
            DispatchQueue.concurrentPerform(iterations: count, execute: body)
        case .serial:
            for column in 0..<count { body(column) }
        }
    }
}
''';p.write_text(s)
p=S/'Sources/SwiftDataFrame/IO/CSVEagerReader.swift';s=p.read_text();s=s.replace('columns: active, sourceOffset: offset)', 'columns: active, mode: options.columnConversionMode, sourceOffset: offset)');s=s.replace('columns: Array(headers.indices), rowCount: rows)', 'columns: Array(headers.indices), mode: options.columnConversionMode, rowCount: rows)');s=s.replace('attempts: [CSVColumnConversion?], columns: [Int], rowCount: Int? = nil, sourceOffset: Int = 0','attempts: [CSVColumnConversion?], columns: [Int], mode: CSVColumnConversionMode,\n        rowCount: Int? = nil, sourceOffset: Int = 0');s=s.replace('DispatchQueue.concurrentPerform(iterations: columns.count) { index in','mode.forEachColumn(count: columns.count) { index in');p.write_text(s)
p=S/'Sources/SwiftDataFrame/IO/CSVReader.swift';s=p.read_text().replace('DispatchQueue.concurrentPerform(iterations: headers.count) { column in','options.columnConversionMode.forEachColumn(count: headers.count) { column in');p.write_text(s)
p=S/'Tests/SwiftDataFrameTests/CSVEagerBatchParityTests.swift';s=p.read_text().replace('arguments: [false, true])','arguments: [false, true], [CSVColumnConversionMode.parallel, .serial])').replace('func mixedReplay(_ headerless: Bool) throws {','func mixedReplay(_ headerless: Bool, _ mode: CSVColumnConversionMode) throws {').replace('        options.delimiter = ";"','        options.columnConversionMode = mode\n        options.delimiter = ";"');s=s.replace('arguments: [0, 10_001, 70_001])','arguments: [0, 10_001, 70_001], [CSVColumnConversionMode.parallel, .serial])').replace('func explicitTypes(_ limit: Int) throws {','func explicitTypes(_ limit: Int, _ mode: CSVColumnConversionMode) throws {').replace('        options.maxRows = limit','        options.columnConversionMode = mode\n        options.maxRows = limit');p.write_text(s)
p=S/'Tests/SwiftDataFrameTests/CSVColumnConversionModeTests.swift';p.write_text('''import Foundation
import Testing
@testable import SwiftDataFrame

@Suite("CSV column conversion modes")
struct CSVColumnConversionModeTests {
    @Test("Serial and parallel reads preserve native types, nulls, and streamed output",
          arguments: [CSVColumnConversionMode.parallel, .serial])
    func publicReads(_ mode: CSVColumnConversionMode) async throws {
        var options = CSVReadOptions()
        options.columnConversionMode = mode
        options.columnTypeOverrides = ["id": .int64, "value": .float64, "flag": .boolean, "date": .date32]
        options.columnDateFormats = ["date": "d/M/yyyy"]
        let csv = "id,value,flag,date,label\\n1,2.5,true,2/1/2020,\\"alpha\\nline\\"\\nNA,invalid,maybe,bad,tail\\n"
        let url = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString + ".csv")
        defer { try? FileManager.default.removeItem(at: url) }
        try Data(csv.utf8).write(to: url)
        let eager = try await DataFrame(csv: url, options: options)
        let integers: [Int64?] = [1, nil]
        let doubles: [Double?] = [2.5, nil]
        let flags: [Bool?] = [true, nil]
        let labels: [String?] = ["alpha\\nline", "tail"]
        #expect(eager[column: "id", as: Int64.self]?.values == integers)
        #expect(eager[column: "value", as: Double.self]?.values == doubles)
        #expect(eager[column: "flag", as: Bool.self]?.values == flags)
        #expect(eager[column: "label", as: String.self]?.values == labels)
        let dates = try #require(eager[column: "date", as: Date.self])
        #expect(dates[0]?.timeIntervalSince1970 == 1_577_923_200)
        #expect(dates[1] == nil)
        var offset = 0
        for try await chunk in DataFrame.readCSVStream(contentsOf: url, options: options, chunkSize: 1) {
            #expect(chunk.rowCount == 1)
            #expect(chunk.dtypes == eager.dtypes)
            #expect(chunk[column: "id", as: Int64.self]?[0] == integers[offset])
            #expect(chunk[column: "value", as: Double.self]?[0] == doubles[offset])
            #expect(chunk[column: "flag", as: Bool.self]?[0] == flags[offset])
            #expect(chunk[column: "date", as: Date.self]?[0] == dates[offset])
            #expect(chunk[column: "label", as: String.self]?[0] == labels[offset])
            offset += 1
        }
        #expect(offset == 2)
    }
}
''')
