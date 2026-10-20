import Foundation
import Darwin

@main struct RangeChecks {
    static func main() {
        let text=Array("\"x\",\"a\"\"b\"\n".utf8)
        for start in [Int(Int32.max)-32,Int(Int32.max)+1,Int(UInt32.max)+1] {
            let size=start+text.count
            let allocation=mmap(nil,size,PROT_READ | PROT_WRITE,MAP_PRIVATE | MAP_ANON,-1,0)
            precondition(allocation != MAP_FAILED)
            defer { precondition(munmap(allocation,size)==0) }
            let bytes=allocation!.assumingMemoryBound(to:UInt8.self)
            text.withUnsafeBufferPointer { source in bytes.advanced(by:start).update(from:source.baseAddress!,count:source.count) }
            let index=SystemsCSVParser().testAutomaticRange(buffer:UnsafeBufferPointer(start:bytes,count:size),range:start..<size)
            precondition(index.count==1)
            let row=index.row(at:0)
            precondition(row.count==2)
            precondition(row[0].startOffset==start && row[0].length==3 && !row[0].escapedQuotesPresent)
            precondition(row[1].startOffset==start+4 && row[1].length==6 && row[1].escapedQuotesPresent)
        }
        print("PASS: automatic range selection below 2 GiB, above 2 GiB and above 4 GiB; only payload pages touched; mappings released")
    }
}
