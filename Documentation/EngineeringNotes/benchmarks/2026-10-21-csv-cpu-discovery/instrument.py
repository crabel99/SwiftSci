from pathlib import Path
import shutil,json
r=Path(__file__).resolve().parent;source=Path('/private/tmp/swiftsci-csv-eager-count-probe-20261021')
s=r/'instrumented';shutil.copytree(source/'Sources/SwiftDataFrame',s/'Sources/SwiftDataFrame',dirs_exist_ok=True)
for f in ['build.py','ResourceProbe.swift']:
 shutil.copy2(Path('/private/tmp/swiftsci-csv-eager-checks-20261021')/f,r/f)
(r/'variants.json').write_text(json.dumps({'profile':{'path':str(s),'pr':None}},indent=2)+'\n')
p=s/'Sources/SwiftDataFrame/IO/CSVEagerReader.swift';t=p.read_text()
t=t.replace('let first = try parser.scanBatch(buffer: buffer, maximumRows: 1)', 'let first = try CSVCPUProfile.measure("header") { try parser.scanBatch(buffer: buffer, maximumRows: 1) }')
t=t.replace('let batch = try parser.scanBatch(buffer: bytes, maximumRows: min(batchRows, remaining))', 'let batch = try CSVCPUProfile.measure("framing") { try parser.scanBatch(buffer: bytes, maximumRows: min(batchRows, remaining)) }',1)
t=t.replace('            var retry = [Int]()','            let finishStart = CSVCPUProfile.cpu()\n            var retry = [Int]()').replace('            active = retry','            CSVCPUProfile.add("finish", since: finishStart)\n            active = retry')
t=t.replace('        return try DataFrame(columns: completed.map {','        let result = try CSVCPUProfile.measure("dataframe") { try DataFrame(columns: completed.map {').replace('            return column\n        })','            return column\n        }) }\n        CSVCPUProfile.emit()\n        return result')
t=t.replace('        var rows = 0\n        var offset = 0','        let start = CSVCPUProfile.cpu()\n        defer { CSVCPUProfile.add("count", since: start) }\n        var rows = 0\n        var offset = 0')
t=t.replace('let batch = try parser.scanBatch(buffer: source, maximumRows: limit)','let batch = try CSVCPUProfile.measure("framing") { try parser.scanBatch(buffer: source, maximumRows: limit) }')
t=t.replace('        let plans = headers.enumerated().map', '        let planStart = CSVCPUProfile.cpu()\n        let plans = headers.enumerated().map').replace('        let attempts: [CSVColumnConversion?] = plans.map', '        CSVCPUProfile.add("plans", since: planStart)\n        let attemptsStart = CSVCPUProfile.cpu()\n        let attempts: [CSVColumnConversion?] = plans.map',1).replace('        append(buffer: source','        CSVCPUProfile.add("attempt-setup", since: attemptsStart)\n        append(buffer: source',1)
t=t.replace('        let input = BatchInput(buffer: buffer, attempts: attempts)','        let start = CSVCPUProfile.cpu()\n        defer { CSVCPUProfile.add("append", since: start) }\n        let input = BatchInput(buffer: buffer, attempts: attempts)')
p.write_text(t)
(s/'Sources/SwiftDataFrame/IO/CSVCPUProfile.swift').write_text('''import Foundation
import Darwin

// [CSV-CPU-20261021] Diagnostic overlay only; one joined coordinator writes.
internal enum CSVCPUProfile {
    nonisolated(unsafe) static var elapsed = [String: Int64]()
    nonisolated(unsafe) static var calls = [String: Int]()
    static func cpu() -> Int64 {
        var t = timespec()
        clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &t)
        return Int64(t.tv_sec) * 1_000_000_000 + Int64(t.tv_nsec)
    }
    static func add(_ key: String, since start: Int64) {
        elapsed[key, default: 0] += cpu() - start
        calls[key, default: 0] += 1
    }
    static func measure<T>(_ key: String, _ body: () throws -> T) rethrows -> T {
        let start = cpu()
        defer { add(key, since: start) }
        return try body()
    }
    static func emit() {
        let record: [String: Any] = ["tag": "CSV-CPU-20261021", "cpu_ns": elapsed, "calls": calls]
        let bytes = try! JSONSerialization.data(withJSONObject: record, options: [.sortedKeys])
        FileHandle.standardError.write(bytes + Data([10]))
        elapsed = [:]
        calls = [:]
    }
}
''')
