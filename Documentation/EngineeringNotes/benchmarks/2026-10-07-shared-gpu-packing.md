# Shared GPU packing and blocked conversion trial

Date: 2026-10-07

## Decision

Keep a shared bulk packer for scoped prepared prediction and retained prepared input. Keep the row-wise strategy as the default and retain the blocked strategy as an explicit package-only candidate. The blocked candidate improves wider, larger workflows without adding a staging array. Small and narrow cases show less benefit, so these measurements do not establish an automatic routing threshold.

Implementation commit `bb67a3bf2c85892fc1b4d1519c70d74a82e4409b` is on `codex/retained-memory-accounting-trial`, based on `ad577702e56b983a40fde8856a3e8b6afb85bf51`. Nothing was pushed. Engineering decisions and measurements remain separate on `codex/engineering-notes`.

## Structural change

`PreparedFloatPacking` accepts the complete prepared batch and a destination buffer. It caches dimensions, checks destination extent and converts to row-major Float32 output. The row-wise loop and blocked loop implement the same scalar conversion. The blocked loop walks 32-by-32 tiles, reads short contiguous runs from each column and writes those values at their row-major positions. It allocates no staging array. The tile size is an experimental candidate, not a measured hardware optimum.

The scoped prepared prediction path calls `ScopedGPURead.withMatrix(batch:packing:)`, which invokes the shared packer. Retained batch construction invokes the same packer. Allocation, import, synchronization, admission transfer and final-owner cleanup remain with the existing scoped and retained owners.

This removes the cross-module per-element callback from prepared GPU prediction. Optimized object symbols confirm that both paths reference the same specialized bulk-packing function. Generic row-array prediction and training retain the original callback entry. CPU computation, schema checks, empty-input behavior and Float32 conversion policy are preserved. Finite Double values can still overflow Float32, as before.

The package-only blocked prediction overload exists to compare strategies. It does not expose a new public precision policy or introduce automatic backend selection.

## Validation

All 226 focused Release tests passed, with no failures or skips. Added tests compare exact Float bit patterns across tile and page edges, signed zero, underflow, overflow, empty batches and irregular widths. Guard elements detect writes outside the destination. GPU tests compare public row-wise, scoped blocked, retained row-wise and retained blocked predictions. Existing snapshot, invalid-input and cleanup tests now also exercise blocked retained construction.

Behavior and standards reviews found no actionable issues. The final worker build also passed the focused suite after feature-width controls were added.

All 760 measured workers passed complete output and learned-parameter hash comparisons, full analytic-oracle checks and cleanup checks. Maximum oracle error was `9.5367431640625e-07`, below the fixed `1e-4` bound. Every worker returned reservations and active MLX bytes to zero, then reported zero cache bytes after explicit clearing.

The full library suite and sanitizers were not rerun. These scoped checks do not establish absence of all leaks or complete reclamation of process RSS.

## Measurement contract

Fit StandardScaler and CPU ordinary least squares on 512 rows with the requested feature width. Use independent held-out rows and training-only preprocessing. All four paths use the same GPU prediction kernel and keep every returned Double array alive through the measured memory snapshot. Inputs and outputs are bit-identical between modes.

The 64-column comparison covers 63, 64, 65, 4,096 and 65,536 rows at 1, 2, 4 and 16 predictions. Widths 16, 65 and 128 cover 65, 4,096 and 65,536 rows at 1 and 16 predictions. Five serial fresh processes per mode and case produce 760 records. Mode order rotates, every worker has a timeout, and a memory-pressure check precedes each launch.

Total time includes held-out transformation, input preparation and completed predictions. Training, fixture generation, warmup, full verification, memory-snapshot overhead and cleanup remain outside timing. Admission estimates and output lifetimes match within each comparison. Scoped import still has its existing unaligned-extent copy fallback; retained construction still pads and verifies sharing.

## Large-input results

All rows below use 65,536 held-out observations. Times are median milliseconds. RSS columns are median process high-water MiB measured before full verification. R means row-wise packing and B means blocked packing.

| Columns | Predictions | Scoped R ms | Scoped B ms | Retained R ms | Retained B ms | Scoped R RSS | Scoped B RSS | Retained R RSS | Retained B RSS |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 16 | 1 | 4.849 | 4.638 | 5.191 | 4.930 | 45.56 | 45.64 | 46.00 | 46.06 |
| 16 | 16 | 36.345 | 29.700 | 12.629 | 12.279 | 53.56 | 53.50 | 53.88 | 53.88 |
| 64 | 1 | 20.567 | 14.745 | 20.947 | 15.519 | 108.25 | 108.05 | 108.44 | 108.52 |
| 64 | 16 | 176.469 | 89.536 | 28.326 | 23.432 | 115.80 | 115.80 | 116.09 | 116.08 |
| 65 | 1 | 20.242 | 14.427 | 20.544 | 15.473 | 109.50 | 109.52 | 109.88 | 109.80 |
| 65 | 16 | 176.189 | 90.382 | 29.110 | 23.492 | 117.70 | 117.38 | 117.75 | 117.70 |
| 128 | 1 | 53.234 | 33.695 | 53.045 | 33.624 | 191.02 | 190.98 | 191.38 | 191.31 |
| 128 | 16 | 520.990 | 201.683 | 59.708 | 41.324 | 199.28 | 199.45 | 199.22 | 199.17 |

At 64 columns and sixteen predictions, blocked scoped prediction reduced total time from 176.469 to 89.536 ms. Blocked retained prediction reduced 28.326 to 23.432 ms. Peak memory stayed essentially the same for each lifetime.

With the row-wise packer, retention gives a 6.23-fold scoped-to-retained ratio in that case. With the blocked packer, the ratio is 3.82-fold. Both paths became faster, but improving scoped preparation reduced the relative advantage attributed to retention. This is the architectural reason to compare lifetimes with the same packing implementation.

At 128 columns and sixteen predictions, blocked scoped prediction reduced 520.990 to 201.683 ms; blocked retained prediction reduced 59.708 to 41.324 ms. At 16 columns, the gains were smaller. Single large predictions generally favored scoped execution or were close; retention still has setup overhead to recover through reuse.

## Smaller-input results

Ratios are row-wise median time divided by blocked median time. Values above one favor blocked packing. Near-one differences should not be treated as established gains.

| Columns | Rows | Predictions | Scoped ratio | Retained ratio |
| ---: | ---: | ---: | ---: | ---: |
| 16 | 65 | 1 | 0.99 | 0.96 |
| 16 | 65 | 16 | 1.00 | 0.97 |
| 16 | 4,096 | 1 | 1.02 | 0.99 |
| 16 | 4,096 | 16 | 1.04 | 1.01 |
| 64 | 65 | 1 | 0.98 | 1.00 |
| 64 | 65 | 16 | 0.98 | 1.08 |
| 64 | 4,096 | 1 | 1.22 | 1.19 |
| 64 | 4,096 | 16 | 1.39 | 1.18 |
| 65 | 65 | 1 | 1.00 | 0.94 |
| 65 | 65 | 16 | 1.07 | 1.00 |
| 65 | 4,096 | 1 | 1.22 | 1.15 |
| 65 | 4,096 | 16 | 1.40 | 1.05 |
| 128 | 65 | 1 | 0.99 | 0.95 |
| 128 | 65 | 16 | 1.01 | 1.01 |
| 128 | 4,096 | 1 | 1.29 | 1.25 |
| 128 | 4,096 | 16 | 1.58 | 1.07 |

The wider 4,096-row scoped cases improve more than the narrow ones. The small cases are approximately tied, with some small regressions in median time. The retained path packs once, so packing improvements account for a smaller part of repeated-prediction time. Historical runs used different implementations and were not interleaved with this run; they are not direct before/after controls.

## Evidence and next work

The results support the shared bulk boundary and further evaluation of blocked packing. They do not establish that 32-by-32 tiles are optimal or identify an automatic policy. The next decision is whether a blocked implementation should become the prepared-input default, based on additional widths, representative workloads and broader integration checks. Padding/import policy remains an independent question.

Hardware was Apple M4 Max with 128 GiB unified memory, macOS 27.0 build 26A428. The Release arm64 binary targets macOS 14; no macOS 14 runtime was tested. The pinned MLX fork remains `4657976edcdd2c60642424985d474b45ddddb390`. The saved build command uses safe Metal math and precise FP32 functions. The binary guard verifies coverage instrumentation is absent.

Binary SHA-256: `109564ed7747868a2aa31109c11b7b2dda4c84f3e2783255ad5112e5478bba76`.

Replay commands are in `Benchmarks/RetainedGPUTrial/README.md` on the implementation branch. Local test bundles, commands and logs are under `~/local-ai/spl/swiftsci/shared-gpu-packing-20261007/`. The engineering-notes archive preserves per-width summaries, all samples, provenance and optimized compiler objects' fingerprints. Archived assembly text has trailing whitespace normalized; raw tool output remains local.

- [16-column results](../archive/2026-10-07/shared-gpu-packing/width-16/summary.json)
- [64-column results](../archive/2026-10-07/shared-gpu-packing/width-64/summary.json)
- [65-column results](../archive/2026-10-07/shared-gpu-packing/width-65/summary.json)
- [128-column results](../archive/2026-10-07/shared-gpu-packing/width-128/summary.json)
- [Compiler fingerprints](../archive/2026-10-07/shared-gpu-packing/compiler/fingerprints.json)
