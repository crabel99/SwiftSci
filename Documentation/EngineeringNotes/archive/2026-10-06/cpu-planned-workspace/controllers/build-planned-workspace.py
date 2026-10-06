import json,shutil,subprocess,sys,tempfile
from pathlib import Path
root=Path('/Users/crabel/Documents/src/SwiftSci');sys.path.insert(0,str(root/'Benchmarks/UnifiedMemoryPrototype'));import run as c
from processes import run_process
prior=Path('/Users/crabel/local-ai/spl/swiftsci/cpu-workspace-20261006/adaptive');out=Path('/Users/crabel/local-ai/spl/swiftsci/cpu-planned-workspace-20261006');out.mkdir(exist_ok=True)
base=json.loads((prior/'build.json').read_text());original=Path(base['source']);source=Path(tempfile.mkdtemp(prefix='source-planned-workspace-',dir=c.CACHE))
for n,h in base['files'].items():
 assert c.digest(original/n)==h
 p=source/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(original/n,p)
p=source/'Sources/SwiftML/Core/CPUWorkspaceTrial.swift';s=p.read_text().replace('import Darwin','import Darwin\nimport Accelerate\n\npublic enum CPUWorkspaceTrialError: Error, Sendable { case capacity }')
s=s.replace('        var adaptive = false','        var adaptive = false\n        var plannedCount = 0')
s=s.replace('public static func begin() {','public static func begin(plannedBytes: Int = 0) {')
s=s.replace('        storage.allocations = 0;', '        precondition(plannedBytes >= 0 && plannedBytes <= storage.capacity * 8 && plannedBytes % Int(getpagesize()) == 0)\n        storage.plannedCount = plannedBytes / 8\n        storage.allocations = 0;')
s=s.replace('"owned_bytes": storage.allocatedCount * 8,','"owned_bytes": storage.allocatedCount * 8, "planned_bytes": storage.plannedCount * 8,')
s=s.replace('throw SwiftMLError.invalidParameter("Trial CPU workspace capacity exceeded")','throw CPUWorkspaceTrialError.capacity')
s=s.replace('        let desired = storage.adaptive ?', '        guard storage.plannedCount == 0 || needed <= storage.plannedCount else { throw CPUWorkspaceTrialError.capacity }\n        let desired = storage.plannedCount > 0 ? storage.plannedCount : storage.adaptive ?')
s=s.replace('} catch is SwiftMLError {}','} catch is CPUWorkspaceTrialError {}')
insert='''    public static func requiredBytes(rows: Int, width: Int) throws -> Int {
        let limit = 32 * 1024 * 1024 / 8
        guard rows > width, width > 0, width < Int32.max, rows <= Int32.max,
              rows <= limit / (width + 1) else { throw CPUWorkspaceTrialError.capacity }
        var trans = Int8(78), m = Int32(rows), n = Int32(width + 1), nrhs = Int32(1)
        var lda = m, ldb = m, lwork = Int32(-1), info = Int32(0)
        var a = 0.0, b = 0.0, query = 0.0
        dgels_(&trans, &m, &n, &nrhs, &a, &lda, &b, &ldb, &query, &lwork, &info)
        guard info == 0, query.isFinite, query > 0, query <= Double(limit) else { throw CPUWorkspaceTrialError.capacity }
        let needed = rows * (width + 1) + rows + Int(query)
        let pageCount = Int(getpagesize()) / 8
        let rounded = ((needed + pageCount - 1) / pageCount) * pageCount
        guard rounded <= limit else { throw CPUWorkspaceTrialError.capacity }
        return rounded * 8
    }
'''
s=s.replace('    public static func check()',insert+'    public static func check()');p.write_text(s)
p=source/'Sources/SwiftML/Core/LinearRegression.swift';s=p.read_text();needle='''        } catch {
            try fitCPUGradientDescent(features: features, targets: targets, learningRate: lr, epochs: epochs)
''';assert s.count(needle)==1;s=s.replace(needle,'''        } catch let error as CPUWorkspaceTrialError {
            throw error
        } catch {
            try fitCPUGradientDescent(features: features, targets: targets, learningRate: lr, epochs: epochs)
''');p.write_text(s)
p=source/'Benchmarks/UnifiedMemoryPrototype/Integration/RetainedMemory.swift';s=p.read_text()
start=s.index('    let sequence: [ConcurrentShape]');end=s.index('    var shapes =',start)
shape=s[start:end].replace('    let sequence: [ConcurrentShape]\n','').replace('sequence =','return')
s=s[:start]+'    let sequence = retentionShapes(profile)\n'+s[end:]
s=s.replace('private struct RetentionEvidence','private func retentionShapes(_ profile: String) -> [ConcurrentShape] {\n'+shape+'}\n\nprivate struct RetentionEvidence')
s=s.replace('cycles: Int, streamScope: String) async throws -> RetentionEvidence','cycles: Int, streamScope: String, workspaceBudget: MemoryBudget? = nil) async throws -> RetentionEvidence')
s=s.replace('            let before = try retentionSnapshot()','''            let reserved = await workspaceBudget?.reservedBytes ?? 0
            if let workspaceBudget {
                let workspace = CPUWorkspaceTrial.snapshot()
                let budgetLimit = await workspaceBudget.limit
                try expect(reserved == budgetLimit && workspace["owned_bytes"]! <= reserved,
                           "workspace capacity stays reserved between fits")
            }
            let before = try retentionSnapshot()''')
s=s.replace('"phase": "job", "fit_ns": fitElapsed','"phase": "job", "workspace_reserved_bytes": reserved, "fit_ns": fitElapsed')
start=s.index('func retainedMemoryTrial(');s=s[:start]+'''func retainedMemoryTrial(profile: String, treatment: String, cycles: Int, streamScope: String = "job") async throws -> [String: Any] {
    try await warmCalibrationRuntime(.cpu)
    Memory.clearCache()
    let warmed = try retentionSnapshot()
    let started = now()
    let reuse = ProcessInfo.processInfo.environment["CPU_WORKSPACE_REUSE"] == "1"
    let planned = reuse && ProcessInfo.processInfo.environment["CPU_WORKSPACE_SIZING"] == "planned"
    let plannedBytes = planned ? try retentionShapes(profile).map { try CPUWorkspaceTrial.requiredBytes(rows: $0.rows, width: $0.width) }.max()! : 0
    let workspaceBudget = planned ? try MemoryBudget(limit: plannedBytes) : nil
    var setupNS: UInt64 = 0
    func measure() async throws -> (RetentionEvidence, [String: UInt64], [String: Int]) {
        setupNS = now() - started
        let evidence: RetentionEvidence
        if streamScope == "sequence" {
            evidence = try await MLX.Stream.withNewDefaultStream(device: profile == "gpu-sizes" ? .gpu : .cpu) {
                try await retentionSequence(profile: profile, treatment: treatment, cycles: cycles, streamScope: streamScope, workspaceBudget: workspaceBudget)
            }
        } else {
            evidence = try await retentionSequence(profile: profile, treatment: treatment, cycles: cycles, streamScope: streamScope, workspaceBudget: workspaceBudget)
        }
        let dropped = try retentionSnapshot()
        let workspace = CPUWorkspaceTrial.snapshot()
        if reuse {
            try expect((1...3).contains(workspace["allocations"]!) && workspace["owned_bytes"]! <= workspace["capacity_bytes"]! && workspace["uses"] == cycles * 3 && workspace["active"] == 0, "all fits use bounded workspace without fallback")
        }
        if planned {
            try expect(workspace["allocations"] == 1 && workspace["owned_bytes"] == plannedBytes, "planned workspace allocated once at reserved capacity")
        }
        return (evidence, dropped, workspace)
    }
    let result: (RetentionEvidence, [String: UInt64], [String: Int])
    if let workspaceBudget {
        result = try await withPlannedCPUWorkspace(bytes: plannedBytes, budget: workspaceBudget) { try await measure() }
    } else {
        if reuse { CPUWorkspaceTrial.begin() }
        do { result = try await measure(); if reuse { CPUWorkspaceTrial.end() } }
        catch { if reuse { CPUWorkspaceTrial.end() }; throw error }
    }
    let (evidence, dropped, workspace) = result
    let workspaceDropped = try retentionSnapshot()
    let measuredBatchNS = now() - started
    let reservedAfter = await workspaceBudget?.reservedBytes ?? 0
    let peakReserved = await workspaceBudget?.peak ?? 0
    try expect(CPUWorkspaceTrial.snapshot()["owned_bytes"] == 0 && reservedAfter == 0, "workspace and reservation released before independent references")
    Memory.clearCache()
    let cleared = try retentionSnapshot()
    let released = malloc_zone_pressure_relief(nil, 0)
    let relieved = try retentionSnapshot()
    try expect(relieved["mlx_active_bytes"] == 0 && relieved["mlx_cached_bytes"] == 0, "final retention cleanup releases MLX allocations")
    for (shape, result) in evidence.references {
        try await validateCalibrationResult(result, shape: shape, device: evidence.device)
    }
    return ["status": "passed", "workspace_reuse": reuse, "workspace": workspace,
            "planned_bytes": plannedBytes, "peak_reserved_bytes": peakReserved, "final_reserved_bytes": reservedAfter,
            "workspace_setup_ns": setupNS, "measured_batch_ns": measuredBatchNS,
            "stream_scope": streamScope, "profile": profile, "treatment": treatment, "cycles": cycles, "fits": cycles * 3,
            "shared_payload_bytes": evidence.payload, "warmed": warmed, "records": evidence.records,
            "after_inputs_dropped": dropped, "after_workspace_dropped": workspaceDropped,
            "after_final_mlx_clear": cleared, "after_final_malloc_relief": relieved,
            "final_malloc_reported_released_bytes": released,
            "scope": "Sequential shape transitions. Planned workspace reservation covers only arena capacity, not inputs, model state, allocator retention or total process footprint. Complete batch timing includes planning, input construction, diagnostics and explicit release. Independent numerical references follow all memory observations."]
}
''';p.write_text(s)
checks='''import Foundation
import SwiftML
import SwiftSciMemoryPrototypeCore

// Disposable integration helper. The global trial arena restricts this to one
// participating batch at a time; the shared budget in the checks enforces that.
func withPlannedCPUWorkspace<R>(bytes: Int, budget: MemoryBudget,
    operation: () async throws -> R) async throws -> R {
    let grant = try await budget.acquire(MemoryEstimate(capacities: [bytes]))
    CPUWorkspaceTrial.begin(plannedBytes: bytes)
    do {
        try Task.checkCancellation()
        let result = try await operation()
        CPUWorkspaceTrial.end()
        try expect(CPUWorkspaceTrial.snapshot()["owned_bytes"] == 0, "owner released before reservation")
        await grant.finish()
        return result
    } catch {
        CPUWorkspaceTrial.end()
        await grant.finish()
        throw error
    }
}

private actor PlannedCheckpoint {
    var reached = false
    func mark() { reached = true }
}

func plannedCPUWorkspaceChecks() async throws -> [String: Any] {
    enum Sentinel: Error { case expected }
    let bytes = try CPUWorkspaceTrial.requiredBytes(rows: 1024, width: 8)
    let budget = try MemoryBudget(limit: bytes)
    let input = try concurrentInput(ConcurrentShape(rows: 1024, width: 8), scaled: true)
    for shouldThrow in [false, true] {
        do {
            try await withPlannedCPUWorkspace(bytes: bytes, budget: budget) {
                _ = try await mixedFit(input, device: .cpu)
                let held = await budget.reservedBytes
                try expect(held == bytes && CPUWorkspaceTrial.snapshot()["owned_bytes"] == bytes, "reservation covers retained owner")
                if shouldThrow { throw Sentinel.expected }
            }
            try expect(!shouldThrow, "throwing branch propagates")
        } catch Sentinel.expected { try expect(shouldThrow, "expected throw") }
        let held = await budget.reservedBytes
        try expect(held == 0 && CPUWorkspaceTrial.snapshot()["owned_bytes"] == 0, "success or throw cleans up both owners")
    }
    let checkpoint = PlannedCheckpoint()
    let active = Task {
        try await withPlannedCPUWorkspace(bytes: bytes, budget: budget) {
            _ = try await mixedFit(input, device: .cpu)
            await checkpoint.mark()
            try await Task.sleep(nanoseconds: 10_000_000_000)
        }
    }
    do {
        for _ in 0..<1000 {
            if await checkpoint.reached { break }
            try await Task.sleep(nanoseconds: 1_000_000)
        }
        let reached = await checkpoint.reached
        try expect(reached, "active owner reaches cancellation checkpoint")
        let held = await budget.reservedBytes
        try expect(held == bytes && CPUWorkspaceTrial.snapshot()["owned_bytes"] == bytes, "cancellable batch still holds allocation and reservation")
        active.cancel()
        do { try await active.value; throw Sentinel.expected } catch is CancellationError {}
    } catch { active.cancel(); _ = try? await active.value; throw error }
    let afterActive = await budget.reservedBytes
    try expect(afterActive == 0 && CPUWorkspaceTrial.snapshot()["owned_bytes"] == 0, "active cancellation cleans up")
    let blocker = try await budget.acquire(MemoryEstimate(capacities: [bytes]))
    let queued = Task {
        try await withPlannedCPUWorkspace(bytes: bytes, budget: budget) { throw Sentinel.expected }
    }
    do {
        for _ in 0..<1000 {
            if await budget.queuedCount == 1 { break }
            try await Task.sleep(nanoseconds: 1_000_000)
        }
        let queuedCount = await budget.queuedCount
        try expect(queuedCount == 1 && !CPUWorkspaceTrial.isEnabled, "queued batch owns no workspace")
        queued.cancel()
        do { _ = try await queued.value; throw Sentinel.expected } catch is CancellationError {}
    } catch { queued.cancel(); _ = try? await queued.value; await blocker.finish(); throw error }
    await blocker.finish()
    let afterQueued = await budget.reservedBytes
    try expect(afterQueued == 0 && CPUWorkspaceTrial.snapshot()["owned_bytes"] == 0, "queued cancellation cleans up")
    let small = Int(getpagesize()), smallBudget = try MemoryBudget(limit: Int(getpagesize()))
    let model = LinearRegression(device: .cpu)
    do {
        try await withPlannedCPUWorkspace(bytes: small, budget: smallBudget) {
            try await model.fit(features: input.train, targets: input.targets)
        }
        throw Sentinel.expected
    } catch is CPUWorkspaceTrialError {}
    let state = await model.getWeightsAndBias()
    try expect(state.weights == nil && state.bias == nil, "undersized plan does not train through fallback")
    let afterCapacityError = await smallBudget.reservedBytes
    try expect(afterCapacityError == 0 && CPUWorkspaceTrial.snapshot()["owned_bytes"] == 0, "capacity error cleans up")
    return ["status": "passed", "checks": ["success lifetime", "throw cleanup", "active cancellation", "queued cancellation", "capacity error without solver fallback"], "planned_bytes": bytes]
}
'''
(source/'Benchmarks/UnifiedMemoryPrototype/Integration/PlannedCPUWorkspace.swift').write_text(checks)
p=source/'Benchmarks/UnifiedMemoryPrototype/Integration/main.swift';s=p.read_text().replace('if args == ["--cpu-workspace-check"] {','if args == ["--planned-cpu-workspace-check"] {\n    try await output(plannedCPUWorkspaceChecks())\n} else if args == ["--cpu-workspace-check"] {');p.write_text(s)
(out/'source.txt').write_text(str(source)+'\n');worker=c.CACHE/'derived/Build/Products/Release/SwiftSciMemoryIntegrationPrototype'
try:
 with (out/'build.log').open('w') as log:r=run_process(base['command'],cwd=source,stdout=log,stderr=subprocess.STDOUT,timeout=1200)
 assert r.returncode==0,'See build.log'
 copy=worker.with_name('SwiftSciCPUPlannedWorkspaceTrial');shutil.copy2(worker,copy)
 c.write(out/'build.json',dict(base_commit=base['base_commit'],source=str(source),command=base['command'],files={n:c.digest(source/n) for n in list(base['files'])+['Benchmarks/UnifiedMemoryPrototype/Integration/PlannedCPUWorkspace.swift']},binary_sha256=c.digest(copy),scope='Disposable batch-planned CPU arena, one allocation with a held workspace-only MemoryBudget reservation. Capacity errors bypass solver fallback in this snapshot. No production edits.'))
 print('BUILD PASSED',copy,flush=True)
finally:shutil.copy2(worker.with_name('SwiftSciMatrixCleanupFixed'),worker)
