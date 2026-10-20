import Foundation
struct Field { var start: Int; var length: Int }
let n = Int(CommandLine.arguments[1])!
var fields = [Field](); fields.reserveCapacity(100_000)
var released: [UInt:String] = [:]
for i in 0..<(n*4+4) {
    if fields.count == fields.capacity {
        fields.withUnsafeBufferPointer { released[UInt(bitPattern:$0.baseAddress!)] = "\(fields.capacity)" }
    }
    fields.append(Field(start:i,length:1))
}
var columns = [[Double?]]()
for _ in 0..<4 {
    var column = [Double?](); column.reserveCapacity(n)
    column.append(1)
    column.withUnsafeBufferPointer { b in
        let address = UInt(bitPattern:b.baseAddress!)
        print("requested=\(n) granted=\(column.capacity) reused_parser_capacity=\(released[address] ?? "none")")
    }
    columns.append(column)
}
withExtendedLifetime((fields,columns)) { print("retained fields=\(fields.count) columns=\(columns.count)") }
