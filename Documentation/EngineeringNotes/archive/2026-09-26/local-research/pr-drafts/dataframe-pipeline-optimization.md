# Optimize dataframe CSV, filtering, sorting and grouped reductions

Draft for review. Target: `Nodibell/SwiftSci:main`. Source: `crabel99:codex/dataframe-pipeline-optimization`. No pull request has been submitted.

---

SwiftDataFrame repeatedly performs dynamic type checks, formats grouping keys as strings, rescans nulls and allocates intermediate CSV indexes. This change moves type dispatch outside row loops, reuses known column metadata, and reduces allocation and data movement across complete dataframe operations.

The branch also fixes numeric comparison and grouping edge cases encountered during optimization. It preserves the public optional-array column representation. Compact storage and its downstream scientific/AI integration are separate work.

## Changes

- Typed numeric filtering and gathering, exact integer/floating comparisons, cached null predicates, and parallel gathering based on estimated output work.
- Stable typed sorting with adaptive Double radix/comparison paths and existing NaN fallback behavior.
- Flat first-seen group IDs, bounded integer lookup/refinement, and typed composite-key identity. Nulls, literal sentinel strings and delimiter-containing tuples remain distinct.
- Compensated grouped sums and means, plus opt-in `sumChecked()` for exact integer totals with explicit overflow errors.
- Flat CSV field storage, lifetime-scoped mapped bytes, parallel scanning for eligible unquoted files, exact final index allocation, fused null counting, and corrected decimal rounding.
- Regression tests, API notes, raw benchmark evidence and comparison workers. The Metal CSV experiment remains an opt-in benchmark because it did not outperform the CPU path.

## Measured improvements

Apple M4 Max, 128 GiB unified memory, native arm64 Release. These are separate matched before/after experiments at one million rows. Do not multiply the stage ratios into a cumulative speedup.

| Change | Before | After | Improvement |
|---|---:|---:|---:|
| Initial cached typed sorting | 213.743 ms | 68.419 ms | 3.12x |
| Typed integer group keys | 249.548 ms | 22.548 ms | 11.07x |
| Later bounded two-key grouping | 49.536 ms | 11.375 ms | 4.35x |
| Later adaptive Double sorting | 65.674 ms | 36.288 ms | 1.81x |
| CSV scan/allocation stage | 38.947 ms | 13.565 ms | 2.87x |
| Final Float64 filtering stage | 3.237 ms | 1.944 ms | 1.66x |
| Final native Int filtering stage | 3.737 ms | 1.951 ms | 1.92x |

The CSV scan/allocation stage reduced whole-process peak RSS from 310.1 to 186.4 MiB, about 40%. Final filtering gains had essentially unchanged peak RSS. These are measured process peaks, including fixtures and retained results, rather than isolated column-allocation measurements.

## Comparison with other libraries

Final source `4c5bb95354`, one million rows, median of 15 timed samples across three fresh processes per library. Each process has two warmups; library order rotates and workloads run serially.

| Operation | SwiftSci | pandas / Python | Kiraa |
|---|---:|---:|---:|
| CSV read | 13.560 ms | 67.064 ms | 9.171 ms |
| Float64 filter | 1.940 ms | 2.121 ms | 2.830 ms |
| Native Int / Int64 filter | 1.971 ms | 1.846 ms | INVALID |
| Stable descending sort | 31.367 ms | 29.229 ms | 58.971 ms |
| Single-key group sum | 4.663 ms | 4.896 ms | 9.361 ms |
| Two-key group sum | 11.336 ms | 10.599 ms | 36.498 ms |
| Filter → sort → group | 17.012 ms | 20.118 ms | 41.025 ms |

All 24 SwiftSci workload/size combinations passed output comparison. Kiraa's native-integer filter failed parity at both sizes and its timings are excluded. Kiraa remains faster on this CSV fixture; pandas remains faster on sorting, two-key grouping and million-row integer filtering. At 100,000 rows, two-key grouping takes 4.107 ms for SwiftSci versus 1.658 ms for pandas and 3.977 ms for Kiraa.

The [committed evidence report](https://github.com/crabel99/SwiftSci/blob/codex/dataframe-pipeline-optimization/Benchmarks/Results/DataFrameOptimization/README.md) includes both sizes, all operations, memory, timing spread, baseline/binary hashes, raw samples, reproduction instructions and rejected alternatives. It also distinguishes unmodified numerical comparison workloads from gains attributable to this PR.

## Validation

- Full Debug suite: 891 passed, zero failed or skipped.
- Full Release suite: 891 passed, zero failed or skipped.
- Both include MLX-dependent tests and 978 device-level executions after parameter expansion.
- Independent filter checks cover 96 tuning layouts, 24 holdout layouts and 96 operator cases, with exact row/value/schema/null-count checks.
- Parser AddressSanitizer and ThreadSanitizer checks each passed 764 cases over 87,060,376 input bytes at the CSV-stage revision. Later commits did not change parser source.
- Regression coverage includes stable ties/null placement, large integers, fractional thresholds, NaNs/infinities, composite-key collisions, compensated/exact sums, CSV quoting, mapped-buffer lifetime and decimal rounding.

The full suites validate implementation commit `4c5bb95354`. The later evidence commit changes no production code. The relocated comparison runner was smoke-tested separately against the recorded binaries; this did not replace the recorded performance run. Remote CI has not yet validated an upstream merge.

## Compatibility and limitations

`sumChecked()` is additive. Group output keys remain String columns in first-appearance order, while identity now avoids earlier string/sentinel collisions. Existing `sum()` retains Double results. Numeric filtering corrects precision-boundary and NaN behavior; the included API notes describe those changes.

The benchmark machine was shared with other applications. The CSV speed claim covers a warm-cache, three-numeric-column fixture without quotes. Libraries differ in inferred CSV types and internal parallelism. Peak RSS includes runtime/import/setup costs. Small timing differences should not be treated as stable universal rankings.

Existing CSV integer-parser overflow, sampled type inference, trailing-delimiter behavior and NaN-sort fallback remain outside this patch. Cross-library floating comparisons use explicit tolerances; exact boundary regression tests complement them. No compact-storage replacement, production GPU CSV path or AI inference speedup is claimed.
