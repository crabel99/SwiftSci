import Foundation
import Darwin
import MLX
import SwiftML
import SwiftSciMemoryPrototypeCore

// Disposable helper. The model receives an owner explicitly; no task-local or global arena exists.
func withPlannedCPUWorkspace<R>(bytes: Int, budget: MemoryBudget,
    operation: (CPUWorkspaceTrial) async throws -> R) async throws -> R {
    let grant = try await budget.acquire(MemoryEstimate(capacities: [bytes]))
    do {
        let owner = try CPUWorkspaceTrial(plannedBytes: bytes)
        do {
            try Task.checkCancellation()
            let result = try await operation(owner)
            owner.end()
            try expect(owner.snapshot()["owned_bytes"] == 0, "release workspace before its grant")
            await grant.finish()
            return result
        } catch {
            owner.end()
            throw error
        }
    } catch { await grant.finish(); throw error }
}

private func pollSemaphore(_ semaphore: DispatchSemaphore) -> Bool { semaphore.wait(timeout: .now()) == .success }
private enum ScopedSentinel: Error { case expected }
private actor ScopedCheckpoint {
    var owners: [Int: CPUWorkspaceTrial] = [:]
    var released: Set<Int> = []
    var completed = false
    func mark(_ id: Int, _ owner: CPUWorkspaceTrial) { owners[id] = owner }
    func release(_ id: Int) { released.insert(id) }
    func finish() { completed = true }
    func wait(_ id: Int) async throws {
        for _ in 0..<5000 {
            if released.contains(id) { return }
            try await Task.sleep(nanoseconds: 1_000_000)
        }
        throw PrototypeError.shape
    }
}
private func waitUntil(_ message: String, _ condition: () async -> Bool) async throws {
    for _ in 0..<3000 {
        if await condition() { return }
        try await Task.sleep(nanoseconds: 1_000_000)
    }
    try expect(false, message)
}
private func assertSame(_ a: MixedResult, _ b: MixedResult) throws {
    let av = a.predictions + a.weights + [a.bias], bv = b.predictions + b.weights + [b.bias]
    try expect(av.count == bv.count && zip(av, bv).allSatisfy { $0.isFinite && $0 == $1 }, "overlapping fit matches original solver exactly")
}

func plannedCPUWorkspaceChecks() async throws -> [String: Any] {
    try CPUWorkspaceTrial.check()
    let shape = ConcurrentShape(rows: 1024, width: 8)
    let bytes = try CPUWorkspaceTrial.requiredBytes(rows: shape.rows, width: shape.width)
    let budget = try MemoryBudget(limit: bytes)
    let input = try concurrentInput(shape, scaled: true)
    let reference = try await mixedFit(input, device: .cpu)
    var escaped: CPUWorkspaceTrial?
    for shouldThrow in [false, true] {
        do {
            try await withPlannedCPUWorkspace(bytes: bytes, budget: budget) { owner in
                escaped = owner
                try assertSame(try await mixedFit(input, device: .cpu, workspace: owner), reference)
                let held = await budget.reservedBytes
                try expect(held == bytes && owner.snapshot()["owned_bytes"] == bytes, "reservation covers retained owner")
                if shouldThrow { throw ScopedSentinel.expected }
            }
            try expect(!shouldThrow, "throwing branch propagates")
        } catch ScopedSentinel.expected { try expect(shouldThrow, "expected throw") }
        let held = await budget.reservedBytes
        try expect(held == 0 && escaped?.snapshot()["owned_bytes"] == 0, "success or throw closes escaped owner before releasing grant")
    }
    let escapedModel = LinearRegression(device: .cpu, trialWorkspace: escaped!)
    do { try await escapedModel.fit(features: input.train, targets: input.targets); throw ScopedSentinel.expected }
    catch CPUWorkspaceTrialError.closed {}
    let escapedState = await escapedModel.getWeightsAndBias()
    try expect(escapedState.weights == nil && escapedState.bias == nil, "closed owner does not use unreserved fallback")
    let small = Int(getpagesize()), smallBudget = try MemoryBudget(limit: Int(getpagesize()))
    var undersizedModel: LinearRegression?
    do {
        try await withPlannedCPUWorkspace(bytes: small, budget: smallBudget) { owner in
            escaped = owner
            let model = LinearRegression(device: .cpu, trialWorkspace: owner); undersizedModel = model
            try await model.fit(features: input.train, targets: input.targets)
        }
        throw ScopedSentinel.expected
    } catch CPUWorkspaceTrialError.capacity {}
    let state = await undersizedModel!.getWeightsAndBias()
    let afterSmall = await smallBudget.reservedBytes
    try expect(state.weights == nil && state.bias == nil && afterSmall == 0 && escaped?.snapshot()["owned_bytes"] == 0, "capacity error releases and bypasses fallback")
    do { try await withPlannedCPUWorkspace(bytes: 1, budget: smallBudget) { _ in throw ScopedSentinel.expected }; throw ScopedSentinel.expected }
    catch CPUWorkspaceTrialError.capacity {}
    let afterInvalid = await smallBudget.reservedBytes
    try expect(afterInvalid == 0, "constructor failure refunds grant")

    // Both batches retain an allocated arena while the third waits for admission.
    let shapeB = ConcurrentShape(rows: 2048, width: 8)
    let bytesB = try CPUWorkspaceTrial.requiredBytes(rows: shapeB.rows, width: shapeB.width)
    let inputB = try concurrentInput(shapeB, scaled: true)
    let referenceB = try await mixedFit(inputB, device: .cpu)
    let shared = try MemoryBudget(limit: bytes + bytesB), gate = ScopedCheckpoint()
    let first = Task.detached {
        try await MLX.Stream.withNewDefaultStream(device: .cpu) {
            try await withPlannedCPUWorkspace(bytes: bytes, budget: shared) { owner in
                for _ in 0..<3 { try assertSame(try await mixedFit(input, device: .cpu, workspace: owner), reference) }
                await gate.mark(1, owner)
                try await gate.wait(1)
            }
        }
    }
    let second = Task.detached {
        try await MLX.Stream.withNewDefaultStream(device: .cpu) {
            try await withPlannedCPUWorkspace(bytes: bytesB, budget: shared) { owner in
                for _ in 0..<3 { try assertSame(try await mixedFit(inputB, device: .cpu, workspace: owner), referenceB) }
                await gate.mark(2, owner)
                try await gate.wait(2)
                try assertSame(try await mixedFit(inputB, device: .cpu, workspace: owner), referenceB)
            }
        }
    }
    var queued: Task<Void, Error>?
    do {
        try await waitUntil("both independent batches become live") { await gate.owners.count == 2 }
        let owners = await gate.owners
        try expect(owners[1] !== owners[2], "different explicit owners")
        let held = await shared.reservedBytes
        try expect(held == bytes + bytesB && owners[1]!.snapshot()["owned_bytes"] == bytes && owners[2]!.snapshot()["owned_bytes"] == bytesB, "shared reservation covers both allocations")
        queued = Task.detached {
            try await withPlannedCPUWorkspace(bytes: bytes, budget: shared) { _ in throw ScopedSentinel.expected }
        }
        try await waitUntil("third batch queues before allocation") { await shared.queuedCount == 1 }
        queued!.cancel()
        do { try await queued!.value; throw ScopedSentinel.expected } catch is CancellationError {}
        first.cancel()
        do { try await first.value; throw ScopedSentinel.expected } catch is CancellationError {}
        let remaining = await shared.reservedBytes
        try expect(remaining == bytesB && owners[1]!.snapshot()["owned_bytes"] == 0 && owners[2]!.snapshot()["owned_bytes"] == bytesB, "cancellation only releases its own owner and grant")
        try await withPlannedCPUWorkspace(bytes: bytes, budget: shared) { owner in
            try assertSame(try await mixedFit(input, device: .cpu, workspace: owner), reference)
            try expect(owner !== owners[2], "replacement has an independent owner")
        }
        await gate.release(2)
        try await second.value
        let after = await shared.reservedBytes, peak = await shared.peak, queuedCount = await shared.queuedCount
        try expect(after == 0 && queuedCount == 0 && peak == bytes + bytesB && owners[2]!.snapshot()["owned_bytes"] == 0, "overlapping batches clean up and remain in budget")
        try expect(owners[1]!.snapshot()["uses"] == 3 && owners[2]!.snapshot()["uses"] == 4, "all overlapping fits use their assigned workspace")
    } catch {
        first.cancel(); second.cancel(); queued?.cancel()
        _ = try? await first.value; _ = try? await second.value
        if let queued { _ = try? await queued.value }
        throw error
    }

    // Scope exit races an escaped synchronous borrower. Its grant must remain held.
    let entered = DispatchSemaphore(value: 0), releaseBorrow = DispatchSemaphore(value: 0)
    let borrowGate = ScopedCheckpoint()
    let scope = Task.detached {
        try await withPlannedCPUWorkspace(bytes: bytes, budget: budget) { owner in
            await borrowGate.mark(1, owner)
            let borrower = Task.detached {
                try owner.withTrialBorrow {
                    entered.signal()
                    guard releaseBorrow.wait(timeout: .now() + 5) == .success else { throw PrototypeError.shape }
                }
            }
            try await waitUntil("borrow entered") { pollSemaphore(entered) }
            await borrowGate.mark(2, owner)
            return borrower
        }
    }
    do {
        try await waitUntil("scope operation reaches return with live borrow") { await borrowGate.owners[2] != nil }
        // Queue another grant while close waits for the synchronous borrower.
        let waiting = Task { try await budget.acquire(MemoryEstimate(capacities: [bytes])) }
        do {
            try await waitUntil("close retains reservation for active borrower") { await budget.queuedCount == 1 }
            let held = await budget.reservedBytes
            try expect(held == bytes, "borrow keeps workspace reservation")
            releaseBorrow.signal()
            let borrower = try await scope.value
            try await borrower.value
            let next = try await waiting.value
            let old = await borrowGate.owners[1]!
            try expect(old.snapshot()["closed"] == 1 && old.snapshot()["owned_bytes"] == 0 && old.snapshot()["uses"] == 1, "borrow finishes before owner release and next admission")
            await next.finish()
        } catch { waiting.cancel(); releaseBorrow.signal(); if let next = try? await waiting.value { await next.finish() }; throw error }
    } catch { releaseBorrow.signal(); if let borrower = try? await scope.value { _ = try? await borrower.value }; throw error }
    let final = await budget.reservedBytes
    try expect(final == 0, "last-borrow test releases every grant")
    return ["status": "passed", "checks": ["independent buffers", "idempotent close", "success lifetime", "throw cleanup", "escaped closed owner rejection", "undersized plan without fallback", "constructor failure refund", "two allocated batches", "queued cancellation", "active batch cancellation isolation", "replacement admission", "surviving batch numerical result", "last synchronous borrow retains grant"], "explicit_fits": 10, "shared_budget_bytes": bytes + bytesB, "final_reserved_bytes": final]
}
