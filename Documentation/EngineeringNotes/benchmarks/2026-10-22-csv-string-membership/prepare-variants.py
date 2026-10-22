from pathlib import Path
import shutil,json
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021')
old='''internal struct CSVStringDecoder: CSVValueDecoder {
    let nullValues: Set<String>

    @inline(__always)
    func decode(buffer: UnsafeBufferPointer<UInt8>, offset: CSVFieldOffset) -> CSVDecodedValue<String> {
        let text = VectorizedByteParsers.parseString(buffer: buffer, offset: offset)
        return nullValues.contains(text) ? .missing : .value(text)
    }
}'''
new='''internal struct CSVStringDecoder: CSVValueDecoder {
    let nullValues: Set<String>
    private let lowStarts: UInt64
    private let highStarts: UInt64

    init(nullValues: Set<String>) {
        self.nullValues = nullValues
        var low: UInt64 = 0
        var high: UInt64 = 0
        for token in nullValues {
            guard token.utf8.allSatisfy({ $0 < 128 }) else {
                lowStarts = .max
                highStarts = .max
                return
            }
            if let first = token.utf8.first {
                if first < 64 { low |= UInt64(1) << first }
                else { high |= UInt64(1) << (first - 64) }
            }
        }
        lowStarts = low
        highStarts = high
    }

    @inline(__always)
    func decode(buffer: UnsafeBufferPointer<UInt8>, offset: CSVFieldOffset) -> CSVDecodedValue<String> {
        let text = VectorizedByteParsers.parseString(buffer: buffer, offset: offset)
        if let first = text.utf8.first, first < 128 {
            let starts = first < 64 ? lowStarts : highStarts
            if starts & (UInt64(1) << (first & 63)) == 0 { return .value(text) }
        }
        return nullValues.contains(text) ? .missing : .value(text)
    }
}'''
variants={}
for name in ['control','ascii-prefix']:
 root=R/'variants'/name;shutil.copytree(S/'Sources/SwiftDataFrame',root/'Sources/SwiftDataFrame')
 if name=='ascii-prefix':
  p=root/'Sources/SwiftDataFrame/IO/CSVColumnConversion.swift';s=p.read_text();assert s.count(old)==1;p.write_text(s.replace(old,new))
 variants[name]={'path':str(root),'pr':None}
(R/'variants.json').write_text(json.dumps(variants,indent=2)+'\n')
shutil.copy2(Path('/private/tmp/swiftsci-csv-local-builder-20261022/build.py'),R/'build.py')
shutil.copy2(Path('/private/tmp/swiftsci-csv-stream-dispatch-20261022/link-variants.py'),R/'link-variants.py')
