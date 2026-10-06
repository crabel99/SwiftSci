import Foundation
import Darwin

private final class Flag: @unchecked Sendable {
    private let lock = NSLock()
    private var value = false
    func set() { lock.withLock { value = true } }
    func get() -> Bool { lock.withLock { value } }
}
private func poll(_ semaphore: DispatchSemaphore) -> Bool { semaphore.wait(timeout: .now()) == .success }
private enum ProbeError: Error { case timeout }
@main struct AsyncCloseProbe {
    static func main() async throws {
        let owner = try CPUWorkspaceTrial(plannedBytes: Int(getpagesize()))
        let entered = DispatchSemaphore(value: 0), leave = DispatchSemaphore(value: 0)
        let closingStarted = Flag(), borrowerReleased = Flag(), lateBodyRan = Flag()
        let borrower = Task.detached {
            try owner.withTrialBorrow {
                entered.signal()
                guard leave.wait(timeout: .now() + 4) == .success else { throw ProbeError.timeout }
                borrowerReleased.set()
            }
        }
        while !poll(entered) { try await Task.sleep(nanoseconds: 1_000_000) }
        let closer = Task.detached { closingStarted.set(); await owner.close() }
        while !closingStarted.get() { try await Task.sleep(nanoseconds: 1_000_000) }
        try await Task.sleep(nanoseconds: 20_000_000)
        // A watchdog lets the old blocking implementation exit with a useful verdict.
        DispatchQueue.global().asyncAfter(deadline: .now() + 2) { leave.signal() }
        var rejected = false
        do { try owner.withTrialBorrow { lateBodyRan.set() } }
        catch CPUWorkspaceTrialError.closed { rejected = true }
        let rejectedBeforeRelease = rejected && !borrowerReleased.get() && !lateBodyRan.get()
        leave.signal()
        try await borrower.value; await closer.value
        let record: [String: Any] = ["status": rejectedBeforeRelease ? "passed" : "failed", "late_borrow_rejected_before_active_borrow_finished": rejectedBeforeRelease, "late_body_ran": lateBodyRan.get(), "owned_bytes_after_close": owner.snapshot()["owned_bytes"]!]
        print(String(data: try JSONSerialization.data(withJSONObject: record, options: .sortedKeys),encoding: .utf8)!)
        if !rejectedBeforeRelease { exit(2) }
    }
}
