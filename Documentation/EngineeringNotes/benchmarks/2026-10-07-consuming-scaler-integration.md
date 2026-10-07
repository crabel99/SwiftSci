# Consuming prepared-batch scaler integration

Date: 2026-10-07

## Decision

Integrate the consuming scaler into `StandardScaler` on the local trial branch. Callers can use `transform(consuming: consume batch)` when they no longer need the input. Unique column buffers are reused. Swift array copy-on-write preserves shared batch, matrix and array snapshots. Both prepared-batch entry points use one numerical implementation, and the benchmark's duplicate scaler kernel is removed.

Implementation commit: `617c69e841ad78ee5bb0863eb2055bb8213ba54b`.
Parent: `5ee5ff7649035a2953d5ed53941116e61891be02`.
Branch: `codex/retained-memory-accounting-trial`.
Nothing was pushed. Engineering decisions and raw evidence stay separately on `codex/engineering-notes`, outside implementation PRs.

## Compatibility and ownership

The existing unlabeled transform retains its input-snapshot semantics. The new labeled overload accepts a consuming parameter. Buffer reuse depends on actual ownership; consuming one reference does not remove other references to the same arrays. Internal aliases between columns also detach before mutation. The implementation gathers every column of a tile before writing any column.

The scaler snapshots fitted means and deviations together under its existing lock. Validation occurs before numerical mutation. An unfitted scaler still throws, including for empty inputs. A fitted scaler still accepts an empty batch before checking its width. Names and original row indices remain intact, including repeated row selections.

Missing input slots already hold NaN. Scaling preserves the existing numeric-NaN output behavior by clearing validity bits and null counts after transformation. Row-width vDSP calls and array-backed division output preserve the existing arithmetic and rounding. Tests compare both prepared-batch entry points with the independent row-matrix API across tile boundaries, short batches and wide matrices.

This adds no allocator, buffer pool, cache or precision mode. It does not broaden the scaler's concurrency contract to permit concurrent mutation of the same Swift value. Concurrent transforms of an already fitted scaler remain supported and are tested.

## Regression and integration evidence

A temporary overload that delegated to the previous copying implementation failed all four unique-storage cases. The numerical assertions passed; the four failures were column-address reuse checks at widths 17 and 513 and row counts 3 and 65. After integration, those cases passed.

The selected Release run passed 847 tests with zero failures and two optional tokenizer skips. New tests cover external arrays, internally shared columns in a unique batch, retained matrix snapshots, errors and empty inputs. Existing traversal, nonfinite-value, row-provenance and concurrent-transform checks now exercise both entry points. The 20-shape worker check also passed, requiring unique reuse, shared detachment and matching output bits. Thirteen benchmark-controller tests passed.

The same nine module test targets as the prior trial were selected. This is not a full-library or sanitizer run. The existing MNIST fixture test still returns early if its developer-local data is absent and counts as passed. No claim is made about that dataset's coverage.

Independent behavior and maintainability reviews found no actionable issues. Both were read-only reviews; executable evidence comes from the recorded test and benchmark runs.

## Matched memory comparison

Sixteen fresh workers ran two rounds of fixed and mixed sizes, logical and padded imports, and copy and consuming ownership. Each worker ran 32 bursts of eight requests, totaling 4,096 requests. The second round reversed storage and import order. All complete prediction hashes matched for corresponding input shapes and request seeds. Every consuming request reused all 65 input columns. Four original-mode workers also validated 32 requests.

The fixed schedule has 65,535 rows. The mixed schedule cycles through 8,191, 65,535, 16,383 and 65,536 rows. Both paths retain the analytic answer before scaling. Copy also retains the raw input through prediction and validation; consuming releases that ownership. Both use the same conservative capacity estimate, including the analytic answer, a 256 MiB reservation limit and two request slots. Admission has not been widened to exploit the reduced storage.

Each burst synchronizes GPU work, clears its cache and idles for one second before sampling memory. Values below are ranges across two workers for the mean RSS of their last four bursts. Percentage reductions pair copy and consuming runs within each round.

| Schedule | Import | Copy RSS MiB | Consuming RSS MiB | Paired reduction |
| --- | --- | ---: | ---: | ---: |
| fixed | logical | 384.53 to 389.13 | 240.31 to 243.00 | 37.5 to 37.6% |
| fixed | padded | 374.33 to 379.39 | 242.62 to 243.02 | 35.1 to 36.0% |
| mixed | logical | 402.29 to 402.84 | 251.27 to 256.09 | 36.4 to 37.5% |
| mixed | padded | 401.77 to 402.39 | 252.78 to 254.91 | 36.6 to 37.2% |

Request reservations drain after each burst. The retained model accounts for measured MLX activity between bursts; final close returns active and cache counters to zero. The archive records live malloc storage, allocated malloc capacity, RSS and physical footprint separately. Reduced RSS does not establish a process-memory cap or prove leak freedom for other workloads.

## Comparison with the prototype

The earlier benchmark-only prototype used the same schedules and request counts. Its historical consuming RSS ranges are shown beside this integration. These are separate runs on the same host, not an interleaved comparison of the two executable versions.

| Schedule | Import | Prototype RSS MiB | Integrated RSS MiB |
| --- | --- | ---: | ---: |
| fixed | logical | 238.41 to 242.23 | 240.31 to 243.00 |
| fixed | padded | 242.52 to 243.83 | 242.62 to 243.02 |
| mixed | logical | 250.58 to 253.91 | 251.27 to 256.09 |
| mixed | padded | 252.54 to 253.37 | 252.78 to 254.91 |

The ownership checks directly verify that the integrated API still reuses every unique input column. The repeated workload assesses whether the prototype's retained-memory benefit survives integration. Neither result establishes a universal savings percentage.

## Timing observations

The table gives each worker's median eight-request burst duration, with ranges across the two rounds, in milliseconds. It includes generation, scaling, prediction, validation and hashing. It excludes cache clearing, idle time and record serialization.

| Schedule | Import | Copy burst ms | Consuming burst ms |
| --- | --- | ---: | ---: |
| fixed | logical | 130.82 to 138.45 | 122.96 to 134.48 |
| fixed | padded | 119.21 to 136.15 | 114.54 to 122.03 |
| mixed | logical | 77.82 to 81.45 | 75.21 to 81.59 |
| mixed | padded | 77.83 to 81.92 | 77.18 to 77.63 |

Use these matched pairs for timing comparisons. Absolute timings from the historical prototype differ and were not collected interleaved with this binary. This cleanup diagnostic is not a serving-throughput benchmark. Small inputs, wider matrices, other models and sustained traffic still need their own performance measurements before broader caller migration.

## Reproduction and next step

The arm64 Release build targets macOS 14, runs on Apple M4 Max with 128 GiB unified memory, and uses macOS 27.0 build 26A428. No macOS 14 runtime was tested. MLX Swift stays pinned to `4657976edcdd2c60642424985d474b45ddddb390`. Coverage is disabled; Metal math is safe with precise FP32 functions.

Worker SHA-256: `e68ad92f400e1e4d8083cec26302e277074db5fee6ab9fad47769e5f1dffcaec`.

Replay commands are in `Benchmarks/RetainedGPUTrial/README.md`. The complete local Xcode bundle and logs are under `~/local-ai/spl/swiftsci/gpu-consuming-scaler-20261007/`. The engineering archive contains source and binary fingerprints, commands, result summaries and every worker trajectory.

Next review callers that discard their prepared input after scaling. Migrate those callers explicitly, then measure end-to-end memory and throughput before changing request admission estimates. Preserve copying behavior where callers retain input snapshots.

- [Validation and paired measurements](../archive/2026-10-07/gpu-consuming-scaler/validation.json)
- [Complete comparison summary](../archive/2026-10-07/gpu-consuming-scaler/comparison/summary.json)
- [Comparison provenance](../archive/2026-10-07/gpu-consuming-scaler/comparison/provenance.json)
- [Ownership checks](../archive/2026-10-07/gpu-consuming-scaler/owned-check.stdout)
- [Previous prototype](2026-10-07-gpu-owned-scaler.md)
