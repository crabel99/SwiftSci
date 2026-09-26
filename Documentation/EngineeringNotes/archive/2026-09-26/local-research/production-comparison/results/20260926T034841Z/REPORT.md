# Production comparison: SwiftSci, pandas and Kiraa

Run 20260926T034841Z on Apple M4 Max, 128 GiB unified memory. SwiftSci `2694d303f86f`; Kiraa `fc5d957401f7`. pandas 3.0.6, NumPy 2.5.3.

These are the real library APIs in native arm64 Release builds, using the committed SwiftSci optimization branch. The compact-storage prototype is excluded. The source trees had no tracked modifications. No production source changed during this comparison.

## Runtime

Values are medians in milliseconds. Each workload has three separately launched processes per library, two warmups per process and five timed repetitions per process: 15 samples in total. Library order rotates between batches. Compilation finishes before timing. Workloads run sequentially.

### 100,000 rows

| Operation | SwiftSci ms | pandas / Python ms | Kiraa ms |
|---|---:|---:|---:|
| Group sum, 9,700 key pairs | 8.277 | 1.541 | 3.970 |

### 1,000,000 rows

| Operation | SwiftSci ms | pandas / Python ms | Kiraa ms |
|---|---:|---:|---:|
| Group sum, 9,700 key pairs | 49.669 | 11.250 | 36.229 |

## Correctness and API differences

Every output column and value is compared with pandas/Python after each batch. Missing values must occupy the same positions. Numeric tolerance is rtol=1e-10 and atol=1e-8. Integer values and group sums in these fixtures fit exactly within Float64, which the checker uses for normalization. Filtering and sorting retain row-order checks; grouped rows are aligned by keys outside timing. This benchmark supplements, rather than replaces, the exact integer boundary regression tests.

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
| 100,000 | Group sum, 9,700 key pairs | 20.1 | 84.3 | 21.3 |
| 1,000,000 | Group sum, 9,700 key pairs | 101.1 | 200.7 | 77.6 |

## Timing spread

Interquartile ranges over the 15 samples, in milliseconds. These describe variation within this run, not confidence intervals across machines.

| Rows | Operation | SwiftSci Q1 to Q3 | pandas / Python Q1 to Q3 | Kiraa Q1 to Q3 |
|---:|---|---:|---:|---:|
| 100,000 | Group sum, 9,700 key pairs | 8.231 to 8.355 | 1.508 to 1.565 | 3.929 to 3.978 |
| 1,000,000 | Group sum, 9,700 key pairs | 49.038 to 49.865 | 10.829 to 11.333 | 35.906 to 37.392 |

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
