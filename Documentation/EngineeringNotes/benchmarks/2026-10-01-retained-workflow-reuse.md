# Fitting access and retained-workflow reuse, 2026-10-01

Scoped fitting reads reduced training-column preparation cost without changing reductions. Retaining an immutable selection then avoided repeated filtering and sorting. Retaining gathered columns saved more time across different training splits, at a higher memory cost. These results support explicit retention choices; they do not establish a universal automatic threshold.

## Commits and scope

Both experiments remain local on `codex/unified-memory-prototype`.

- `ab8b5ef8e8ef9c26eb098618d584ddd26114d20c` adds scoped column reads to the scaler's training-scratch fill. The training row order, vDSP reduction calls, scratch size and packing are unchanged.
- `d482c656d94de032d4e155a0ebb9a9f90b8f0622` adds retained selection and gathered snapshot trials with changing held-out folds and one common numerical kernel.

Production `Sources/` are unchanged. This record belongs only to `codex/engineering-notes`. Nothing was pushed or submitted as a PR. Earlier results and ownership constraints are recorded in [bounded gathering and scoped reads](2026-10-01-bounded-gather.md). The implementation discussion remains [issue #40](https://github.com/Nodibell/SwiftSci/issues/40).

## Scoped fitting access

The following five-process medians compare the quantized-key fixture with one million rows, eight features, 90% requested selection and no nulls. Times are milliseconds; peak RSS is decimal MB.

| Variant | Fit stage ms | Workflow ms | Peak RSS MB |
| --- | ---: | ---: | ---: |
| prepared | 14.94 | 289.42 | 361.5 |
| keys-gather-fused | 8.55 | 211.07 | 289.4 |
| keys-tile-borrowed-4096 | 27.21 | 211.61 | 240.2 |
| keys-tile-borrowed-fit-4096 | 12.48 | 196.77 | 240.2 |

The controlled comparison is between packing-only borrowing and fitting-plus-packing borrowing. Fitting fell from about 27 ms to 12 ms and workflow time from about 212 ms to 197 ms, with unchanged peak memory. The change still gathers a full training column into scratch before calling the same reductions. It does not bound all statistics scratch or change precision policy.

This commit passed 319 Release check scenarios and 240 fresh-process measurements across the existing twelve fixture cases.

## Reuse experiment

The three strategies use the same scoped-read, 4,096-row tiled preparation kernel, LAPACK fitting and BLAS prediction. The retained gathered snapshot uses typed column owners, so storage-library and numerical-kernel differences do not explain the comparison.

- `recompute` rebuilds the selection for every fit.
- `selection` retains the sorted original row identities and immutable source owners.
- `gather` retains an ordered copy of the selected columns and their original row identities.

The original source table stays retained in every strategy. Setup is charged once. Each successive fit holds out a different one of five row-position residue classes. Fitting and scaling use only that fold's training rows. No fitted scaler, matrix or prediction output is reused across folds. Each pass releases its full result and retains only a small verification record.

Two fixture shapes were tested. The 100,000-row, 32-feature case uses quantized keys, 50% requested selection and 1% nulls per feature. The million-row, eight-feature case uses highly varied keys, 90% requested selection and no nulls. Each strategy and pass count ran in five fresh processes, with strategy order rotating between rounds.

| Input rows × features | Fits | Strategy | Setup ms | Setup + work ms | Whole sequence ms | Peak RSS MB |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| 100,000 × 32 | 1 | recompute | 0.0 | 21.5 | 22.8 | 55.9 |
| 100,000 × 32 | 1 | selection | 4.8 | 20.4 | 21.8 | 55.9 |
| 100,000 × 32 | 1 | gather | 8.1 | 19.9 | 21.3 | 65.3 |
| 100,000 × 32 | 3 | recompute | 0.0 | 64.8 | 68.7 | 55.9 |
| 100,000 × 32 | 3 | selection | 4.7 | 54.5 | 58.6 | 55.9 |
| 100,000 × 32 | 3 | gather | 8.2 | 43.4 | 47.5 | 65.3 |
| 100,000 × 32 | 5 | recompute | 0.0 | 105.0 | 111.7 | 55.9 |
| 100,000 × 32 | 5 | selection | 4.7 | 82.7 | 88.9 | 55.9 |
| 100,000 × 32 | 5 | gather | 8.2 | 67.4 | 73.8 | 65.3 |
| 1,000,000 × 8 | 1 | recompute | 0.0 | 238.1 | 251.0 | 237.2 |
| 1,000,000 × 8 | 1 | selection | 122.6 | 229.2 | 242.3 | 237.2 |
| 1,000,000 × 8 | 1 | gather | 143.7 | 209.5 | 223.6 | 296.6 |
| 1,000,000 × 8 | 3 | recompute | 0.0 | 718.0 | 757.2 | 240.4 |
| 1,000,000 × 8 | 3 | selection | 122.6 | 437.2 | 476.2 | 240.4 |
| 1,000,000 × 8 | 3 | gather | 141.4 | 332.3 | 372.1 | 296.7 |
| 1,000,000 × 8 | 5 | recompute | 0.0 | 1200.4 | 1264.8 | 240.5 |
| 1,000,000 × 8 | 5 | selection | 123.0 | 651.8 | 717.1 | 240.5 |
| 1,000,000 × 8 | 5 | gather | 142.7 | 460.7 | 524.7 | 296.8 |

For five fits on the million-row case, retaining a selection reduced setup-inclusive work from about 1,200 ms to 652 ms at similar peak RSS. Retaining gathered columns reduced it further to 461 ms, with about 56 MB more peak RSS. The wider, smaller fixture also benefited from retention, with a smaller absolute memory difference.

The gathered snapshot was faster even at one fit in these measured cases. That does not establish a crossover count of one for other schemas, selection densities, source lifetimes or memory pressure. Small single-fit differences on the wider fixture should not be used to choose a threshold.

## Verification and timing boundaries

The final Release build passed 401 check scenarios. New checks cover every training fold on nullable and non-nullable fixtures, production matrix agreement bit for bit, cache snapshots after source mutation, and final owner release. A cache is an immutable snapshot, not a live view of later table edits. Creating a new cache is required to use those edits.

Ninety measured reuse processes executed 270 fits. Each fit checked analytic coefficients and every prediction. It also recorded a deterministic fingerprint of matrix bit patterns, row identities and scaling parameters. After timing and RSS capture, the worker replayed every fold through the production prepared-batch path, ran the independent scalar oracle, and compared fingerprints. The controller required the same fingerprints across strategies and rounds. The fingerprint is an equivalence check, not a cryptographic guarantee.

The maximum observed reference matrix or prediction absolute error was `5.4312110364662658e-13`. Matrix, coefficient and prediction tolerances were unchanged. Production replay and the scalar oracle occurred after the recorded peak-RSS sample.

`setup_plus_work_ns` includes cache setup and the timed preparation, fitting and prediction calls. It excludes per-pass fingerprint scans, result checks and inter-pass cleanup. `sequence_ns` includes those costs. The scans can affect cache state before the next pass; both timings are retained so the comparison does not hide this experimental consumption step. Full input and target construction is separately timed and excluded from both sequence totals. All strategies warm one workflow before measuring.

RSS includes source input, warmup, retained caches, timed work, verification scans and allocator behavior before production replay. It is not exact live bytes. Source retention is explicit, so the gathered strategy does not obtain a memory advantage by releasing the original table. Owner counters exclude Swift arrays and framework allocations.

The machine was Apple M4 Max with 128 GiB RAM, Swift 6.4 and macOS 27.0. Runs used native library threading after clearing thread-count overrides and confirmed AC power at both ends. No thermal isolation, competing-load guarantee or hardware-counter profiling is claimed. Earlier commit timings should not be combined with this run as though they were simultaneous measurements.

Full production CI was not rerun for the isolated prototype. The GPU ownership check remains covered, but these workflow measurements are CPU results and do not demonstrate MLX throughput or asynchronous safety.

## Design implication

The useful boundary is a retained immutable dataset plus an explicit representation choice. Retaining row identities can avoid repeated selection work without retaining another full selected-value copy. Materializing an ordered snapshot can reduce repeated numerical read cost when its memory budget is acceptable.

A production proposal should make snapshot ownership and source-mutation behavior clear. Expected reuse and available memory should inform representation choice; row count alone is insufficient. The present evidence supports keeping both choices available. It does not yet justify an automatic policy, a public API change or a minimum-toolchain change.

Before integration, extend the same contract to actual ingestion, mutation-heavy workloads, source release, memory pressure and foreign-buffer or MLX lifetimes. A reusable matrix is a separate opportunity when preprocessing is truly unchanged; this experiment deliberately changed training folds and did not reuse matrices.

## Evidence identity

The local archive `unified-memory-reuse-20261001` retains separate `fitting` and `reuse` records. Raw manifests include local paths and remain outside the public notes branch.

| Evidence | Fitting | Reuse |
| --- | --- | --- |
| Worker SHA-256 | `5f81ca0867fcef8f2d54a66476345127127972b650e310d0ec3eed72ce3668e2` | `9b4ac53fd55767006fca2ac45c5a77d21ff5edfceb9f2f862f39c4a6470be533` |
| Build manifest SHA-256 | `a771a02d1b6478047552223c118b35c18460bba18ae2f5ff67b7db29b8f9a2a1` | `1b2cb0d7fa0fdaf8e43b371165b511e8c7fec8c14069b4e535dc9e8e613597d5` |
| Samples SHA-256 | `4b9ff0f199708f1ac3d00815e3140b7e78ccf7a42e6425ebb5c8e8d2d945212b` | `101a865a9b7df318315538ed8e8a75e8df3b8bd20bcdd33f5bfefac01751d8a6` |

Working-file fingerprints were checked before committing each experiment. This sanitized record preserves the results and limitations without personal machine identifiers.
