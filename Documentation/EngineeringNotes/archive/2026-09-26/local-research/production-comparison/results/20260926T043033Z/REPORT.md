# Production comparison: SwiftSci, pandas and Kiraa

Run 20260926T043033Z on Apple M4 Max, 128 GiB unified memory. SwiftSci `dc31b5f1afc7`; Kiraa `fc5d957401f7`. pandas 3.0.6, NumPy 2.5.3.

These are the real library APIs in native arm64 Release builds, using the committed SwiftSci optimization branch. The compact-storage prototype is excluded. The source trees had no tracked modifications. No production source changed during this comparison.

## Runtime

Values are medians in milliseconds. Each workload has three separately launched processes per library, two warmups per process and five timed repetitions per process: 15 samples in total. Library order rotates between batches. Compilation finishes before timing. Workloads run sequentially.

### 100,000 rows

| Operation | SwiftSci ms | pandas / Python ms | Kiraa ms |
|---|---:|---:|---:|
| Read CSV | 6.367 | 6.973 | 2.760 |
| Filter Float64 | 0.325 | 0.291 | 0.298 |
| Filter native Int / Int64 | 0.372 | 0.268 | INVALID |
| Filter Int32 | 0.378 | 0.270 | n/a |
| Filter Float32 | 0.380 | 0.295 | n/a |
| Stable descending sort | 3.149 | 2.362 | 4.660 |
| Group sum, 100 keys | 0.489 | 0.758 | 0.883 |
| Group sum, 9,700 key pairs | 4.048 | 1.593 | 3.994 |
| Filter → sort → group sum | 1.957 | 1.978 | 3.482 |
| Mean + sample variance | 0.059 | 0.070 | 0.059 |
| Pearson correlation | 0.175 | 0.270 | n/a |
| Exponential smoothing + 24 forecasts | 1.285 | 40.028 | n/a |

### 1,000,000 rows

| Operation | SwiftSci ms | pandas / Python ms | Kiraa ms |
|---|---:|---:|---:|
| Read CSV | 40.158 | 68.824 | 9.901 |
| Filter Float64 | 3.293 | 2.155 | 2.921 |
| Filter native Int / Int64 | 3.780 | 1.925 | INVALID |
| Filter Int32 | 3.794 | 1.834 | n/a |
| Filter Float32 | 3.807 | 2.370 | n/a |
| Stable descending sort | 36.113 | 29.734 | 59.256 |
| Group sum, 100 keys | 4.636 | 4.713 | 9.476 |
| Group sum, 9,700 key pairs | 11.543 | 10.106 | 35.774 |
| Filter → sort → group sum | 19.875 | 20.252 | 41.998 |
| Mean + sample variance | 0.589 | 0.613 | 0.592 |
| Pearson correlation | 1.729 | 2.536 | n/a |
| Exponential smoothing + 24 forecasts | 13.080 | 394.862 | n/a |

## Correctness and API differences

Every output column and value is compared with pandas/Python after each batch. Missing values must occupy the same positions. Numeric tolerance is rtol=1e-10 and atol=1e-8. Integer values and group sums in these fixtures fit exactly within Float64, which the checker uses for normalization. Filtering and sorting retain row-order checks; grouped rows are aligned by keys outside timing. This benchmark supplements, rather than replaces, the exact integer boundary regression tests.

Kiraa integer filtering failed parity: the tested ColumnPredicate/Series path returns an all-false mask for an Int64 column. Its Series comparison implementation only accepts double storage. Invalid timings are excluded from rankings.

Kiraa has no matching scalar Int32 or Float32 column storage in this checkout. No equivalent correlation or forecasting API was identified, so those cases compare SwiftSci with Python only.

Kiraa composite grouping preserves both original key columns and uses ordinal index labels. The adapter reads those actual columns for parity checks. SwiftSci emits group keys as strings, which are converted to numeric keys outside timing. Kiraa single-key grouping uses string index labels.

CSV inference also differs: Kiraa represents the numeric ID and group fields as Float64, while pandas retains integer columns. Value parity is checked, but identical physical types are not claimed.

## Workloads

- The baseline dataframe has integer ID and group columns, Float64 values, 100 groups, and a missing value every 101 rows. Values follow ((id × 7919) mod 100003) / 100. Both sizes use the same deterministic construction.
- Float filtering selects values greater than 500. Integer filtering uses the numerator and a threshold of 50000, with the same null positions. Swift native Int and Kiraa Int64 use 64-bit integers on this Mac; pandas uses nullable Int64. The Int32 case uses nullable Int32 in pandas. The Float32 case rounds all values to Float32 before filtering.
- Sorting is descending, stable, with nulls last. Grouping includes key factorization and summing both numeric value columns. Two-key grouping adds id mod 97, yielding 9,700 populated key pairs. The pipeline measures the combined public filter, sort and group calls.
- CSV reads use identical input files and a warm filesystem cache. File hashes are recorded.
- Statistics use the original non-null Double array. Python uses NumPy for mean, sample variance and correlation; forecasting uses statsmodels. The smoothing parameter is fixed at 0.3, initialization uses the first observation, optimization is disabled, and 24 point forecasts are compared. The forecasting APIs also calculate different auxiliary diagnostics.
- Timings exclude imports, input construction, result extraction, parity checks and JSON serialization. Results remain alive until timing ends. This is library-level execution, not a CLI or daemon benchmark.

## Memory

Median whole-process peak RSS across three launches, in MiB, sampled before JSON result extraction. It includes imports, setup arrays, input frames, retained results and allocator caches across repetitions. It is not incremental operation memory, nor a minimal-service memory estimate. The workers retain some fixture arrays that an application could release. statsmodels is imported only for forecasting.

| Rows | Operation | SwiftSci MiB | pandas / Python MiB | Kiraa MiB |
|---:|---|---:|---:|---:|
| 100,000 | Read CSV | 42.0 | 117.1 | 22.1 |
| 100,000 | Filter Float64 | 16.2 | 79.9 | 11.7 |
| 100,000 | Filter native Int / Int64 | 15.5 | 81.2 | INVALID |
| 100,000 | Filter Int32 | 16.6 | 80.7 | n/a |
| 100,000 | Filter Float32 | 16.6 | 79.3 | n/a |
| 100,000 | Stable descending sort | 22.8 | 83.0 | 15.6 |
| 100,000 | Group sum, 100 keys | 13.6 | 81.2 | 17.8 |
| 100,000 | Group sum, 9,700 key pairs | 18.2 | 84.6 | 21.3 |
| 100,000 | Filter → sort → group sum | 18.8 | 82.0 | 21.4 |
| 100,000 | Mean + sample variance | 14.2 | 77.8 | 10.9 |
| 100,000 | Pearson correlation | 14.2 | 79.4 | n/a |
| 100,000 | Exponential smoothing + 24 forecasts | 16.6 | 175.8 | n/a |
| 1,000,000 | Read CSV | 308.5 | 327.6 | 253.7 |
| 1,000,000 | Filter Float64 | 98.1 | 149.4 | 66.2 |
| 1,000,000 | Filter native Int / Int64 | 113.4 | 161.7 | INVALID |
| 1,000,000 | Filter Int32 | 98.1 | 159.2 | n/a |
| 1,000,000 | Filter Float32 | 98.1 | 147.2 | n/a |
| 1,000,000 | Stable descending sort | 136.6 | 201.7 | 80.2 |
| 1,000,000 | Group sum, 100 keys | 75.5 | 138.2 | 67.8 |
| 1,000,000 | Group sum, 9,700 key pairs | 99.6 | 199.1 | 76.7 |
| 1,000,000 | Filter → sort → group sum | 124.9 | 174.3 | 91.9 |
| 1,000,000 | Mean + sample variance | 75.3 | 134.4 | 53.4 |
| 1,000,000 | Pearson correlation | 83.0 | 149.7 | n/a |
| 1,000,000 | Exponential smoothing + 24 forecasts | 98.4 | 328.5 | n/a |

## Timing spread

Interquartile ranges over the 15 samples, in milliseconds. These describe variation within this run, not confidence intervals across machines.

| Rows | Operation | SwiftSci Q1 to Q3 | pandas / Python Q1 to Q3 | Kiraa Q1 to Q3 |
|---:|---|---:|---:|---:|
| 100,000 | Read CSV | 6.186 to 6.688 | 6.889 to 7.103 | 2.697 to 2.833 |
| 100,000 | Filter Float64 | 0.324 to 0.326 | 0.280 to 0.323 | 0.286 to 0.304 |
| 100,000 | Filter native Int / Int64 | 0.370 to 0.379 | 0.261 to 0.280 | INVALID |
| 100,000 | Filter Int32 | 0.375 to 0.379 | 0.261 to 0.292 | n/a |
| 100,000 | Filter Float32 | 0.374 to 0.383 | 0.292 to 0.304 | n/a |
| 100,000 | Stable descending sort | 3.125 to 3.164 | 2.328 to 2.465 | 4.641 to 4.677 |
| 100,000 | Group sum, 100 keys | 0.486 to 0.492 | 0.699 to 0.766 | 0.881 to 0.888 |
| 100,000 | Group sum, 9,700 key pairs | 4.016 to 4.106 | 1.483 to 1.688 | 3.884 to 4.237 |
| 100,000 | Filter → sort → group sum | 1.933 to 1.961 | 1.948 to 2.050 | 3.418 to 3.519 |
| 100,000 | Mean + sample variance | 0.057 to 0.059 | 0.069 to 0.071 | 0.058 to 0.059 |
| 100,000 | Pearson correlation | 0.174 to 0.176 | 0.262 to 0.278 | n/a |
| 100,000 | Exponential smoothing + 24 forecasts | 1.280 to 1.294 | 39.876 to 40.574 | n/a |
| 1,000,000 | Read CSV | 39.987 to 40.329 | 68.368 to 69.374 | 9.740 to 10.012 |
| 1,000,000 | Filter Float64 | 3.269 to 3.312 | 2.134 to 2.206 | 2.830 to 2.950 |
| 1,000,000 | Filter native Int / Int64 | 3.741 to 3.787 | 1.889 to 2.011 | INVALID |
| 1,000,000 | Filter Int32 | 3.778 to 3.820 | 1.819 to 1.865 | n/a |
| 1,000,000 | Filter Float32 | 3.783 to 3.819 | 2.279 to 2.428 | n/a |
| 1,000,000 | Stable descending sort | 35.896 to 36.267 | 29.340 to 30.134 | 59.067 to 59.477 |
| 1,000,000 | Group sum, 100 keys | 4.535 to 4.668 | 4.695 to 4.772 | 9.333 to 9.709 |
| 1,000,000 | Group sum, 9,700 key pairs | 11.491 to 11.754 | 9.736 to 10.557 | 35.407 to 36.019 |
| 1,000,000 | Filter → sort → group sum | 19.789 to 19.979 | 19.937 to 20.645 | 41.257 to 42.863 |
| 1,000,000 | Mean + sample variance | 0.587 to 0.596 | 0.610 to 0.616 | 0.588 to 0.601 |
| 1,000,000 | Pearson correlation | 1.722 to 1.751 | 2.510 to 2.664 | n/a |
| 1,000,000 | Exponential smoothing + 24 forecasts | 12.606 to 13.154 | 391.487 to 396.252 | n/a |

## Interpretation limits

Other applications were actively using several CPU cores during the run. Process-name CPU snapshots are retained at the beginning and end. These results describe a shared M4 Max, not an isolated thermal or power-controlled machine. Close other workloads before treating small differences as stable rankings.

BLAS thread limits are set to one where honored. They do not restrict Kiraa’s parallel CSV parser. All SWIFTPANDAS overrides are cleared. Both row counts are below Kiraa’s recorded 10-million-row GPU-group threshold. This compares each library’s default CPU paths, including its internal parallelism. It does not measure MLX inference or GPU model performance.

This run improves two details from the earlier overlap harness: pandas filtering uses its ordinary selection result without a redundant .copy(), and statsmodels loads only for forecasting. Consequently, compare libraries within this run; older Python filtering, startup and memory figures are not directly comparable. Swift packages remain in their own declared language modes; the Kiraa client uses Swift 5 mode to match its original benchmark.

## Reproduce

Build from source, then run the comparison and report sequentially:

```sh
cd ~/local-ai/spl/swiftsci/production-comparison
SWIFTPANDAS_USE_BINARY=0 swift build -c release --arch arm64 -j 8 --force-resolved-versions
~/local-ai/spl/swiftsci/benchmark/.venv/bin/python run.py
# Exit 2 means a completed run contained parity failures; inspect them before using timings.
~/local-ai/spl/swiftsci/benchmark/.venv/bin/python report.py
```

metadata.json records revisions, binary and harness hashes, input hashes, toolchain and thread limits. measurements.json retains every sample and per-batch result checks. The harness/ directory preserves the exact sources used. requirements.txt captures the Python environment. No PR or push is part of this benchmark.
