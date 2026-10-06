import json,sys,subprocess
from pathlib import Path
root=Path('/Users/crabel/Documents/src/SwiftSci');sys.path.insert(0,str(root/'Benchmarks/UnifiedMemoryPrototype'));from processes import run_process
out=Path('/Users/crabel/local-ai/spl/swiftsci/cpu-async-cleanup-20261006');out.mkdir(exist_ok=True)
old=Path('/Users/crabel/Library/Caches/SwiftSci/unified-memory-prototype/source-scoped-workspace-ve4aqyg_/Sources/SwiftML/Core/CPUWorkspaceTrial.swift')
command=['xcrun','swiftc','-O','-parse-as-library',str(old),'/private/tmp/OldCloseAdapter.swift','/private/tmp/AsyncCloseProbe.swift','-o',str(out/'before-probe')]
r=run_process(command,text=True,capture_output=True,timeout=60);(out/'before-build.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr
r=run_process([str(out/'before-probe')],text=True,capture_output=True,timeout=10);record=json.loads(r.stdout);assert r.returncode==2 and record['status']=='failed' and not record['late_borrow_rejected_before_active_borrow_finished'];(out/'before.json').write_text(json.dumps(record,indent=2)+'\n');print(record)
