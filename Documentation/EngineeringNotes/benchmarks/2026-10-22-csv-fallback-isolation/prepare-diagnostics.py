from pathlib import Path
import json,shutil
R=Path(__file__).resolve().parent;P=Path('/private/tmp/swiftsci-csv-prefix-selection-20261022');v=json.loads((R/'variants.json').read_text())
for source,label in [('cleanup','diagnostic-cleanup'),('production','diagnostic-selected'),('preflight','diagnostic-preflight')]:
 D=R/'variants'/label;shutil.copytree(Path(v[source]['path'])/'Sources/SwiftDataFrame',D/'Sources/SwiftDataFrame')
 body='''import Foundation

// Study-only entry points, never added to the production worktree.
public enum CSVPreparationDiagnostics {
    @inline(never)
    public static func makeAttempt(nullValues: Set<String>, selectedRows: Int) -> Any {
        var options = CSVReadOptions()
        options.nullValues = nullValues
        options.columnTypeOverrides = ["text": .utf8]
        let bytes = [UInt8]()
        return bytes.withUnsafeBufferPointer { buffer in
            let records = CSVRecordIndex(fields: [], rowStarts: [0])
            let plan = CSVColumnPlan(buffer: buffer, records: records, startRow: 0,
                rowCount: 0, column: 0, name: "text", options: options)
            return plan.conversion(type: .utf8, ROW_LABEL: selectedRows)
        }
    }

    @inline(never)
    public static func makePrefix(nullValues: Set<String>, selectedRows: Int) -> Any? {
PREFIX_BODY
    }

    @inline(never)
    public static func hashValues(_ values: [String], nullValues: Set<String>) -> [String?] {
        var result = [String?]()
        result.reserveCapacity(values.count)
        for value in values { result.append(nullValues.contains(value) ? nil : value) }
        return result
    }
}
'''
 body=body.replace('ROW_LABEL','capacity' if source=='cleanup' else 'selectedRowCount')
 prefix='        return nil' if source=='cleanup' else '''        guard let decoder = CSVASCIIPrefixStringDecoder(nullValues: nullValues, selectedRowCount: selectedRows) else { return nil }
        return decoder'''
 body=body.replace('PREFIX_BODY',prefix);(D/'Sources/SwiftDataFrame/CSVPreparationDiagnostics.swift').write_text(body)
 v[label]={'path':str(D),'pr':None}
(R/'variants.json').write_text(json.dumps(v,indent=2)+'\n')
