let keys: [Int64?] = (0..<257).map { $0 % 13 == 0 ? nil : Int64($0 % 17) + 9_007_199_254_740_992 }
var values: [Double?] = (0..<2_049).map { $0 % 19 == 0 ? nil : Double(($0 * 37) % 101) }
let second: [Int64?] = (0..<64).map { $0 % 7 == 0 ? nil : Int64.min + Int64(($0 / 3) % 2) }
