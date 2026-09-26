# Production comparison: SwiftSci, pandas and Kiraa

Run 20260926T033814Z on Apple M4 Max, 128 GiB unified memory. SwiftSci `2694d303f86f`; Kiraa `fc5d957401f7`. pandas 3.0.6, NumPy 2.5.3.

These are the real library APIs in native arm64 Release builds, using the committed SwiftSci optimization branch. The compact-storage prototype is excluded. The source trees had no tracked modifications. No production source changed during this comparison.

## Runtime

Values are medians in milliseconds. Each workload has three separately launched processes per library, two warmups per process and five timed repetitions per process: 15 samples in total. Library order rotates between batches. Compilation finishes before timing. Workloads run sequentially.

### 100,000 rows

| Operation | SwiftSci ms | pandas / Python ms | Kiraa ms |
|---|---:|---:|---:|
| Read CSV | 13.639 | 7.127 | 2.705 |
| Filter Float64 | 0.326 | 0.290 | 0.314 |
| Filter native Int / Int64 | 0.380 | 0.269 | INVALID |
| Filter Int32 | 0.381 | 0.262 | n/a |
| Filter Float32 | 0.382 | 0.295 | n/a |
| Stable descending sort | 5.160 | 2.426 | 4.664 |
| Group sum, 100 keys | 0.492 | 0.760 | 0.957 |
| Group sum, 9,700 key pairs | 8.326 | 1.804 | 4.036 |
| Filter → sort → group sum | 3.074 | 2.056 | 3.455 |
| Mean + sample variance | 0.058 | 0.069 | 0.058 |
| Pearson correlation | 0.174 | 0.258 | n/a |
| Exponential smoothing + 24 forecasts | 1.320 | 40.505 | n/a |

### 1,000,000 rows

| Operation | SwiftSci ms | pandas / Python ms | Kiraa ms |
|---|---:|---:|---:|
| Read CSV | 112.010 | 68.675 | 10.073 |
| Filter Float64 | 3.273 | 2.155 | 3.128 |
| Filter native Int / Int64 | 3.801 | 1.897 | INVALID |
| Filter Int32 | 3.782 | 1.823 | n/a |
| Filter Float32 | 3.817 | 2.294 | n/a |
| Stable descending sort | 65.404 | 29.984 | 59.335 |
| Group sum, 100 keys | 4.617 | 5.333 | 9.403 |
| Group sum, 9,700 key pairs | 49.496 | 10.608 | 36.624 |
| Filter → sort → group sum | 36.913 | 20.847 | 42.307 |
| Mean + sample variance | 0.595 | 0.626 | 0.588 |
| Pearson correlation | 1.740 | 2.531 | n/a |
| Exponential smoothing + 24 forecasts | 12.720 | 396.951 | n/a |

## Correctness and API differences

Every output column and value is compared with pandas/Python after each batch. Missing values must occupy the same positions. Numeric tolerance is rtol=1e-10 and atol=1e-8. Integer values and group sums in these fixtures fit exactly within Float64, which the checker uses for normalization. Filtering and sorting retain row-order checks; grouped rows are aligned by keys outside timing. This benchmark supplements, rather than replaces, the exact integer boundary regression tests.

Kiraa integer filtering failed parity at both sizes: the tested ColumnPredicate/Series path returns an all-false mask for an Int64 column. Its Series comparison implementation only accepts double storage. The measured time is retained in raw data but excluded from performance rankings. We did not convert the column to Double or patch Kiraa to make this case pass.

Kiraa has no matching scalar Int32 or Float32 column storage in this checkout. No equivalent correlation or forecasting API was identified, so those cases compare SwiftSci with Python only.

Correction after source review: Kiraa composite grouping preserves both original key columns and uses ordinal index labels. The adapter reads those actual columns for parity checks. SwiftSci emits group keys as strings, which are converted to numeric keys outside timing. Kiraa single-key grouping uses string index labels. The original adapter unnecessarily reconstructed composite keys. Timed aggregation was unaffected, but its key validation was incomplete. A corrected rerun at both row counts passed all actual key and aggregate comparisons. See [the corrected measurements](../20260926T034841Z/measurements.json). The original harness and raw results remain unchanged.

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
| 100,000 | Read CSV | 71.8 | 121.3 | 22.1 |
| 100,000 | Filter Float64 | 16.6 | 80.1 | 11.7 |
| 100,000 | Filter native Int / Int64 | 16.2 | 81.1 | INVALID |
| 100,000 | Filter Int32 | 16.6 | 80.5 | n/a |
| 100,000 | Filter Float32 | 15.0 | 79.2 | n/a |
| 100,000 | Stable descending sort | 28.1 | 82.9 | 15.5 |
| 100,000 | Group sum, 100 keys | 14.5 | 80.6 | 19.2 |
| 100,000 | Group sum, 9,700 key pairs | 20.1 | 84.4 | 20.8 |
| 100,000 | Filter → sort → group sum | 23.8 | 85.3 | 23.0 |
| 100,000 | Mean + sample variance | 14.2 | 77.7 | 10.9 |
| 100,000 | Pearson correlation | 15.0 | 79.5 | n/a |
| 100,000 | Exponential smoothing + 24 forecasts | 16.7 | 178.2 | n/a |
| 1,000,000 | Read CSV | 584.4 | 321.7 | 253.3 |
| 1,000,000 | Filter Float64 | 98.1 | 149.5 | 66.1 |
| 1,000,000 | Filter native Int / Int64 | 113.4 | 161.8 | INVALID |
| 1,000,000 | Filter Int32 | 98.2 | 157.3 | n/a |
| 1,000,000 | Filter Float32 | 98.2 | 146.6 | n/a |
| 1,000,000 | Stable descending sort | 151.8 | 204.3 | 80.5 |
| 1,000,000 | Group sum, 100 keys | 75.6 | 138.2 | 68.0 |
| 1,000,000 | Group sum, 9,700 key pairs | 101.1 | 200.6 | 76.7 |
| 1,000,000 | Filter → sort → group sum | 121.1 | 176.9 | 92.0 |
| 1,000,000 | Mean + sample variance | 75.3 | 134.4 | 53.3 |
| 1,000,000 | Pearson correlation | 83.0 | 149.7 | n/a |
| 1,000,000 | Exponential smoothing + 24 forecasts | 98.5 | 328.6 | n/a |

## Timing spread

Interquartile ranges over the 15 samples, in milliseconds. These describe variation within this run, not confidence intervals across machines.

| Rows | Operation | SwiftSci Q1 to Q3 | pandas / Python Q1 to Q3 | Kiraa Q1 to Q3 |
|---:|---|---:|---:|---:|
| 100,000 | Read CSV | 13.351 to 14.617 | 7.075 to 7.406 | 2.609 to 2.791 |
| 100,000 | Filter Float64 | 0.325 to 0.331 | 0.281 to 0.376 | 0.311 to 0.315 |
| 100,000 | Filter native Int / Int64 | 0.380 to 0.386 | 0.265 to 0.275 | INVALID |
| 100,000 | Filter Int32 | 0.379 to 0.385 | 0.259 to 0.278 | n/a |
| 100,000 | Filter Float32 | 0.381 to 0.387 | 0.291 to 0.305 | n/a |
| 100,000 | Stable descending sort | 5.064 to 5.195 | 2.328 to 2.576 | 4.628 to 4.687 |
| 100,000 | Group sum, 100 keys | 0.489 to 0.494 | 0.710 to 0.793 | 0.910 to 0.965 |
| 100,000 | Group sum, 9,700 key pairs | 8.246 to 8.432 | 1.538 to 1.900 | 3.980 to 4.054 |
| 100,000 | Filter → sort → group sum | 3.030 to 3.186 | 2.016 to 2.134 | 3.334 to 3.525 |
| 100,000 | Mean + sample variance | 0.058 to 0.059 | 0.068 to 0.072 | 0.058 to 0.060 |
| 100,000 | Pearson correlation | 0.172 to 0.177 | 0.256 to 0.261 | n/a |
| 100,000 | Exponential smoothing + 24 forecasts | 1.271 to 1.337 | 40.033 to 40.664 | n/a |
| 1,000,000 | Read CSV | 111.254 to 113.150 | 67.979 to 69.202 | 9.735 to 10.500 |
| 1,000,000 | Filter Float64 | 3.265 to 3.281 | 2.129 to 2.240 | 3.103 to 3.156 |
| 1,000,000 | Filter native Int / Int64 | 3.767 to 3.811 | 1.874 to 2.021 | INVALID |
| 1,000,000 | Filter Int32 | 3.771 to 3.787 | 1.815 to 1.834 | n/a |
| 1,000,000 | Filter Float32 | 3.798 to 3.841 | 2.274 to 2.409 | n/a |
| 1,000,000 | Stable descending sort | 65.298 to 65.640 | 28.970 to 30.626 | 58.853 to 59.610 |
| 1,000,000 | Group sum, 100 keys | 4.566 to 4.669 | 5.186 to 5.452 | 9.182 to 9.839 |
| 1,000,000 | Group sum, 9,700 key pairs | 48.958 to 49.944 | 10.386 to 10.913 | 36.400 to 37.200 |
| 1,000,000 | Filter → sort → group sum | 36.584 to 37.148 | 20.617 to 21.151 | 42.096 to 43.078 |
| 1,000,000 | Mean + sample variance | 0.575 to 0.598 | 0.601 to 0.644 | 0.587 to 0.593 |
| 1,000,000 | Pearson correlation | 1.732 to 1.750 | 2.478 to 2.569 | n/a |
| 1,000,000 | Exponential smoothing + 24 forecasts | 12.561 to 12.898 | 396.077 to 399.467 | n/a |

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
