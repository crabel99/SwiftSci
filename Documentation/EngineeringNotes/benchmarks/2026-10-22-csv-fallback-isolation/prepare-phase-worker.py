from pathlib import Path
import json,subprocess,hashlib
R=Path(__file__).resolve().parent;P=Path('/private/tmp/swiftsci-csv-prefix-selection-20261022')
s=(R/'ResourceProbe.swift').read_text();s=s[:s.index('@MainActor @main struct ReferenceProbe')]
s+='''@MainActor @main struct PreparationProbe {
    static func main() async throws {
        let args = Array(CommandLine.arguments.dropFirst())
        let input = try JSONDecoder().decode(Input.self, from: Data(contentsOf: URL(fileURLWithPath: args[0])))
        let action = args[1], rows = Int(args[2])!, repetitions = Int(args[3])!
        let tokens = Set(input.null_tokens)
        var checksum = 0
        var readCPU: Int64 = 0, readWall: UInt64 = 0
        var expected: Bool? = nil
        if action == "factory" || action == "prefix" {
            let first: Any? = action == "factory" ? CSVPreparationDiagnostics.makeAttempt(nullValues: tokens, selectedRows: rows) : CSVPreparationDiagnostics.makePrefix(nullValues: tokens, selectedRows: rows)
            expected = first != nil
            withExtendedLifetime(first) {}
            let c0 = cpu(), t0 = DispatchTime.now().uptimeNanoseconds
            if action == "factory" {
                for _ in 0..<repetitions {
                    let value = CSVPreparationDiagnostics.makeAttempt(nullValues: tokens, selectedRows: rows)
                    withExtendedLifetime(value) {}
                    checksum += 1
                }
            } else {
                for _ in 0..<repetitions {
                    let value = CSVPreparationDiagnostics.makePrefix(nullValues: tokens, selectedRows: rows)
                    if value != nil { checksum += 1 }
                    withExtendedLifetime(value) {}
                }
            }
            readWall = DispatchTime.now().uptimeNanoseconds - t0
            readCPU = cpu() - c0
            precondition(checksum == (expected! ? repetitions : 0))
        } else {
            precondition(action == "hash")
            var options = CSVReadOptions()
            options.nullValues = []
            options.columnTypeOverrides = Dictionary(uniqueKeysWithValues: input.names.map { ($0, ColumnDType.utf8) })
            let frame = try await DataFrame(csv: URL(fileURLWithPath: input.path), options: options)
            precondition(frame.rowCount == input.rows)
            let values: [[String]] = input.names.map { name in
                frame[column: name, as: String.self]!.values.map { value in
                    guard let value else { fatalError("Missing raw String field") }
                    return value
                }
            }
            for _ in 0..<2 {
                for column in values { withExtendedLifetime(CSVPreparationDiagnostics.hashValues(column, nullValues: tokens)) {} }
            }
            var output: [[String?]] = []
            let c0 = cpu(), t0 = DispatchTime.now().uptimeNanoseconds
            for _ in 0..<repetitions {
                output = values.map { CSVPreparationDiagnostics.hashValues($0, nullValues: tokens) }
                withExtendedLifetime(output) {}
            }
            readWall = DispatchTime.now().uptimeNanoseconds - t0
            readCPU = cpu() - c0
            for (column, expectedHash) in zip(output,input.hashes) {
                var digest = Digest()
                for value in column {
                    digest.append(value) { d, v in d.integer(UInt32(v.utf8.count)); d.buffer.append(contentsOf:v.utf8) }
                }
                precondition(digest.finish() == expectedHash)
            }
            checksum = output.count * input.rows
        }
        let result: [String: Any] = ["validated":true,"action":action,"rows":rows,"repetitions":repetitions,
            "total_cpu_ns":readCPU,"elapsed_ns":readWall,"cpu_per_iteration_ns":Double(readCPU)/Double(repetitions),
            "checksum":checksum,"admitted":expected as Any? ?? NSNull(),"all_native_utf8_tokens":tokens.allSatisfy(\\.isContiguousUTF8),
            "peak_bytes":peak(),"heap_after_bytes":heap(),"hash_fingerprint":["missing-0".hashValue,"ordinary-value".hashValue],
            "scope":"Diagnostic snapshot. Factory includes plan creation, attempt allocation, opaque Any boxing and release. Prefix includes actual constructor and optional opaque ownership. Hash uses already-decoded values, native Set membership and optional output allocation; final native output hashes checked outside timing. These phases are not additive portions of a full read."]
        print(String(decoding:try JSONSerialization.data(withJSONObject:result,options:[.sortedKeys]),as:UTF8.self))
    }
}
'''
(R/'PreparationProbe.swift').write_text(s)
(R/'HashFingerprint.swift').write_text('''import Foundation
let result: [String: Any] = ["values":["missing-0".hashValue,"ordinary-value".hashValue],"fixed":ProcessInfo.processInfo.environment["SWIFT_DETERMINISTIC_HASHING"] ?? "unset"]
print(String(decoding:try JSONSerialization.data(withJSONObject:result,options:[.sortedKeys]),as:UTF8.self))
''')
