# Sorting prototype design decision

Use candidate A's narrow radix design as the base. The cross-judge scored A 22/25 and B 16/25. The parent agrees on the base after reading both packages. The recorded usage examples in both drafts contain API mistakes and are not implementation instructions. Actual callers use column.sortedIndices(ascending:) and frame.sortBy(_:ascending:).

Keep two independent branches at d23bf7cac9. Radix reuses its existing transformed keys and source-ordered valid indices. For each active digit, workers count into private histogram rows, the coordinator prefixes by bucket then source-worker order, and workers scatter into disjoint destination intervals. There are two concurrentPerform joins per digit, separated by serial prefix work. Borrows enclose all parallel work. A private unchecked-Sendable pointer context describes the borrow and manual write proof; do not obscure pointers by converting them to Int addresses.

The competing chunk experiment uses contiguous records containing a transformed UInt64 key and original Int row. Each chunk sorts by key and original row, so stable ties do not rely on an undocumented local-sort ordering assumption. Adjacent chunks merge with left-on-equal selection through a second record array. Merge passes join before owner swaps. The final Int result and missing rows become the existing public permutation. These are algorithm scratch records, not a general column-storage migration.

Adapt candidate B's explicit left-biased merges and source-order provenance. Reject its unspecified allocation-free local stable-sort requirement. Use the existing standard-library buffer sort, account for its uncertain internal temporary storage, and measure process memory separately. Record buffers and materializing the Int permutation have a larger explicit peak than radix. A merge-level serial tail is a measured limitation, not a reason to add merge-path partitioning before evidence.

Reject both drafts' extra policy or strategy overrides. Separate frozen executables and public calls isolate candidates without a new interface. Reject speculative 32-bit recovery on this macOS target. No arithmetic fallback is needed for histogram dimensions bounded by actual available workers and an already allocated valid row count. Range boundaries use quotient and remainder rather than multiplying count by worker number.

The source review at 2196173097 included the scalar gather specialization. The experiment deliberately returns to d23bf7cac9, which has the same sort implementation but excludes that gather change. New source is limited to one private algorithm helper and its call site in each branch, with the same public regression tests.

The frozen evaluation-plan.md owns the measurement and acceptance rules. Candidate proposals for 10M-row tests, a universal percentage threshold, or comparing RSS against an exact allocator prediction are not adopted. Production compatibility is unchanged. Both prototypes remain removable until correctness, operation timing and held-out evidence justify a choice.

Implementation starts with the parallel radix helper and public stable-permutation tests. If pointer ownership or preparation requires more public types, stop and revise this design rather than building a scheduler framework.
