import Foundation

@main struct CountParity {
    static func main() throws {
        var fixtures = 0
        var checks = 0
        func compare(_ bytes: [UInt8], delimiter: UInt8, quote: UInt8) throws {
            try bytes.withUnsafeBufferPointer { buffer in
                let parser = SystemsCSVParser(delimiterByte: delimiter, quoteByte: quote)
                let expected = parser.parseIndex(buffer: buffer, minimumParallelBytes: .max).count
                let actual = try parser.countRecords(buffer: buffer)
                precondition(actual == expected)
                checks += 1
                for limit in [0, 1, 2, 100] {
                    let limited = try parser.countRecords(buffer: buffer, maximumRows: limit)
                    precondition(limited == min(expected, limit))
                    checks += 1
                }
            }
            fixtures += 1
        }
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
                    try compare(bytes, delimiter: delimiter, quote: quote)
                }
            }
        }
        for length in [65_535, 65_536, 65_537] {
            try compare(Array(("\"" + String(repeating: "x", count: length) + "\ninside\",tail\r\nnext,row\n").utf8), delimiter: 44, quote: 34)
        }
        print("{\"fixtures\":\(fixtures),\"checks\":\(checks),\"passed\":true}")
    }
}
