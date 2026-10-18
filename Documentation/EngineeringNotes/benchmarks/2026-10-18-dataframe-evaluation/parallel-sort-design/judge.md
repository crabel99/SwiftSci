# Cross-judge decision

## Scores

| Criterion | Candidate A | Candidate B |
|---|---:|---:|
| Actual public API and compatibility | 4/5 | 2/5 |
| Disjoint synchronous ownership | 5/5 | 5/5 |
| Bounded, honest scratch accounting | 5/5 | 2/5 |
| Small private implementation | 4/5 | 3/5 |
| Independent public-operation falsification | 4/5 | 4/5 |
| **Total** | **22/25** | **16/25** |

## Judgment

Use Candidate A as the radix experiment's base. It stays closest to the existing serial radix path: reuse key preparation, add worker-private 2,048-bin histograms, prefix in worker order, and scatter stably into disjoint ranges. Its ownership argument is complete and its added scratch is bounded by worker count. The implementation can remain one private Double-specific kernel with no scheduler or public policy.

Candidate A still needs pruning. Its caller examples are close but not exact. The grounded forms are `column.sortedIndices(ascending: true)` and `frame.sortBy("key", ascending: false)`; `sortedIndices` is not throwing and `sortBy` takes an unlabeled column name. Drop the proposed test-only strategy enum. Independent branches from the same fixed commit, exercised through the real public operations, give a stronger experiment and avoid permanent selection machinery. Drop the speculative 32-bit fallback because the package targets macOS 14. Describe each active digit as two synchronous `concurrentPerform` phases with a serial prefix step, rather than three barriers. Prefer a narrow `@unchecked Sendable` borrowed-pointer context with the disjoint-range proof beside it over converting addresses to `Int` merely because gather currently does so.

Candidate B has a sound merge ownership proof, especially its deterministic contiguous runs, disjoint output ranges, synchronous joins, and left-biased merges. Its proposed caller API is wrong: the actual API uses `ascending: Bool`, not `SortOrder`, `order:`, or `sortBy(column:)`. More seriously, the design requires a stable local range sorter that adds no chunk-sized scratch but neither grounds such an implementation nor specifies one. Reusing the cached-value helper may allocate pair arrays, while writing a new in-place stable sorter would enlarge the experiment and confound the comparison. The forced no-extra-scratch condition is therefore an unsupported design constraint.

Keep merge as the independent measured control, but replace Candidate B's local-sort section with the intended concrete design. Prepare contiguous `(UInt64 key, Int row)` records after the full NaN-rejecting scan. Sort each worker-owned record slice with the standard library buffer sort, using key then row as the comparison so equal numeric keys retain source order. Merge adjacent runs into a second record buffer, choosing the left record on equal keys. Account for both record buffers and any uncontracted standard-library temporary allocation. Do not claim parity with radix scratch. This design accepts extra memory to remove indirect key loads and tests whether that locality beats radix's linear passes.

## Required grafts and falsifiers

Both experiments should retain Candidate B's explicit source/destination non-aliasing rule, owner lifetime through each synchronous phase, deterministic uneven-range partitioning, and Release-focused validation. Candidate A should retain its transactional full preparation scan, signed-zero normalization, descending key complement, source-ordered missing list, and NaN fallback before concurrent writes.

Falsify each branch through `sortedIndices(ascending:)` and `sortBy(_:ascending:)`, not only a prepared-buffer helper. Compare exact permutations and gathered Double bit patterns against the unchanged baseline for both directions, duplicates across worker boundaries, signed zeros, nulls, infinities, late NaN, constant radix digits, and threshold edges. Use the frozen screening and held-out process plan as written. Report permutation time, complete-sort time, logical simultaneous scratch, and RSS. Any mismatch, nondeterminism, sanitizer finding, protected-case regression beyond the frozen limit, or failure of the held-out timing rule rejects that branch.
