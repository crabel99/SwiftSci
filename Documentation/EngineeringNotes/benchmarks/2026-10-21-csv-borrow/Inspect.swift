import Foundation
import SwiftDataFrame
@main struct Inspect {
 static func main() async throws {
  let f = try await DataFrame(csv:URL(fileURLWithPath:CommandLine.arguments[1]))
  let columns = f.columns.map { c -> [String:Any] in
   let v = (c as! TypedColumn<Double>).values
   return ["name":c.name,"count":v.count,"capacity":v.capacity,"element_stride":MemoryLayout<Double?>.stride]
  }
  print(String(decoding:try JSONSerialization.data(withJSONObject:columns,options:[.sortedKeys]),as:UTF8.self))
 }
}
