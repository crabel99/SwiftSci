# Prepared imputer integration and CPU comparison

Date: 2026-10-07

## Decision and scope

Keep native prepared-column fitting and consuming transforms for `Imputer`. This removes row-array conversion from preprocessing pipelines containing an imputer and a native scaler. Unique columns reuse their buffers; shared columns detach only when replacement is needed. Clean columns remain shared. Swift copy-on-write protects retained batches, arrays and matrices.

Implementation commit: `8386d2476f32a1f685314134cd0be1b5f291e79d` on `codex/retained-memory-accounting-trial`, following `a075d7f52ef8fb75ba8b623e1ca21235f89764ab`. This increment remains local. The primary checkout was not switched. This report and measured evidence belong only to `codex/engineering-notes`.

Mean, median, most-frequent and constant strategies share the existing row implementation's statistic formulas. Arithmetic order, ties, all-missing fallback, empty input, failed-fit state, names and original row indices retain their existing behavior. The output clears missing flags, including when an explicitly chosen fill statistic is NaN.

## Integration boundary

The prepared `RegressionPipeline` validates finite inputs before running its transformers. This change preserves that policy. Callers must first fit a preprocessing `Pipeline` on training data, then use its fitted imputer and scaler to clean training and held-out batches before passing them to prepared regression. A constant NaN or a statistic involving infinities can still produce an input that regression rejects.

The public prepared regression documentation now explains this sequence. Moving imputation inside the regression boundary would be a separate API-policy decision and needs its own tests. The present measurements do not establish GPU inference or training performance.

## Validation

Three ownership assertions failed before implementation. Seven new test functions cover native nested dispatch, unique buffer reuse, shared clean columns, retained matrices, internal aliases, strategy edges, missing flags, provenance, failed refits, empty/error behavior and concurrent readers.

The final selected Release run passed 872 tests, with zero failures and two optional skips. It includes SwiftDataFrame, SwiftStats, SwiftPreprocessing, SwiftML, SwiftCluster, SwiftOptimize, SwiftExplain, SwiftNLP and benchmark support. This is not full-library or sanitizer certification. Optional tokenizer assets remain unavailable; the existing MNIST fixture early-return behavior also limits that test's evidence.

An earlier broad run failed a pointer-identity assertion because its literal array fixture could use static shared storage. The fixture now constructs dynamic arrays before asserting unique ownership. A focused rerun passed all seven tests, then the complete selected run passed. The production implementation did not change during that correction. Both earlier and final evidence are retained and labeled.

Twelve controller tests passed, covering output contracts, memory checks and worker cleanup. All 27 comparison workers completed 304,416 measured requests. Every output element matched an independent exact formula, and complete output hashes matched across paths and rounds. Consumed paths checked each column's buffer address. All worker processes exited. MLX active and cached allocations stayed at zero because this workload is CPU-only.

## Method

The public preprocessing pipeline contains `Imputer` with mean replacement, followed by `MinMaxScaler`. Fitting uses training-only data. Held-out fixtures include complete columns, numeric NaNs and entries marked missing. Expected transformed values are independently specified as an exact binary fraction or 0.5 for replaced entries.

The row reference explicitly materializes rows and invokes the existing row pipeline in the same executable. It represents the former whole-pipeline compatibility path, not a separate build of the parent commit. The copied prepared path retains its source through validation. The consumed path transfers ownership and verifies buffer reuse.

Three rounds ran serially in fresh processes; case and path order reversed in the middle round. Small is 64 rows by 3 columns with 32,768 requests per worker. Medium is 4,096 by 17 with 1,024 requests. Large is 65,535 by 65 with 32 requests. Timing includes fixture creation, missing marking, transformation, exact validation and hashing. It excludes fitting, warmup, JSON serialization and final cleanup.

Each worker has a 180-second deadline and a 2 GiB memory bound. The controller checks memory pressure before launch and owns child process groups through exit. There is no cache flush or allocator pressure relief. Ordinary activity on the user's computer was allowed.

## Results

Rates and RSS are medians of three fresh workers. The speed ratio is the median of within-round consumed/row ratios. RSS is sampled after requests and includes allocator retention; lifetime peak is recorded separately, and happened to match the reported RSS at these snapshots.

| Case | Rows requests/s | Copied columns requests/s | Consumed columns requests/s | Consumed/rows speed | Rows RSS MiB | Copied RSS MiB | Consumed RSS MiB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| small | 79840.1 | 376783.7 | 413454.6 | 5.18x | 18.9 | 18.9 | 18.8 |
| medium | 658.2 | 1957.8 | 2024.5 | 3.06x | 26.2 | 22.2 | 20.6 |
| large | 13.6 | 31.4 | 32.0 | 2.37x | 274.5 | 158.3 | 93.0 |

Across the three rounds, consumed throughput was 5.05 to 5.24 times the row path for small inputs, 3.03 to 3.08 times for medium, and 2.34 to 2.39 times for large. Large consumed RSS was 93.0 to 95.1 MiB, compared with 267.7 to 289.5 MiB for rows, a 65% to 67% reduction.

Against copied prepared columns, consuming improved throughput by 7.1% to 9.8% for small, 2.2% to 3.4% for medium, and 1.7% to 6.3% for large. Large RSS fell another 41% to 49%. Small RSS stayed around 19 MiB for all paths. Avoiding row materialization accounts for most of the measured speed benefit; ownership transfer provides an additional memory benefit.

These observations support the implementation without introducing a size threshold. They do not establish a universal speedup, formal statistical equivalence, or a complete production baseline. No Python comparator was run for this increment.

## Reproduction and evidence

The host is Apple M4 Max with 128 GiB unified memory and macOS 27.0 build 26A428. The arm64 Release worker uses the existing pinned dependencies, coverage disabled, safe Metal math and precise FP32 settings. No macOS 14 runtime was exercised.

Worker SHA-256: `a63878e71c741bac47fb1da2de9a1a2a1d8aef0ffc83b05e12314c96d22f101b`.

Run `Benchmarks/Tools/compare_imputer_pipeline.py` with `--worker`, a new `--output` directory and `--rounds 3`. Commands, all production source fingerprints, worker outputs and test summaries are preserved below. Logs are compressed without loss. Xcode result bundles remain in the local evidence directory.

- [Measured summary](../archive/2026-10-07/prepared-imputer/comparison/summary.json)
- [Source and binary fingerprints](../archive/2026-10-07/prepared-imputer/comparison/provenance.json)
- [Paired results and validation](../archive/2026-10-07/prepared-imputer/validation.json)
- [Final selected Release result](../archive/2026-10-07/prepared-imputer/verified-release-summary.json)
- [Implementation file fingerprints](../archive/2026-10-07/prepared-imputer/commit.json)
