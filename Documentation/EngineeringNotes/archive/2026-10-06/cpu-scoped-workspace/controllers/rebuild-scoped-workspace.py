import json,shutil,sys,subprocess
from pathlib import Path
root=Path('/Users/crabel/Documents/src/SwiftSci');sys.path.insert(0,str(root/'Benchmarks/UnifiedMemoryPrototype'));import run as c
from processes import run_process
out=Path('/Users/crabel/local-ai/spl/swiftsci/cpu-scoped-workspace-20261006');source=Path((out/'source.txt').read_text().strip());base=json.loads(Path('/Users/crabel/local-ai/spl/swiftsci/cpu-planned-workspace-20261006/build.json').read_text());worker=c.CACHE/'derived/Build/Products/Release/SwiftSciMemoryIntegrationPrototype'
try:
 with (out/'build-fixed.log').open('w') as log:r=run_process(base['command'],cwd=source,stdout=log,stderr=subprocess.STDOUT,timeout=1200)
 assert r.returncode==0,'See build-fixed.log'
 copy=worker.with_name('SwiftSciCPUScopedWorkspaceTrial');shutil.copy2(worker,copy)
 c.write(out/'build.json',dict(base_commit=base['base_commit'],source=str(source),command=base['command'],files={n:c.digest(source/n) for n in sorted(set(base['files'])|{'Benchmarks/UnifiedMemoryPrototype/Integration/MixedDevice.swift'})},binary_sha256=c.digest(copy),scope='Disposable explicitly injected per-batch owner with workspace-only MemoryBudget reservation. No production edits.'))
 print('BUILD PASSED',copy,flush=True)
finally:shutil.copy2(worker.with_name('SwiftSciMatrixCleanupFixed'),worker)
