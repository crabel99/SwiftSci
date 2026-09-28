import json,subprocess
from pathlib import Path
root=Path('/Users/LOCAL_USER/Documents/src/SwiftSci')
d=json.load(open(root/'.build/index-build/arm64-apple-macosx/debug/description.json'))
v=next(v for k,v in d['swiftCommands'].items() if 'SwiftSciBenchmarkWorker' in k)
a=v['otherArguments']; kept=[];i=0
while i<len(a):
 x=a[i]
 if x in ['-incremental','-enable-batch-mode','-serialize-diagnostics','-j16','-parseable-output']:
  i+=1;continue
 if x=='-module-cache-path':kept += [x,'/private/tmp/swiftsci-suite-finish/boundary/module-cache'];i+=2;continue
 if x=='-Xfrontend':
  if a[i+1]=='-entry-point-function-name':i+=4
  else:i+=2
  continue
 kept.append(x);i+=1
cmd=[v['executable'],'-typecheck','-I',v['importPath'],*kept,*map(str,Path('/private/tmp/swiftsci-suite-finish/boundary').glob('*.swift'))]
r=subprocess.run(cmd,text=True,capture_output=True)
print(r.stdout);print(r.stderr);print('EXIT',r.returncode)
