from pathlib import Path
import json,shutil
R=Path(__file__).resolve().parent;E=Path('/private/tmp/swiftsci-csv-cpu-profile-20261021');variants={}
for label,src in [('original','/private/tmp/swiftsci-csv-scoped-simd-20261021'),('current','/private/tmp/swiftsci-csv-count-only-control-20261021')]:
 s=R/('profile-'+label);shutil.copytree(Path(src)/'Sources/SwiftDataFrame',s/'Sources/SwiftDataFrame',dirs_exist_ok=True)
 p=s/'Sources/SwiftDataFrame/IO/CSVReadCursor.swift';t=p.read_text()
 t=t.replace('case .finished: return nil','case .finished: CSVStageProfile.emit(); return nil')
 t=t.replace('let batch = try parser.scanBatch(buffer: buffer, maximumRows: rows)','let batch = try CSVStageProfile.measure("framing") { try parser.scanBatch(buffer: buffer, maximumRows: rows) }')
 t=t.replace('let result = try CSVReader.buildFrame(buffer: buffer, records: batch.records,\n                startRow: 0, rowCount: batch.records.count, headers: input.headers, options: options)','let result = try CSVStageProfile.measure("conversion") { try CSVReader.buildFrame(buffer: buffer, records: batch.records,\n                startRow: 0, rowCount: batch.records.count, headers: input.headers, options: options) }')
 p.write_text(t)
 helper=(E/'instrumented-sink/Sources/SwiftDataFrame/IO/CSVCPUProfile.swift').read_text().replace('CSVCPUProfile','CSVStageProfile').replace('CSV-CPU-20261021','CSV-CONVERSION-20261021')
 (s/'Sources/SwiftDataFrame/IO/CSVStageProfile.swift').write_text(helper)
 variants[label]={'path':str(s),'pr':None}
(R/'variants.json').write_text(json.dumps(variants,indent=2)+'\n')
shutil.copy2(E/'build.py',R/'build.py');shutil.copy2(E/'ResourceProbe.swift',R/'ResourceProbe.swift');shutil.copy2(E/'StreamProbe.swift',R/'StreamProbe.swift')
