from pathlib import Path
import shutil,json
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021')
v=json.loads((R/'variants.json').read_text())
for label,size in [('strided',2),('quartet',4)]:
 T=R/(label+'-trial');shutil.copytree(S/'Sources/SwiftDataFrame',T/'Sources/SwiftDataFrame');v[label]={'path':str(T),'pr':None}
 p=T/'Sources/SwiftDataFrame/IO/CSVEagerReader.swift';s=p.read_text();old='''        DispatchQueue.concurrentPerform(iterations: columns.count) { index in
            let column = columns[index]
            input.attempts[column]?.appendIndexed(buffer: input.buffer, records: records,
                startRow: 0, rowCount: count, column: column, sourceOffset: sourceOffset)
        }'''
 new=f'''        let workers = (columns.count + {size-1}) / {size}
        DispatchQueue.concurrentPerform(iterations: workers) {{ index in
            for position in stride(from: index, to: columns.count, by: workers) {{
                let column = columns[position]
                input.attempts[column]?.appendIndexed(buffer: input.buffer, records: records,
                    startRow: 0, rowCount: count, column: column, sourceOffset: sourceOffset)
            }}
        }}''';assert old in s;p.write_text(s.replace(old,new))
(R/'variants.json').write_text(json.dumps(v,indent=2)+'\n')
