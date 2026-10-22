# Native UTF-8 preflight review

Recommend a separate trial. Rejecting an over-budget token set should not require scanning most of its bytes first. This changes the preparation algorithm, not a fixture-specific threshold.

The public [String storage predicate](https://developer.apple.com/documentation/swift/string/iscontiguousutf8) is suitable. [Swift's implementation](https://github.com/swiftlang/swift/blob/main/stdlib/public/core/StringProtocol.swift#L164-L186) returns the fast UTF-8 storage flag. [UTF8View.count](https://github.com/swiftlang/swift/blob/main/stdlib/public/core/StringUTF8View.swift#L292-L299) then reads the stored byte count; foreign storage takes a different path. Do not call makeContiguousUTF8 or copy foreign tokens to make them eligible.

Use this order:

1. Require more than two tokens and count <= selectedRowCount / 2.
2. Set remaining = selectedRowCount - count - count. This avoids multiplying count or summing lengths, so admission cannot overflow.
3. First Set traversal checks each token's isContiguousUTF8 before reading utf8.count. Reject if its byte count exceeds remaining; otherwise subtract it.
4. Only after every length fits, traverse the same immutable Set again, validate ASCII bytes once, and form the masks. Exact-budget completion succeeds. Reject non-ASCII tokens and saturated masks as before.

For admitted inputs, two token traversals plus scanned bytes fit the row-derived budget. Rejected byte budgets cost at most one metadata traversal, without scanning token contents. Set and String value semantics preserve the snapshot; retain the original Set only on success. Decode behavior and canonical String membership remain unchanged.

A non-ASCII token encountered late can still waste an ASCII validation scan. The proposal fixes length-budget rejection, not every preparation failure.

Compare against cleanup alone and the current candidate at both old and new admission boundaries. Cover mixed native/foreign storage, exact budgets, long tokens, null density, and eager/streamed modes. Verify foreign fixtures actually have noncontiguous storage. Require measured CPU and memory acceptance; traversal accounting cannot establish a CPU-optimal crossover.
