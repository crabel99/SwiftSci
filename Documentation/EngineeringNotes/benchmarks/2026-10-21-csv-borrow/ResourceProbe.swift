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
        let parts = mode.split(separator: "-")
        precondition(parts.count == 2)
        let kind = String(parts[0])
        let options = options(kind: kind, known: parts[1] == "known", width: width)
        try await run(reps: reps, memory: memory,
            operation: { try await DataFrame(csv: URL(fileURLWithPath: a[5]), options: options) },
            validate: { validate($0, kind: kind, rows: n, width: width) })
    }
    static func options(kind: String, known: Bool, width: Int) -> CSVReadOptions {
        var options = CSVReadOptions()
        if known {
            let types: [ColumnDType]
            switch kind {
            case "mixed": types = [.int64, .float64, .boolean, .utf8]
            case "missing": types = Array(repeating: .float64, count: width)
            case "text": types = [.int64, .utf8]
            case "dates": types = [.int64, .date32]
            default: preconditionFailure("Unknown fixture")
            }
            options.columnTypeOverrides = Dictionary(uniqueKeysWithValues: types.enumerated().map { ("c\($0.offset)", $0.element) })
        }
        return options
    }
    static func validate(_ df: DataFrame, kind: String, rows n: Int, width: Int) {
        precondition(df.shape.rows == n && df.columnNames == (0..<width).map { "c\($0)" })
        switch kind {
        case "mixed":
            let integers = df[column: "c0", as: Int64.self]!
            let doubles = df[column: "c1", as: Double.self]!
            let bools = df[column: "c2", as: Bool.self]!
            let strings = df[column: "c3", as: String.self]!
            for i in 0..<n {
                precondition(integers[i] == (i % 11 == 0 ? nil : Int64(i - 10000)))
                precondition(doubles[i] == ((i + 1) % 11 == 0 ? nil : value(i, 0)))
                precondition(bools[i] == ((i + 2) % 11 == 0 ? nil : i % 2 == 0))
                precondition(strings[i] == ((i + 3) % 11 == 0 || i % 37 == 0 ? nil : "station-\(i % 97)"))
            }
        case "missing":
            for j in 0..<width {
                let column = df[column: "c\(j)", as: Double.self]!
                for i in 0..<n { precondition(column[i] == ((i + j) % 11 == 0 ? nil : value(i, j))) }
            }
        case "text":
            let ids = df[column: "c0", as: Int64.self]!
            let strings = df[column: "c1", as: String.self]!
            let prefix = "prefix, \"quoted\"\n" + String(repeating: "abcdefgh", count: 1024)
            for i in 0..<n {
                precondition(ids[i] == Int64(i))
                precondition(strings[i] == prefix + "-\(i)")
            }
        case "dates":
            let ids = df[column: "c0", as: Int64.self]!
            let dates = df[column: "c1", as: Date.self]!
            var calendar = Calendar(identifier: .gregorian)
            calendar.timeZone = TimeZone(secondsFromGMT: 0)!
            for i in 0..<n {
                precondition(ids[i] == Int64(i))
                precondition(dates[i] == calendar.date(from: DateComponents(year: 2026, month: 1, day: i % 28 + 1)))
            }
        default: preconditionFailure("Unknown fixture")
        }
    }
}
