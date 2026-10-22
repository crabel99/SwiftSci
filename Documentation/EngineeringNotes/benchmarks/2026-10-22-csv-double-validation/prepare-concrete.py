from pathlib import Path
import json,shutil
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');T=R/'concrete-trial';assert not T.exists();shutil.copytree(S/'Sources/SwiftDataFrame',T/'Sources/SwiftDataFrame');p=T/'Sources/SwiftDataFrame/IO/CSVColumnConversion.swift';s=p.read_text()
s=s.replace('case .double(let attempt): attempt.append(buffer, records, startRow, rowCount, column, sourceOffset: sourceOffset)','case .double(let attempt): attempt.appendDouble(buffer, records, startRow, rowCount, column, sourceOffset: sourceOffset)')
a=s.index('    func append<Records: CSVRecordAccess>(',s.index('internal final class CSVColumnAttempt'));b=s.index('    // Borrow the builder',a);wrapper=s[a:b].replace('func append<Records:', 'func appendDouble<Records:').replace('    ) {\n','    ) where Decoder == CSVDoubleDecoder {\n',1).replace('Self.appendRows(', 'appendConcreteDoubleRows(')
s=s[:b]+wrapper+s[b:]
a=s.index('    private static func appendRows<Records:');b=s.index('    func column(named name:',a);body=s[a:b].replace('    private static func appendRows<Records:', 'private func appendConcreteDoubleRows<Records:').replace('decoder: Decoder, validates: Bool, into values: inout CSVColumnBuilder<Decoder.Value>','decoder: CSVDoubleDecoder, validates: Bool, into values: inout CSVColumnBuilder<Double>')
s+='\n'+body;p.write_text(s)
v=json.loads((R/'variants.json').read_text());v['concrete']={'path':str(T),'pr':None};(R/'variants.json').write_text(json.dumps(v,indent=2)+'\n')
