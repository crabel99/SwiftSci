        let keys: [Int64?] = (0..<257).map { (index: Int) -> Int64? in
            if index % 13 == 0 { return nil }
            let offset = Int64(index % 17)
            return 9_007_199_254_740_992 + offset
        }
        var values: [Double?] = (0..<2_049).map { (index: Int) -> Double? in
            if index % 19 == 0 { return nil }
            let remainder = (index * 37) % 101
            return Double(remainder)
        }
        let second: [Int64?] = (0..<64).map { (index: Int) -> Int64? in
            if index % 7 == 0 { return nil }
            let offset = Int64((index / 3) % 2)
            return Int64.min + offset
        }
precondition(keys.count == 257)
precondition(values.count == 2049)
precondition(second.count == 64)
for i in keys.indices { precondition(keys[i] == (i % 13 == 0 ? nil : 9_007_199_254_740_992 + Int64(i % 17))) }
for i in values.indices { let expected: Double? = i % 19 == 0 ? nil : Double((i * 37) % 101); precondition(values[i] == expected) }
for i in second.indices { let expected: Int64? = i % 7 == 0 ? nil : Int64.min + Int64((i / 3) % 2); precondition(second[i] == expected) }
print("All 2370 fixture values match the original formulas")
