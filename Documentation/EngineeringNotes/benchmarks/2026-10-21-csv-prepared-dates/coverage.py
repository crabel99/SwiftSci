from pathlib import Path
import subprocess,json,shutil,re,hashlib
R=Path(__file__).resolve().parent;S=Path('/private/tmp/swiftsci-csv-ingestion-20261021');B=Path('/Users/crabel/local-ai/spl/swiftsci/csv-sort-throughput-20261017/tests-derived/Build')
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record=json.loads((R/'prepared-dates-debug-command.json').read_text());assert record['exit_code']==0
for path,digest in record['source_sha256'].items():assert h(S/path)==digest
shutil.copy2(B/'ProfileData/00006041-001C093C0A80801C/Coverage.profdata',R/'coverage.profdata')
binary=B/'Products/Debug/SwiftDataFrameTests.xctest/Contents/MacOS/SwiftDataFrameTests'
results=[]
for name in ['CSVReader.swift', 'CSVDateParser.swift']:
 source=S/'Sources/SwiftDataFrame/IO'/name
 cmd=['xcrun','llvm-cov','show',str(binary),'-instr-profile='+str(R/'coverage.profdata'),str(source)]
 p=subprocess.run(cmd,capture_output=True,text=True,check=True);(R/(name+'.coverage.txt')).write_text(p.stdout)
 diff=subprocess.check_output(['git','diff','a5f6e78a751365ec360efdd4ae8f028db04b441b','--unified=0','--',str(source)],cwd=S,text=True)
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
 results.append({'file':name,'added_executable':len(executable),'uncovered':missed,'covered':len(executable)-len(missed),'source_sha256':h(source),'coverage_sha256':h(R/(name+'.coverage.txt'))})
receipt={'binary_sha256':h(binary),'profile_sha256':h(R/'coverage.profdata'),'results':results}
(R/'patch-coverage.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(results,indent=2))
assert all(r['added_executable'] and not r['uncovered'] for r in results)
