# Retained memory reservation handoff trial

Date: 2026-10-06

## Decision and scope

Keep retained-result accounting on the local trial branch `codex/retained-memory-accounting-trial`, based on PR #62's head. The submitted prepared-memory PR remains unchanged. The trial adds 31 lines to the existing admission implementation and ten focused tests. Its interface is package-only.

- Base: `2cd1cbe52a12537d472fd2176eae2676e30dcc80`.
- Trial: `53ee8dbcb86396eac01a1e258ded10ff595d8a2f`.
- PR #62: https://github.com/Nodibell/SwiftSci/pull/62.

## Ownership contract

An operation initially reserves its estimated peak. After backend work finishes and excluded workspace is freed, `transfer(retaining:)` replaces that grant with a smaller or equal retained grant in one actor operation. It never waits for fresh admission. Only then does it admit FIFO waiters into the released capacity.

A successful transfer makes the original token inactive. Finishing or destroying it cannot release the replacement grant. An inactive token or an attempt to increase the reservation throws without changing accounting. Cancellation is checked before the transfer; if the operation has completed, its new token is returned so the caller can own or release it. Concurrent finish and transfer calls are resolved in actor order.

The allocation owner holds the new token. It must free the allocation before releasing the token. ARC fallback releases admission asynchronously, which can conservatively delay another job. This remains estimate-based admission; it does not intercept allocations or enforce a process RSS limit.

## Alternatives and tradeoff

Reacquiring retained bytes while holding the full operation grant can deadlock at capacity. Releasing the full grant first can admit competing work before the retained bytes are accounted for. The atomic transfer avoids both cases while preserving the existing queue, cancellation handling, and release mechanism.

A generic result wrapper cannot establish this contract for arbitrary Swift arrays. An array or model alias can escape the wrapper and keep storage alive after its token disappears. The fixture therefore owns one exclusive allocation and exposes only a numerical reduction. It frees that allocation in its destructor before its token is destroyed. This demonstrates the ownership order without introducing a production container API.

## Validation

A dependency-free Swift package compiled the exact trial `MemoryBudget.swift`, the seven existing admission tests, and ten new handoff tests. All 17 passed in each configuration:

- Release.
- Debug with Address Sanitizer.
- Debug with Thread Sanitizer.

The sanitizer runtimes were verified in the linked test executables. Each run includes 128 finish/transfer races, 128 competing-transfer races, and 128 concurrent jobs that hand off smaller results. Other cases cover full-capacity handoff, FIFO blocking, cancellation, invalid estimates, zero and maximum capacities, and the final storage owner's cleanup.

The local evidence directory is `retained-memory-accounting-20261006`. It contains `qualification.json`, the isolated `Package.swift`, and logs for each run. The JSON records source and binary hashes. Qualification used Swift 6.4 on Apple silicon with macOS 27. These are focused admission and ownership tests; the full SwiftSci/MLX suite was not rerun for this experiment. No performance improvement is claimed from these tests.

## Next integration boundary

Choose one real retained owner and attach the reservation to its actual storage lifetime. A refit must account for old and replacement state simultaneously until replacement succeeds. Prediction outputs and public array copies need explicit ownership semantics before they can be included. Do not double-count retained bytes when estimating subsequent operations on the same budget.

The trial does not yet integrate production model state, multiple independent retained owners, asynchronous GPU completion, or arbitrary escaping storage aliases. Those need caller-specific validation before promotion into a production PR. Keep the engineering record on `codex/engineering-notes`.
