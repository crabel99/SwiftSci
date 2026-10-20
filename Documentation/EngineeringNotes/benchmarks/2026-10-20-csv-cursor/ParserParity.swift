import Foundation
import SwiftDataFrame
import CryptoKit

@main struct ParserParity {
    static func main() throws {
        var state: UInt64 = 0xCA5E
        func next() -> UInt64 {
            state = state &* 6364136223846793005 &+ 1442695040888963407
            return state
        }
        var cases = ["", "a,", "a,b,", "a\n", "\r\n", "\"a", "\"a\"\"", "a,b\n1,", "\"\",x\n"]
        let alphabet = Array("ab,\"\r\n012".utf8)
        for _ in 0..<2000 {
            cases.append(String(decoding:(0..<Int(next() % 513)).map { _ in alphabet[Int(next() % UInt64(alphabet.count))] },as:UTF8.self))
        }
        for fields in [16383,16384,16385,32767,32768,32769] {
            cases.append(Array(repeating:"\"x\"",count:fields).joined(separator:",")+"\n")
            cases.append(Array(repeating:"\"x\"",count:fields).joined(separator:",")+",")
        }
        cases.append("a,b\n\""+String(repeating:"x",count:2_000_000)+"\",\"z\"\n")
        var digest = SHA256()
        var total = 0
        for text in cases {
            let bytes = Array(text.utf8)
            let rows = bytes.withUnsafeBufferPointer { SystemsCSVParser().parse(buffer:$0) }
            let values = rows.map { row in row.map { [$0.startOffset,$0.length,$0.escapedQuotesPresent ? 1 : 0] } }
            digest.update(data:try JSONSerialization.data(withJSONObject:values,options:[.sortedKeys]))
            total += rows.reduce(0) { $0 + $1.count }
        }
        print("cases=\(cases.count) fields=\(total) sha256=\(digest.finalize().map { String(format:"%02x",$0) }.joined())")
    }
}
