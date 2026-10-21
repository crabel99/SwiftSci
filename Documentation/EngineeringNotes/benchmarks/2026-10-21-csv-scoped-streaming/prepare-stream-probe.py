from pathlib import Path
R=Path(__file__).resolve().parent
s=(R/'ResourceProbe.swift').read_text();s=s[:s.index('@MainActor @main struct ReferenceProbe')]
s+='''func checkedStream(_ stream: AsyncThrowingStream<DataFrame, any Error>, input: Input) async throws -> Bool {
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
        options.delimiter = Character(input.delimiter); options.nullValues = Set(input.null_tokens)
        options.maxRows = input.max_rows
        let mapping: [String: ColumnDType] = ["String":.utf8,"Double":.float64,"Int64":.int64,"Date":.date32]
        options.columnTypeOverrides = Dictionary(uniqueKeysWithValues: zip(input.names, input.types).map { ($0.0,mapping[$0.1]!) })
        options.columnDateFormats = input.date_formats ?? (input.id.hasPrefix("energy-date-") ? ["Date": "d/M/yyyy"] : [:])
        let url = URL(fileURLWithPath: input.path)
        let r0 = resident(), p0 = peak(), h0 = heap(), c0 = cpu(), t0 = DispatchTime.now().uptimeNanoseconds
        let count = try await consume(DataFrame.readCSVStream(contentsOf: url, chunkSize: chunkSize, options: options))
        let t1 = DispatchTime.now().uptimeNanoseconds, c1 = cpu(), h1 = heap(), p1 = peak(), r1 = resident()
        let valid = try await checkedStream(DataFrame.readCSVStream(contentsOf: url, chunkSize: chunkSize, options: options), input: input)
        let result: [String: Any] = ["validated":valid && count == input.rows,"rows":count,"input":input.id,"chunk_size":chunkSize,
            "total_ns":Int64(t1-t0),"total_cpu_ns":c1-c0,"rss_before_bytes":r0,"rss_after_bytes":r1,"rss_growth_bytes":r1-r0,
            "peak_before_bytes":p0,"peak_after_bytes":p1,"heap_before_bytes":h0,"heap_after_bytes":h1,
            "scope":"One public stream consumed and released, no consumer retention, exact row count; separate untimed repeat verifies native types and all per-column value/null hashes. Peak captured before validation. Includes source mapping, framing, conversion, per-chunk scheduling and output release."]
        print(String(decoding:try JSONSerialization.data(withJSONObject:result,options:[.sortedKeys]),as:UTF8.self))
    }
}
'''
(R/'StreamProbe.swift').write_text(s)
