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
    let raw_string_hashes: [String: String]?
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
@inline(never) func parseOnly(_ bytes: UnsafeBufferPointer<UInt8>, _ fields: [CSVFieldOffset]) -> [String?] {
    var values = [String?]()
    values.reserveCapacity(fields.count)
    for field in fields { values.append(VectorizedByteParsers.parseString(buffer: bytes, offset: field)) }
    return values
}
@inline(never) func parseAndMatch(_ bytes: UnsafeBufferPointer<UInt8>, _ fields: [CSVFieldOffset], _ tokens: Set<String>) -> [String?] {
    var values = [String?]()
    values.reserveCapacity(fields.count)
    for field in fields {
        let text = VectorizedByteParsers.parseString(buffer: bytes, offset: field)
        values.append(tokens.contains(text) ? nil : text)
    }
    return values
}
@inline(never) func copyOnly(_ texts: [String]) -> [String?] {
    var values = [String?]()
    values.reserveCapacity(texts.count)
    for text in texts { values.append(text) }
    return values
}
@inline(never) func matchOnly(_ texts: [String], _ tokens: Set<String>) -> [String?] {
    var values = [String?]()
    values.reserveCapacity(texts.count)
    for text in texts { values.append(tokens.contains(text) ? nil : text) }
    return values
}
func stringDigest(_ values: [String?]) -> String {
    var d = Digest()
    for value in values {
        d.append(value) { digest, text in
            digest.integer(UInt32(text.utf8.count))
            digest.buffer.append(contentsOf: text.utf8)
        }
    }
    return d.finish()
}
@MainActor @main struct PhaseProbe {
    static func main() async throws {
        let args = Array(CommandLine.arguments.dropFirst())
        let input = try JSONDecoder().decode(Input.self, from: Data(contentsOf: URL(fileURLWithPath: args[0])))
        let tokens = Set(input.null_tokens)
        var options = CSVReadOptions()
        options.nullValues = tokens
        options.delimiter = Character(input.delimiter)
        options.columnConversionMode = .serial
        let mapping: [String: ColumnDType] = ["String":.utf8,"Double":.float64,"Int64":.int64,"Date":.date32,"Bool":.boolean]
        options.columnTypeOverrides = Dictionary(uniqueKeysWithValues: zip(input.names,input.types).map { ($0.0,mapping[$0.1]!) })
        let url = URL(fileURLWithPath: input.path)
        let c0 = cpu(), t0 = DispatchTime.now().uptimeNanoseconds
        var frame: DataFrame? = try await DataFrame(csv: url, options: options)
        let t1 = DispatchTime.now().uptimeNanoseconds, c1 = cpu(), fullPeak = peak()
        let checks = validate(frame!, input: input, mode: "known")
        precondition(checks["passed"] as? Bool == true)
        let c2 = cpu(), t2 = DispatchTime.now().uptimeNanoseconds
        frame = nil
        let t3 = DispatchTime.now().uptimeNanoseconds, c3 = cpu()
        let full: [String: Int64] = ["total_cpu_ns":c1-c0+c3-c2,"total_ns":Int64(t1-t0+t3-t2),"peak_bytes":fullPeak]
        let data = try Data(contentsOf: url, options: .mappedIfSafe)
        let columns = input.types.indices.filter { input.types[$0] == "String" }
        var results = [[String: Any]]()
        data.withUnsafeBytes { raw in
            let bytes = raw.bindMemory(to: UInt8.self)
            let fields: [[CSVFieldOffset]] = {
                let records = SystemsCSVParser(delimiterByte: input.delimiter.utf8.first!).parse(buffer: bytes)
                precondition(records.count == input.rows + 1)
                return columns.map { col in (1...input.rows).map { row in records[row][col] } }
            }()
            let texts: [[String]] = fields.map { fs in fs.map { field in VectorizedByteParsers.parseString(buffer: bytes, offset: field) } }
            let modes = ["copy","match","parse","parse-match"]
            for round in 0..<8 {
                let index = round % 4
                var order = Array(modes[index...] + modes[..<index])
                if round >= 4 { order.reverse() }
                for (position, col) in columns.enumerated() {
                    for mode in order {
                        let h0 = heap(), r0 = resident(), c0 = cpu(), t0 = DispatchTime.now().uptimeNanoseconds
                        var output: [String?]?
                        switch mode {
                        case "copy": output = copyOnly(texts[position])
                        case "match": output = matchOnly(texts[position], tokens)
                        case "parse": output = parseOnly(bytes, fields[position])
                        default: output = parseAndMatch(bytes, fields[position], tokens)
                        }
                        let t1 = DispatchTime.now().uptimeNanoseconds, c1 = cpu(), h1 = heap(), r1 = resident()
                        let expected = mode == "match" || mode == "parse-match" ? input.hashes[col] : input.raw_string_hashes![input.names[col]]!
                        precondition(output!.count == input.rows)
                        let digest = stringDigest(output!)
                        precondition(digest == expected, "String phase hash mismatch")
                        let c2 = cpu(), t2 = DispatchTime.now().uptimeNanoseconds
                        output = nil
                        let t3 = DispatchTime.now().uptimeNanoseconds, c3 = cpu()
                        results.append(["mode":mode,"column":input.names[col],"round":round,"validated":true,"sha256":digest,
                            "total_cpu_ns":c1-c0+c3-c2,"total_ns":Int64(t1-t0+t3-t2),"held_heap_delta_bytes":h1-h0,"held_rss_delta_bytes":r1-r0])
                    }
                }
            }
        }
        let result: [String: Any] = ["input":input.id,"validated":true,"full_read":full,"checks":checks,"phases":results,
            "scope":"Diagnostic serial String-field replay. Complete read measured first. Parsing/index setup and predecoded input creation are untimed. Four allocating modes use the same fields and token Set; rotated order; full independent native digests. Validation CPU excluded; output release included. Phase medians are not additive fractions of full-read cost. Heap deltas are allocator observations; retained replay state differs from production."]
        print(String(decoding:try JSONSerialization.data(withJSONObject:result,options:[.sortedKeys]),as:UTF8.self))
    }
}
