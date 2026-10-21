import Foundation

@main struct FlatBorrowChecks {
    static func main() {
        var comparisons = 0
        for rows in [0, 1, 2, 257, 16385] {
            for width in [1, 4, 13] {
                var fields = [PackedCSVField]()
                var starts = [0]
                for row in 0..<rows {
                    let columns = row % 11 == 10 ? width - 1 : width
                    for column in 0..<columns {
                        fields.append(PackedCSVField(startOffset: row * 100 + column, length: column, escapedQuotesPresent: row % 2 == 0))
                    }
                    starts.append(fields.count)
                }
                let index = CSVRecordIndex(fields: fields, rowStarts: starts)
                let checked = index.withFlatFields { view in
                    for row in 0...rows {
                        for column in 0...width {
                            let a = view.field(row: row, column: column)
                            let b = index.field(row: row, column: column)
                            precondition(a?.startOffset == b?.startOffset && a?.length == b?.length && a?.escapedQuotesPresent == b?.escapedQuotesPresent)
                            comparisons += 1
                        }
                    }
                    return true
                }
                precondition(checked == true)
            }
        }
        let bytes = Array("a,b\n\"x\",\"y\"\n".utf8)
        bytes.withUnsafeBufferPointer { buffer in
            let index = SystemsCSVParser().parseIndex(buffer: buffer)
            precondition(index.withFlatFields { _ in true } == nil)
        }
        print("PASS: \(comparisons) flat borrowed/owning lookups, empty and ragged rows, compact fallback exclusion")
    }
}
