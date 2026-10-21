from pathlib import Path
import subprocess,json,hashlib,re
r=Path(__file__).resolve().parent;records={}
for v in list(json.loads((r/'variants.json').read_text())):
 p=r/'build'/v/'SwiftDataFrame.o'
 symbols=subprocess.check_output(['xcrun','nm',str(p)],text=True)
 demangled=subprocess.run(['xcrun','swift-demangle'],input=symbols,capture_output=True,text=True,check=True).stdout
 size=subprocess.check_output(['xcrun','size','-m',str(p)],text=True)
 relocs=subprocess.check_output(['xcrun','llvm-objdump','--reloc',str(p)],text=True)
 records[v]=dict(object_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),text_section_bytes=int(re.search(r'Section \(__TEXT, __text\): (\d+)',size)[1]),column_symbols=[l for l in demangled.splitlines() if 'buildIndexedColumn' in l or 'CSVFlatRecordView.field' in l],lookup_call_relocations=[l for l in relocs.splitlines() if 'ARM64_RELOC_BRANCH26' in l and ('CSVFlatRecordViewV5field' in l or 'CSVRecordIndexV5field' in l or 'CSVCompactRecordViewV5field' in l or 'CSVFieldStorage' in l)])
 print(v,records[v]['text_section_bytes'],records[v]['column_symbols'],flush=True)
(r/'codegen.json').write_text(json.dumps(records,indent=2)+'\n')
