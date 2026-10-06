import json,shutil,subprocess,sys,tempfile
from pathlib import Path
root=Path('/Users/crabel/Documents/src/SwiftSci');sys.path.insert(0,str(root/'Benchmarks/UnifiedMemoryPrototype'));import run as c
from processes import run_process
prior=Path('/Users/crabel/local-ai/spl/swiftsci/cpu-workspace-20261006');out=prior/'adaptive';out.mkdir(exist_ok=True)
base=json.loads((prior/'build.json').read_text());original=Path(base['source']);source=Path(tempfile.mkdtemp(prefix='source-adaptive-workspace-',dir=c.CACHE))
for n,h in base['files'].items():
 assert c.digest(original/n)==h
 p=source/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(original/n,p)
p=source/'Sources/SwiftML/Core/CPUWorkspaceTrial.swift';s=p.read_text().replace('import Foundation','import Foundation\nimport Darwin')
s=s.replace('        var enabled = false','        var enabled = false\n        var adaptive = false\n        var allocatedCount = 0')
s=s.replace('storage.allocations = 0; storage.uses = 0; storage.enabled = true','storage.allocations = 0; storage.uses = 0; storage.enabled = true\n        storage.adaptive = ProcessInfo.processInfo.environment["CPU_WORKSPACE_SIZING"] == "adaptive"')
s=s.replace('storage.pointer == nil ? 0 : storage.capacity * 8','storage.allocatedCount * 8')
s=s.replace('storage.pointer?.deinitialize(count: storage.capacity)','storage.pointer?.deinitialize(count: storage.allocatedCount)')
s=s.replace('storage.pointer = nil; storage.enabled = false','storage.pointer = nil; storage.allocatedCount = 0; storage.enabled = false')
s=s.replace('matrixCount: Int, rhsCount: Int,','matrixCount: Int, rhsCount: Int, scratchCount: Int = 1,')
s=s.replace('rhsCount < storage.capacity - matrixCount else','rhsCount < storage.capacity - matrixCount, scratchCount > 0,\n              scratchCount <= storage.capacity - matrixCount - rhsCount else')
s=s.replace('        if storage.pointer == nil {\n            storage.pointer = .allocate(capacity: storage.capacity)\n            storage.pointer!.initialize(repeating: 0, count: storage.capacity)', '''        let pageCount = Int(getpagesize()) / MemoryLayout<Double>.stride
        let needed = matrixCount + rhsCount + scratchCount
        let desired = storage.adaptive ? ((needed + pageCount - 1) / pageCount) * pageCount : storage.capacity
        if storage.allocatedCount < desired {
            storage.pointer?.deinitialize(count: storage.allocatedCount)
            storage.pointer?.deallocate()
            storage.pointer = .allocate(capacity: desired)
            storage.pointer!.initialize(repeating: 0, count: desired)
            storage.allocatedCount = desired''')
s=s.replace('storage.capacity - matrixCount - rhsCount)', 'storage.allocatedCount - matrixCount - rhsCount)')
p.write_text(s)
p=source/'Sources/SwiftML/Core/LinearRegression.swift';s=p.read_text();start=s.index('    private func fitCPUWorkspace<');end=s.index('    /// Explicit Gradient Descent CPU backend.',start);body=s[start:end]
qstart=body.index('        var lwork = Int32(-1)');qend=body.index('        dgels_(&trans, &r, &c, &nrhs, AColMajor, &lda, bVec, &ldb, work, &lwork, &info)',qstart)
query=body[qstart:qend];query=query.replace('AColMajor, &lda, bVec,','&queryA, &lda, &queryB,')
query=query.replace('        var lwork', '        var queryA = 0.0, queryB = 0.0\n        var lwork',1)
query=query.replace('        guard lwork > 0 && Int(lwork) <= scratchCount else { throw SwiftMLError.invalidParameter("Trial LAPACK scratch capacity exceeded") }','        guard lwork > 0 else { throw SwiftMLError.invalidParameter("Trial LAPACK workspace query invalid") }')
body=body[:qstart]+body[qend:]
old='        try CPUWorkspaceTrial.withBuffers(matrixCount: rows * cols, rhsCount: Int(ldb)) { AColMajor, bVec, work, scratchCount in'
new=query+'\n        try CPUWorkspaceTrial.withBuffers(matrixCount: rows * cols, rhsCount: Int(ldb), scratchCount: Int(lwork)) { AColMajor, bVec, work, _ in'
assert old in body;body=body.replace(old,new)
s=s[:start]+body+s[end:];p.write_text(s)
p=source/'Benchmarks/UnifiedMemoryPrototype/Integration/RetainedMemory.swift';s=p.read_text()
s=s.replace('    case "cpu-same":', '    case "cpu-growing": sequence = [ConcurrentShape(rows: 100_000, width: 8), ConcurrentShape(rows: 8192, width: 128), ConcurrentShape(rows: 100_000, width: 32)]\n    case "cpu-small": sequence = [ConcurrentShape(rows: 1024, width: 8), ConcurrentShape(rows: 4096, width: 32), ConcurrentShape(rows: 8192, width: 8)]\n    case "cpu-same":')
s=s.replace('workspace["allocations"] == 1 && workspace["uses"] == cycles * 3', '(1...3).contains(workspace["allocations"]!) && workspace["owned_bytes"]! <= workspace["capacity_bytes"]! && workspace["uses"] == cycles * 3')
s=s.replace('"all fits use one bounded workspace without fallback"','"all fits use bounded workspace without fallback"');p.write_text(s)
p=source/'Benchmarks/UnifiedMemoryPrototype/Integration/main.swift';s=p.read_text().replace('["cpu-same", "cpu-sizes", "gpu-sizes"].contains(args[1])','["cpu-same", "cpu-sizes", "cpu-growing", "cpu-small", "gpu-sizes"].contains(args[1])');p.write_text(s)
(out/'source.txt').write_text(str(source)+'\n')
worker=c.CACHE/'derived/Build/Products/Release/SwiftSciMemoryIntegrationPrototype'
try:
 with (out/'build.log').open('w') as log:r=run_process(base['command'],cwd=source,stdout=log,stderr=subprocess.STDOUT,timeout=1200)
 assert r.returncode==0,'See build.log'
 copy=worker.with_name('SwiftSciCPUAdaptiveWorkspaceTrial');shutil.copy2(worker,copy)
 c.write(out/'build.json',dict(base_commit=base['base_commit'],source=str(source),command=base['command'],files={n:c.digest(source/n) for n in base['files']},binary_sha256=c.digest(copy),scope='Disposable fixed and adaptive CPU workspace comparison. LAPACK workspace-size query precedes matrix construction; one bounded arena grows only to the rounded required size. No production changes.'))
 print('BUILD PASSED',copy,flush=True)
finally:shutil.copy2(worker.with_name('SwiftSciMatrixCleanupFixed'),worker)
