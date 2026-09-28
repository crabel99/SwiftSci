# SwiftSci optimization branch

Branch: `codex/dataframe-optimizations`. Local commits only.

| Commit | Change |
|---|---|
| `1575579581` | Specialize typed-column filtering and Int64 gathering; avoid generic null-count reduction. |
| `05eb2226d5` | Count missing values during gathering and reuse known zero counts. |

The first commit contains the previously measured final 8x filtering step, from 32.40 to 4.00 ms. Its cumulative gain over the original main baseline was about 41x, from 165.99 to 4.00 ms. Those historical timings came from the three-library benchmark.

## Second commit measurements

Direct Release comparison against the first commit on this Mac, one million rows. Three batches alternate executable order, with two warmups and fifteen measured iterations per process. Times below are pooled medians of 45 samples. Output checks passed. Executable hashes and raw samples are in `null-count.json`.

| Operation | Before, ms | After, ms | Speedup |
|---|---:|---:|---:|
| full | 3.898 | 3.370 | 1.16x |
| gather | 2.663 | 2.287 | 1.16x |
| gather_int | 1.048 | 0.917 | 1.14x |
| gather_double | 0.549 | 0.417 | 1.32x |
| construct_nonnull | 63.594 | 44.945 | 1.41x |

Both committed changes pass the scoped dataframe, statistics, forecasting and independent validation suites. The second commit passes 266 tests in Debug and 266 in Release. This is not the full SwiftSci MLX-dependent test suite.

## Rejected allocation experiments

Replacing nil-filled gather arrays with manually initialized storage made the Double gather faster, but the complete filter slower in two alternating comparisons. The recheck measured filter time at 3.477 to 3.677 ms and Double gather at 0.417 to 0.261 ms. The unchanged selection operation also became slower; the cause was not established. Do not attribute that change to a particular compiler optimization without further evidence.

A standard-library map alternative also regressed the complete filter, from 3.490 to 4.412 ms, and Double gathering, from 0.424 to 0.917 ms. Neither experiment is in the working tree or committed. Patches, raw measurements and two passing ownership tests are retained here. The manually initialized candidate passed 268 scoped tests in each configuration before it was rejected for performance.

## Next storage experiment

Kiraa's separate numeric buffers and validity bitmap remain the next larger design to evaluate. SwiftSci's Optional<Double> and Optional<Int64> each occupy 16 bytes on this Mac. A packed 8-byte numeric value plus validity bits could reduce data movement.

Prototype this behind the column interface, using the existing Arrow ownership facilities where suitable. Measure filtering, sorting, grouping, null handling and conversion to the public `[T?]` values. Include reference lifetimes and copy semantics. Public TypedColumn.values and concrete downcasts make this an API and ownership decision as well as an allocation optimization.

The broader plan is in [FEATURE-INTEGRATION.md](../FEATURE-INTEGRATION.md).


## Final matched comparison

The committed branch was rebuilt and compared with the unchanged pandas and Kiraa workloads at 100,000 and 1,000,000 rows. All output-value comparisons passed. At one million rows:

| Operation | SwiftSci, ms | pandas/NumPy, ms | Kiraa, ms |
|---|---:|---:|---:|
| CSV read | 113.939 | 67.939 | 9.886 |
| Filter | 3.477 | 2.302 | 2.925 |
| Sort | 208.463 | 30.738 | 59.197 |
| Group | 253.771 | 4.998 | 9.689 |
| Statistics | 0.596 | 0.626 | 0.589 |

SwiftSci filtering takes about 1.51 times the pandas duration in this run. Sorting and grouping remain the largest gaps. These are CPU workloads on one shared Mac; the complete benchmark report records type differences and measurement limits.

[Final benchmark report](/Users/LOCAL_USER/local-ai/spl/swiftpandas/benchmark/results/20260926T000220Z/REPORT.md)
