import Foundation
import SwiftDataFrame
import Darwin

func cpu() -> Int64 {
    var r = rusage(); getrusage(RUSAGE_SELF, &r)
    return Int64(r.ru_utime.tv_sec + r.ru_stime.tv_sec) * 1_000_000_000 + Int64(r.ru_utime.tv_usec + r.ru_stime.tv_usec) * 1_000
}
func heap() -> UInt64 {
    var s = malloc_statistics_t(); malloc_zone_statistics(nil, &s)
    return UInt64(s.size_in_use)
}
func peak() -> Int64 { var r = rusage(); getrusage(RUSAGE_SELF, &r); return Int64(r.ru_maxrss) }
func value(_ row: Int, _ col: Int) -> Double { Double((row * 17 + col * 31) % 1009) + 0.5 }

@MainActor @main struct ResourceProbe {
    static func run<T>(reps: Int, memory: Bool, operation: @MainActor () async throws -> T, validate: @MainActor (T) -> Void) async throws {
        var records = [[String: Int64]]()
        let repeats = memory ? 1 : reps + 2
        for i in 0..<repeats {
            let heapBefore = heap(), peakBefore = peak()
            let c0 = cpu(), t0 = DispatchTime.now().uptimeNanoseconds
            var output: T? = try await operation()
            let t1 = DispatchTime.now().uptimeNanoseconds, c1 = cpu()
            let heldHeap = heap(), peakHeld = peak()
            validate(output!)
            let c2 = cpu(), t2 = DispatchTime.now().uptimeNanoseconds
            output = nil
            let t3 = DispatchTime.now().uptimeNanoseconds, c3 = cpu()
            if memory || i >= 2 {
                records.append(["call_ns":Int64(t1-t0),"call_cpu_ns":c1-c0,"release_ns":Int64(t3-t2),"release_cpu_ns":c3-c2,
                    "total_ns":Int64(t1-t0+t3-t2),"total_cpu_ns":c1-c0+c3-c2,"heap_before_bytes":Int64(heapBefore),
                    "held_heap_bytes":Int64(heldHeap),"held_heap_delta_bytes":Int64(heldHeap)-Int64(heapBefore),"heap_after_release_bytes":Int64(heap()),
                    "process_peak_before_bytes":peakBefore,"process_peak_held_bytes":peakHeld])
            }
        }
        let result: [String:Any] = ["validated":true,"arguments":Array(CommandLine.arguments.dropFirst()),"samples":records,
            "scope":"CPU and wall deltas include API call and result release, exclude independent full-output validation. Heap is malloc size in use, not retained capacity of all allocators. Peak is process high-water captured before validation." ]
        print(String(decoding:try JSONSerialization.data(withJSONObject:result,options:[.sortedKeys]),as:UTF8.self))
    }
    static func main() async throws {
        let a=Array(CommandLine.arguments.dropFirst());let mode=a[0],n=Int(a[1])!,width=Int(a[2])!,reps=Int(a[3])!,memory=a[4]=="memory"
        let names=(0..<width).map { "c\($0)" }
        if mode == "csv" || mode == "csv-quoted" {
            let url=URL(fileURLWithPath:a[5])
            try await run(reps:reps,memory:memory,operation:{try await DataFrame(csv:url)},validate:{ df in
                precondition(df.shape.rows==n && df.columnNames==names)
                for j in 0..<width { let c=df[column:names[j],as:Double.self]!;for i in 0..<n { precondition(c[i]==value(i,j)) } }
            });return
        }
        let frame=try DataFrame(columns:(0..<width).map { j in TypedColumn<Double>(name:names[j],values:(0..<n).map { Optional(value($0,j)) }) as any AnyColumn })
        if mode == "target" {
            try await run(reps:reps,memory:memory,operation:{try frame.toTargetVector(names[0])},validate:{ r in
                precondition(r.count==n);for i in 0..<n { precondition(r[i]==value(i,0)) }
            });return
        }
        if mode == "matrix" {
            try await run(reps:reps,memory:memory,operation:{try frame.toFlatFeatureMatrix(names)},validate:{ r in
                precondition(r.rows==n && r.cols==width);for i in 0..<n { for j in 0..<width {precondition(r.flat[i*width+j]==value(i,j))} }
            });return
        }
        let indices=(0..<n).filter { $0 % 3 != 0 }.reversed().map { $0 }
        if mode == "gather" {
            try await run(reps:reps,memory:memory,operation:{frame.gathered(at:indices)},validate:{r in
                precondition(r.shape.rows==indices.count && r.columnNames==names)
                for j in 0..<width { let c=r[column:names[j],as:Double.self]!;for i in indices.indices {precondition(c[i]==value(indices[i],j))} }
            });return
        }
        #if HAS_COMPACT
        if mode == "compact-matrix" {
            let batch=try frame.prepareNumericBatch(names)
            try await run(reps:reps,memory:memory,operation:{try batch.selectingRows(indices).matrix()},validate:{r in
                precondition(r.rowCount==indices.count && r.columnCount==width)
                r.values.withUnsafeBufferPointer { b in for i in indices.indices {for j in 0..<width {precondition(b[i*width+j]==value(indices[i],j))}} }
            });return
        }
        #endif
        preconditionFailure("Unknown mode")
    }
}
