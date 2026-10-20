import Foundation
import SwiftDataFrame
import Darwin

@main struct SortAlgorithmTrial {
  static func check(_ output: DataFrame, source: DataFrame, indices: [Int]) {
    precondition(output.columnNames == source.columnNames)
    for (original, result) in zip(source.columns, output.columns) {
      precondition(original.dtype == result.dtype && result.count == indices.count)
      func exact<T: SupportedType>(_ c: TypedColumn<T>, _ r: TypedColumn<T>) {
        var missing = 0
        for i in indices.indices {
          precondition(r.values[i] == c.values[indices[i]])
          if r.values[i] == nil { missing += 1 }
        }
        precondition(r.nullCount == missing)
      }
      if let c = original as? TypedColumn<Double>, let r = result as? TypedColumn<Double> {
        for i in indices.indices { precondition(r.values[i]?.bitPattern == c.values[indices[i]]?.bitPattern) }
        precondition(r.nullCount == indices.reduce(0) { $0 + (c.values[$1] == nil ? 1 : 0) })
      } else if let c = original as? TypedColumn<Int64>, let r = result as? TypedColumn<Int64> { exact(c,r)
      } else if let c = original as? TypedColumn<String>, let r = result as? TypedColumn<String> { exact(c,r)
      } else if let c = original as? TypedColumn<Bool>, let r = result as? TypedColumn<Bool> { exact(c,r)
      } else if let c = original as? TypedColumn<Date>, let r = result as? TypedColumn<Date> { exact(c,r)
      } else { preconditionFailure("Unsupported validation type") }
    }
  }
  static func main() throws {
    let a = Array(CommandLine.arguments.dropFirst())
    let mode = a[0], n = Int(a[1])!, width = Int(a[2])!, pattern = a[3], layout = a[4]
    let ascending = a[5] == "asc", seed = UInt64(a[6])!, repetitions = Int(a[7])!
    var state: UInt64 = seed
    let values: [Double?] = (0..<n).map { i in
      state = state &* 6364136223846793005 &+ 1442695040888963407
      if pattern == "nulls" && i % 7 == 0 { return nil }
      if pattern == "sparse" && i % 101 != 0 { return nil }
      switch pattern {
      case "identity": return Double(i)
      case "reverse": return Double(n-i)
      case "ties": return Double((state >> 32) % 101)
      default: return Double(state >> 11) * 0x1p-53 - 0.5
      }
    }
    var columns: [any AnyColumn] = [TypedColumn<Double>(name: "key", values: values)]
    for j in 1..<width {
      let name = "v\(j)"
      if layout == "dates" {
        columns.append(TypedColumn<Date>(name:name, values:(0..<n).map { $0 % 29 == 0 ? nil : Date(timeIntervalSince1970:Double($0)) }))
      } else if layout == "mixed" && j % 3 == 1 {
        columns.append(TypedColumn<String>(name: name, values: (0..<n).map { $0 % 19 == 0 ? nil : "row-\($0)-longer-than-inline-string" }))
      } else if layout == "mixed" && j % 3 == 2 {
        columns.append(TypedColumn<Bool>(name: name, values: (0..<n).map { $0 % 23 == 0 ? nil : $0 % 2 == 0 }))
      } else { columns.append(TypedColumn<Int64>(name: name, values: (0..<n).map { Int64($0) })) }
    }
    let frame = try DataFrame(columns: columns)
    let expected = values.indices.sorted { i, j in
      switch (values[i],values[j]) {
      case (nil,nil): return i < j
      case (nil,_): return false
      case (_,nil): return true
      case let (x?,y?): return x == y ? i < j : ascending ? x < y : x > y
      }
    }
    func cpu() -> Int64 {
      var u = rusage(); getrusage(RUSAGE_SELF, &u)
      return Int64(u.ru_utime.tv_sec + u.ru_stime.tv_sec) * 1_000_000_000 + Int64(u.ru_utime.tv_usec + u.ru_stime.tv_usec) * 1_000
    }
    func heap() -> Int64 { var s = malloc_statistics_t(); malloc_zone_statistics(nil, &s); return Int64(s.size_in_use) }
    func peak() -> Int64 { var u = rusage(); getrusage(RUSAGE_SELF, &u); return Int64(u.ru_maxrss) }
    let memory = a[8] == "memory"
    var records = [[String:Int64]]()
    for step in 0..<(memory ? 1 : repetitions+2) {
      let h0 = heap(), p0 = peak(), c0 = cpu(), t0 = DispatchTime.now().uptimeNanoseconds
      var output: DataFrame? = mode == "gather" ? frame.gathered(at: expected) : try frame.sortBy("key", ascending: ascending)
      let t1 = DispatchTime.now().uptimeNanoseconds, c1 = cpu(), h1 = heap(), p1 = peak()
      check(output!, source: frame, indices: expected)
      let c2 = cpu(), t2 = DispatchTime.now().uptimeNanoseconds
      output = nil
      let t3 = DispatchTime.now().uptimeNanoseconds, c3 = cpu(), h2 = heap()
      if memory || step >= 2 {
        records.append(["total_ns":Int64(t1-t0+t3-t2),"total_cpu_ns":c1-c0+c3-c2,
          "call_ns":Int64(t1-t0),"call_cpu_ns":c1-c0,"release_ns":Int64(t3-t2),"release_cpu_ns":c3-c2,
          "heap_before_bytes":h0,"held_heap_delta_bytes":h1-h0,"heap_after_release_bytes":h2,
          "process_peak_before_bytes":p0,"process_peak_held_bytes":p1])
      }
    }
    let result: [String:Any] = ["arguments":a,"samples":records,"validated":true,
      "index_sha":String(expected.reduce(UInt64(0)) { ($0 ^ UInt64($1)) &* 1099511628211 })]
    print(String(decoding:try JSONSerialization.data(withJSONObject:result,options:[.sortedKeys]),as:UTF8.self))
  }
}
