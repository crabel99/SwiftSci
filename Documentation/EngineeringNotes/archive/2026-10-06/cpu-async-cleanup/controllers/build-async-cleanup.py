import json,shutil,sys,subprocess,tempfile
from pathlib import Path
root=Path('/Users/crabel/Documents/src/SwiftSci');sys.path.insert(0,str(root/'Benchmarks/UnifiedMemoryPrototype'));import run as c
from processes import run_process
base=json.loads(Path('/Users/crabel/local-ai/spl/swiftsci/cpu-scoped-workspace-20261006/build.json').read_text());out=Path('/Users/crabel/local-ai/spl/swiftsci/cpu-async-cleanup-20261006');out.mkdir(exist_ok=True)
source=Path(tempfile.mkdtemp(prefix='source-async-cleanup-',dir=c.CACHE));shutil.copytree(base['source'],source,dirs_exist_ok=True);(out/'source.txt').write_text(str(source)+'\n')
p=source/'Sources/SwiftML/Core/CPUWorkspaceTrial.swift';old=p.read_text();required=old[old.index('    public static func requiredBytes'):old.index('    public static func check')]
p.write_text('''import Foundation
import Darwin
import Accelerate

public enum CPUWorkspaceTrialError: Error, Sendable { case capacity, closed }

// Disposable CPU owner. State is locked briefly; numerical borrowing remains exclusive.
public final class CPUWorkspaceTrial: @unchecked Sendable {
    private enum State { case open, closing, closed }
    private let stateLock = NSLock()
    private let borrowLock = NSLock()
    private let plannedCount: Int
    private var pointer: UnsafeMutablePointer<Double>?
    private var state: State = .open
    private var active = false
    private var closers: [CheckedContinuation<Void, Never>] = []
    private var allocations = 0
    private var releases = 0
    private var uses = 0
    public init(plannedBytes: Int) throws {
        guard plannedBytes > 0, plannedBytes <= 32 * 1024 * 1024,
              plannedBytes % Int(getpagesize()) == 0 else { throw CPUWorkspaceTrialError.capacity }
        plannedCount = plannedBytes / MemoryLayout<Double>.stride
    }
    deinit {
        precondition(!active && closers.isEmpty)
        pointer?.deinitialize(count: plannedCount); pointer?.deallocate()
    }
    public func snapshot() -> [String: Int] {
        stateLock.withLock {
            ["capacity_bytes": plannedCount * 8, "planned_bytes": plannedCount * 8,
             "owned_bytes": pointer == nil ? 0 : plannedCount * 8,
             "allocations": allocations, "releases": releases, "uses": uses,
             "active": active ? 1 : 0, "closing": state == .closing ? 1 : 0,
             "closed": state == .closed ? 1 : 0, "pending_closers": closers.count]
        }
    }
    // Cleanup deliberately waits through cancellation. Existing native work must finish.
    public func close() async {
        await withCheckedContinuation { continuation in
            let completed = stateLock.withLock {
                if state == .closed { return true }
                state = .closing
                if active {
                    closers.append(continuation)
                    return false
                }
                releaseStorage()
                return true
            }
            if completed { continuation.resume() }
        }
    }
    // Called only with stateLock held and no borrower accessing the pointer.
    private func releaseStorage() {
        precondition(!active)
        if let pointer {
            pointer.deinitialize(count: plannedCount); pointer.deallocate()
            self.pointer = nil
            releases += 1
        }
        state = .closed
    }
    private func finishBorrow(succeeded: Bool) {
        let waiting = stateLock.withLock {
            precondition(active)
            active = false
            if succeeded { uses += 1 }
            guard state == .closing else { return [CheckedContinuation<Void, Never>]() }
            releaseStorage()
            let waiting = closers
            closers.removeAll()
            return waiting
        }
        // Resuming outside the lock allows closers and diagnostics to make progress.
        for continuation in waiting { continuation.resume() }
    }
    func withBuffers(matrixCount: Int, rhsCount: Int, scratchCount: Int = 1,
        _ body: (UnsafeMutablePointer<Double>, UnsafeMutablePointer<Double>, UnsafeMutablePointer<Double>, Int) throws -> Void) throws {
        try stateLock.withLock { guard state == .open else { throw CPUWorkspaceTrialError.closed } }
        borrowLock.lock(); defer { borrowLock.unlock() }
        let buffer = try stateLock.withLock {
            // A borrower queued before close must also observe the transition.
            guard state == .open else { throw CPUWorkspaceTrialError.closed }
            guard matrixCount > 0, rhsCount > 0, scratchCount > 0,
                  matrixCount < plannedCount, rhsCount < plannedCount - matrixCount,
                  scratchCount <= plannedCount - matrixCount - rhsCount else { throw CPUWorkspaceTrialError.capacity }
            precondition(!active)
            if pointer == nil {
                pointer = .allocate(capacity: plannedCount)
                pointer!.initialize(repeating: 0, count: plannedCount)
                allocations += 1
            }
            active = true
            return pointer!
        }
        var succeeded = false
        defer { finishBorrow(succeeded: succeeded) }
        try body(buffer, buffer + matrixCount, buffer + matrixCount + rhsCount,
                 plannedCount - matrixCount - rhsCount)
        succeeded = true
    }
    // Test-only entry point. No pointer is exposed to the caller.
    public func withTrialBorrow(_ body: () throws -> Void) throws {
        try withBuffers(matrixCount: 16, rhsCount: 8) { a, b, _, _ in
            a[0] = 17; b[0] = 23
            try body()
            precondition(a[0] == 17 && b[0] == 23)
        }
    }
''' + required + '''    public static func check() async throws {
        enum Sentinel: Error { case expected }
        let a = try CPUWorkspaceTrial(plannedBytes: Int(getpagesize()))
        let b = try CPUWorkspaceTrial(plannedBytes: Int(getpagesize()))
        do {
            do { try a.withTrialBorrow { throw Sentinel.expected }; preconditionFailure() }
            catch Sentinel.expected {}
            try a.withBuffers(matrixCount: 16, rhsCount: 8) { ap, _, _, _ in
                try b.withBuffers(matrixCount: 16, rhsCount: 8) { bp, _, _, _ in
                    precondition(ap != bp); bp[0] = 99; precondition(ap[0] == 17)
                }
            }
            await a.close(); await a.close()
            precondition(a.snapshot()["owned_bytes"] == 0 && a.snapshot()["releases"] == 1 && b.snapshot()["owned_bytes"]! > 0)
            do { try a.withTrialBorrow {}; preconditionFailure("Closed owner reused") }
            catch CPUWorkspaceTrialError.closed {}
            try b.withBuffers(matrixCount: 16, rhsCount: 8) { p, _, _, _ in precondition(p[0] == 99) }
            await b.close()
        } catch { await a.close(); await b.close(); throw error }
    }
}
''')
p=source/'Benchmarks/UnifiedMemoryPrototype/Integration/PlannedCPUWorkspace.swift';s=p.read_text().replace('owner.end()', 'await owner.close()').replace('try CPUWorkspaceTrial.check()', 'try await CPUWorkspaceTrial.check()')
a=s.index('    // Scope exit races');b=s.index('    let final = await budget.reservedBytes',a)
s=s[:a]+'''    // A fitted model and exported values outlive the workspace, which is already closed.
    let returnedModel = try await withPlannedCPUWorkspace(bytes: bytes, budget: budget) { owner in
        escaped = owner
        let model = LinearRegression(device: .cpu, trialWorkspace: owner)
        try await model.fit(features: input.train, targets: input.targets)
        return model
    }
    let heldAfterReturn = await budget.reservedBytes
    try expect(heldAfterReturn == 0 && escaped?.snapshot()["closed"] == 1 && escaped?.snapshot()["owned_bytes"] == 0, "returned model owns no live scratch")
    let returnedPredictions = try await returnedModel.predict(features: input.query)
    let returnedState = await returnedModel.getWeightsAndBias()
    try expect(returnedPredictions == reference.predictions && returnedState.weights == reference.weights && returnedState.bias == reference.bias, "returned model remains usable after workspace close")
    try await withPlannedCPUWorkspace(bytes: bytesB, budget: shared) { owner in
        try assertSame(try await mixedFit(inputB, device: .cpu, workspace: owner), referenceB)
    }
    let laterPredictions = try await returnedModel.predict(features: input.query)
    try expect(laterPredictions == returnedPredictions && returnedPredictions == reference.predictions, "later workspace use cannot overwrite retained model or results")

    // Successful and throwing native borrowers both drain before asynchronous close returns.
    for shouldThrow in [false, true] {
        let entered = DispatchSemaphore(value: 0), releaseBorrow = DispatchSemaphore(value: 0)
        let borrowGate = ScopedCheckpoint(), closeGate = ScopedCheckpoint()
        let scope = Task.detached {
            try await withPlannedCPUWorkspace(bytes: bytes, budget: budget) { owner in
                await borrowGate.mark(1, owner)
                let borrower = Task.detached {
                    try owner.withTrialBorrow {
                        entered.signal()
                        guard releaseBorrow.wait(timeout: .now() + 5) == .success else { throw PrototypeError.shape }
                        if shouldThrow { throw ScopedSentinel.expected }
                    }
                }
                try await waitUntil("borrow entered") { pollSemaphore(entered) }
                return borrower
            }
        }
        var extraClosers: [Task<Void, Never>] = []
        do {
            try await waitUntil("owner publishes closing while native borrower is active") {
                guard let owner = await borrowGate.owners[1] else { return false }
                return owner.snapshot()["closing"] == 1 && owner.snapshot()["active"] == 1
            }
            let owner = await borrowGate.owners[1]!
            try expect(owner.snapshot()["owned_bytes"] == bytes, "closing retains active allocation")
            for id in 1...2 {
                extraClosers.append(Task.detached { await owner.close(); await closeGate.mark(id, owner) })
            }
            try await waitUntil("repeated closers join the existing close") { owner.snapshot()["pending_closers"] == 3 }
            extraClosers[0].cancel()
            try expect(await closeGate.owners.isEmpty, "cancelled close still waits for the borrower")
            do { try owner.withTrialBorrow { throw ScopedSentinel.expected }; throw ScopedSentinel.expected }
            catch CPUWorkspaceTrialError.closed {}
            // Queued admission cannot proceed while the old owner still holds storage.
            let waiting = Task { try await budget.acquire(MemoryEstimate(capacities: [bytes])) }
            do {
                try await waitUntil("closing reservation remains held") { await budget.queuedCount == 1 }
                let held = await budget.reservedBytes
                try expect(held == bytes && owner.snapshot()["active"] == 1, "grant survives cancelled closer and late borrower rejection")
                releaseBorrow.signal()
                let borrower = try await scope.value
                do { try await borrower.value; try expect(!shouldThrow, "throwing borrower propagates") }
                catch ScopedSentinel.expected { try expect(shouldThrow, "expected native throw") }
                for closer in extraClosers { await closer.value }
                let next = try await waiting.value
                let snapshot = owner.snapshot()
                try expect(snapshot["closed"] == 1 && snapshot["owned_bytes"] == 0 && snapshot["active"] == 0 && snapshot["releases"] == 1 && snapshot["pending_closers"] == 0 && snapshot["uses"] == (shouldThrow ? 0 : 1), "all closers observe one completed release")
                await next.finish()
                await owner.close()
                try expect(owner.snapshot()["releases"] == 1, "close remains idempotent after completion")
            } catch { waiting.cancel(); releaseBorrow.signal(); if let next = try? await waiting.value { await next.finish() }; throw error }
        } catch {
            releaseBorrow.signal()
            if let borrower = try? await scope.value { _ = try? await borrower.value }
            for closer in extraClosers { await closer.value }
            throw error
        }
    }
''' +s[b:]
s=s.replace('try expect(await closeGate.owners.isEmpty, "cancelled close still waits for the borrower")','let noneClosed = await closeGate.owners.isEmpty\n            try expect(noneClosed, "cancelled close still waits for the borrower")')
s=s.replace('"last synchronous borrow retains grant"', '"closing rejects new work", "multiple asynchronous closers", "cancelled close drains", "throwing borrower drains", "last borrow retains grant", "returned model and results survive close"').replace('"explicit_fits": 10', '"explicit_fits": 12');p.write_text(s)
p=source/'Benchmarks/UnifiedMemoryPrototype/Integration/main.swift';p.write_text(p.read_text().replace('try CPUWorkspaceTrial.check()', 'try await CPUWorkspaceTrial.check()'))
# First rerun the same small failing-before probe against the new owner.
probe=out/'after-probe'
command=['xcrun','swiftc','-O','-parse-as-library',str(source/'Sources/SwiftML/Core/CPUWorkspaceTrial.swift'),'/private/tmp/AsyncCloseProbe.swift','-o',str(probe)]
r=run_process(command,text=True,capture_output=True,timeout=60);(out/'after-probe-build.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr
records=[]
for _ in range(10):
 r=run_process([str(probe)],text=True,capture_output=True,timeout=10);record=json.loads(r.stdout);assert r.returncode==0 and record['status']=='passed';records.append(record)
c.write(out/'after-probe.json',records);print('Focused probe passed ten runs',flush=True)
worker=c.CACHE/'derived/Build/Products/Release/SwiftSciMemoryIntegrationPrototype'
try:
 with (out/'build.log').open('w') as log:r=run_process(base['command'],cwd=source,stdout=log,stderr=subprocess.STDOUT,timeout=1200)
 assert r.returncode==0,'See async cleanup build.log'
 copy=worker.with_name('SwiftSciCPUAsyncCleanupTrial');shutil.copy2(worker,copy)
 c.write(out/'build.json',dict(base_commit=base['base_commit'],source=str(source),command=base['command'],files={n:c.digest(source/n) for n in base['files']},binary_sha256=c.digest(copy),scope='Disposable CPU workspace with asynchronous close, explicit closing state, late-borrow rejection and result lifetime tests. Workspace-only reservations; no production edits.'))
 print('BUILD PASSED',copy,flush=True)
finally:shutil.copy2(worker.with_name('SwiftSciMatrixCleanupFixed'),worker)
