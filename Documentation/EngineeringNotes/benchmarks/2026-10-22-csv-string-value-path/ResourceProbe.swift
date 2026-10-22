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
        case "Bool":
            let c = df[column: name, as: Bool.self]!
            for i in 0..<df.shape.rows { d.append(c[i]) { $0.integer(UInt8($1 ? 1 : 0)) } }
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
@MainActor @main struct ReferenceProbe {
    static func main() async throws {
        let args = Array(CommandLine.arguments.dropFirst())
        let input = try JSONDecoder().decode(Input.self, from: Data(contentsOf: URL(fileURLWithPath: args[0])))
        let mode = args[1], phase = args[2], reps = Int(args[3])!
        var options = CSVReadOptions()
        if args.count > 4 {
            precondition(["serial", "parallel"].contains(args[4]))
            options.columnConversionMode = args[4] == "serial" ? .serial : .parallel
        }
        options.delimiter = Character(input.delimiter); options.nullValues = Set(input.null_tokens)
        options.maxRows = input.max_rows
        let mapping: [String: ColumnDType] = ["String":.utf8,"Double":.float64,"Int64":.int64,"Date":.date32,"Bool":.boolean]
        if mode == "known" {
            options.columnTypeOverrides = Dictionary(uniqueKeysWithValues: zip(input.names, input.types).map { ($0.0,mapping[$0.1]!) })
        } else if input.id == "energy" {
            options.columnTypeOverrides = ["Date":.utf8,"Time":.utf8]
        }
        if mode == "known" { options.columnDateFormats = input.date_formats ?? (input.id.hasPrefix("energy-date-") ? ["Date": "d/M/yyyy"] : [:]) }
        let url = URL(fileURLWithPath: input.path)
        let repeats = phase == "timing" ? reps + 2 : 1
        var records = [[String: Int64]](), checks = [String: Any](), passed = true
        for i in 0..<repeats {
            let h0 = heap(), p0 = peak(), r0 = resident(), c0 = cpu(), t0 = DispatchTime.now().uptimeNanoseconds
            var output: DataFrame? = try await DataFrame(csv: url, options: options)
            let t1 = DispatchTime.now().uptimeNanoseconds, c1 = cpu(), h1 = heap(), p1 = peak(), r1 = resident()
            checks = validate(output!, input: input, mode: mode)
            let c2 = cpu(), t2 = DispatchTime.now().uptimeNanoseconds
            output = nil
            let t3 = DispatchTime.now().uptimeNanoseconds, c3 = cpu()
            if phase != "timing" || i >= 2 {
                records.append(["total_ns":Int64(t1-t0+t3-t2),"total_cpu_ns":c1-c0+c3-c2,
                    "call_ns":Int64(t1-t0),"call_cpu_ns":c1-c0,"release_ns":Int64(t3-t2),"release_cpu_ns":c3-c2,
                    "rss_before_bytes":r0,"rss_held_bytes":r1,"rss_held_delta_bytes":r1-r0,"rss_after_release_bytes":resident(),"heap_before_bytes":h0,"held_heap_bytes":h1,"held_heap_delta_bytes":h1-h0,"heap_after_release_bytes":heap(),
                    "process_peak_before_bytes":p0,"process_peak_held_bytes":p1])
            }
            if checks["passed"] as? Bool != true { passed = false; break }
        }
        let result: [String: Any] = ["validated":passed,"input":input.id,"mode":mode,"phase":phase,"samples":records,"checks":checks,
            "scope":"Public CSV read plus release; full independent per-column SHA256 validation excluded from CPU/wall. Peak/held memory captured before validation. Date-format cases explicitly use d/M/yyyy and keep Time as text."]
        print(String(decoding:try JSONSerialization.data(withJSONObject:result,options:[.sortedKeys]),as:UTF8.self))
    }
}
