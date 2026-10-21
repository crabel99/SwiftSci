import Foundation
let patterns = ["d/M/yyyy", "dd/MM/yyyy", "M/d/yyyy", "MM/dd/yyyy", "yyyy-MM-dd", "yyyy/M/d", "d.M.yyyy", "yyyy-d-M"]
var checked = 0
var converted = 0
for pattern in patterns {
    let formatter = DateFormatter()
    formatter.locale = Locale(identifier: "en_US_POSIX")
    formatter.calendar = Calendar(identifier: .gregorian)
    formatter.timeZone = TimeZone(secondsFromGMT: 0)
    formatter.dateFormat = pattern
    formatter.isLenient = false
    let numeric = CSVNumericDateFormat(pattern)!
    let fields = pattern.split(whereSeparator: { "/-.".contains($0) })
    let separators = pattern.filter { "/-.".contains($0) }.map(String.init)
    for year in [1600, 1700, 1900, 1969, 1970, 1999, 2000, 2024, 2100, 9999] {
        for month in 1...12 {
            for day in [0, 1, 28, 29, 30, 31, 32] {
                var text = ""
                for index in fields.indices {
                    let value = fields[index].first == "y" ? year : fields[index].first == "M" ? month : day
                    let width = fields[index].count
                    text += String(repeating: "0", count: max(0, width - String(value).count)) + String(value)
                    if index < 2 { text += separators[index] }
                }
                let bytes = Array(text.utf8)
                let result = bytes.withUnsafeBufferPointer { numeric.parse(buffer: $0, range: $0.indices) }
                let expected = formatter.date(from: text)
                precondition(result == expected, "\(pattern):\(text): \(String(describing: result)) != \(String(describing: expected))")
                checked += 1
                if result != nil { converted += 1 }
            }
        }
    }
}
print("PASS \(checked) Foundation parity checks, \(converted) successful direct conversions")
