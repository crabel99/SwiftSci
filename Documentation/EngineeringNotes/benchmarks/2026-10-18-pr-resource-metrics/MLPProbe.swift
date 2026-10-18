import Foundation
import SwiftML
import SwiftPreprocessing
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

@MainActor @main struct MLPProbe {
    static var metadata = [String:String]()
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
        let result: [String:Any] = ["context":metadata,"validated":true,"arguments":Array(CommandLine.arguments.dropFirst()),"samples":records,
            "scope":"CPU and wall deltas include API call and result release, exclude independent full-output validation. Heap is malloc size in use, not retained capacity of all allocators. Peak is process high-water captured before validation." ]
        print(String(decoding:try JSONSerialization.data(withJSONObject:result,options:[.sortedKeys]),as:UTF8.self))
    }
    static func main() async throws {
        let a=Array(CommandLine.arguments.dropFirst());let n=Int(a[1])!,width=Int(a[2])!,reps=Int(a[3])!,memory=a[4]=="memory"
        let model=MLPRegressor(hiddenLayerSizes:[width,width/2],activation:.relu,maxIter:1,seed:42,requestedDevice:.cpu)
        let training=(0..<8).map { i in (0..<width).map { j in value(i,j)/1024 } }
        try await model.fit(features:training,targets:(0..<8).map { Double($0)/8 })
        let layers=await model.trainedLayers!
        let input=(0..<n).map { i in (0..<width).map { j in value(i,j)/1024 } }
        var expected=[Double]()
        for row in input {
            var x=row
            for (index,layer) in layers.enumerated() {
                var y=layer.b
                for j in 0..<layer.outDim {
                    for k in 0..<layer.inDim { y[j] += x[k]*layer.W[k*layer.outDim+j] }
                    if index < layers.count-1 { y[j]=max(0,y[j]) }
                }
                x=y
            }
            expected.append(x[0])
        }
        let bits = layers.flatMap { $0.W + $0.b }.map { $0.bitPattern }
        metadata["weights_hash"] = String(bits.reduce(UInt64(1469598103934665603)) { ($0 ^ $1) &* 1099511628211 })
        metadata["oracle_hash"] = String(expected.reduce(UInt64(1469598103934665603)) { ($0 ^ $1.bitPattern) &* 1099511628211 })
        try await run(reps:reps,memory:memory,operation:{try await model.predict(features:input)},validate:{ r in
            precondition(r.count==n)
            for i in 0..<n {precondition(r[i].isFinite && abs(r[i]-expected[i]) <= 1e-10*max(1,abs(expected[i])))}
        })
    }
}
