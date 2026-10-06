import json,shutil,sys,subprocess,tempfile
from pathlib import Path
root=Path('/Users/crabel/Documents/src/SwiftSci');sys.path.insert(0,str(root/'Benchmarks/UnifiedMemoryPrototype'));import run as c
from processes import run_process
base=json.loads(Path('/Users/crabel/local-ai/spl/swiftsci/cpu-planned-workspace-20261006/build.json').read_text())
out=Path('/Users/crabel/local-ai/spl/swiftsci/cpu-scoped-workspace-20261006');out.mkdir(exist_ok=True)
source=Path(tempfile.mkdtemp(prefix='source-scoped-workspace-',dir=c.CACHE));shutil.copytree(base['source'],source,dirs_exist_ok=True);(out/'source.txt').write_text(str(source)+'\n')
p=source/'Sources/SwiftML/Core/CPUWorkspaceTrial.swift';old=p.read_text();required=old[old.index('    public static func requiredBytes'):old.index('    public static func check')]
p.write_text('''import Foundation
import Darwin
import Accelerate

public enum CPUWorkspaceTrialError: Error, Sendable { case capacity, closed }

// Disposable explicit-owner trial. The lock protects synchronous borrowing and close.
public final class CPUWorkspaceTrial: @unchecked Sendable {
    private let lock = NSLock()
    private let plannedCount: Int
    private var pointer: UnsafeMutablePointer<Double>?
    private var closed = false
    private var allocations = 0
    private var uses = 0
    public init(plannedBytes: Int) throws {
        guard plannedBytes > 0, plannedBytes <= 32 * 1024 * 1024,
              plannedBytes % Int(getpagesize()) == 0 else { throw CPUWorkspaceTrialError.capacity }
        plannedCount = plannedBytes / MemoryLayout<Double>.stride
    }
    deinit { pointer?.deinitialize(count: plannedCount); pointer?.deallocate() }
    public func snapshot() -> [String: Int] {
        lock.lock(); defer { lock.unlock() }
        return ["capacity_bytes": plannedCount * 8, "planned_bytes": plannedCount * 8,
                "owned_bytes": pointer == nil ? 0 : plannedCount * 8,
                "allocations": allocations, "uses": uses, "active": 0, "closed": closed ? 1 : 0]
    }
    public func end() {
        lock.lock(); defer { lock.unlock() }
        pointer?.deinitialize(count: plannedCount); pointer?.deallocate(); pointer = nil
        closed = true
    }
    func withBuffers(matrixCount: Int, rhsCount: Int, scratchCount: Int = 1,
        _ body: (UnsafeMutablePointer<Double>, UnsafeMutablePointer<Double>, UnsafeMutablePointer<Double>, Int) throws -> Void) throws {
        lock.lock(); defer { lock.unlock() }
        guard !closed else { throw CPUWorkspaceTrialError.closed }
        guard matrixCount > 0, rhsCount > 0, scratchCount > 0,
              matrixCount < plannedCount, rhsCount < plannedCount - matrixCount,
              scratchCount <= plannedCount - matrixCount - rhsCount else { throw CPUWorkspaceTrialError.capacity }
        if pointer == nil {
            pointer = .allocate(capacity: plannedCount)
            pointer!.initialize(repeating: 0, count: plannedCount)
            allocations += 1
        }
        let buffer = pointer!
        try body(buffer, buffer + matrixCount, buffer + matrixCount + rhsCount,
                 plannedCount - matrixCount - rhsCount)
        uses += 1
    }
    // Only the disposable lifetime checks use this entry point. Pointers cannot escape it.
    public func withTrialBorrow(_ body: () throws -> Void) throws {
        try withBuffers(matrixCount: 16, rhsCount: 8) { a, b, _, _ in
            a[0] = 17; b[0] = 23
            try body()
            precondition(a[0] == 17 && b[0] == 23)
        }
    }
''' + required + '''    public static func check() throws {
        enum Sentinel: Error { case expected }
        let a = try CPUWorkspaceTrial(plannedBytes: Int(getpagesize()))
        let b = try CPUWorkspaceTrial(plannedBytes: Int(getpagesize()))
        defer { a.end(); b.end() }
        do { try a.withTrialBorrow { throw Sentinel.expected }; preconditionFailure() }
        catch Sentinel.expected {}
        try a.withBuffers(matrixCount: 16, rhsCount: 8) { ap, _, _, _ in
            try b.withBuffers(matrixCount: 16, rhsCount: 8) { bp, _, _, _ in
                precondition(ap != bp); bp[0] = 99; precondition(ap[0] == 17)
            }
        }
        a.end(); a.end()
        precondition(a.snapshot()["owned_bytes"] == 0 && b.snapshot()["owned_bytes"]! > 0)
        do { try a.withTrialBorrow {}; preconditionFailure("Closed owner reused") }
        catch CPUWorkspaceTrialError.closed {}
        try b.withBuffers(matrixCount: 16, rhsCount: 8) { p, _, _, _ in precondition(p[0] == 99) }
    }
}
''')
p=source/'Sources/SwiftML/Core/LinearRegression.swift';s=p.read_text().replace('    private var cpuWeights:', '    private var trialWorkspace: CPUWorkspaceTrial?\n    private var cpuWeights:')
s=s.replace('public init(device: ExecutionDevice = .auto) {\n        self.requestedDevice = device','public init(device: ExecutionDevice = .auto, trialWorkspace: CPUWorkspaceTrial? = nil) {\n        self.trialWorkspace = trialWorkspace\n        self.requestedDevice = device')
s=s.replace('if CPUWorkspaceTrial.isEnabled { try fitCPUWorkspace(features: features, targets: targets) }','if let trialWorkspace { try fitCPUWorkspace(features: features, targets: targets, workspace: trialWorkspace) }')
s=s.replace('private func fitCPUWorkspace<F: RegressionFeatures>(features: F, targets: [Double]) throws','private func fitCPUWorkspace<F: RegressionFeatures>(features: F, targets: [Double], workspace: CPUWorkspaceTrial) throws').replace('CPUWorkspaceTrial.withBuffers(', 'workspace.withBuffers(');p.write_text(s)
p=source/'Benchmarks/UnifiedMemoryPrototype/Integration/MixedDevice.swift';s=p.read_text().replace('func mixedFit(_ input: ConcurrentInput, device: ExecutionDevice) async','func mixedFit(_ input: ConcurrentInput, device: ExecutionDevice, workspace: CPUWorkspaceTrial? = nil) async').replace('let model = LinearRegression(device: device)','let model = LinearRegression(device: device, trialWorkspace: workspace)',1);p.write_text(s)
p=source/'Benchmarks/UnifiedMemoryPrototype/Integration/RetainedMemory.swift';s=p.read_text();s=s.replace('workspaceBudget: MemoryBudget? = nil) async','workspaceBudget: MemoryBudget? = nil, owner: CPUWorkspaceTrial? = nil) async').replace('mixedFit(input, device: device)','mixedFit(input, device: device, workspace: owner)')
s=s.replace('CPUWorkspaceTrial.snapshot()', '(owner?.snapshot() ?? ["owned_bytes": 0, "allocations": 0, "uses": 0, "active": 0])')
s=s.replace('let planned = reuse && ProcessInfo.processInfo.environment["CPU_WORKSPACE_SIZING"] == "planned"','let planned = reuse')
s=s.replace('func measure() async', 'func measure(_ owner: CPUWorkspaceTrial?) async').replace('workspaceBudget: workspaceBudget)', 'workspaceBudget: workspaceBudget, owner: owner)')
a=s.index('    let result: (RetentionEvidence,');b=s.index('    let (evidence, dropped, workspace)',a)
s=s[:a]+'''    let result: (RetentionEvidence, [String: UInt64], [String: Int])
    var releasedOwner: CPUWorkspaceTrial?
    if let workspaceBudget {
        result = try await withPlannedCPUWorkspace(bytes: plannedBytes, budget: workspaceBudget) { owner in
            releasedOwner = owner
            return try await measure(owner)
        }
    } else { result = try await measure(nil) }
'''+s[b:]
s=s.replace('try expect((owner?.snapshot() ?? ["owned_bytes": 0, "allocations": 0, "uses": 0, "active": 0])["owned_bytes"] == 0 && reservedAfter == 0','try expect((releasedOwner?.snapshot()["owned_bytes"] ?? 0) == 0 && reservedAfter == 0');p.write_text(s)
p=source/'Benchmarks/UnifiedMemoryPrototype/Integration/main.swift';s=p.read_text();s=s.replace('    try expect(CPUWorkspaceTrial.snapshot()["owned_bytes"] == 0, "workspace check releases capacity")\n','');p.write_text(s)
# Lifetime and overlap checks are supplied separately and copied into this snapshot.
shutil.copy2('/private/tmp/ScopedCPUWorkspace.swift',source/'Benchmarks/UnifiedMemoryPrototype/Integration/PlannedCPUWorkspace.swift')
worker=c.CACHE/'derived/Build/Products/Release/SwiftSciMemoryIntegrationPrototype'
try:
 with (out/'build.log').open('w') as log:r=run_process(base['command'],cwd=source,stdout=log,stderr=subprocess.STDOUT,timeout=1200)
 assert r.returncode==0,'See scoped build.log'
 copy=worker.with_name('SwiftSciCPUScopedWorkspaceTrial');shutil.copy2(worker,copy)
 names=set(base['files'])|{'Benchmarks/UnifiedMemoryPrototype/Integration/MixedDevice.swift'}
 c.write(out/'build.json',dict(base_commit=base['base_commit'],source=str(source),command=base['command'],files={n:c.digest(source/n) for n in sorted(names)},binary_sha256=c.digest(copy),scope='Disposable per-batch CPU workspace, explicit model injection and workspace-only reservations; no production edits.'))
 print('BUILD PASSED',copy,flush=True)
finally:shutil.copy2(worker.with_name('SwiftSciMatrixCleanupFixed'),worker)
