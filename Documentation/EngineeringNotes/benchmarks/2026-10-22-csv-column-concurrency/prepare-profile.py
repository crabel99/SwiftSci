from pathlib import Path
import shutil,json
R=Path(__file__).resolve().parent
S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021')
D=R/'instrumented'
shutil.copytree(S/'Sources/SwiftDataFrame',D/'Sources/SwiftDataFrame')
old=Path('/private/tmp/swiftsci-csv-cpu-profile-20261021/instrument.py').read_text()
a=old.index("p=s/'Sources/SwiftDataFrame/IO/CSVEagerReader.swift'")
code=old[a:]
code=code.replace('CSV-CPU-20261021','CSV-CPU-20261022')
# The count operation moved into begin after the original instrumentation.
code=code.replace("t=t.replace('        var rows = 0\\n        var offset = 0'", "t=t.replace('        var rows = 0\\n        var offset = 0'")
exec(compile(code,str(R/'prepare-profile.py'),'exec'),{'s':D})
p=D/'Sources/SwiftDataFrame/IO/CSVEagerReader.swift'
t=p.read_text().replace('let capacity = rows + (try parser.countRecords(buffer: remainder, maximumRows: remaining))','let capacity = rows + (try CSVCPUProfile.measure("count") { try parser.countRecords(buffer: remainder, maximumRows: remaining) })')
p.write_text(t)
for f in ['build.py','ResourceProbe.swift']:
 shutil.copy2(Path('/private/tmp/swiftsci-csv-plan-profile-20261022')/f,R/f)
(R/'variants.json').write_text(json.dumps({'profile':{'path':str(D),'pr':None}},indent=2)+'\n')
