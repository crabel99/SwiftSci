# Owned column and selection prototype, 2026-10-01

The prototype supports retaining compact buffers and explicit ownership. It does not support replacing all eager materialization with indirect selections. Direct matrix preparation reduced memory use in every measured case, but the million-row workflows took 16% to 19% longer. Keep this trial separate from production and test locality before choosing a storage policy.

## Source and scope

- Trial branch: `codex/unified-memory-prototype`, local commit `692a5578cec6a1d62cbe2df2d4747044154da69f`.
- Base: `codex/baseline-hardware-policy` at `f9e13de32e492b0a49eb0c6647a2136e9ccf6aa4`.
- Design: [unified-memory research](2026-10-01-unified-memory-design.md).
- Related implementation discussion: [upstream issue #40](https://github.com/Nodibell/SwiftSci/issues/40).
- Source directory: `Benchmarks/UnifiedMemoryPrototype`; run instructions are in its README.

The branch adds one executable target and experiment files. Production `Sources/` are unchanged. This record stays on `codex/engineering-notes`; it must not enter an implementation PR. The prototype has not been pushed or submitted for review.

The trial uses dense typed owners, optional validity bitmaps, copy-on-write edits, immutable buffer leases, composed row selections and direct matrix preparation. It preserves null versus valid NaN and exact Int64 payloads. CPU columns use ordinary typed allocations. A separate Metal check uses shared buffers to verify a retained input snapshot during a submitted GPU read and host mutation.

## Comparison

Three variants perform the same filtering, stable sorting, training-only scaling, column-major matrix preparation, LAPACK QR fit and BLAS prediction. `prepared` uses the actual `PreparedNumericBatch` and `StandardScaler`. `view-prepared` retains row selections until one gather, then uses those same production APIs. `owner-fused` retains selections and writes scaled values directly into the final owned matrix, preserving the scaler's row-width vDSP arithmetic.

The direct variant changes the pipeline as well as ownership. Its gains cannot be attributed solely to a different allocation type. The control already uses dense Double storage; this is not a comparison against optional-per-element storage.

Each table cell lists prepared / view-prepared / owner-fused. Times are median milliseconds. Memory is median peak process RSS in decimal MB. Selection is the requested fraction before complete-case filtering; null rates apply per feature.

| Input rows | Features | Selection | Nulls | Workflow ms | Peak RSS MB |
| ---: | ---: | ---: | ---: | --- | --- |
| 1,000 | 4 | 90% | 0% | 0.197 / 0.185 / 0.173 | 8.0 / 8.2 / 7.9 |
| 100,000 | 4 | 10% | 1% | 2.245 / 2.298 / 2.155 | 13.6 / 13.7 / 12.9 |
| 100,000 | 8 | 90% | 0% | 28.540 / 28.610 / 24.637 | 52.4 / 45.0 / 29.7 |
| 100,000 | 32 | 50% | 1% | 35.670 / 33.341 / 28.891 | 76.7 / 77.1 / 53.9 |
| 1,000,000 | 4 | 50% | 1% | 130.447 / 142.980 / 154.726 | 138.3 / 142.7 / 107.2 |
| 1,000,000 | 8 | 90% | 0% | 309.470 / 324.251 / 359.382 | 358.4 / 393.5 / 240.1 |

At 100,000 rows and 32 features, direct preparation used 19.0% less workflow time and 29.7% less peak RSS. At one million rows and eight features, it used 33.0% less peak RSS but 16.1% more workflow time. Retaining selections followed by ordinary prepared-batch operations did not deliver a consistent improvement by itself.

## Verification and method

- Release build passed with Swift 6.4 on Apple M4 Max, 128 GiB RAM, macOS 27.0. Reported cache line size was 128 bytes and VM page size was 16,384 bytes.
- All 28 check scenarios passed, including bitmap boundaries, shared validity mutation, duplicate edits, invalid-edit atomicity, retained lease lifetime, exact integer snapshots, composed selections and the Metal read lease.
- Six fixture shapes, three variants and five rounds produced 90 validated fresh-process measurements. Every variant had the same selected rows for each fixture.
- Analytic coefficients and independent scalar calculations checked row identity, matrix values, fit coefficients and predictions, including held-out rows. Maximum observed matrix or prediction absolute error was `4.3809400551708677e-13`. The small check fixtures also matched production scaled matrix values bit for bit.
- Each process constructed inputs and targets, warmed the workflow once, timed one workflow, captured RSS, and then ran the independent oracle. Input construction is reported separately in the raw results. These times apply to already-constructed inputs, not full ingestion.
- Variant order rotated between rounds. Thread-count overrides were removed. AC power was confirmed at the beginning and end. This is one machine and one session, with no claim of thermal isolation or hardware-counter profiling.
- RSS includes input construction, warmup, runtime and BLAS workspaces. It excludes the later oracle. It is not exact live memory or GPU allocation size. Logical materialization counts are intermediate payload accounting, not measurements of physical copy traffic.
- Full production tests and the formal benchmark gate were not rerun for this isolated executable. These exploratory results do not supersede the production baseline.

## Decision and next experiment

Preserve the compact owners and snapshot semantics as candidates. Do not adopt the indirect pipeline unconditionally. A plausible cause of the large-input regression is repeatedly reading sorted indices from the original columns while the control gathers contiguous values. Sorting also reads different layouts between variants. Neither explanation is established by the current timings.

Next, time filtering, sort-key access, gathering, scaling and packing separately. Compare one deliberate contiguous gather after ordering against repeated indirect reads, then evaluate tiled packing. Retain the same correctness contract and fixture range, add already-ordered, high-cardinality and skewed keys, and measure input construction as well as repeated workflows. Choose a policy from those measurements rather than a threshold fitted to this dataset.

The Metal check proves one ownership scenario, not GPU performance. MLX import and release, asynchronous cancellation, foreign Arrow owners, concurrent mutation, append and chunked storage still need separate qualification. No production ABI or minimum deployment version decision follows from this trial.

## Evidence identity

The second comparison run is authoritative for this experiment. It moved deterministic target generation outside the timed solver. The earlier exploratory run had target construction inside that boundary and should not be mixed with these measurements.

- Worker SHA-256: `83cec81379174c2ef787f04e27cd8620701e72827ba2d8c8850f50adbab21431`.
- Build manifest SHA-256: `c1129f7eeeede04bc998ea39baf56b130ced9561e27cb5332a6464765a4d7fea`.
- Raw samples SHA-256: `a2cc45ba504b3d02c7e2c879c657fd9526b24a4e3e5a67fc2e55caffa98b6523`.

Raw build, checks, samples and summary JSON are retained in the local experiment archive named `unified-memory-prototype-20261001`. The build manifest fingerprints the exact working source used before its commit. Those fingerprints were verified against the final committed files. Raw manifests include local paths and remain outside the public notes branch. This sanitized report contains no credentials or personal machine identifiers.
