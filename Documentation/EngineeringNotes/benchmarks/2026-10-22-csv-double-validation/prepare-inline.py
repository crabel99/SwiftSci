from pathlib import Path
import shutil,json
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');variants=json.loads((R/'variants.json').read_text())
for label,signature in [('outer','    func append<Records: CSVRecordAccess>(\n'),('inner','    private static func appendRows<Records: CSVRecordAccess>(\n')]:
 T=R/(label+'-trial');assert not T.exists();shutil.copytree(S/'Sources/SwiftDataFrame',T/'Sources/SwiftDataFrame');p=T/'Sources/SwiftDataFrame/IO/CSVColumnConversion.swift';s=p.read_text();a=s.index('internal final class CSVColumnAttempt');i=s.index(signature,a);s=s[:i]+'    @inline(__always)\n'+s[i:];p.write_text(s);variants[label]={'path':str(T),'pr':None}
(R/'variants.json').write_text(json.dumps(variants,indent=2)+'\n')
