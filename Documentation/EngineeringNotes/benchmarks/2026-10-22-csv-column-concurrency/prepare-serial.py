from pathlib import Path
import shutil,json
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');T=R/'serial-trial';shutil.copytree(S/'Sources/SwiftDataFrame',T/'Sources/SwiftDataFrame')
p=T/'Sources/SwiftDataFrame/IO/CSVEagerReader.swift';s=p.read_text();old='''        DispatchQueue.concurrentPerform(iterations: columns.count) { index in
            let column = columns[index]
            input.attempts[column]?.appendIndexed(buffer: input.buffer, records: records,
                startRow: 0, rowCount: count, column: column, sourceOffset: sourceOffset)
        }''';new='''        for column in columns {
            input.attempts[column]?.appendIndexed(buffer: input.buffer, records: records,
                startRow: 0, rowCount: count, column: column, sourceOffset: sourceOffset)
        }''';assert old in s;p.write_text(s.replace(old,new));v=json.loads((R/'variants.json').read_text());v['serial']={'path':str(T),'pr':None};(R/'variants.json').write_text(json.dumps(v,indent=2)+'\n')
