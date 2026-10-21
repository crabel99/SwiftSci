from pathlib import Path
import subprocess,json,re,hashlib
R=Path(__file__).resolve().parent;D=R/'stream-coverage-final';S=Path('/private/tmp/swiftsci-csv-streaming-20261021')
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((D/'receipt.json').read_text())
for name,digest in receipt.items():assert h(D/name)==digest
results=[]
for rel in ['Core/ChunkedDataFrame.swift','Core/DataFrame.swift','IO/CSVReader.swift','IO/CSVReadCursor.swift','IO/CSVRecordIndex.swift','IO/SystemsCSVParser.swift']:
 source=S/'Sources/SwiftDataFrame'/rel
 p=subprocess.run(['xcrun','llvm-cov','show',str(D/'SwiftDataFrameTests'),'-instr-profile='+str(D/'Coverage.profdata'),str(source)],capture_output=True,text=True,check=True)
 (D/(source.name+'.coverage.txt')).write_text(p.stdout)
 diff=subprocess.check_output(['git','diff','85f240ef707e59486f87177103928786b36db56e','--unified=0','--',str(source)],cwd=S,text=True)
 added=set();current=None
 for line in diff.splitlines():
  m=re.match(r'@@ -\d+(?:,\d+)? \+(\d+)',line)
  if m:current=int(m[1]);continue
  if line.startswith(('+++','---')):continue
  if current is not None:
   if line.startswith('+'):added.add(current);current+=1
   elif not line.startswith(('-','\\')):current+=1
 hits={}
 for line in p.stdout.splitlines():
  m=re.match(r'\s*(\d+)\|\s*([^|]*)\|',line)
  if m and m[2].strip():hits[int(m[1])]=hits.get(int(m[1]),False) or m[2].strip()!='0'
 executable=sorted(added & hits.keys());missed=[i for i in executable if not hits[i]]
 results.append({'file':rel,'added_executable':len(executable),'uncovered':missed,'covered':len(executable)-len(missed),'source_sha256':h(source)})
print(json.dumps(results,indent=2));(D/'patch-coverage.json').write_text(json.dumps(results,indent=2)+'\n')
