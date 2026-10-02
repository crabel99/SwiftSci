# Bounded gathering and scoped reads, 2026-10-01

Reusable packing tiles plus scoped column reads retained nearly the full-gather speed while recovering most of the indirect path's memory benefit. For the million-row, eight-feature quantized fixture, the scoped tile used about 202 ms and 240 MB peak RSS. Full gathering used about 201 ms and 289 MB. The production prepared-batch control used about 285 ms and 361 MB. The small timing difference between the first two is not evidence that either is faster on this fixture.

## Scope and commits

Both changes are local on `codex/unified-memory-prototype` and follow the [sort-key and gather locality experiment](2026-10-01-unified-memory-locality.md).

1. `8ea1f287d33615e8d8f3ab0ecc6d54964b0bc440` adds reusable 256-, 4,096-, and 16,384-row packing tiles and exact scratch-allocation checks.
2. `58f45c5fdf35b89943f78080bbd7e905324c7bf7` adds a controlled 4,096-row variant that loads values through retained immutable column leases.

Production `Sources/` are unchanged. No branch was pushed and no PR was opened. Findings remain on `codex/engineering-notes`. This work informs [issue #40](https://github.com/Nodibell/SwiftSci/issues/40); it is not a public API or deployment-version decision.

## What changed

The packing loop gathers a tile into row-major scratch, applies the existing row-width vDSP arithmetic, and copies contiguous column segments into the final column-major matrix. Two scratch buffers are reused for every tile, including the last partial tile. A 4,096-row tile with eight Double features uses 512 KiB for these two numeric buffers. At 32 features it uses 2 MiB. This is the bounded packing allocation, not the entire workflow's memory requirement.

Fitting still retains one full training-column scratch pair to preserve the production reduction order. The final matrix and input columns remain full size. BLAS workspaces and selection indices also consume memory.

The first tile implementation retained the earlier optional-value accessor for every input value. Stage timings showed tile loading dominated packing. The second implementation changes only that load path. After the immutable complete-row selection validates indices and excludes nulls, retained column leases provide scoped buffers. No pointer escapes this kernel. Scaler fitting, arithmetic, tile size and output layout are unchanged between the ordinary and scoped 4,096-row variants.

## First comparison: tile size

Medians below are for one million rows and eight features with quantized keys. All are from the same tile-size run. Times are milliseconds and RSS is decimal MB.

| Variant | Workflow ms | Peak RSS MB |
| --- | ---: | ---: |
| prepared | 282.16 | 361.4 |
| keys-fused | 259.94 | 240.1 |
| keys-gather-fused | 202.41 | 286.2 |
| keys-tile-256 | 245.86 | 240.2 |
| keys-tile-4096 | 246.40 | 240.2 |
| keys-tile-16384 | 245.85 | 237.1 |

The three sizes produced similar workflow times on this case. Tiling improved the indirect path and retained its lower memory footprint, but it did not match full gathering. This did not support tuning a universal tile size from these timings. The scoped-read trial used the middle size, 4,096 rows, to isolate access cost.

## Controlled comparison: scoped column reads

Each cell lists production prepared control / cached-key full gather / cached-key scoped 4,096-row tiles. Values are medians of five fresh processes. Selection fractions precede complete-case filtering and null rates apply per feature. Input and target construction are outside the workflow timer.

| Input rows × features | Sort keys | Selection / nulls | Workflow ms | Peak RSS MB |
| --- | --- | --- | --- | --- |
| 1,000 × 4 | quantized | 90% / 0% | 0.184 / 0.135 / 0.126 | 7.9 / 8.0 / 8.0 |
| 100,000 × 4 | quantized | 10% / 1% | 2.066 / 1.589 / 1.489 | 13.6 / 13.0 / 13.0 |
| 100,000 × 8 | quantized | 90% / 0% | 26.518 / 18.668 / 17.057 | 44.8 / 36.1 / 30.4 |
| 100,000 × 32 | quantized | 50% / 1% | 32.538 / 21.457 / 20.562 | 76.6 / 66.5 / 55.9 |
| 1,000,000 × 4 | quantized | 50% / 1% | 121.081 / 94.074 / 92.846 | 135.2 / 115.0 / 104.1 |
| 1,000,000 × 8 | quantized | 90% / 0% | 284.750 / 201.234 / 201.853 | 361.4 / 289.3 / 240.2 |
| 100,000 × 8 | continuous | 90% / 0% | 28.300 / 19.627 / 18.459 | 44.8 / 36.1 / 30.4 |
| 100,000 × 8 | ordered | 90% / 0% | 15.402 / 10.342 / 9.107 | 44.7 / 36.1 / 30.4 |
| 100,000 × 8 | skewed | 90% / 0% | 21.005 / 14.290 / 12.995 | 44.8 / 36.1 / 30.4 |
| 1,000,000 × 8 | continuous | 90% / 0% | 311.757 / 226.117 / 226.171 | 361.4 / 289.3 / 240.2 |
| 1,000,000 × 8 | ordered | 90% / 0% | 148.249 / 101.871 / 87.880 | 358.3 / 289.3 / 240.1 |
| 1,000,000 × 8 | skewed | 90% / 0% | 217.013 / 152.670 / 142.636 | 361.4 / 289.3 / 237.6 |

Scoped tiles were close to full-gather speed on both million-row random-key cases, and faster in several other cases. They used less peak RSS in the wider and larger cases. The 1,000-row case still has similar process memory, and the earlier fresh-process construction overhead remains unresolved. These are synthetic workflow observations, not a general speedup guarantee.

The following stage medians are milliseconds for the million-row, eight-feature quantized case. Tile load, scale and write are subdivisions of pack time. They must not be added to pack again.

| Variant | Sort | Full column gather | Fit scale | Pack | Tile load | Tile scale | Tile write |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| prepared | 138.36 | 30.39 | 14.61 | 53.80 | 0.00 | 0.00 | 0.00 |
| keys-fused | 93.97 | 0.00 | 25.53 | 89.57 | 0.00 | 0.00 | 0.00 |
| keys-gather-fused | 93.06 | 25.86 | 8.38 | 25.13 | 0.00 | 0.00 | 0.00 |
| keys-tile-4096 | 93.28 | 0.01 | 25.42 | 79.39 | 66.14 | 5.27 | 7.86 |
| keys-tile-borrowed-4096 | 92.35 | 0.01 | 25.01 | 36.01 | 22.14 | 5.47 | 7.98 |

The scoped-read change reduced tile loading without changing its memory layout or numerical work. This supports using a validated, retained buffer at kernel boundaries. It does not identify individual cache misses or prove that all optional-access costs have been removed. Hardware counters were not collected.

## Validation

- The tile-size commit passed 253 Release check scenarios and 360 measured workflows. The scoped-read commit passed 286 check scenarios and 300 measured workflows.
- Every check fixture matched production matrix values bit for bit. Dedicated sizes covered 255/256/257, 4,095/4,096/4,097 and 16,383/16,384/16,385 rows, including partial tiles.
- Checks explicitly retain input and result while inspecting allocation counters. The first attempt assumed lexical variable scope implied lifetime, and its assertion failed after objects became eligible for release. Explicit retention corrected that test assumption. Checks now verify exact peak scratch bytes, scratch release after preparation, and final owner release balance.
- The measurement runner checks the same exact owner budget against the indirect variant on all twelve cases. The tile contribution is `2 * min(tileRows, selectedRows) * features * sizeof(Double)`. Owner counters exclude Swift arrays, allocator metadata and framework workspaces; RSS measures the broader process peak.
- All 300 final workers passed the independent matrix, fit and prediction oracle, with maximum observed matrix or prediction absolute error `3.3892000317337079e-11`. Existing tolerances were unchanged. Selected-row counts agreed across variants.
- Float and exact Int64 storage, nullable mutation, retained snapshots and the Metal read-lease check remain covered. The reported workflow timings are CPU results. This trial does not qualify MLX interoperability, asynchronous cancellation or concurrent mutation.
- The machine was Apple M4 Max with 128 GiB RAM, Swift 6.4 and macOS 27.0. Both runs confirmed AC power at the start and end. Variants rotated between rounds and used native library threading after clearing overrides. No thermal isolation or competing-load guarantee is claimed.
- Each fresh process constructed inputs and targets, warmed one workflow, timed one workflow, recorded RSS, and then ran its oracle. RSS includes construction, warmup and framework workspaces. Input construction has a separate timer. These timings do not establish cold end-to-end ingestion performance.
- Full production CI was not rerun for these isolated prototype changes. The authoritative public baseline remains unchanged.

## Design implication and next test

Keep stable typed owners, retained immutable leases, explicit selection validation and deliberate materialization boundaries together. The measurement supports that combination. It does not support making every operation allocate Metal storage or exposing arbitrary mutable pointers.

Retain full gathering as a comparison for repeated reuse. The tiled path regathers each invocation; a reusable gathered batch may repay its allocation over multiple operations. Next compare those reuse patterns, and separately test borrowing in the training-statistics read loop while retaining the same input order and reduction calls. Do not change the scaler's reduction order merely to bound its scratch memory without a new numerical qualification.

The scratch-size sweep should eventually use byte budgets as well as row counts across wider schemas. A production policy also needs ingestion, mutation frequency, long-lived selections, foreign-buffer lifetime and memory-pressure measurements. The present experiment does not select an automatic threshold.

## Evidence identity

Local archive `unified-memory-tiles-20261001` contains separate `tile-sizes` and `scoped-read` JSON records. Raw build manifests include local paths and stay outside the public notes branch.

| Evidence | Tile sizes | Scoped reads |
| --- | --- | --- |
| Worker SHA-256 | `2fe245540139f9c3bc515d299315bcf49a2ca03cd5d4a51fd3fa35dc1a4bf4a0` | `dd20a2f371e9b30f10415ded4380a7176b9d416f295e42feda204a45df2fd5da` |
| Build manifest SHA-256 | `a49f31193d39a71d2c0d0ba3054d2ca62af5b25fff6f97527de99f0694738c4b` | `d6c61389a18acd6045c5c0641dd1b8ad5c391a634dfeab4e1885103318a4f673` |
| Samples SHA-256 | `223932c70a846558982d1100571b449ed6a96d8abce7510cf34ab3237c8f3db6` | `5afae232ba52ecdef82383fbe83c9988f77fcee23173a7bc10eec9dad14c8e1f` |

Each build manifest fingerprints the exact working files used before its commit. Fingerprints were checked before committing both revisions. This sanitized report preserves the result and limitations without local usernames or device identifiers.
