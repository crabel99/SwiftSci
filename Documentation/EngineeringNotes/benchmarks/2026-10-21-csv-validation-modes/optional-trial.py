from pathlib import Path
import json,shutil
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-control-20261021');T=R/'optional-trial';shutil.copytree(S/'Sources/SwiftDataFrame',T/'Sources/SwiftDataFrame',dirs_exist_ok=True)
p=T/'Sources/SwiftDataFrame/IO/CSVColumnConversion.swift';t=p.read_text();a=t.index('internal enum CSVDecodedValue<Value>');b=t.index('internal protocol CSVValueDecoder',a);t=t[:a]+t[b:]
t=t.replace('func decode(buffer: UnsafeBufferPointer<UInt8>, offset: CSVFieldOffset) -> CSVDecodedValue<Value>','func decode(buffer: UnsafeBufferPointer<UInt8>, offset: CSVFieldOffset) -> Value?\n    func isMissing(buffer: UnsafeBufferPointer<UInt8>, offset: CSVFieldOffset) -> Bool')
a=t.index('            switch decoder.decode(buffer: buffer, offset: field)');b=t.index('\n        }\n        return nil',a)
t=t[:a]+'''            let value = decoder.decode(buffer: buffer, offset: field)
            if validates && value == nil && !decoder.isMissing(buffer: buffer, offset: field) { return field }
            values.append(value)'''+t[b:]
for typ in ['Int64','Double','Bool','String','Date']:t=t.replace('-> CSVDecodedValue<'+typ+'>','-> '+typ+'?')
t=t.replace('return .missing','return nil').replace('return .value(Int64(value))','return Int64(value)').replace('return .value(value)','return value').replace('.map(CSVDecodedValue.value) ?? .invalid','')
t=t.replace('return nullValues.contains(text) ? .missing : .value(text)','return nullValues.contains(text) ? nil : text')
# Insert the null classifier for each decoder, sharing its existing matching policy.
for name in ['CSVIntegerDecoder','CSVDoubleDecoder','CSVDateDecoder','CSVBooleanDecoder','CSVStringDecoder']:
 start=t.index('internal struct '+name);end=t.find('\ninternal struct ',start+1);end=len(t) if end<0 else end
 section=t[start:end];close=section.rfind('\n}')
 body='return nulls.contains(buffer: buffer, offset: offset)' if name in ['CSVIntegerDecoder','CSVDoubleDecoder','CSVDateDecoder'] else 'return nullValues.contains(VectorizedByteParsers.parseString(buffer: buffer, offset: offset))'
 section=section[:close]+'''\n    @inline(__always)
    func isMissing(buffer: UnsafeBufferPointer<UInt8>, offset: CSVFieldOffset) -> Bool {
        '''+body+'''\n    }
'''+section[close:];t=t[:start]+section+t[end:]
p.write_text(t)
v=json.loads((R/'variants.json').read_text());v['optional']={'path':str(T),'pr':None};(R/'variants.json').write_text(json.dumps(v,indent=2)+'\n')
s=(R/'result-pilot.py').read_text().replace("engines=['before','result']","engines=['before','optional']").replace("R/'result-pilot.json'","R/'optional-pilot.json'");(R/'optional-pilot.py').write_text(s)
