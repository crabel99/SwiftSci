# Retained snapshots and direct matrix preparation

Recorded 2026-10-04. This is a local experiment on `codex/memory-kernel-trial`, not a production API commitment or a proposed default change.

## Branch and evidence

The parent `codex/unified-memory-prototype` remains at `aa5c71968c080f4188357c4cb628389f89ca00a2`. This trial compares the previously qualified initialized-owner prototype at `5904a0eaebcd0da60400fb593f3fadbe335e675c` with the current code at `59b77f7fd2200e62a1e3b7f4e040804bfb5e5892`.

The two reversible commits are `30b1646291e71d8f926ededd48ed4686ac9359f1`, which introduces snapshot treatments, and `59b77f7fd2200e62a1e3b7f4e040804bfb5e5892`, which adds optional direct matrix packing. Neither branch has been pushed for this trial. This report belongs only on `codex/engineering-notes`.

Evidence is in `~/local-ai/spl/swiftsci/memory-snapshot-trial-20261004/`. It includes executable fingerprints, per-file source hashes, raw samples, comparison scripts, final source verification, correctness outputs and the rejected strided-division experiment. Every compiled source file matches the final commit. Only the prototype README changed after the build.

## Per-snapshot requirements and treatment

A memory module can accept different treatment for different snapshots in the same application. The present implementation offers `retainSource` and `materialize`. Treatment changes storage and retention, never row identity, stored precision or missingness. Selection composition preserves order and duplicates. Null values remain distinct from NaNs, and signed zero retains its bits.

`SelectionCache` now owns a `SelectedTable` snapshot. The snapshot keeps original identities together with the mapping into its stored columns. This replaces separately coordinated input, identity and materialization fields. Materialized snapshots use implicit dense positions; a later selection composes its mapping. Source mutation continues to detach shared owners. A materialized selection can outlive the original allocation without retaining it.

The snapshot is still an internal prototype. The CPU preparation adapter can access its columns and physical positions, and the existing pointer lease is not a compiler-enforced nonescaping borrow. This trial does not complete the broader safe-borrowing or asynchronous device-submission design.

Hard requirements should remain distinct from preferences. Precision, missingness, snapshot isolation and any enforced byte limit are correctness constraints. Expected reuse, sparse mutation and intended device consumption guide a choice among implementations that meet those constraints. A preference must never silently change Float64 to Float32 or discard missingness.

This pattern has precedent. Metal exposes per-resource storage and CPU cache modes for different access patterns, and Arrow exposes allocation through memory pools. These APIs support explicit policies; they do not establish a universal optimal representation. [Metal resource fundamentals](https://developer.apple.com/documentation/metal/resource-fundamentals), [Metal CPU cache modes](https://developer.apple.com/documentation/metal/mtlcpucachemode), [Arrow memory interfaces](https://arrow.apache.org/docs/python/api/memory.html).

For this prototype, keep the two measured treatments explicit. Do not add an automatic optimal mode, chunk every column or place all data in Metal storage. Capacity builders, mutation-oriented storage, byte admission and completion-owned device lifetimes remain separate experiments.

## Direct packing experiment

The new `keys-tile-direct-borrowed-fit-4096` variant retains one gathered tile, performs the existing contiguous row-width vDSP addition and division, then places each normalized row into the final column-major matrix. It removes the full scaled tile and the subsequent column-wise copy. Destructive LAPACK workspace remains separate.

The first attempt sent vDSP division directly into a strided matrix destination. It failed the existing bitwise matrix comparison. A standalone reproduction found 31 differing elements across widths 1, 2, 3, 4, 8, 16, 32 and 64, with examples differing in the last bit. This is evidence of stride-dependent rounding on this toolchain, not proof of a vDSP defect. The failed binary, sources and reproducer are preserved under `strided-division-rejected/`. No tolerance was relaxed. The accepted experiment keeps contiguous division.

The direct variant remains optional. It halves tile scratch, but generally loses packing speed and does not justify replacing the existing two-buffer default.

## Verification

- 570 Release core scenarios passed, including production bitwise matrix agreement, analytic QR coefficients and predictions, original row identities, both snapshot treatments, all five held-out folds, feature widths through 64 and exact tile scratch budgets. The existing shared-Metal snapshot check passed within this run.
- 151 mutation scenarios passed.
- 14 focused snapshot scenarios passed under AddressSanitizer, including missingness, NaNs, signed zero, duplicate and nested selection, invalid extents, source mutation, release of the source after materialization and final owner release.
- 12 real-file integration scenarios passed across CSV and Parquet, 10,000 and 100,000 rows, and production, retained-selection and gathered strategies. Each ran three training-only fits and checked an independent production replay.
- 240 fresh-process workflow measurements and 60 reuse measurements completed successfully. Reuse proofs agreed between old and new executables and across all three strategies.

The full library suite, minimum deployment target, MLX device comparison, concurrent memory-pressure workloads and device cancellation were not requalified in this trial. Existing unrelated numerical failures have not been changed or waived.

## Timing method

Machine: Apple M4 Max with 128 GiB unified memory, macOS 27.0. Native arm64 Release builds use the existing qualified compiler and dependency settings recorded in the build manifests. Runs used AC power, serial fresh processes, five rounds and rotated comparison order. Thread-limit environment overrides were removed. Each workflow warms its numerical path before measurement. Reuse includes cache setup and three changing training folds; proof scans and the independent replay are outside reported work time.

The measurements are medians from this machine. Five rounds do not establish a general crossover or eliminate scheduler and cache variation. Allocation ledgers measure owned scalar payload, not Swift array metadata or physical memory traffic. RSS is a process high-water mark with library and allocator costs. Original source data remains retained during reuse comparisons.

## Single-workflow comparison

Ratios below one are faster. Direct versus tiled compares two variants of the same candidate executable. Snapshot versus prior compares the default tiled workflow between candidate and prior executables. All rows include preparation, QR fitting and prediction; construction is separately available in the raw records.

| Rows | Width | Selection / null per mille | Key order | Direct / tiled workflow | Direct / tiled packing | Snapshot / prior workflow | Tile scratch saved |
| ---: | ---: | --- | --- | ---: | ---: | ---: | ---: |
| 1,000 | 4 | 900 / 0 | quantized | 1.021 | 1.118 | 1.050 | 28.1 KiB |
| 100,000 | 4 | 100 / 10 | quantized | 1.036 | 1.325 | 1.039 | 128.0 KiB |
| 100,000 | 8 | 900 / 0 | quantized | 1.039 | 1.125 | 0.994 | 256.0 KiB |
| 100,000 | 32 | 500 / 10 | quantized | 0.986 | 0.914 | 0.999 | 1024.0 KiB |
| 1,000,000 | 4 | 500 / 10 | quantized | 0.969 | 1.191 | 1.076 | 128.0 KiB |
| 1,000,000 | 8 | 900 / 0 | quantized | 1.063 | 1.088 | 1.003 | 256.0 KiB |
| 100,000 | 8 | 900 / 0 | continuous | 0.996 | 1.054 | 1.056 | 256.0 KiB |
| 100,000 | 8 | 900 / 0 | ordered | 0.993 | 1.038 | 1.064 | 256.0 KiB |
| 100,000 | 8 | 900 / 0 | skewed | 0.975 | 1.049 | 1.093 | 256.0 KiB |
| 1,000,000 | 8 | 900 / 0 | continuous | 1.080 | 1.073 | 0.956 | 256.0 KiB |
| 1,000,000 | 8 | 900 / 0 | ordered | 1.120 | 1.183 | 1.037 | 256.0 KiB |
| 1,000,000 | 8 | 900 / 0 | skewed | 1.077 | 1.108 | 0.973 | 256.0 KiB |

The direct path reduced tile payload in every case. Several million-row workflows were 6% to 12% slower. The 32-column case was about 1% faster and saved 1 MiB of tile scratch. These results support retaining an experimental lower-scratch path, not changing the default. Snapshot refactoring also has mixed timings, including regressions; its immediate benefit is a coherent ownership and identity contract.

## Repeated-workflow comparison

All cases run three different training folds. Times include setup plus work, in milliseconds. Peak owned payload includes the retained source, selected storage, output and tile owners, but excludes Swift array metadata and solver arrays.

| Rows × width | Treatment | Prior ms | Candidate ms | Candidate / prior | Candidate owner peak MiB |
| --- | --- | ---: | ---: | ---: | ---: |
| 100,000 × 32 | selection | 62.29 | 64.91 | 1.042 | 35.91 |
| 100,000 × 32 | gather | 46.98 | 51.46 | 1.095 | 44.75 |
| 100,000 × 32 | recompute | 73.75 | 73.61 | 0.998 | 35.91 |
| 1,000,000 × 8 | selection | 528.23 | 499.80 | 0.946 | 123.33 |
| 1,000,000 × 8 | gather | 404.51 | 385.06 | 0.952 | 178.26 |
| 1,000,000 × 8 | recompute | 842.54 | 855.14 | 1.015 | 123.33 |

On these two candidate workloads, materialization reduced setup-inclusive three-pass time by about 21% to 23% relative to retained selection. It increased peak owned payload by about 8.8 MiB and 54.9 MiB respectively while the source stayed retained. The new snapshot implementation itself regressed about 9.5% against the old gathered cache on the smaller 32-column workload. Do not describe the abstraction as a general speed improvement.

The next useful measurement is total retained memory and time under an explicit byte budget, with source retention and release controlled. Review selection-index allocation and gather overhead before considering automatic treatment selection. A smaller scratch buffer alone is not sufficient evidence of a better application workflow.

## Artifact fingerprints

- `baseline`: `e30012b9c9f02c61772d33ee37b5c408053136ab7bbedc206eb5af9bb49e164d`
- `candidate`: `0c10d0a1c92d2ceb523b707e685e081f44fbe26792f5d4d32bec183b50cab465`
- `workflow-samples.json`: `d111ebfed51782d96d6820d280691d8a8c5a7087570f919920ea1d3ed4a9fbed`
- `workflow-summary.json`: `86e6072ada67e737ab3b0850d9a03da3d4bf41372a81c45108019e63ff54da2b`
- `reuse-samples.json`: `8504803485c9b031a812575bb58eb75bdfbcfe4ba1438cefcd64b75c86f3e063`
- `reuse-summary.json`: `1efdd26d35d30c0af79e9eb7dfb7d7f1963dd0a98348f457ded59b47bf879023`
- `checks.json`: `aa49ac3cb124996d4c9254a04160d83995e4b82cd916eab2bd211afcf0f193bd`
- `mutation-checks.json`: `c6e5eb7554551cbce53f680af991254b9c7ef2bc92909eb3832e63d3881c90ad`
- `ingestion-checks.json`: `eb72be82b55394d17c9438512b6dce1cc1ca72a7ac6d11754176de75f194960f`
- `final-source-verification.json`: `c212e7fd1687df551709584fa6d101a3fea56c8388c9118b11125f446c730172`
