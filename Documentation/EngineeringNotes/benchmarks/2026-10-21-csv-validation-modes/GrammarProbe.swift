import Foundation
import SwiftDataFrame
import CryptoKit

var hash = SHA256()
@MainActor func append(_ value: Int) {
    var bits = Int64(value).littleEndian
    withUnsafeBytes(of: &bits) { hash.update(bufferPointer: $0) }
}
var fixtures = 0
for delimiter: UInt8 in [44, 59, 10, 34, 0, 255] {
    for quote: UInt8 in [34, 39, 10, 44, 0] {
        var seed: UInt64 = 81_471
        let alphabet: [UInt8] = [65, 10, 13, 34, delimiter, quote]
        for length in 0..<1024 {
            var bytes = [UInt8]()
            for _ in 0..<(length % 97) {
                seed = seed &* 6_364_136_223_846_793_005 &+ 1
                bytes.append(alphabet[Int(seed >> 32) % alphabet.count])
            }
            bytes.withUnsafeBufferPointer { buffer in
                let rows = SystemsCSVParser(delimiterByte: delimiter, quoteByte: quote).parse(buffer: buffer)
                append(rows.count)
                for row in rows {
                    append(row.count)
                    for field in row {
                        append(field.startOffset); append(field.length)
                        append(field.escapedQuotesPresent ? 1 : 0)
                    }
                }
            }
            fixtures += 1
        }
    }
}
print("\(fixtures) \(hash.finalize().map { String(format: "%02x", $0) }.joined())")
