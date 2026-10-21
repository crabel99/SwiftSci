from pathlib import Path
import shutil,json
r=Path(__file__).resolve().parent;shutil.copytree(r/'scoped',r/'arrays')
p=r/'arrays/Sources/SwiftDataFrame/IO/CSVRecordIndex.swift';s=p.read_text()
a='''        return values.withUnsafeBufferPointer { fields in
            rowStarts.withUnsafeBufferPointer { starts in
                body(CSVFlatRecordView(fields: fields, rowStarts: starts))
            }
        }''';b='''        return values.withUnsafeBufferPointer { blocks in
            rowStarts.withUnsafeBufferPointer { starts in
                body(CSVCompactRecordView(blocks: blocks, rowStarts: starts))
            }
        }'''
assert s.count(a)==1 and s.count(b)==1
s=s.replace(a,'        return body(CSVFlatRecordView(fields: values, rowStarts: rowStarts))').replace(b,'        return body(CSVCompactRecordView(blocks: values, rowStarts: rowStarts))')
s=s.replace('UnsafeBufferPointer<PackedCSVField>','[PackedCSVField]').replace('UnsafeBufferPointer<Int>','[Int]').replace('UnsafeBufferPointer<[CompactCSVField]>','[[CompactCSVField]]')
p.write_text(s)
p=r/'variants.json';v=json.loads(p.read_text());v['arrays']={**v['scoped'],'path':str(r/'arrays')};p.write_text(json.dumps(v,indent=2)+'\n')
