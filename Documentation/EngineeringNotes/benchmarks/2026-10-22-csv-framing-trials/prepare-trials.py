from pathlib import Path
import shutil,json,subprocess
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');P=Path('/private/tmp/swiftsci-csv-wide-profile-20261022')
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=S,text=True).strip()=='9c067c6c5116d78c0849073acea7fb150404efab'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=S)
for f in ['build.py','ResourceProbe.swift','StreamProbe.swift','GrammarProbe.swift']:
 shutil.copy2(P/f,R/f)
v={}
for name in ['consume','header']:
 D=R/(name+'-trial');shutil.copytree(S/'Sources/SwiftDataFrame',D/'Sources/SwiftDataFrame');v[name]={'path':str(D),'pr':None}
p=R/'consume-trial/Sources/SwiftDataFrame/IO/CSVRecordIndex.swift';s=p.read_text();s=s.replace('blocks: CSVFieldBlocks<','blocks: consuming CSVFieldBlocks<');old='''    func finished() -> [[Field]] {
        var result = completed
        if !current.isEmpty { result.append(current) }
        return result
    }''';new='''    consuming func finished() -> [[Field]] {
        if !current.isEmpty { completed.append(current) }
        return completed
    }''';assert old in s;p.write_text(s.replace(old,new))
p=R/'consume-trial/Sources/SwiftDataFrame/IO/SystemsCSVParser.swift';s=p.read_text().replace('fields: CSVFieldBlocks<Field>, rowStarts: [Int], rowCount: Int, nextOffset: Int','fields: consuming CSVFieldBlocks<Field>, rowStarts: [Int], rowCount: Int, nextOffset: Int');p.write_text(s)
p=R/'header-trial/Sources/SwiftDataFrame/IO/SystemsCSVParser.swift';s=p.read_text();old='var fields = CSVFieldBlocks<Field>(byteCount: Output.keepsCoordinates ? range.count : 0)';new='var fields = CSVFieldBlocks<Field>(byteCount: Output.keepsCoordinates && maximumRows != 1 ? range.count : 0)';assert old in s;p.write_text(s.replace(old,new))
(R/'variants.json').write_text(json.dumps(v,indent=2)+'\n')
