from pathlib import Path
import json,subprocess,sys
r=Path(__file__).resolve().parent
proof=json.loads(Path('/private/tmp/swiftsci-prepared-classification-20261026/verification/baseline-probe-proof.json').read_text())
name=sys.argv[1]
old=Path('/private/tmp/swiftsci-prepared-classification-20261026/verification')
compile=[str(r/(name+'.swift')) if x==str(old/'BaselineLogisticProbe.swift') else str(r/(name+'.o')) if x==str(old/'baseline-probe.o') else x for x in proof['compile']]
compile += (["-whole-module-optimization"] + sys.argv[2:]) if len(sys.argv)>2 else []
response=r/(name+'.LinkFileList');response.write_text('\n'.join(list(proof['objects'])+[str(r/(name+'.o'))])+'\n')
link=[str(r/name) if x==str(old/'baseline-probe') else '@'+str(response) if x=='@'+str(old/'baseline-probe.LinkFileList') else x for x in proof['link']]
for cmd in (compile,link):subprocess.run(cmd,check=True)
print('Linked original libraries:',r/name)
