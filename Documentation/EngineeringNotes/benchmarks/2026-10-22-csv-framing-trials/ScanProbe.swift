import Foundation
import Darwin
import CryptoKit

func cpu() -> Int64 {
    var r = rusage()
    getrusage(RUSAGE_SELF, &r)
    return Int64(r.ru_utime.tv_sec + r.ru_stime.tv_sec) * 1_000_000_000
        + Int64(r.ru_utime.tv_usec + r.ru_stime.tv_usec) * 1_000
}

@main struct ScanProbe {
    static func main() throws {
        let args = CommandLine.arguments
        let data = try Data(contentsOf: URL(fileURLWithPath: args[1]), options: .alwaysMapped)
        let delimiter = UInt8(args[2])!
        let limit = Int(args[3])!
        var digest = SHA256()
        var digestBuffer = Data()
        func append(_ integer: Int) {
            var value = UInt64(integer).littleEndian
            withUnsafeBytes(of: &value) { digestBuffer.append(contentsOf: $0) }
            if digestBuffer.count >= 65536 {
                digest.update(data: digestBuffer)
                digestBuffer.removeAll(keepingCapacity: true)
            }
        }
        var totalCPU: Int64 = 0
        var batches = 0
        var rows = 0
        var fields = 0
        try data.withUnsafeBytes { raw in
            let buffer = raw.bindMemory(to: UInt8.self)
            let parser = SystemsCSVParser(delimiterByte: delimiter)
            var offset = 0
            while offset < buffer.count {
                let bytes = UnsafeBufferPointer(rebasing: buffer[offset...])
                let start = cpu()
                var batch: CSVRecordBatch? = try parser.scanBatch(buffer: bytes,
                    maximumRows: batches == 0 ? 1 : limit)
                totalCPU += cpu() - start
                guard !batch!.records.isEmpty else { break }
                let next = batch!.nextOffset
                for r in 0..<batch!.records.count {
                    let row = batch!.records.row(at: r)
                    append(row.count)
                    for field in row {
                        append(offset + field.startOffset)
                        append(field.length)
                        append(field.escapedQuotesPresent ? 1 : 0)
                    }
                    fields += row.count
                }
                rows += batch!.records.count
                batches += 1
                let releaseStart = withExtendedLifetime(batch) { cpu() }
                batch = nil
                totalCPU += cpu() - releaseStart
                offset += next
            }
        }
        digest.update(data: digestBuffer)
        let hash = digest.finalize().map { String(format: "%02x", $0) }.joined()
        let result: [String: Any] = ["cpu_ns": totalCPU, "rows":rows, "fields":fields,
            "batches":batches, "sha256":hash,
            "scope":"Batch framing and coordinate release, with first header scan limited to one row; mapping and full-coordinate digest excluded."]
        print(String(decoding: try JSONSerialization.data(withJSONObject: result, options: [.sortedKeys]), as: UTF8.self))
    }
}
