import Foundation
import SwiftDataFrame
@main struct Semantics {
 static func main() async throws {
  let cases: [(String,String,[[String?]])] = [
   ("quoted", "a,b\n\"alpha\",\"beta\"\n", [["alpha"],["beta"]]),
   ("escaped", "a,b\n\"a \"\"quoted\"\" word\",\"x\"\n", [["a \"quoted\" word"],["x"]]),
   ("multiline", "a,b\n\"first\nsecond\",\"x\"\n", [["first\nsecond"],["x"]]),
   ("crlf", "a,b\r\n\"alpha\",\"beta\"\r\n", [["alpha"],["beta"]]),
   ("comma", "a,b\n\"alpha,beta\",\"x\"", [["alpha,beta"],["x"]]),
   ("empty", "a,b\n\"\",\"x\"\n", [[nil],["x"]]),
   ("two-rows", "a,b\n\"alpha\",\"beta\"\n\"gamma\",\"delta\"\n", [["alpha","gamma"],["beta","delta"]])
  ]
  let root=FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
  try FileManager.default.createDirectory(at:root,withIntermediateDirectories:true)
  defer { try? FileManager.default.removeItem(at:root) }
  for (name,text,expected) in cases {
   let path=root.appendingPathComponent(name+".csv");try text.write(to:path,atomically:true,encoding:.utf8)
   var options=CSVReadOptions();options.inferTypes=false
   let df=try await DataFrame(csv:path,options:options)
   precondition(df.columnNames == ["a","b"])
   for (i,column) in df.columns.enumerated() { precondition((column as! TypedColumn<String>).values == expected[i]) }
  }
  print("PASS: 7 explicit CSV semantic fixtures")
 }
}
