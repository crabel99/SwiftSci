# Production comparison: SwiftSci, pandas and Kiraa

Run 20260926T051154Z on Apple M4 Max, 128 GiB unified memory. SwiftSci `4dc6b533dd3c`; Kiraa `fc5d957401f7`. pandas 3.0.6, NumPy 2.5.3.

These are the real library APIs in native arm64 Release builds, using the committed SwiftSci optimization branch. The compact-storage prototype is excluded. The source trees had no tracked modifications. No production source changed during this comparison.

## Runtime

Values are medians in milliseconds. Each workload has three separately launched processes per library, two warmups per process and five timed repetitions per process: 15 samples in total. Library order rotates between batches. Compilation finishes before timing. Workloads run sequentially.

### 100,000 rows

| Operation | SwiftSci ms | pandas / Python ms | Kiraa ms |
|---|---:|---:|---:|
| Read CSV | 5.343 | 6.871 | 2.667 |
| Filter Float64 | 0.324 | 0.284 | 0.284 |
| Filter native Int / Int64 | 0.377 | 0.259 | INVALID |
| Filter Int32 | 0.375 | 0.255 | n/a |
| Filter Float32 | 0.379 | 0.289 | n/a |
| Stable descending sort | 3.101 | 2.327 | 4.558 |
| Group sum, 100 keys | 0.483 | 0.676 | 0.927 |
| Group sum, 9,700 key pairs | 4.009 | 1.566 | 3.999 |
| Filter → sort → group sum | 1.902 | 1.948 | 3.443 |
| Mean + sample variance | 0.058 | 0.069 | 0.059 |
| Pearson correlation | 0.173 | 0.257 | n/a |
| Exponential smoothing + 24 forecasts | 1.317 | 39.698 | n/a |

### 1,000,000 rows

| Operation | SwiftSci ms | pandas / Python ms | Kiraa ms |
|---|---:|---:|---:|
| Read CSV | 13.484 | 67.621 | 9.080 |
| Filter Float64 | 3.241 | 2.107 | 2.837 |
| Filter native Int / Int64 | 3.753 | 1.833 | INVALID |
| Filter Int32 | 3.727 | 1.842 | n/a |
| Filter Float32 | 3.775 | 2.261 | n/a |
| Stable descending sort | 35.706 | 28.405 | 58.511 |
| Group sum, 100 keys | 4.635 | 4.762 | 9.277 |
| Group sum, 9,700 key pairs | 11.132 | 10.100 | 36.096 |
| Filter → sort → group sum | 19.838 | 19.885 | 41.590 |
| Mean + sample variance | 0.587 | 0.614 | 0.588 |
| Pearson correlation | 1.810 | 2.579 | n/a |
| Exponential smoothing + 24 forecasts | 12.557 | 391.630 | n/a |

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
| 100,000 | Read CSV | 32.1 | 115.8 | 20.5 |
| 100,000 | Filter Float64 | 15.8 | 79.6 | 11.7 |
| 100,000 | Filter native Int / Int64 | 15.4 | 80.4 | INVALID |
| 100,000 | Filter Int32 | 14.3 | 80.7 | n/a |
| 100,000 | Filter Float32 | 14.3 | 78.8 | n/a |
| 100,000 | Stable descending sort | 20.5 | 81.9 | 12.5 |
| 100,000 | Group sum, 100 keys | 13.6 | 80.2 | 17.6 |
| 100,000 | Group sum, 9,700 key pairs | 16.4 | 84.0 | 19.0 |
| 100,000 | Filter → sort → group sum | 18.4 | 81.8 | 19.7 |
| 100,000 | Mean + sample variance | 13.4 | 77.6 | 10.9 |
| 100,000 | Pearson correlation | 14.2 | 79.1 | n/a |
| 100,000 | Exponential smoothing + 24 forecasts | 15.8 | 169.2 | n/a |
| 1,000,000 | Read CSV | 186.5 | 321.7 | 253.3 |
| 1,000,000 | Filter Float64 | 98.1 | 147.1 | 65.0 |
| 1,000,000 | Filter native Int / Int64 | 113.4 | 158.3 | INVALID |
| 1,000,000 | Filter Int32 | 98.1 | 155.9 | n/a |
| 1,000,000 | Filter Float32 | 98.1 | 144.4 | n/a |
| 1,000,000 | Stable descending sort | 136.6 | 201.6 | 80.3 |
| 1,000,000 | Group sum, 100 keys | 75.5 | 138.2 | 67.7 |
| 1,000,000 | Group sum, 9,700 key pairs | 99.6 | 199.7 | 77.1 |
| 1,000,000 | Filter → sort → group sum | 124.9 | 174.4 | 88.8 |
| 1,000,000 | Mean + sample variance | 75.3 | 134.5 | 53.4 |
| 1,000,000 | Pearson correlation | 82.9 | 149.6 | n/a |
| 1,000,000 | Exponential smoothing + 24 forecasts | 98.4 | 328.7 | n/a |

## Timing spread

Interquartile ranges over the 15 samples, in milliseconds. These describe variation within this run, not confidence intervals across machines.

| Rows | Operation | SwiftSci Q1 to Q3 | pandas / Python Q1 to Q3 | Kiraa Q1 to Q3 |
|---:|---|---:|---:|---:|
| 100,000 | Read CSV | 5.315 to 5.464 | 6.689 to 7.191 | 2.644 to 2.718 |
| 100,000 | Filter Float64 | 0.323 to 0.324 | 0.277 to 0.362 | 0.282 to 0.301 |
| 100,000 | Filter native Int / Int64 | 0.376 to 0.379 | 0.255 to 0.266 | INVALID |
| 100,000 | Filter Int32 | 0.373 to 0.376 | 0.252 to 0.260 | n/a |
| 100,000 | Filter Float32 | 0.378 to 0.385 | 0.286 to 0.297 | n/a |
| 100,000 | Stable descending sort | 3.084 to 3.117 | 2.267 to 2.366 | 4.554 to 4.571 |
| 100,000 | Group sum, 100 keys | 0.480 to 0.496 | 0.671 to 0.686 | 0.893 to 0.934 |
| 100,000 | Group sum, 9,700 key pairs | 3.964 to 4.035 | 1.452 to 1.671 | 3.767 to 4.016 |
| 100,000 | Filter → sort → group sum | 1.898 to 1.923 | 1.924 to 1.983 | 3.419 to 3.475 |
| 100,000 | Mean + sample variance | 0.058 to 0.058 | 0.069 to 0.071 | 0.059 to 0.059 |
| 100,000 | Pearson correlation | 0.170 to 0.174 | 0.255 to 0.260 | n/a |
| 100,000 | Exponential smoothing + 24 forecasts | 1.298 to 1.338 | 39.524 to 39.968 | n/a |
| 1,000,000 | Read CSV | 13.291 to 13.676 | 67.294 to 68.250 | 9.006 to 9.200 |
| 1,000,000 | Filter Float64 | 3.233 to 3.284 | 2.094 to 2.122 | 2.770 to 2.905 |
| 1,000,000 | Filter native Int / Int64 | 3.741 to 3.795 | 1.820 to 1.927 | INVALID |
| 1,000,000 | Filter Int32 | 3.721 to 3.738 | 1.789 to 1.881 | n/a |
| 1,000,000 | Filter Float32 | 3.768 to 3.889 | 2.221 to 2.330 | n/a |
| 1,000,000 | Stable descending sort | 35.632 to 36.019 | 28.262 to 29.146 | 58.455 to 58.840 |
| 1,000,000 | Group sum, 100 keys | 4.574 to 4.652 | 4.707 to 4.801 | 9.046 to 9.311 |
| 1,000,000 | Group sum, 9,700 key pairs | 11.087 to 11.350 | 10.024 to 10.721 | 35.662 to 36.317 |
| 1,000,000 | Filter → sort → group sum | 19.761 to 19.928 | 19.465 to 20.024 | 40.208 to 42.445 |
| 1,000,000 | Mean + sample variance | 0.585 to 0.592 | 0.610 to 0.637 | 0.582 to 0.619 |
| 1,000,000 | Pearson correlation | 1.806 to 1.847 | 2.544 to 2.743 | n/a |
| 1,000,000 | Exponential smoothing + 24 forecasts | 12.263 to 12.672 | 389.586 to 393.418 | n/a |

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
