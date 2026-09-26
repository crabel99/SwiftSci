# SwiftSci and Python benchmark

Run 20260925T195437Z on Apple M4 Max. SwiftSci `f65e15de19d3`.

Release Swift build. Two warmups and seven measured runs per workload, with separate sequential processes for each library. Setup, result extraction, JSON serialization, compilation and imports are outside operation timings. CSV reads use the same file and a warm filesystem cache. Each operation retains its result until after timing.

Python uses pandas for dataframes, NumPy for statistics and statsmodels for simple exponential smoothing. Numeric inputs use 64-bit integers and doubles. There are 100 groups and one missing value every 101 rows. Sorting is stable, descending, with missing values last. All output columns and values are compared, with matching nulls and numeric tolerances of rtol=1e-10 and atol=1e-8.

Forecasting fixes alpha at 0.3, starts at the first observation, disables parameter optimization and predicts 24 steps. Only point forecasts are compared. The libraries produce different auxiliary diagnostics, so this is a comparison of their fit-and-forecast APIs, not identical kernels.

BLAS thread limits are set to one where honored. These are CPU library workloads. The benchmark does not measure MLX, GPU performance or general language speed.

| Rows | Operation | Swift median ms | Python median ms | Faster | Swift peak MiB | Python peak MiB |
|---:|---|---:|---:|---|---:|---:|
| 100,000 | csv | 13.486 | 7.053 | Python 1.91x | 68.1 | 206.5 |
| 100,000 | filter | 15.440 | 0.293 | Python 52.63x | 18.1 | 160.2 |
| 100,000 | sort | 40.152 | 2.333 | Python 17.21x | 23.5 | 160.7 |
| 100,000 | group | 24.604 | 0.678 | Python 36.31x | 15.8 | 160.0 |
| 100,000 | stats | 0.058 | 0.068 | Swift 1.17x | 13.4 | 155.2 |
| 100,000 | correlation | 0.170 | 0.254 | Swift 1.49x | 15.0 | 158.7 |
| 100,000 | forecast | 1.263 | 41.254 | Swift 32.67x | 15.9 | 176.8 |
| 1,000,000 | csv | 111.283 | 66.416 | Python 1.68x | 582.1 | 444.8 |
| 1,000,000 | filter | 151.543 | 2.256 | Python 67.17x | 113.4 | 232.2 |
| 1,000,000 | sort | 444.937 | 30.115 | Python 14.77x | 132.7 | 282.0 |
| 1,000,000 | group | 247.015 | 4.825 | Python 51.19x | 103.9 | 217.4 |
| 1,000,000 | stats | 0.593 | 0.609 | Swift 1.03x | 75.3 | 212.7 |
| 1,000,000 | correlation | 1.800 | 2.500 | Swift 1.39x | 83.0 | 228.1 |
| 1,000,000 | forecast | 12.704 | 410.085 | Swift 32.28x | 98.5 | 327.8 |

Peak RSS covers each whole workload process before output serialization, including imports, input construction, retained arrays and allocator caches across repetitions. It is not incremental operation memory. Python imports all three libraries even for dataframe-only cases. Memory values therefore describe this harness, not a minimal application.

Process startup and all benchmark imports, measured separately after one warmup:

- SwiftSci: 7.2 ms median.
- Python: 974.3 ms median.

Numeric value parity checks passed. SwiftSci converts numeric group keys to strings during aggregation; the harness converts those keys back to numbers outside timing for comparison. Grouping therefore matches values but not output types. Raw timings include each repetition for inspection. These are short runs on a shared Mac, not controlled thermal or power benchmarks. Library implementations and default validation differ. Repeat on representative SPL datasets before choosing a replacement.

Re-run from the benchmark directory with `.venv/bin/python run.py`. Build the Swift executable first with `swift build -c release --arch arm64 -j 8`.
