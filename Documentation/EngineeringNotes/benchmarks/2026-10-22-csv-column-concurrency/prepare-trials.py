from pathlib import Path
import json,shutil
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-count-only-scan-20261021')
v=json.loads((R/'variants.json').read_text())
for name in ['parity','paired']:
 T=R/(name+'-trial');shutil.copytree(S/'Sources/SwiftDataFrame',T/'Sources/SwiftDataFrame');v[name]={'path':str(T),'pr':None}
p=R/'paired-trial/Sources/SwiftDataFrame/IO/CSVEagerReader.swift';s=p.read_text();old='''        DispatchQueue.concurrentPerform(iterations: columns.count) { index in
            let column = columns[index]
            input.attempts[column]?.appendIndexed(buffer: input.buffer, records: records,
                startRow: 0, rowCount: count, column: column, sourceOffset: sourceOffset)
        }''';new='''        DispatchQueue.concurrentPerform(iterations: (columns.count + 1) / 2) { index in
            for position in (index * 2)..<min(index * 2 + 2, columns.count) {
                let column = columns[position]
                input.attempts[column]?.appendIndexed(buffer: input.buffer, records: records,
                    startRow: 0, rowCount: count, column: column, sourceOffset: sourceOffset)
            }
        }''';assert old in s;p.write_text(s.replace(old,new))
p=R/'parity-trial/Sources/SwiftDataFrame/IO/SystemsCSVParser.swift';s=p.read_text();old='''        try Task.checkCancellation()
        switch scanRecords(buffer: buffer, range: buffer.indices, fieldType: PackedCSVField.self,''';new='''        try Task.checkCancellation()
        if delimiterByte != lfByte && quoteByte != lfByte {
            return try countRowBoundaries(buffer: buffer, maximumRows: maximumRows)
        }
        switch scanRecords(buffer: buffer, range: buffer.indices, fieldType: PackedCSVField.self,''';assert old in s;s=s.replace(old,new)
pos=s.index('    private enum ScanResult<Value>')
method='''    // Quote parity marks embedded line endings without visiting each quote.
    private func countRowBoundaries(buffer: UnsafeBufferPointer<UInt8>, maximumRows: Int?) throws -> Int {
        guard let bytes = buffer.baseAddress, !buffer.isEmpty else { return 0 }
        let weights = SIMD16<UInt8>(1, 2, 4, 8, 16, 32, 64, 128, 1, 2, 4, 8, 16, 32, 64, 128)
        var cursor = 0
        var rows = 0
        var insideQuotes = false
        while cursor < buffer.count {
            try Task.checkCancellation()
            let end = cursor + min(65_536, buffer.count - cursor)
            while end - cursor >= 16 {
                let block = UnsafeRawPointer(bytes.advanced(by: cursor)).loadUnaligned(as: SIMD16<UInt8>.self)
                let quotes = SIMD16<UInt8>.zero.replacing(with: weights, where: block .== SIMD16(repeating: quoteByte))
                let lines = SIMD16<UInt8>.zero.replacing(with: weights, where: block .== SIMD16(repeating: lfByte))
                var parity = UInt16(quotes.lowHalf.wrappedSum()) | (UInt16(quotes.highHalf.wrappedSum()) << 8)
                let lineMask = UInt16(lines.lowHalf.wrappedSum()) | (UInt16(lines.highHalf.wrappedSum()) << 8)
                parity ^= parity << 1
                parity ^= parity << 2
                parity ^= parity << 4
                parity ^= parity << 8
                if insideQuotes { parity = ~parity }
                rows += (lineMask & ~parity).nonzeroBitCount
                insideQuotes = parity & 0x8000 != 0
                cursor += 16
                if let maximumRows, maximumRows > 0, rows >= maximumRows { return maximumRows }
            }
            while cursor < end {
                let byte = bytes[cursor]
                if byte == quoteByte {
                    insideQuotes.toggle()
                } else if byte == lfByte && !insideQuotes {
                    rows += 1
                    if rows == maximumRows { return rows }
                }
                cursor += 1
            }
        }
        try Task.checkCancellation()
        let last = bytes[buffer.count - 1]
        if insideQuotes || (last != lfByte && (last != delimiterByte || delimiterByte == quoteByte)) { rows += 1 }
        return rows
    }

'''
s=s[:pos]+method+s[pos:];p.write_text(s)
(R/'variants.json').write_text(json.dumps(v,indent=2)+'\n')
shutil.copy2(Path('/private/tmp/swiftsci-csv-batch-profile-20261022/CountParity.swift'),R/'CountParity.swift')
