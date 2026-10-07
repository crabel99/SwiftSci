# Consuming MinMax columns in prepared pipelines

Date: 2026-10-07

A later [completed interleaved comparison](2026-10-07-consuming-minmax-followup.md) records the requested follow-up. The timing limitation below describes the earlier run.

## Decision

Retain the MinMaxScaler ownership change as a local trial. Correctness and storage-reuse checks pass, and the completed workloads show lower resident memory for large and mixed consumed inputs. Throughput is not yet qualified for production. Concurrent host work confounded both the initial timing comparison and the attempted interleaved follow-up.

Implementation commit: `a075d7f52ef8fb75ba8b623e1ca21235f89764ab`.
Parent: `4c6d91b263bd16cd776eb315f6e1cafd44b6abab`.
Branch: `codex/retained-memory-accounting-trial`.
Nothing was pushed. This report and raw evidence belong only on `codex/engineering-notes`.

## Implementation and contracts

`MinMaxScaler.transform(consuming:)` reuses each column's buffer when uniquely owned. The ordinary prepared transform delegates to the same implementation. Swift array copy-on-write preserves shared caller snapshots, internal column aliases and previously exported matrices. Native pipelines already transfer ownership through the transformer protocol, so no new pipeline state or allocation policy is needed.

The old implementation allocated output columns plus two full-column scratch arrays. The candidate runs the existing scalar add, scalar multiply and scalar add directly on each destination column. It preserves `span < 1e-12` and the separate arithmetic rounding boundaries. There is no fused multiply-add, clipping, changed fitting behavior or new size crossover. Missing entries become numeric NaNs; column names and original row indices are retained. Validation still precedes mutation, including the existing empty-before-width-check behavior.

Apple documents that equal-sized vDSP input and output vectors generally support in-place operation unless a routine says otherwise. The scalar add and multiply functions use that contract. See [Apple's vDSP documentation](https://developer.apple.com/documentation/accelerate/vdsp-library).

## Validation and review

Four parameterized storage-reuse assertions failed before the production patch. Value and shared-snapshot checks passed in that first run. After implementation, 865 selected Release tests passed with zero failures and two optional tokenizer skips. This covers nine modules, not full-library or sanitizer certification. The existing MNIST test still returns early when its developer-local fixture is absent and is counted as passed.

New tests cover unique buffers, external and internal aliases, retained matrices, error order, empty inputs and nested protocol dispatch. An independent copy of the previous allocating arithmetic checks signed zero, subnormals, overflow, infinities, NaNs, reversed and zero-width ranges, and both sides of the constant-column threshold across twelve row counts. Finite-value bit patterns must match; NaNs must match classification. Missing-value, row-provenance and concurrent shared-input tests also pass.

Twelve controller tests passed, including rejection of a mismatched scaler identity. Behavior and standards reviews found no blockers. The standards review suggested sharing the benchmark's short MinMax training setup with the existing StandardScaler helper. It remains explicit to avoid changing other benchmark workflows in this patch. The test's allocating reference deliberately remains independent.

## Completed continuous workloads

The benchmark controller now accepts `--scaler minmax`; StandardScaler remains the default. MinMaxScaler fits only a separate 512-row training fixture, with target range `[-2, 3]`. Held-out inputs pass through public RegressionPipeline prediction with a nested Pipeline and a GPU LinearRegression model. Copy retains the original input until validation finishes; owned explicitly consumes it.

Every request creates seeded data, computes an independent analytic answer, predicts, checks every value within absolute error `1e-4`, and hashes the complete output. The old and new implementations completed 24 fresh workers each, totaling 608,256 measured requests. Complete hashes match across versions, ownership modes and all rounds.

Two continuously refilled request slots use the same conservative 256 MiB whole-request reservation limit. Each child also has a 256 MiB MLX cache limit. There is no cache clearing, idle interval or JSON serialization during the measured window. Timing includes input generation, admission, preprocessing, prediction, analytic checks and hashing. It excludes fitting, warmup and final cleanup. This is in-process linear inference, not network serving, model training or LLM inference.

Small uses 32,768 requests of 64 rows and 3 columns. Medium uses 16,384 requests of 4,096 rows and 17 columns. Large uses 512 requests of 65,535 rows and 65 columns. Mixed uses 1,024 requests cycling through 8,191, 65,535, 16,383 and 65,536 rows with 65 columns.

Every completed worker drained reservations and returned MLX active allocation to its fitted-model baseline after requests. Final cleanup released the model and returned active and cached MLX allocations to zero. This is not a proof of general leak freedom. RSS includes allocator retention, model state, GPU caches and small retained timing/hash records. The reservation limit is not a process RSS cap.

## Exploratory results and timing limitation

The following rows record the completed runs. Throughput is the median of three fresh workers per cell. RSS is the range after the continuous window while the model and normal caches remain present. It is neither peak nor post-cleanup memory. These rates are not an accepted speedup or regression verdict.

| Workload | Caller ownership | Previous requests/s | Candidate requests/s | Previous RSS MiB | Candidate RSS MiB |
| --- | --- | ---: | ---: | ---: | ---: |
| small | copy | 5864.8 | 4514.5 | 35.16 to 35.25 | 35.19 to 35.33 |
| small | owned | 5736.1 | 4539.4 | 35.09 to 35.27 | 33.47 to 34.36 |
| medium | copy | 2906.4 | 2195.2 | 36.62 to 39.78 | 39.17 to 43.64 |
| medium | owned | 2903.3 | 2233.0 | 35.55 to 36.67 | 33.25 to 35.23 |
| large | copy | 91.4 | 85.5 | 302.97 to 333.16 | 327.03 to 330.59 |
| large | owned | 92.7 | 88.8 | 300.28 to 310.70 | 182.97 to 189.52 |
| mixed | copy | 153.5 | 131.6 | 362.19 to 375.55 | 363.33 to 378.39 |
| mixed | owned | 148.0 | 135.5 | 289.92 to 302.70 | 209.58 to 212.34 |

For consumed inputs, large-batch RSS fell by about 39% and mixed-size RSS by about 27% to 30% across corresponding runs. Small and medium inputs provide little practical memory benefit. These observations are workload-specific, not universal memory guarantees.

The separate timing passes showed lower candidate rates. Concurrent Time Machine, VS Code, local AI and other processes were active, so those observations cannot isolate the implementation's effect. To test this, the old scaler was rebuilt and measured alternately with the saved candidate executable. Both executables then showed large shifts relative to their earlier rates. Alternation alone did not provide a sufficiently stable comparison.

That follow-up was intentionally stopped after 12 complete workers. Its completed records remain exploratory; the interrupted worker is excluded. Only this comparison's controller received SIGTERM. Its existing cleanup handler terminated and reaped its child. A final process check found no SwiftSci trial worker running, and the saved candidate executable was restored. Other user workloads were left untouched.

The memory change is committed locally because its storage ownership and compatibility are verified. Do not promote it on a claim of equal or better throughput yet. The next step is a quiet-host interleaved run using the retained old and new executables, with the same predictions, budgets, case ordering and cleanup gates. A repeatable slowdown must be investigated rather than attributed to noise.

## Reproduction and evidence

The candidate is the arm64 Release executable from the 865-test run. The control rebuild uses the parent's MinMaxScaler source with the same new benchmark; three compact-scaler tests pass on that control. The implementation is linked into each executable, and only the MinMaxScaler production source differs. Both use the same MLX resources.

Tests ran on Apple M4 Max with 128 GiB unified memory, macOS 27.0 build 26A428, targeting macOS 14. No macOS 14 runtime was tested. MLX Swift remains pinned to `4657976edcdd2c60642424985d474b45ddddb390`. Coverage is disabled, Metal math is safe, and FP32 functions are precise. The controller rejects instrumented binaries before measurement.

- Rebuilt baseline executable: `3f06110e47b16d0c6d48259f56075e35629fc23b08a677d141c40df78b9198d1`.
- Candidate executable: `5f113578cb54ee88daee6ca6efc91ba9e160fe38a9e42911dc46bb5ade948e1f`.

Local result bundles, logs and saved source are under `~/local-ai/spl/swiftsci/gpu-consuming-minmax-20261007/`. Raw completed worker records are archived with lossless gzip compression. The interrupted worker's partial output stays local and is excluded from the archive. Source and binary fingerprints distinguish every measured artifact. The interleaving driver is retained for the quieter rerun. No report or measured data is added to the implementation branch.

- [Validation and paired exploratory results](../archive/2026-10-07/gpu-consuming-minmax/validation.json)
- [Initial candidate summary](../archive/2026-10-07/gpu-consuming-minmax/candidate/summary.json)
- [Initial baseline summary](../archive/2026-10-07/gpu-consuming-minmax/baseline/summary.json)
- [Stopped comparison and reason](../archive/2026-10-07/gpu-consuming-minmax/interleaved-stopped.json)
- [Previous pipeline integration](2026-10-07-consuming-pipeline-integration.md)
