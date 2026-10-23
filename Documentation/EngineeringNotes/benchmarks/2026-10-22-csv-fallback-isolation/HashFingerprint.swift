import Foundation
let result: [String: Any] = ["values":["missing-0".hashValue,"ordinary-value".hashValue],"fixed":ProcessInfo.processInfo.environment["SWIFT_DETERMINISTIC_HASHING"] ?? "unset"]
print(String(decoding:try JSONSerialization.data(withJSONObject:result,options:[.sortedKeys]),as:UTF8.self))
