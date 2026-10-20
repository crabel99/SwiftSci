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
@main struct IndexProbe {
    static func main() throws {
        let data = try Data(contentsOf:URL(fileURLWithPath:CommandLine.arguments[1]),options:.alwaysMapped)
        try data.withUnsafeBytes { raw in
            let bytes=raw.bindMemory(to:UInt8.self)
            var samples = [[String:Int64]]()
            var expected: Int? = nil
            for i in 0..<7 {
                let c0=cpu(),t0=DispatchTime.now().uptimeNanoseconds
                var index: CSVRecordIndex? = SystemsCSVParser().parseIndex(buffer:bytes)
                let t1=DispatchTime.now().uptimeNanoseconds,c1=cpu()
                let checksum=walk(index!,width:index!.row(at:0).count)
                if let expected { precondition(checksum==expected) } else { expected=checksum }
                let c2=cpu(),t2=DispatchTime.now().uptimeNanoseconds
                index=nil
                let t3=DispatchTime.now().uptimeNanoseconds,c3=cpu()
                if i>=2 { samples.append(["cpu_ns":c1-c0+c3-c2,"elapsed_ns":Int64(t1-t0+t3-t2),"build_cpu_ns":c1-c0,"release_cpu_ns":c3-c2]) }
            }
            let result:[String:Any] = ["checksum":expected!,"samples":samples]
            print(String(decoding:try JSONSerialization.data(withJSONObject:result,options:[.sortedKeys]),as:UTF8.self))
        }
    }
}
