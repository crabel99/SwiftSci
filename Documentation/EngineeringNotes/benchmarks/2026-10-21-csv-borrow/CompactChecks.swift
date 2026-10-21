import Foundation

@main struct CompactChecks {
    static func main() {
        precondition(MemoryLayout<CompactCSVField>.stride == 8)
        precondition(MemoryLayout<PackedCSVField>.stride == 16)
        let limit = Int(Int32.max)
        for offset in [0,1,limit-1,limit] { precondition(CompactCSVField.canRepresent(endOffset:offset)) }
        for offset in [-1,limit+1,Int(UInt32.max),Int.max] { precondition(!CompactCSVField.canRepresent(endOffset:offset)) }
        for start in [0,1,limit] {
            for length in [0,1,limit] {
                for escaped in [false,true] {
                    let value=CompactCSVField(startOffset:start,length:length,escapedQuotesPresent:escaped).offset
                    precondition(value.startOffset==start && value.length==length && value.escapedQuotesPresent==escaped)
                }
            }
        }
        for start in [limit+1,Int(UInt32.max)+1,Int.max-1] {
            let value=PackedCSVField(startOffset:start,length:1,escapedQuotesPresent:true).offset
            precondition(value.startOffset==start && value.length==1 && value.escapedQuotesPresent)
        }
        var cases=["", "a,b\n1\n2,3\n\n4,5,6", "a,b\n1,", "a,b\n\"first\nsecond\",\"x\"\"y\"\n"]
        for width in [1,2,7,16383,16384,16385] {
            let row=Array(repeating:"\"x\"",count:width).joined(separator:",")
            cases.append(Array(repeating:row,count:width>100 ? 4 : 20001).joined(separator:"\n"))
            cases.append(row+"\n1\n"+row+",")
        }
        var checked=0
        for text in cases {
            let bytes=Array(text.utf8)
            bytes.withUnsafeBufferPointer { buffer in
                let parser=SystemsCSVParser()
                let compact=parser.scanIndex(buffer:buffer,range:0..<buffer.count,fieldType:CompactCSVField.self)
                let wide=parser.scanIndex(buffer:buffer,range:0..<buffer.count,fieldType:PackedCSVField.self)
                let selected=parser.parseIndex(buffer:buffer)
                precondition(compact.rowStarts==wide.rowStarts && compact.rowStarts==selected.rowStarts)
                for row in 0..<wide.count {
                    let expected=wide.row(at:row)
                    for column in 0...expected.count {
                        let a=compact.field(row:row,column:column),b=wide.field(row:row,column:column),c=selected.field(row:row,column:column)
                        precondition(a?.startOffset==b?.startOffset && a?.length==b?.length && a?.escapedQuotesPresent==b?.escapedQuotesPresent)
                        precondition(a?.startOffset==c?.startOffset && a?.length==c?.length && a?.escapedQuotesPresent==c?.escapedQuotesPresent)
                        let d = compact.withCompactFields { view in view.field(row: row, column: column) }!
                        precondition(a?.startOffset==d?.startOffset && a?.length==d?.length && a?.escapedQuotesPresent==d?.escapedQuotesPresent)
                        checked+=1
                    }
                }
            }
        }
        print("PASS: 8-byte compact / 16-byte wide; selection boundaries; escaped-length boundaries; wide offsets above 4 GiB; \(checked) compact/wide/automatic/borrowed field comparisons across \(cases.count) inputs")
    }
}
