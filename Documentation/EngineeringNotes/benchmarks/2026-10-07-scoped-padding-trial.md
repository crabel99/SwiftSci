# Scoped page-padded import trial

Date: 2026-10-07

## Decision

Retain page-padded scoped import as an explicit package-only experiment. Keep the public logical-extent import default unchanged. The candidate reduces peak memory for large unaligned inputs by approximately one packed Float32 payload. Timing is less conclusive, particularly for small inputs, and does not justify a global default change.

Implementation commit: `fbafdb53a694a7eea666aa8969c2dc24c852bb8a`.
Parent: `a4449211543d089a4c37bc8476f9d525a223190e`.
Branch: `codex/retained-memory-accounting-trial`. Nothing was pushed. This report and its evidence belong to `codex/engineering-notes` and must remain outside implementation PRs.

## Question and mechanism

The existing scoped import shares an input only when its start address and logical byte length are page-aligned. Otherwise it copies the logical values into MLX-owned storage. A page-aligned allocation alone does not remove that logical-extent copy.

The candidate rounds the backing allocation to a page boundary, packs the same logical values using the existing 16-by-16 converter, and initializes only the unused tail. It imports the complete padded allocation and slices and reshapes a view to the logical extent. Each call evaluates that view, completes its construction, and checks that its native pointer matches the expected location in the original buffer.

The operation receives the logical shape and cannot see padding through that view. The import captures the buffer owner, and the existing read scope waits for GPU completion before releasing its input and buffer. The completion defer also covers pointer-check failure and exceptions from the operation. The matrix helper's autorelease pool drains temporary Metal ownership after completion.

`ScopedGPURead.ImportPolicy` names the two treatments. Existing callers retain `.logicalExtent`. The new benchmark selects `.paddedAllocation` explicitly through a package-only prediction overload. It does not expose a public routing policy, change CPU computation, or retain an allocation between predictions. All comparison modes use the same default packing strategy. Retained input remains a separate control that prepares the input once.

Padding costs less than one page per allocation, plus view metadata and the pointer-verification barrier. The rounded allocation is checked against the device buffer limit and the one-dimensional MLX shape limit. Those costs are part of the measured workflow.

## Validation

The Release integration run passed 842 tests with zero failures and two skips. Xcode reports 1,031 successful executions when parameterized cases are included. The selected targets were SwiftDataFrame, SwiftStats, SwiftPreprocessing, SwiftML, SwiftCluster, SwiftOptimize, SwiftExplain, SwiftNLP and SwiftSciBenchmarkSupport.

New tests check native pointer identity for prefix and offset views, exact logical shape and output values, unchanged source storage, owner release after normal return and after a throw following GPU submission, nondefault GPU streams, rejection of incomplete padded allocations, page-edge prepared matrices, and CPU/GPU prediction parity with the unchanged default.

The two skipped tests require the optional Llama tokenizer fixture. An existing MNIST test returns early when a developer-specific NPZ fixture is absent and is reported passed by XCTest. Neither gap establishes coverage of those fixtures. This was not a full-library or sanitizer run.

All 720 benchmark workers passed full output and learned-parameter hash comparisons, the unchanged `1e-4` analytic-oracle bound, and tracked cleanup checks. Maximum absolute oracle error was `9.5367431640625e-07`. Every worker returned reservation bytes and active MLX bytes to zero; explicit cache clearing then returned cache bytes to zero. The candidate also verified input pointer sharing on every prediction call.

Independent behavior review found no actionable issues in the scoped ownership, bounds, default routing or tests. Standards review found no documented violations or actionable heuristic findings. The behavior review did not independently inspect the dependency's stream implementation; executable tests covered the nondefault-stream behavior. These checks do not prove complete RSS reclamation or the absence of every possible leak.

## Comparison contract

Use 512 generated training rows to fit StandardScaler and CPU ordinary least squares. Transform independent held-out rows without refitting. All paths use the same GPU prediction kernel and preserve every returned Double prediction array through the memory snapshot.

Widths were 17, 64 and 65. Row counts were 63, 64, 65, 4,095, 4,096, 4,097, 65,535 and 65,536. Each case used one or sixteen predictions and five fresh-process rounds of the public default, padded scoped candidate and retained default. The driver rotates mode order, runs one worker at a time, checks memory pressure before launch, and bounds each worker to 90 seconds. No build or other GPU workload launched by this task overlapped the comparison. Other workstation activity was not controlled.

Total workflow time includes held-out transformation, preparation and completed predictions. Training, fixture generation, warmup, validation, snapshots and cleanup are excluded. Padded view creation, pointer verification and synchronization are inside timing. This comparison tests real API paths rather than an isolated copy loop.

On this 16 KiB-page machine, 64 Float32 columns align every 64 rows. Widths 17 and 65 align every 4,096 rows. The default alignment column below follows that byte-count rule; the padded candidate verifies its actual pointer sharing.

## Large-input results

Times are median milliseconds. Memory is median process high-water MiB sampled before full validation. D is public scoped default, P is padded scoped candidate, and R is retained default.

| Columns | Rows | Predictions | D aligned | D ms | P ms | R ms | D MiB | P MiB | R MiB |
| ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 17 | 65535 | 1 | no | 4.664 | 4.619 | 4.979 | 51.14 | 47.02 | 47.20 |
| 17 | 65535 | 16 | no | 36.534 | 37.613 | 11.469 | 59.00 | 54.89 | 55.02 |
| 17 | 65536 | 1 | yes | 4.488 | 4.704 | 5.080 | 46.91 | 47.05 | 47.20 |
| 17 | 65536 | 16 | yes | 35.487 | 36.965 | 9.960 | 54.77 | 54.92 | 55.08 |
| 64 | 65535 | 1 | no | 14.922 | 13.867 | 14.627 | 123.80 | 107.94 | 108.09 |
| 64 | 65535 | 16 | no | 114.216 | 108.356 | 20.138 | 131.64 | 115.81 | 115.89 |
| 64 | 65536 | 1 | yes | 13.988 | 14.263 | 14.425 | 107.88 | 107.95 | 108.20 |
| 64 | 65536 | 16 | yes | 112.841 | 112.057 | 21.023 | 115.72 | 115.83 | 115.97 |
| 65 | 65535 | 1 | no | 14.864 | 14.289 | 14.499 | 125.58 | 109.45 | 109.62 |
| 65 | 65535 | 16 | no | 108.325 | 97.992 | 20.852 | 133.44 | 117.31 | 117.47 |
| 65 | 65536 | 1 | yes | 14.374 | 14.554 | 15.382 | 109.47 | 109.48 | 109.64 |
| 65 | 65536 | 16 | yes | 99.931 | 97.335 | 21.505 | 117.27 | 117.38 | 117.48 |

At 65,535 rows and sixteen predictions, the candidate reduced peak memory from 131.64 to 115.81 MiB at 64 columns and from 133.44 to 117.31 MiB at 65 columns. The reductions, about 15.83 and 16.13 MiB, are close to their 16.00 and 16.25 MiB packed payloads. The 17-column case saved about 4.11 MiB for a 4.25 MiB payload. Aligned neighboring inputs showed essentially unchanged peak memory.

The corresponding unaligned timing medians at 64 and 65 columns were 114.216 to 108.356 ms and 108.325 to 97.992 ms. The 17-column case was slightly slower with padding. These medians suggest a possible large-unaligned timing benefit, but the data do not establish a general speedup.

Retention still makes a much larger difference when predictions reuse the same prepared input. At 64 columns and 65,535 rows, sixteen predictions took 108.356 ms with scoped padding versus 20.138 ms with retained input. Removing a copy does not remove repeated validation, packing, allocation and import. This supports keeping packing, import policy and lifetime choice as separate decisions.

## Smaller-input results and uncertainty

The table below shows sixteen-prediction cases. Ranges are observed minimum to maximum across five workers, not confidence intervals. Some small cases have large timing spread, and neighboring shapes do not show a stable timing rule. Complete single-prediction samples are in the archive.

| Columns | Rows | Default aligned | Default median ms | Padded median ms | Default range ms | Padded range ms |
| ---: | ---: | --- | ---: | ---: | --- | --- |
| 17 | 63 | no | 9.277 | 10.522 | 8.417 to 13.374 | 8.324 to 12.963 |
| 17 | 64 | no | 9.043 | 9.343 | 7.891 to 14.435 | 7.408 to 16.183 |
| 17 | 65 | no | 9.727 | 9.657 | 6.827 to 15.015 | 6.949 to 13.471 |
| 17 | 4095 | no | 11.967 | 14.253 | 8.333 to 13.078 | 8.755 to 16.993 |
| 17 | 4096 | yes | 10.713 | 10.386 | 10.134 to 16.780 | 9.737 to 13.577 |
| 17 | 4097 | no | 14.160 | 10.336 | 8.150 to 15.879 | 8.672 to 13.648 |
| 64 | 63 | no | 9.042 | 14.481 | 6.647 to 11.497 | 8.738 to 15.946 |
| 64 | 64 | yes | 9.320 | 10.868 | 7.251 to 11.230 | 7.431 to 16.446 |
| 64 | 65 | no | 7.852 | 9.088 | 6.939 to 12.660 | 7.563 to 12.457 |
| 64 | 4095 | no | 18.020 | 17.699 | 11.982 to 21.707 | 13.631 to 19.641 |
| 64 | 4096 | yes | 20.097 | 20.517 | 19.410 to 22.812 | 13.119 to 21.584 |
| 64 | 4097 | no | 21.766 | 17.925 | 12.829 to 24.600 | 12.676 to 20.170 |
| 65 | 63 | no | 7.909 | 10.432 | 5.881 to 15.419 | 7.452 to 14.229 |
| 65 | 64 | no | 13.486 | 11.122 | 10.963 to 15.608 | 9.619 to 15.980 |
| 65 | 65 | no | 8.281 | 8.413 | 7.500 to 10.317 | 8.190 to 15.326 |
| 65 | 4095 | no | 21.095 | 21.468 | 12.956 to 21.597 | 19.628 to 26.995 |
| 65 | 4096 | yes | 21.029 | 19.232 | 19.160 to 22.169 | 17.791 to 26.634 |
| 65 | 4097 | no | 20.698 | 15.689 | 18.052 to 22.107 | 11.989 to 21.369 |

The extra view construction and completion barrier are not free. The current evidence favors preserving the existing default while retaining the padded candidate for further memory-policy work. It does not justify a measured row-count threshold, nor a claim that avoiding every copy always improves latency.

## Limits and next step

This is one generated regression workflow on one Apple-silicon machine. It does not cover all operations, allocation patterns, model sizes or memory-pressure states. Peak RSS includes prepared columns and returned outputs. MLX active memory overlaps imported external buffers and must not be added to their payload size. Admission estimates are not a process-memory cap.

Hardware was Apple M4 Max with 128 GiB unified memory, macOS 27.0 build 26A428. The arm64 Release binary targets macOS 14; no macOS 14 runtime was tested. MLX Swift remains pinned to fork commit `4657976edcdd2c60642424985d474b45ddddb390`. The saved build command selects safe Metal math and precise FP32 functions; the driver rejects coverage instrumentation.

Binary SHA-256: `b63947486f8c436de959883409d7dc66bebf5405b860167a4d964502d3bc35b3`.

Next, evaluate whether import policy should follow an explicit memory preference or admission estimate, using an application workload with a real memory limit. Keep the public default unchanged until that tradeoff is demonstrated. Do not combine a new lifetime policy, padding policy and packing change in one comparison.

Local commands, logs and test bundle are under `~/local-ai/spl/swiftsci/scoped-padding-trial-20261007/`. Replay instructions are in `Benchmarks/RetainedGPUTrial/README.md` on the implementation branch. The engineering-notes archive preserves all 720 records, summaries, provenance, compact test outcomes and the implementation commit identity.

- [17-column results](../archive/2026-10-07/scoped-padding-trial/width-17/summary.json)
- [64-column results](../archive/2026-10-07/scoped-padding-trial/width-64/summary.json)
- [65-column results](../archive/2026-10-07/scoped-padding-trial/width-65/summary.json)
- [Validation limits](../archive/2026-10-07/scoped-padding-trial/validation.json)
