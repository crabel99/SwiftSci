import Foundation

@main struct CursorChecks {
    static func main() {
        var fixtures = ["", "a,b\n", "a,b\n1\n2,3\n\n4,5,6", "a,b\n1,", "a,b\n\"first\nsecond\",z\n"]
        for width in [1,2,7,17,16383,16384,16385] {
            let row = (0..<width).map { "\"\($0)\"" }.joined(separator:",")
            fixtures.append(Array(repeating:row,count:width>100 ? 4 : 40001).joined(separator:"\n"))
            fixtures.append(row+"\n\"x\"\n"+row+",")
        }
        var checked = 0
        for text in fixtures {
            let bytes = Array(text.utf8)
            bytes.withUnsafeBufferPointer { buffer in
                let index = SystemsCSVParser().parseIndex(buffer:buffer)
                for column in [0,1,2,6,16,16383,16384] {
                    for start in [0,min(1,index.count),max(0,index.count/2),index.count] {
                        var cursor = index.columnCursor(column:column,startRow:start)
                        for row in start..<index.count {
                            let a=cursor.next(), b=index.field(row:row,column:column)
                            precondition(a?.startOffset==b?.startOffset && a?.length==b?.length && a?.escapedQuotesPresent==b?.escapedQuotesPresent)
                            checked += 1
                        }
                        precondition(cursor.next()==nil)
                    }
                }
            }
        }
        print("PASS: \(checked) cursor offsets across \(fixtures.count) ragged, empty, wide and block-boundary inputs")
    }
}
