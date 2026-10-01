# Locality experiment, 2026-10-01

Cached sort keys and one ordered gather recovered the large-input speed loss from the [first owned-column trial](2026-10-01-unified-memory-prototype.md). In the confirmation run, the combined path used 22% to 34% less workflow time than the production prepared-batch control across twelve synthetic cases. It retained part of the memory savings. Keep both the combined and indirect variants until the memory-budget policy is tested.

## Source and boundaries

Trial branch `codex/unified-memory-prototype`, commit `8fac435c37ff78f06931de5d0ef171166e56b685`, builds on the first trial at `692a5578cec6a1d62cbe2df2d4747044154da69f`. Production `Sources/` and public APIs are unchanged. This is a local experiment for [issue #40](https://github.com/Nodibell/SwiftSci/issues/40), not a submitted patch or a new formal performance baseline. Engineering conclusions remain on `codex/engineering-notes`.

The question was whether the first trial's million-row slowdown came from sorting through repeated column lookups, repeated indirect numerical reads after sorting, or matrix traversal order. This experiment separated the first two changes. It did not isolate traversal order independently or measure hardware cache misses.

Six variants keep the same filtering, stable ordering, training-only scaling, matrix, LAPACK fit and BLAS prediction contract. `prepared` and `view-prepared` retain the existing production scaler. `owner-fused` is the indirect direct-packing trial. `gather-fused` adds one contiguous column gather after sorting. `keys-fused` adds only cached sort keys. `keys-gather-fused` combines both changes. The latter three preserve the same row-width vDSP arithmetic as the first trial.

## Measurements

Values below are medians of five fresh processes per variant and case. Each arrow compares the production `prepared` control with `keys-gather-fused`. Workflow time excludes input and target construction. Selection is the requested fraction before complete-case filtering; null rates apply per feature. RSS is decimal MB.

| Input rows × features | Sort keys | Selection / nulls | Workflow ms | Time reduction | Peak RSS MB |
| --- | --- | --- | --- | ---: | --- |
| 1,000 × 4 | quantized | 90% / 0% | 0.186 → 0.141 | 24.0% | 8.0 → 8.0 |
| 100,000 × 4 | quantized | 10% / 1% | 2.250 → 1.762 | 21.7% | 13.7 → 13.0 |
| 100,000 × 8 | quantized | 90% / 0% | 27.474 → 19.639 | 28.5% | 44.9 → 36.0 |
| 100,000 × 32 | quantized | 50% / 1% | 34.784 → 23.001 | 33.9% | 76.7 → 66.5 |
| 1,000,000 × 4 | quantized | 50% / 1% | 128.173 → 99.939 | 22.0% | 135.2 → 116.9 |
| 1,000,000 × 8 | quantized | 90% / 0% | 315.093 → 219.456 | 30.4% | 361.5 → 289.4 |
| 100,000 × 8 | continuous | 90% / 0% | 29.690 → 21.178 | 28.7% | 48.3 → 36.0 |
| 100,000 × 8 | ordered | 90% / 0% | 15.509 → 11.341 | 26.9% | 44.8 → 36.0 |
| 100,000 × 8 | skewed | 90% / 0% | 22.094 → 15.402 | 30.3% | 46.3 → 36.0 |
| 1,000,000 × 8 | continuous | 90% / 0% | 339.908 → 240.880 | 29.1% | 361.5 → 286.2 |
| 1,000,000 × 8 | ordered | 90% / 0% | 160.719 → 109.967 | 31.6% | 359.1 → 286.2 |
| 1,000,000 × 8 | skewed | 90% / 0% | 237.937 → 162.478 | 31.7% | 361.4 → 289.3 |

The quantized fixture has 1,024 possible key values. The continuous fixture has highly varied deterministic finite keys, the ordered fixture starts in row order, and the skewed fixture repeats zero for about 90% of keys. Original row order breaks ties in every variant.

The combined path used about 20% less peak process memory in the million-row, eight-feature quantized case. Its approximately 289 MB peak was higher than the approximately 240 MB indirect variant from this comparison. The gather buys faster repeated reads at the cost of an additional selected-column representation. Small RSS differences are noisy: the sparse case was slightly higher than the control in screening and lower in confirmation.

## Where time went

The following median stage times are milliseconds for one million rows and eight features with quantized keys. Stage medians do not sum exactly to the median workflow. Filtering, selection bookkeeping, timing overhead and solving also contribute.

| Variant | Cache keys | Sort | Gather columns | Fit scale | Scale and pack | Workflow | Peak RSS MB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| prepared | 0.00 | 145.60 | 33.04 | 15.49 | 64.41 | 315.09 | 361.5 |
| view-prepared | 0.00 | 190.22 | 27.07 | 14.40 | 65.29 | 348.13 | 393.5 |
| owner-fused | 0.00 | 183.78 | 0.00 | 27.03 | 109.81 | 370.69 | 240.2 |
| gather-fused | 0.00 | 186.81 | 28.36 | 8.78 | 28.14 | 303.07 | 289.2 |
| keys-fused | 2.50 | 100.16 | 0.00 | 29.59 | 111.43 | 295.38 | 240.1 |
| keys-gather-fused | 2.45 | 100.06 | 28.23 | 8.64 | 27.52 | 219.46 | 289.4 |

Caching keys reduced the sort stage. Gathering once reduced both scaler fitting and matrix packing enough to repay the gather in these cases. The independent variants support both conclusions. They do not establish which cache level, branch cost or compiler optimization accounts for each gain. That would require hardware profiling.

The indirect path remains useful when memory is the tighter constraint. The experiment does not justify choosing a universal row-count threshold or always gathering every selection.

## Correctness and reproducibility

- Final Release checks passed all 154 scenarios, including ownership, validity bitmaps, snapshot edits, exact Int64 storage, Metal read leases and bitwise agreement with the production scaler on the small check fixtures.
- Screening passed 270 fresh-process measurements. Confirmation passed 360 measurements across twelve cases, six variants and five rounds. Every worker ran an independent scalar and analytic oracle after timing; selected-row counts agreed across variants.
- The maximum observed matrix or prediction absolute error in confirmation was `3.3892000317337079e-11`. Matrix checks retained the absolute `1e-10` limit; prediction checks retained `1e-9 * max(1, abs(expected))`. Coefficients and intercept were checked separately. No tolerance was changed.
- The final source added cached-key payload accounting, an explicit matrix-length check, and the three additional million-row key-pattern cases after screening. An intermediate build was interrupted to correct a missing test-loop brace; it produced no benchmark evidence.
- Machine context was Apple M4 Max, 128 GiB RAM, Swift 6.4 and macOS 27.0. Native library thread policies were used after clearing thread-count overrides. AC power was confirmed at both ends. No thermal isolation or competing-load guarantee is claimed.
- Each process constructed input and targets, warmed the workflow, measured one workflow, captured peak RSS, and then validated. RSS includes construction, warmup and runtime workspaces. It is not exact live storage or GPU memory. Logical numeric payload accounting excludes selection-index storage and opaque allocator traffic.
- Fresh-process construction for the 1,000-row case was about 0.136 ms for the control and 1.174 ms for the owned variant. These are separately measured construction costs. The workflow times are warmed, so adding them is not a measurement of a fully cold end-to-end run. Tiny one-shot tasks remain a limitation.
- Full production CI was not rerun because this commit changes only the isolated prototype. The GPU check verifies ownership; the reported workflow speedups are CPU results.

## Next boundary to test

Retain the stable owner and explicit snapshot rules. Use cached sort keys as a candidate when ordering indirect selections. Test bounded or tiled gathering next, against both the faster fully gathered path and the lower-memory indirect path. Include repeated operations on the same selection and actual ingestion before defining a storage policy. The goal is to recover more of the memory saving while preserving this speed improvement.

A production proposal also needs mutation frequency, retained snapshots, batch reuse, foreign ownership and MLX lifetime tests. These results do not settle chunk size, automatic backend dispatch, asynchronous cancellation, minimum deployment version or public ABI.

## Evidence identity

- Final worker SHA-256: `b85e87cf6af56ab0c700e25fd51405e3616b74b9e71989e050dc4f4153477481`.
- Final build manifest SHA-256: `9fc9f66e0029365be9d6fba9e5586e54cab6d41d94e6f33ccd322715f5eaa5b4`.
- Final raw samples SHA-256: `8bec24f07123f3c383dfa9aa167655366efa3bd2cb674adc02ec864dc78b24c8`.

The build manifest fingerprints the pre-commit working files. All listed fingerprints were verified against the files committed at the revision above. Screening and confirmation JSON are retained locally under the archive name `unified-memory-locality-20261001`. Raw manifests contain local paths and are excluded from the public notes branch. This report is sanitized for that branch.
