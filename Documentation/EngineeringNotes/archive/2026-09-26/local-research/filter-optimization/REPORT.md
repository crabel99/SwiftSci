# Filter optimization results

Three independently validated changes are committed locally on `codex/dataframe-pipeline-optimization`. The branch remains unpublished. The measured production filter gain is 1.67 to 1.92 times at one million rows, with essentially unchanged peak process memory.

## Accepted changes

| Commit | Change | Evidence |
|---|---|---|
| `7bff91c08d` | Estimate gather work from selected rows and column storage width; reuse the column descriptor array across workers. | Helps large narrow tables and preserves wide-table behavior. Final dispatch threshold is 512 KiB of estimated output across at least two columns. |
| `4bfa26a0e6` | Native-width floating comparison for null-free columns and exactly representable thresholds. | Small operator-dependent Float32 gains. Nullable columns and nonrepresentable thresholds retain exact widened comparisons. |
| `4c5bb95354` | Use cached counts for null predicates on wholly present or wholly missing columns. | Eliminates needless scans and speeds full-index construction. Mixed columns retain existing behavior. |

## Matched before and after

Baseline is `4dc6b533dd`; candidate is `4c5bb95354`. The same production executable source and fixtures run in serial fresh processes with alternating binary order. Each library operation has three processes, two warmups per process, and five timed repetitions. Complete output equality passed for every pair. Values below are medians in milliseconds.

| Rows | Filter type | Before ms | After ms | Speedup |
|---:|---|---:|---:|---:|
| 100,000 | Float64 | 0.324 | 0.208 | 1.56x |
| 100,000 | Int | 0.378 | 0.210 | 1.80x |
| 100,000 | Int32 | 0.381 | 0.209 | 1.82x |
| 100,000 | Float32 | 0.377 | 0.214 | 1.76x |
| 1,000,000 | Float64 | 3.237 | 1.944 | 1.66x |
| 1,000,000 | Int | 3.737 | 1.951 | 1.92x |
| 1,000,000 | Int32 | 3.723 | 1.947 | 1.91x |
| 1,000,000 | Float32 | 3.768 | 1.985 | 1.90x |

[Raw matched results](/Users/LOCAL_USER/local-ai/spl/swiftsci/filter-optimization/production-before-after/summary.json). Million-row peak RSS stayed effectively unchanged. These production fixtures contain missing values, so their improvement primarily comes from gathering. The null-free Float path is evaluated separately below.

## Breadth and regressions

The tuning matrix has 96 layouts and the holdout has 24 previously unused layouts. They vary numeric type, row count, width, selection density, null density and match distribution. Holdout cases use another seed, intermediate sizes and widths, and String/Bool payloads. Every column value, row position, schema and null count is checked against an independent expected result before timing.

The initial 4 MiB dispatch threshold regressed some moderate wide-table gathers by serializing work that previously ran in parallel. Lowering the work threshold to 512 KiB removed those material regressions in the full tuning rerun. The initial unguarded native Float comparison also regressed dense nullable selections. Restricting it to columns with cached nullCount zero avoids that case. No rule depends on a benchmark ID or the observed match percentage.

For tuning cases with baseline full-filter time at least 0.05 ms, the revised gather and Float candidate had a 1.109 geometric-mean speedup. Three-column cases had a 1.350 speedup. The worst full-filter slowdown was about 3.3%. Those aggregate ratios exclude very short operations because timer and scheduling variation dominate their percentages.

The final implementation, including cached null checks, reached a 1.129 geometric-mean speedup across the 20 holdout cases above 0.05 ms. The four three-column holdouts averaged 1.717. The initial holdout showed slowdowns of 10.6% and 6.1% in two cases. One follow-up compared those two cases and two positive controls for five fresh-process rounds without code changes. The slow cases then measured 0.7% slower and 2.7% faster; the controls retained 1.89x and 1.78x speedups. The original holdout remains recorded, and it was not used to retune the code.

All 96 operator cases passed independent selected-index checks. They cover equality, inequality, all four ordered comparisons, both null predicates, four numeric types, exact and fractional thresholds, NaNs, infinities, and null-free/nullable columns. The guarded Float32 change averaged 1.033x across the eight null-free operator cases, including the unchanged null checks. Individual ordered-comparison gains varied; do not apply one multiplier to all filters.

For one million present values, cached `isNotNull` changed from about 1.93 ms to 0.34–0.51 ms across the four numeric types. Cached `isNull` returns an empty selection directly; several samples fall below timer resolution, so no finite speedup ratio is claimed. Ordinary comparison and mixed-null-predicate geometric means stayed within about 0.4% of their preceding candidate.

## Rejected and retained experiments

- Native integer-width comparison added dispatch but produced effectively unchanged operator timing, around 0.999x for both Int and Int32. It was removed.
- Replacing indices globally with bitmaps or nonempty blocks did not improve the broad storage prototype matrix. Million-row median elapsed-time ratios were 1.056 and 1.064 relative to indices. Clustered runs can benefit, but sparse and nullable inputs can regress.
- Compact numeric buffers preserve a substantial memory advantage, approximately half the optional-array payload. Converting optional inputs into compact storage and back inside one filter took 4.22–4.76 times as long by median million-row case ratio. Keep this work on the separate storage branch and migrate consumers together.
- Run-aware block copying remains a candidate for later work. Its dispatch must account for actual run structure and validity patterns, including the cost of detecting them. Selection percentage alone is insufficient.

The [storage experiment report](/Users/LOCAL_USER/local-ai/spl/swiftsci/filter-optimization/storage-experiment/REPORT.md) records all 1,728 validated cases and distinguishes payload memory, live allocations and whole-process peak RSS. It is a standalone serial prototype, so its timings are not production SwiftSci speedups.

## Full production comparison

All 24 SwiftSci workload/size combinations passed comparison with pandas/Python. The only parity failures were the two previously known Kiraa native-integer filter cases. Invalid Kiraa timings remain excluded. Million-row medians follow.

| Operation | SwiftSci ms | pandas/Python ms | Kiraa ms |
|---|---:|---:|---:|
| csv | 13.560 | 67.064 | 9.171 |
| filter | 1.940 | 2.121 | 2.830 |
| filter_int | 1.971 | 1.846 | INVALID |
| filter_int32 | 1.949 | 1.782 | n/a |
| filter_float32 | 1.983 | 2.253 | n/a |
| sort | 31.367 | 29.229 | 58.971 |
| group | 4.663 | 4.896 | 9.361 |
| group_two | 11.336 | 10.599 | 36.498 |
| pipeline | 17.012 | 20.118 | 41.025 |
| stats | 0.587 | 0.608 | 0.590 |
| correlation | 1.713 | 2.421 | n/a |
| forecast | 12.605 | 388.562 | n/a |

[Full production report](/Users/LOCAL_USER/local-ai/spl/swiftsci/production-comparison/results/20260926T104626Z/REPORT.md) includes both sizes, memory, timing spread, correctness limitations, versions and reproduction commands.

## Validation and limits

- Complete Debug suite: 891 passed, zero failed or skipped.
- Complete Release suite: 891 passed, zero failed or skipped.
- Both full suites include MLX-dependent tests.
- New regression tests cover large narrow gathers, duplicate/reordered indices, String/Bool payloads, Float/Double bit-pattern boundaries, exact mixed-integer comparisons, and cached null predicates across all eight supported types and derived columns.
- Independent source review found no actionable correctness or concurrency defects. Tracked source is clean. Pre-existing `.vscode/` and `Benchmarks/CompactStorage/` were left untouched.

Hardware was an Apple M4 Max with 128 GiB unified memory and Swift 6.4. An unrelated Energy Park calculation and other applications used CPU during timing. Our benchmark processes were serialized, with compilation and test runs completed before timing. Small rankings can change with load and scheduling; the repeated larger filter gains are the stronger result. Benchmarks use warm inputs and do not measure an entire application or AI inference.

## Reproduction assets

- [Table and operator benchmark](/Users/LOCAL_USER/local-ai/spl/swiftsci/filter-matrix/README.md)
- [Original tuning](/Users/LOCAL_USER/local-ai/spl/swiftsci/filter-matrix/results/tuning/summary.json)
- [Revised tuning](/Users/LOCAL_USER/local-ai/spl/swiftsci/filter-matrix/results/tuning-revised/summary.json)
- [Holdout](/Users/LOCAL_USER/local-ai/spl/swiftsci/filter-matrix/results/holdout/summary.json)
- [Holdout confirmation](/Users/LOCAL_USER/local-ai/spl/swiftsci/filter-matrix/results/holdout-confirmation/summary.json)
- [Cached-null operator comparison](/Users/LOCAL_USER/local-ai/spl/swiftsci/filter-matrix/results/operators-cached/summary.json)
- [Matched production runner](/Users/LOCAL_USER/local-ai/spl/swiftsci/filter-optimization/compare-production.py)
- [Debug test summary](/Users/LOCAL_USER/local-ai/spl/swiftsci/full-suite-validation/debug-20260926T104326Z-x4cAFJ/summary.json)
- [Release test summary](/Users/LOCAL_USER/local-ai/spl/swiftsci/full-suite-validation/release-20260926T104427Z-yygDpe/summary.json)

Candidate binaries and metadata are preserved under `filter-matrix/binaries`. Metadata records source revisions, diff hashes, compiler and binary hashes. Rejected patches and assembly probes are retained under `filter-optimization/candidates`.
