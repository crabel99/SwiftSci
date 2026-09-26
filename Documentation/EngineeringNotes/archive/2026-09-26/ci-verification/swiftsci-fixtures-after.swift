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
