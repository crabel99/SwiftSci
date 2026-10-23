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
@MainActor @main struct PreparationProbe {
    static func main() async throws {
        let args = Array(CommandLine.arguments.dropFirst())
        let input = try JSONDecoder().decode(Input.self, from: Data(contentsOf: URL(fileURLWithPath: args[0])))
        let action = args[1], rows = Int(args[2])!, repetitions = Int(args[3])!
        let tokens = Set(input.null_tokens)
        var checksum = 0
        var readCPU: Int64 = 0, readWall: UInt64 = 0
        var expected: Bool? = nil
        if action == "factory" || action == "prefix" {
            let first: Any? = action == "factory" ? CSVPreparationDiagnostics.makeAttempt(nullValues: tokens, selectedRows: rows) : CSVPreparationDiagnostics.makePrefix(nullValues: tokens, selectedRows: rows)
            expected = first != nil
            withExtendedLifetime(first) {}
            let c0 = cpu(), t0 = DispatchTime.now().uptimeNanoseconds
            if action == "factory" {
                for _ in 0..<repetitions {
                    let value = CSVPreparationDiagnostics.makeAttempt(nullValues: tokens, selectedRows: rows)
                    withExtendedLifetime(value) {}
                    checksum += 1
                }
            } else {
                for _ in 0..<repetitions {
                    let value = CSVPreparationDiagnostics.makePrefix(nullValues: tokens, selectedRows: rows)
                    if value != nil { checksum += 1 }
                    withExtendedLifetime(value) {}
                }
            }
            readWall = DispatchTime.now().uptimeNanoseconds - t0
            readCPU = cpu() - c0
            precondition(checksum == (expected! ? repetitions : 0))
        } else {
            precondition(action == "hash")
            var options = CSVReadOptions()
            options.nullValues = []
            options.columnTypeOverrides = Dictionary(uniqueKeysWithValues: input.names.map { ($0, ColumnDType.utf8) })
            let frame = try await DataFrame(csv: URL(fileURLWithPath: input.path), options: options)
            precondition(frame.rowCount == input.rows)
            let values: [[String]] = input.names.map { name in
                frame[column: name, as: String.self]!.values.map { value in
                    guard let value else { fatalError("Missing raw String field") }
                    return value
                }
            }
            for _ in 0..<2 {
                for column in values { withExtendedLifetime(CSVPreparationDiagnostics.hashValues(column, nullValues: tokens)) {} }
            }
            var output: [[String?]] = []
            let c0 = cpu(), t0 = DispatchTime.now().uptimeNanoseconds
            for _ in 0..<repetitions {
                output = values.map { CSVPreparationDiagnostics.hashValues($0, nullValues: tokens) }
                withExtendedLifetime(output) {}
            }
            readWall = DispatchTime.now().uptimeNanoseconds - t0
            readCPU = cpu() - c0
            for (column, expectedHash) in zip(output,input.hashes) {
                var digest = Digest()
                for value in column {
                    digest.append(value) { d, v in d.integer(UInt32(v.utf8.count)); d.buffer.append(contentsOf:v.utf8) }
                }
                precondition(digest.finish() == expectedHash)
            }
            checksum = output.count * input.rows
        }
        let result: [String: Any] = ["validated":true,"action":action,"rows":rows,"repetitions":repetitions,
            "total_cpu_ns":readCPU,"elapsed_ns":readWall,"cpu_per_iteration_ns":Double(readCPU)/Double(repetitions),
            "checksum":checksum,"admitted":expected as Any? ?? NSNull(),"all_native_utf8_tokens":tokens.allSatisfy(\.isContiguousUTF8),
            "peak_bytes":peak(),"heap_after_bytes":heap(),"hash_fingerprint":["missing-0".hashValue,"ordinary-value".hashValue],
            "scope":"Diagnostic snapshot. Factory includes plan creation, attempt allocation, opaque Any boxing and release. Prefix includes actual constructor and optional opaque ownership. Hash uses already-decoded values, native Set membership and optional output allocation; final native output hashes checked outside timing. These phases are not additive portions of a full read."]
        print(String(decoding:try JSONSerialization.data(withJSONObject:result,options:[.sortedKeys]),as:UTF8.self))
    }
}
