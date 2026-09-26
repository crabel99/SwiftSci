# Flat group IDs and bounded integer lookup

Branch: `codex/dataframe-optimizations`. Changes are committed locally.

## Changes

- `464c0b3cae` replaces per-group row arrays with one row-to-group array, representative rows and row counts. Numeric reductions visit source rows in order. Transforms expand values through the same group IDs.
- `e861980165` replaces hashing with an array lookup when integer keys occupy a narrow enough range. Group IDs still follow first appearance, including a separate null group.

The lookup holds at most 65,536 entries and at most one entry per input row. On this 64-bit Mac the lookup itself uses at most 512 KiB, in addition to the group-ID arrays. Bounds checks use overflow-reporting subtraction. A range that exceeds the limit falls back to hashing immediately, without scanning the remaining keys first. Sparse and wide integer ranges retain hashing.

## Evidence

Before these changes, the focused million-row probe measured grouped sum at 22.568 ms and row counts at 19.341 ms. Native sampling showed dictionary lookup and hashing as the largest costs, followed by numeric reduction. The experiments tested flat storage and sequential reads first, then bounded lookup separately.

Each direct comparison alternates before/after executable order across three batches, with two warmups and fifteen measured iterations per process. The tables report medians of 45 measured samples. Output checks passed. Executable hashes were checked against the saved binaries.

| Step | Operation | Before, ms | After, ms | Speedup |
|---|---|---:|---:|---:|
| Flat group IDs | group | 24.090 | 18.936 | 1.27x |
| Flat group IDs | group_count | 19.849 | 17.471 | 1.14x |
| Bounded lookup | group | 18.490 | 3.962 | 4.67x |
| Bounded lookup | group_count | 15.823 | 2.559 | 6.18x |

## Key distribution checks

These probes use a key column and one numeric value column. All have one million rows except the unique-key case, which has 100,000. They compare the flat-ID hash implementation against bounded lookup plus hash fallback. They are not the same workload as the three-column matched benchmark.

| Distribution | Before, ms | After, ms |
|---|---:|---:|
| dense | 17.461 | 3.205 |
| sparse | 17.920 | 16.763 |
| near_min | 17.753 | 3.150 |
| all_null | 10.148 | 3.376 |
| nullable | 18.369 | 3.252 |
| unique | 23.664 | 23.291 |

All complete output checks passed. Narrow, nullable and near-Int64.min ranges improved substantially. Sparse and unique-key timings stayed close to the hash baseline; small differences should not be treated as separate speedups.

## Validation

281 scoped tests pass in Debug and Release. Tests cover accumulation order, all numeric aggregation operations, first/last behavior, NaN and infinity, all-null groups, transforms, key formatting, first-seen order, empty inputs, numeric widths, lookup-budget boundaries, sparse fallback and integer extremes. The scope is dataframe, statistics, forecasting and independent checks, not every SwiftSci module.

The final matched run passed all output comparisons at 100,000 and 1,000,000 rows. Million-row results:

| Operation | SwiftSci, ms | Kiraa, ms | pandas/NumPy, ms |
|---|---:|---:|---:|
| Filter | 3.554 | 2.835 | 2.546 |
| Sort | 65.710 | 58.721 | 30.777 |
| Group | 3.809 | 9.778 | 5.421 |

SwiftSci is faster on this grouped-sum workload, which has a single integer key with 100 groups and two numeric value columns. This does not establish an advantage for arbitrary keys, multiple-key grouping or every aggregation. The results are local CPU measurements on a shared Mac.

[Complete matched report](/Users/crabel/local-ai/spl/swiftpandas/benchmark/results/20260926T003937Z/REPORT.md)

Column storage remains unchanged. Packed values and validity bitmaps are still a separate storage-design proposal.
