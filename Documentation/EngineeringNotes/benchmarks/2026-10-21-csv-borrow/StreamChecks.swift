import Foundation
import SwiftDataFrame
func value(_ row: Int, _ col: Int) -> Double { Double((row * 17 + col * 31) % 1009) + 0.5 }
@MainActor @main struct StreamChecks {
    static func equal<T: SupportedType & Equatable>(_ chunk: DataFrame, _ whole: DataFrame, name: String, start: Int, type: T.Type) {
        let a = chunk[column: name, as: T.self]!
        let b = whole[column: name, as: T.self]!
        for i in 0..<chunk.shape.rows { precondition(a[i] == b[start + i]) }
    }
    static func main() async throws {
        let cases = try JSONSerialization.jsonObject(with: Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[1]))) as! [[Any]]
        var checked = 0
        for entry in cases {
            let mode = entry[0] as! String, n = entry[1] as! Int, width = entry[2] as! Int
            let kind = String(mode.split(separator: "-")[0])
            let opts = options(kind: kind, known: mode.hasSuffix("known"), width: width)
            let url = URL(fileURLWithPath: entry[3] as! String)
            let whole = try await DataFrame(csv: url, options: opts)
            validate(whole, kind: kind, rows: n, width: width)
            var start = 0
            for try await chunk in DataFrame.readCSVStream(contentsOf: url, chunkSize: 257, options: opts) {
                precondition(chunk.columnNames == whole.columnNames && chunk.shape.rows > 0 && chunk.shape.rows <= 257)
                for name in whole.columnNames {
                    if whole[column: name, as: Int64.self] != nil { equal(chunk, whole, name: name, start: start, type: Int64.self) }
                    else if whole[column: name, as: Double.self] != nil { equal(chunk, whole, name: name, start: start, type: Double.self) }
                    else if whole[column: name, as: Bool.self] != nil { equal(chunk, whole, name: name, start: start, type: Bool.self) }
                    else if whole[column: name, as: Date.self] != nil { equal(chunk, whole, name: name, start: start, type: Date.self) }
                    else { equal(chunk, whole, name: name, start: start, type: String.self) }
                }
                start += chunk.shape.rows
                checked += chunk.shape.rows * width
            }
            precondition(start == n)
        }
        print("PASS: 8 streaming workloads, 257-row chunks, \(checked) exact field comparisons")
    }
    static func options(kind: String, known: Bool, width: Int) -> CSVReadOptions {
        var options = CSVReadOptions()
        if known {
            let types: [ColumnDType]
            switch kind {
            case "mixed": types = [.int64, .float64, .boolean, .utf8]
            case "missing": types = Array(repeating: .float64, count: width)
            case "text": types = [.int64, .utf8]
            case "dates": types = [.int64, .date32]
            default: preconditionFailure("Unknown fixture")
            }
            options.columnTypeOverrides = Dictionary(uniqueKeysWithValues: types.enumerated().map { ("c\($0.offset)", $0.element) })
        }
        return options
    }
    static func validate(_ df: DataFrame, kind: String, rows n: Int, width: Int) {
        precondition(df.shape.rows == n && df.columnNames == (0..<width).map { "c\($0)" })
        switch kind {
        case "mixed":
            let integers = df[column: "c0", as: Int64.self]!
            let doubles = df[column: "c1", as: Double.self]!
            let bools = df[column: "c2", as: Bool.self]!
            let strings = df[column: "c3", as: String.self]!
            for i in 0..<n {
                precondition(integers[i] == (i % 11 == 0 ? nil : Int64(i - 10000)))
                precondition(doubles[i] == ((i + 1) % 11 == 0 ? nil : value(i, 0)))
                precondition(bools[i] == ((i + 2) % 11 == 0 ? nil : i % 2 == 0))
                precondition(strings[i] == ((i + 3) % 11 == 0 || i % 37 == 0 ? nil : "station-\(i % 97)"))
            }
        case "missing":
            for j in 0..<width {
                let column = df[column: "c\(j)", as: Double.self]!
                for i in 0..<n { precondition(column[i] == ((i + j) % 11 == 0 ? nil : value(i, j))) }
            }
        case "text":
            let ids = df[column: "c0", as: Int64.self]!
            let strings = df[column: "c1", as: String.self]!
            let prefix = "prefix, \"quoted\"\n" + String(repeating: "abcdefgh", count: 1024)
            for i in 0..<n {
                precondition(ids[i] == Int64(i))
                precondition(strings[i] == prefix + "-\(i)")
            }
        case "dates":
            let ids = df[column: "c0", as: Int64.self]!
            let dates = df[column: "c1", as: Date.self]!
            var calendar = Calendar(identifier: .gregorian)
            calendar.timeZone = TimeZone(secondsFromGMT: 0)!
            for i in 0..<n {
                precondition(ids[i] == Int64(i))
                precondition(dates[i] == calendar.date(from: DateComponents(year: 2026, month: 1, day: i % 28 + 1)))
            }
        default: preconditionFailure("Unknown fixture")
        }
    }
}
