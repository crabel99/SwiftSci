import json,shutil,subprocess,sys,tempfile
from pathlib import Path
root=Path('/Users/crabel/Documents/src/SwiftSci');sys.path.insert(0,str(root/'Benchmarks/UnifiedMemoryPrototype'));import run as c
from processes import run_process
out=Path('/Users/crabel/local-ai/spl/swiftsci/cpu-workspace-20261006');out.mkdir(exist_ok=True)
worker=c.CACHE/'derived/Build/Products/Release/SwiftSciMemoryIntegrationPrototype'
base=json.loads(Path(str(worker)+'.build.json').read_text());assert c.digest(worker)==base['binary_sha256'];assert all(c.digest(root/n)==v for n,v in base['files'].items())
source=Path(tempfile.mkdtemp(prefix='source-cpu-workspace-',dir=c.CACHE))
for n in base['files']:
 p=source/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/n,p)
workspace='''import Foundation

// THROWAWAY: one exclusive, bounded CPU workspace for a sequential-fit experiment.
// This is not a production API or a process-wide memory budget.
public enum CPUWorkspaceTrial {
    private static let storage = Storage()
    private final class Storage: @unchecked Sendable {
        let lock = NSLock()
        var enabled = false
        var pointer: UnsafeMutablePointer<Double>?
        let capacity = 32 * 1024 * 1024 / MemoryLayout<Double>.stride
        var allocations = 0
        var uses = 0
        var active = 0
    }
    public static var isEnabled: Bool {
        storage.lock.lock(); defer { storage.lock.unlock() }
        return storage.enabled
    }
    public static func begin() {
        storage.lock.lock(); defer { storage.lock.unlock() }
        precondition(storage.pointer == nil && !storage.enabled)
        storage.allocations = 0; storage.uses = 0; storage.enabled = true
    }
    public static func snapshot() -> [String: Int] {
        storage.lock.lock(); defer { storage.lock.unlock() }
        return ["capacity_bytes": storage.capacity * 8,
                "owned_bytes": storage.pointer == nil ? 0 : storage.capacity * 8,
                "allocations": storage.allocations, "uses": storage.uses, "active": storage.active]
    }
    public static func end() {
        storage.lock.lock(); defer { storage.lock.unlock() }
        precondition(storage.active == 0)
        storage.pointer?.deinitialize(count: storage.capacity)
        storage.pointer?.deallocate(); storage.pointer = nil; storage.enabled = false
    }
    static func withBuffers(matrixCount: Int, rhsCount: Int,
        _ body: (UnsafeMutablePointer<Double>, UnsafeMutablePointer<Double>, UnsafeMutablePointer<Double>, Int) throws -> Void) throws {
        storage.lock.lock(); defer { storage.lock.unlock() }
        guard storage.enabled, matrixCount > 0, rhsCount > 0,
              matrixCount <= storage.capacity, rhsCount < storage.capacity - matrixCount else {
            throw SwiftMLError.invalidParameter("Trial CPU workspace capacity exceeded")
        }
        if storage.pointer == nil {
            storage.pointer = .allocate(capacity: storage.capacity)
            storage.pointer!.initialize(repeating: 0, count: storage.capacity)
            storage.allocations += 1
        }
        storage.active += 1
        defer { storage.active -= 1 }
        let pointer = storage.pointer!
        try body(pointer, pointer + matrixCount, pointer + matrixCount + rhsCount,
                 storage.capacity - matrixCount - rhsCount)
        storage.uses += 1
    }
    public static func check() throws {
        enum Sentinel: Error { case expected }
        begin(); defer { end() }
        do {
            try withBuffers(matrixCount: 16, rhsCount: 8) { a, b, _, _ in
                a[0] = 17; b[0] = 23; throw Sentinel.expected
            }
            preconditionFailure("Expected throw")
        } catch Sentinel.expected {}
        precondition(snapshot()["active"] == 0)
        try withBuffers(matrixCount: 16, rhsCount: 8) { a, b, _, _ in
            precondition(a[0] == 17 && b[0] == 23)
        }
        do {
            try withBuffers(matrixCount: 32 * 1024 * 1024 / 8, rhsCount: 1) { _, _, _, _ in
                preconditionFailure("Over-capacity body executed")
            }
            preconditionFailure("Over-capacity request accepted")
        } catch is SwiftMLError {}
        precondition(snapshot()["allocations"] == 1 && snapshot()["uses"] == 1 && snapshot()["active"] == 0)
    }
}
'''
(source/'Sources/SwiftML/Core/CPUWorkspaceTrial.swift').write_text(workspace)
p=source/'Sources/SwiftML/Core/LinearRegression.swift';s=p.read_text()
start=s.index('    private func fitCPUAnalytical<F: RegressionFeatures>');end=s.index('    /// Explicit Gradient Descent CPU backend.',start)
original=s[start:end]
candidate=original.replace('private func fitCPUAnalytical<','private func fitCPUWorkspace<',1)
candidate=candidate.replace('        var AColMajor = [Double](repeating: 0.0, count: rows * cols)','        try CPUWorkspaceTrial.withBuffers(matrixCount: rows * cols, rhsCount: Int(ldb)) { AColMajor, bVec, work, scratchCount in')
candidate=candidate.replace('        var bVec = [Double](repeating: 0.0, count: Int(ldb))\n','')
candidate=candidate.replace('&AColMajor','AColMajor').replace('&bVec','bVec')
candidate=candidate.replace('        var work = [Double](repeating: 0.0, count: Int(lwork))','        guard lwork > 0 && Int(lwork) <= scratchCount else { throw SwiftMLError.invalidParameter("Trial LAPACK scratch capacity exceeded") }')
candidate=candidate.replace('&work,','work,')
candidate=candidate.replace('Array(bVec.prefix(cols))','Array(UnsafeBufferPointer(start: bVec, count: cols))')
idx=candidate.rfind('    }');candidate=candidate[:idx]+'        }\n'+candidate[idx:]
s=s[:end]+candidate+'\n'+s[end:]
s=s.replace('            try fitCPUAnalytical(features: features, targets: targets)','            if CPUWorkspaceTrial.isEnabled { try fitCPUWorkspace(features: features, targets: targets) }\n            else { try fitCPUAnalytical(features: features, targets: targets) }',1)
p.write_text(s)
p=source/'Benchmarks/UnifiedMemoryPrototype/Integration/RetainedMemory.swift';s=p.read_text()
s=s.replace('            let result: MixedResult','            let fitStart = now()\n            let result: MixedResult')
s=s.replace('            let fixture = shape.fixture','            let fitElapsed = now() - fitStart\n            let fixture = shape.fixture')
s=s.replace('"phase": "job", "stream": streamDescription','"phase": "job", "fit_ns": fitElapsed, "stream": streamDescription')
s=s.replace('try await warmCalibrationRuntime(.cpu); try await warmCalibrationRuntime(.gpu)','try await warmCalibrationRuntime(.cpu)')
s=s.replace('    let warmed = try retentionSnapshot()','    let warmed = try retentionSnapshot()\n    let reuse = ProcessInfo.processInfo.environment["CPU_WORKSPACE_REUSE"] == "1"\n    if reuse { CPUWorkspaceTrial.begin() }\n    defer { if reuse { CPUWorkspaceTrial.end() } }')
s=s.replace('    let dropped = try retentionSnapshot()','    let dropped = try retentionSnapshot()\n    let workspace = CPUWorkspaceTrial.snapshot()\n    if reuse {\n        try expect(workspace["allocations"] == 1 && workspace["uses"] == cycles * 3 && workspace["active"] == 0, "all fits use one bounded workspace without fallback")\n        CPUWorkspaceTrial.end()\n        try expect(CPUWorkspaceTrial.snapshot()["owned_bytes"] == 0, "workspace owner released")\n    }\n    let workspaceDropped = try retentionSnapshot()')
s=s.replace('"status": "passed", "stream_scope"','"workspace_reuse": reuse, "workspace": workspace, "after_workspace_dropped": workspaceDropped, "status": "passed", "stream_scope"')
p.write_text(s)
p=source/'Benchmarks/UnifiedMemoryPrototype/Integration/main.swift';s=p.read_text().replace('(1...3).contains(cycles)','(1...12).contains(cycles)')
s=s.replace('if args.count == 5, args[0] == "--memory-lifetime"','if args == ["--cpu-workspace-check"] {\n    try CPUWorkspaceTrial.check()\n    try expect(CPUWorkspaceTrial.snapshot()["owned_bytes"] == 0, "workspace check releases capacity")\n    try output(["status": "passed", "checks": "throw, reuse, capacity rejection, release"])\n} else if args.count == 5, args[0] == "--memory-lifetime"')
p.write_text(s)
(out/'source.txt').write_text(str(source)+'\n')
changed=['Sources/SwiftML/Core/CPUWorkspaceTrial.swift','Sources/SwiftML/Core/LinearRegression.swift','Benchmarks/UnifiedMemoryPrototype/Integration/RetainedMemory.swift','Benchmarks/UnifiedMemoryPrototype/Integration/main.swift']
for n in changed:
 original=root/n
 diff=subprocess.run(['diff','-u',str(original) if original.exists() else '/dev/null',str(source/n)],capture_output=True,text=True)
 (out/(Path(n).name+'.patch')).write_text(diff.stdout)
try:
 with (out/'build.log').open('w') as log:r=run_process(base['command'],cwd=source,stdout=log,stderr=subprocess.STDOUT,timeout=1200)
 assert r.returncode==0,'See build.log'
 copy=worker.with_name('SwiftSciCPUWorkspaceTrial');shutil.copy2(worker,copy)
 c.write(out/'build.json',dict(base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),source=str(source),command=base['command'],files={n:c.digest(source/n) for n in list(base['files'])+['Sources/SwiftML/Core/CPUWorkspaceTrial.swift']},binary_sha256=c.digest(copy),scope='Disposable bounded CPU workspace trial. Environment-selected arm, same solver algorithm, CPU-only warmup before enabling the pool. No production changes.'))
 print('BUILD PASSED',copy,flush=True)
finally:
 shutil.copy2(worker.with_name('SwiftSciMatrixCleanupFixed'),worker)
 assert c.digest(worker)==base['binary_sha256']
