import Foundation
import Darwin

func cpu() -> Int64 {
    var r = rusage(); getrusage(RUSAGE_SELF, &r)
    return Int64(r.ru_utime.tv_sec + r.ru_stime.tv_sec) * 1_000_000_000 + Int64(r.ru_utime.tv_usec + r.ru_stime.tv_usec) * 1000
}
@inline(never) func walk(_ index: CSVRecordIndex, width: Int) -> Int {
    var result = 0
    for column in 0..<width {
        #if CURSOR
        var cursor = index.columnCursor(column: column, startRow: 1)
        #endif
        for row in 1..<index.count {
            #if CURSOR
            let offset = cursor.next()
            #else
            let offset = index.field(row: row, column: column)
            #endif
            if let offset {
                result &+= offset.startOffset &+ offset.length &+ (offset.escapedQuotesPresent ? 1 : 0)
            }
        }
    }
    return result
}
@main struct LookupProbe {
    static func main() throws {
        let a = CommandLine.arguments
        let data = try Data(contentsOf:URL(fileURLWithPath:a[1]),options:.alwaysMapped)
        try data.withUnsafeBytes { bytes in
            let index = SystemsCSVParser().parseIndex(buffer:bytes.bindMemory(to:UInt8.self))
            let width = index.row(at:0).count
            var samples = [[String:Int64]]()
            let expected = walk(index,width:width)
            for i in 0..<12 {
                let c0=cpu(),t0=DispatchTime.now().uptimeNanoseconds
                let value=walk(index,width:width)
                let t1=DispatchTime.now().uptimeNanoseconds,c1=cpu()
                precondition(value==expected)
                if i>=2 { samples.append(["cpu_ns":c1-c0,"elapsed_ns":Int64(t1-t0)]) }
            }
            let r:[String:Any] = ["checksum":expected,"rows":index.count,"width":width,"samples":samples]
            print(String(decoding:try JSONSerialization.data(withJSONObject:r,options:[.sortedKeys]),as:UTF8.self))
        }
    }
}
