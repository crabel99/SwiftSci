import Foundation
import SwiftDataFrame
import Darwin
import CryptoKit

struct Input: Decodable {
    let id: String, path: String, delimiter: String
    let rows: Int
    let names: [String], types: [String], hashes: [String]
    let null_tokens: [String]
    let integral: [Bool]
    let max_rows: Int?
    let date_formats: [String: String]?
}
func cpu() -> Int64 {
    var r = rusage(); getrusage(RUSAGE_SELF, &r)
    return Int64(r.ru_utime.tv_sec + r.ru_stime.tv_sec) * 1_000_000_000 + Int64(r.ru_utime.tv_usec + r.ru_stime.tv_usec) * 1_000
}
func resident() -> Int64 {
    var info = mach_task_basic_info()
    var count = mach_msg_type_number_t(MemoryLayout<mach_task_basic_info>.size / MemoryLayout<integer_t>.size)
    let result = withUnsafeMutablePointer(to: &info) { pointer in
        pointer.withMemoryRebound(to: integer_t.self, capacity: Int(count)) {
            task_info(mach_task_self_, task_flavor_t(MACH_TASK_BASIC_INFO), $0, &count)
        }
    }
    precondition(result == KERN_SUCCESS)
    return Int64(info.resident_size)
}
func heap() -> Int64 {
    var s = malloc_statistics_t(); malloc_zone_statistics(nil, &s)
    return Int64(s.size_in_use)
}
func peak() -> Int64 { var r = rusage(); getrusage(RUSAGE_SELF, &r); return Int64(r.ru_maxrss) }
struct Digest {
    var hash = SHA256(), buffer = Data(), nulls = 0
    mutating func integer<T: FixedWidthInteger>(_ value: T) {
        var value = value.littleEndian
        withUnsafeBytes(of: &value) { buffer.append(contentsOf: $0) }
    }
    mutating func append<T>(_ value: T?, encode: (inout Digest, T) -> Void) {
        if let value { buffer.append(1); encode(&self, value) }
        else { buffer.append(0); nulls += 1 }
        if buffer.count >= 65536 { hash.update(data: buffer); buffer.removeAll(keepingCapacity: true) }
    }
    mutating func finish() -> String {
        hash.update(data: buffer)
        return hash.finalize().map { String(format: "%02x", $0) }.joined()
    }
}
func validate(_ df: DataFrame, input: Input, mode: String) -> [String: Any] {
    var failures = [String](), details = [[String: Any]]()
    if df.shape.rows != input.rows { failures.append("row count") }
    if df.columnNames != input.names { failures.append("column names/order") }
    for (j, name) in input.names.enumerated() {
        let type = df.dtypes[name]?.description ?? "absent"
        let expected = input.types[j]
        let allowed = type == expected || (mode == "infer" && expected == "Double" && type == "Int64" && input.integral[j])
        if !allowed { failures.append("type: \(name): \(type), expected \(expected)") }
        var d = Digest()
        switch type {
        case "Double":
            let c = df[column: name, as: Double.self]!
            for i in 0..<df.shape.rows { d.append(c[i]) { $0.integer($1.bitPattern) } }
        case "Int64":
            let c = df[column: name, as: Int64.self]!
            for i in 0..<df.shape.rows { d.append(c[i]) { $0.integer(Double($1).bitPattern) } }
        case "String":
            let c = df[column: name, as: String.self]!
            for i in 0..<df.shape.rows { d.append(c[i]) { digest, value in
                digest.integer(UInt32(value.utf8.count)); digest.buffer.append(contentsOf: value.utf8)
            } }
        case "Date":
            let c = df[column: name, as: Date.self]!
            for i in 0..<df.shape.rows { d.append(c[i]) { $0.integer($1.timeIntervalSince1970.bitPattern) } }
        default: failures.append("unsupported output: \(name): \(type)")
        }
        let actual = d.finish()
        if actual != input.hashes[j] { failures.append("values/nulls: \(name)") }
        details.append(["name":name,"type":type,"nulls":d.nulls,"sha256":actual])
    }
    return ["passed":failures.isEmpty,"failures":failures,"columns":details]
}
func checkedStream(_ stream: AsyncThrowingStream<DataFrame, any Error>, input: Input) async throws -> Bool {
    var hashes = input.names.map { _ in Digest() }
    var rows = 0
    for try await frame in stream {
        guard frame.columnNames == input.names else { return false }
        rows += frame.rowCount
        for (j, name) in input.names.enumerated() {
            guard frame.dtypes[name]?.description == input.types[j] else { return false }
            switch input.types[j] {
            case "Double":
                for value in frame[column: name, as: Double.self]!.values {
                    hashes[j].append(value) { $0.integer($1.bitPattern) }
                }
            case "Int64":
                for value in frame[column: name, as: Int64.self]!.values {
                    hashes[j].append(value) { $0.integer(Double($1).bitPattern) }
                }
            case "Date":
                for value in frame[column: name, as: Date.self]!.values {
                    hashes[j].append(value) { $0.integer($1.timeIntervalSince1970.bitPattern) }
                }
            case "String":
                for value in frame[column: name, as: String.self]!.values {
                    hashes[j].append(value) { digest, value in
                        digest.integer(UInt32(value.utf8.count)); digest.buffer.append(contentsOf: value.utf8)
                    }
                }
            default: return false
            }
        }
    }
    guard rows == input.rows else { return false }
    for j in hashes.indices {
        guard hashes[j].finish() == input.hashes[j] else { return false }
    }
    return true
}
func consume(_ frames: AsyncThrowingStream<DataFrame, any Error>) async throws -> Int {
    var count = 0
    for try await frame in frames { count += frame.rowCount }
    return count
}
@MainActor @main struct StreamProbe {
    static func main() async throws {
        let args = Array(CommandLine.arguments.dropFirst())
        let input = try JSONDecoder().decode(Input.self, from: Data(contentsOf: URL(fileURLWithPath: args[0])))
        let chunkSize = Int(args[1])!
        var options = CSVReadOptions()
        if args.count > 2 {
            precondition(["serial", "parallel"].contains(args[2]))
            options.columnConversionMode = args[2] == "serial" ? .serial : .parallel
        }
        options.delimiter = Character(input.delimiter); options.nullValues = Set(input.null_tokens)
        options.maxRows = input.max_rows
        let mapping: [String: ColumnDType] = ["String":.utf8,"Double":.float64,"Int64":.int64,"Date":.date32]
        options.columnTypeOverrides = Dictionary(uniqueKeysWithValues: zip(input.names, input.types).map { ($0.0,mapping[$0.1]!) })
        options.columnDateFormats = input.date_formats ?? (input.id.hasPrefix("energy-date-") ? ["Date": "d/M/yyyy"] : [:])
        let url = URL(fileURLWithPath: input.path)
        for _ in 0..<2 {
            let count = try await consume(DataFrame.readCSVStream(contentsOf: url, chunkSize: chunkSize, options: options))
            precondition(count == input.rows)
        }
        var samples = [[String: Any]]()
        for _ in 0..<5 {
            let r0 = resident(), p0 = peak(), h0 = heap(), c0 = cpu(), t0 = DispatchTime.now().uptimeNanoseconds
            let count = try await consume(DataFrame.readCSVStream(contentsOf: url, chunkSize: chunkSize, options: options))
            let t1 = DispatchTime.now().uptimeNanoseconds, c1 = cpu(), h1 = heap(), p1 = peak(), r1 = resident()
            precondition(count == input.rows)
            samples.append(["total_ns": Int64(t1-t0), "total_cpu_ns": c1-c0,
                "rss_before_bytes":r0,"rss_after_bytes":r1,"rss_growth_bytes":r1-r0,
                "peak_before_bytes":p0,"peak_after_bytes":p1,"heap_before_bytes":h0,"heap_after_bytes":h1])
        }
        let valid = try await checkedStream(DataFrame.readCSVStream(contentsOf: url, chunkSize: chunkSize, options: options), input: input)
        let result: [String: Any] = ["validated": valid, "rows":input.rows,"input":input.id,
            "chunk_size":chunkSize,"samples":samples,"warmups":2,
            "scope":"Two warmup streams, five separately timed full streams with row checks, then one untimed full native type/value/null/order validation. Per-worker medians are observations; repeated reads are not independent workers. Peak RSS includes warmups and preceding reads."]
        print(String(decoding:try JSONSerialization.data(withJSONObject:result,options:[.sortedKeys]),as:UTF8.self))
    }
}
