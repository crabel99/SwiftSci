import Foundation
import Darwin

private final class Signal: @unchecked Sendable {
    private let lock = NSLock()
    private var value = false
    func set() { lock.withLock { value = true } }
    func get() -> Bool { lock.withLock { value } }
}
private enum Failure: Error { case expected, check(String) }
private func require(_ value: Bool, _ message: String) throws { if !value { throw Failure.check(message) } }
private func poll(_ semaphore: DispatchSemaphore) -> Bool { semaphore.wait(timeout: .now()) == .success }
private func until(_ predicate: () -> Bool) async throws {
    for _ in 0..<3000 {
        if predicate() { return }
        try await Task.sleep(nanoseconds: 1_000_000)
    }
    throw Failure.check("deadline")
}
@main struct AsyncCloseStress {
    static func main() async throws {
        let rounds = 100
        for round in 0..<rounds {
            let owner = try CPUWorkspaceTrial(plannedBytes: Int(getpagesize()))
            let entered = DispatchSemaphore(value: 0), release = DispatchSemaphore(value: 0)
            let requested = Signal(), queuedRan = Signal(), closedA = Signal(), closedB = Signal()
            let shouldThrow = round % 2 == 0
            let first = Task.detached {
                try owner.withTrialBorrow {
                    entered.signal()
                    guard release.wait(timeout: .now() + 5) == .success else { throw Failure.check("borrow deadline") }
                    if shouldThrow { throw Failure.expected }
                }
            }
            try await until { poll(entered) }
            let queued = Task.detached {
                requested.set()
                do { try owner.withTrialBorrow { queuedRan.set() }; return false }
                catch CPUWorkspaceTrialError.closed { return true }
            }
            try await until { requested.get() }
            try await Task.sleep(nanoseconds: 1_000_000)
            let a = Task.detached { await owner.close(); closedA.set() }
            try await until { owner.snapshot()["closing"] == 1 }
            let b = Task.detached { await owner.close(); closedB.set() }
            try await until { owner.snapshot()["pending_closers"] == 2 }
            a.cancel()
            do { try owner.withTrialBorrow { throw Failure.check("late body executed") }; throw Failure.check("late admission") }
            catch CPUWorkspaceTrialError.closed {}
            try require(owner.snapshot()["active"] == 1 && owner.snapshot()["owned_bytes"]! > 0, "live borrower remains owned")
            try require(!closedA.get() && !closedB.get(), "closers do not finish early")
            release.signal()
            do { try await first.value; try require(!shouldThrow, "throw must propagate") }
            catch Failure.expected { try require(shouldThrow, "unexpected throw") }
            let rejected = try await queued.value
            await a.value; await b.value
            await owner.close()
            let state = owner.snapshot()
            try require(rejected && !queuedRan.get(), "previously queued borrower rejects after close")
            try require(state["owned_bytes"] == 0 && state["active"] == 0 && state["closed"] == 1 && state["pending_closers"] == 0, "closed state complete")
            try require(state["allocations"] == 1 && state["releases"] == 1 && state["uses"] == (shouldThrow ? 0 : 1), "exactly one allocation and release")
        }
        weak var weakOwner: CPUWorkspaceTrial?
        do {
            let owner = try CPUWorkspaceTrial(plannedBytes: Int(getpagesize()))
            weakOwner = owner
            try owner.withTrialBorrow {}
        }
        try require(weakOwner == nil, "unclosed unborrowed owner uses ARC fallback")
        print("{\"status\":\"passed\",\"rounds\":\(rounds),\"throwing_borrowers\":50,\"normal_borrowers\":50,\"arc_fallback\":true}")
    }
}
