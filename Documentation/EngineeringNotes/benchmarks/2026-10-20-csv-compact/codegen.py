from pathlib import Path
import subprocess,json,re,hashlib
R=Path(__file__).resolve().parent;out={}
for v in ['active','compact','inlined','packed']:
 obj=R/'build'/v/'SwiftDataFrame.o'
 commands=[['xcrun','nm',str(obj)],['xcrun','llvm-objdump','--reloc',str(obj)],['xcrun','size','-m',str(obj)]]
 symbols,relocs,size=[subprocess.check_output(cmd,text=True) for cmd in commands]
 calls=[l for l in relocs.splitlines() if 'ARM64_RELOC_BRANCH26' in l and 'CSVFieldStorage' in l]
 out[v]=dict(commands=commands,object_sha256=hashlib.sha256(obj.read_bytes()).hexdigest(),lookup_symbols=[l for l in symbols.splitlines() if 'CSVFieldStorage' in l],lookup_call_relocations=calls,text_section_bytes=int(re.search(r'Section \(__TEXT, __text\): (\d+)',size)[1]))
 print(v,'lookup call relocations',len(calls),'text bytes',out[v]['text_section_bytes'])
(R/'codegen.json').write_text(json.dumps(out,indent=2)+'\n')
