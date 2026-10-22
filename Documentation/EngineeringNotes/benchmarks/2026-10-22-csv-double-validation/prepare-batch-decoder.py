from pathlib import Path
import json,shutil
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021');T=R/'batchdecoder-trial';assert not T.exists();shutil.copytree(S/'Sources/SwiftDataFrame',T/'Sources/SwiftDataFrame');p=T/'Sources/SwiftDataFrame/IO/CSVColumnConversion.swift';s=p.read_text()
a=s.index('    // Borrow the builder once per batch');b=s.index('    func column(named name:',a);block=s[a:b];fn=block[block.index('    private static func appendRows'):].replace('    private static func appendRows<Records:', '    @inline(__always)\n    func appendRows<Records:').replace('        decoder: Decoder, validates: Bool, into values: inout CSVColumnBuilder<Decoder.Value>','        validates: Bool, into values: inout CSVColumnBuilder<Value>').replace('decoder.decodeValue(', 'decodeValue(').replace('decoder.decode(', 'decode(')
s=s[:a]+s[b:]
s=s.replace('Self.appendRows(buffer, records, startRow, rowCount, column,\n            decoder: decoder, validates: validates, into: &values)','decoder.appendRows(buffer, records, startRow, rowCount, column,\n            validates: validates, into: &values)')
s=s.replace('internal extension CSVValueDecoder {\n','internal extension CSVValueDecoder {\n'+fn,1)
old='''    func decode(buffer: UnsafeBufferPointer<UInt8>, offset: CSVFieldOffset) -> CSVDecodedValue<Value>''';new=old+'''
    func appendRows<Records: CSVRecordAccess>(
        _ buffer: UnsafeBufferPointer<UInt8>, _ records: Records,
        _ startRow: Int, _ rowCount: Int, _ column: Int,
        validates: Bool, into values: inout CSVColumnBuilder<Value>
    ) -> CSVFieldOffset?''';assert old in s;s=s.replace(old,new,1);p.write_text(s)
v=json.loads((R/'variants.json').read_text());v['batchdecoder']={'path':str(T),'pr':None};(R/'variants.json').write_text(json.dumps(v,indent=2)+'\n')
