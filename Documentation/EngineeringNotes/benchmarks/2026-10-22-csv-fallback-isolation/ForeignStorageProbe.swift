import Foundation
let units = [unichar](repeating: 0x0100, count: 128)
let cocoa = units.withUnsafeBufferPointer { p in NSString(characters: p.baseAddress!, length: p.count) }
let bridged = cocoa as String
let mutable = NSMutableString(string: String(repeating: "Ā", count:128))
let copied = mutable as String
let rows: [[String: Any]] = [["source":"NSString UTF16","native_utf8":bridged.isContiguousUTF8,"utf8_bytes":bridged.utf8.count], ["source":"NSMutableString","native_utf8":copied.isContiguousUTF8,"utf8_bytes":copied.utf8.count]]
print(String(decoding:try JSONSerialization.data(withJSONObject:rows,options:[.sortedKeys]),as:UTF8.self))
