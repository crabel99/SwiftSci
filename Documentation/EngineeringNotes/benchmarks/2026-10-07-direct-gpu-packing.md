# Direct packing into retained GPU storage

Date: 2026-10-07

## Decision

Keep direct packing in the local memory trial. It removes the temporary Float array and reduces preparation time and peak memory for the large input. Repeated prediction retains its performance benefit. Small single predictions still favor the existing scoped path, so this evidence does not justify replacing every caller.

Implementation commit `dc2d23df38a96f398faba718d0e581e7e5fc2ff9` is on `codex/retained-memory-accounting-trial`, based on `df2388f1e31a546c9442b47cf8ab10466b1bd588`. The implementation and report remain local. Engineering evidence stays on `codex/engineering-notes`.

## Implementation

The package-only retained-input factory accepts a PreparedNumericBatch, validates finite Double values, and converts its columns directly into row-major Float32 shared storage. Both this factory and the existing Float-array factory use the same allocation, MLX import, admission transfer, and final-owner cleanup code. The initializer is private and synchronous. No buffer pointer escapes through it.

This removes an intermediate allocation and copy. It does not remove Double-to-Float conversion. Conversion follows the existing scalar policy, including signed zero, underflow and overflow. A finite Double can exceed the Float32 range and become infinity. This change does not introduce a new numerical-range guarantee.

The generic retained owner still does not own the feature schema. A production adapter should keep validated schema and storage together before callers adopt this path.

## Comparison protocol

The three modes use the same executable and prediction kernel. Scoped input validates and packs on each prediction. Staged retained input packs once through a temporary Float array. Direct retained input packs once directly into shared storage. Both retained modes use the same prediction entry and ownership rules.

Fit StandardScaler and CPU ordinary least squares on 512 rows with 64 features, using seed 41. Construct a GPU model from the learned parameters. Generate held-out data with seed 937 and transform it using the training statistics. The analytic target is a bias of 3 plus all raw features weighted by `(column % 7 - 3) / 16`.

Measure 64 or 65,536 held-out rows with either one or sixteen predictions. Timing includes held-out transformation, input preparation and completed predictions. It excludes training, fixture generation, validation, cleanup and memory-snapshot overhead. GPU warmup uses training-sized data. Retained prediction includes construction of its small MLX parameter arrays on each call.

Every returned Double prediction array remains alive through the measured memory snapshot and full validation. Five fresh processes per case and mode produce 60 samples. Mode order rotates each round. Workers run serially with a 90-second timeout and a memory-pressure check before launch.

The common work allowance is 128 MiB within a 256 MiB admission budget. Retained construction also acquires and transfers an input grant. These estimates are not a cap on process RSS.

## Results

Times are milliseconds. Preparation, workflow and peak RSS columns show medians of five samples. The range shows minimum and maximum total workflow time.

| Rows | Predictions | Mode | Preparation ms | Workflow ms | Workflow range ms | Peak RSS MiB |
| ---: | ---: | --- | ---: | ---: | --- | ---: |
| 64 | 1 | Scoped | 0.021 | 0.720 | 0.380 to 0.734 | 24.45 |
| 64 | 1 | Staged retained | 0.422 | 1.056 | 1.044 to 2.338 | 24.81 |
| 64 | 1 | Direct retained | 0.414 | 1.087 | 1.055 to 1.208 | 24.86 |
| 64 | 16 | Scoped | 0.021 | 8.039 | 7.287 to 9.686 | 24.61 |
| 64 | 16 | Staged retained | 0.437 | 4.909 | 4.682 to 6.893 | 24.91 |
| 64 | 16 | Direct retained | 0.419 | 5.470 | 3.986 to 6.346 | 24.86 |
| 65,536 | 1 | Scoped | 9.311 | 19.991 | 19.799 to 21.187 | 107.75 |
| 65,536 | 1 | Staged retained | 28.272 | 29.769 | 27.648 to 31.277 | 147.16 |
| 65,536 | 1 | Direct retained | 18.160 | 19.426 | 19.152 to 23.380 | 107.98 |
| 65,536 | 16 | Scoped | 9.018 | 185.019 | 179.806 to 187.482 | 115.56 |
| 65,536 | 16 | Staged retained | 26.761 | 35.439 | 33.832 to 36.989 | 153.28 |
| 65,536 | 16 | Direct retained | 18.098 | 26.850 | 25.140 to 27.384 | 115.78 |

For 65,536 rows and sixteen predictions, direct packing reduced total time from 35.439 ms to 26.850 ms compared with staged retention, a 24.2% reduction. Peak RSS fell by 37.50 MiB. Compared with scoped prediction, direct retention was 6.89 times faster including preparation, with peak RSS within 0.22 MiB.

For one large prediction, direct retention took 19.426 ms versus 19.991 ms for scoped prediction. Their ranges overlap. Treat this as roughly equal performance, not a demonstrated single-prediction speedup. Direct retention removed about 39.17 MiB of peak RSS compared with staged retention in that case.

Small single predictions favored the scoped path. Small repeated predictions favored both retained modes, but direct retention had a slower median than staged retention with overlapping ranges. The removed staging array matters most for the large input in this experiment.

This comparison measures a complete prediction workflow. Its speedup includes avoided validation, packing, and buffer acquisition. It is not a GPU arithmetic speedup. Process high-water measurements cannot assign every saved resident byte to a particular allocation.

## Validation and limitations

All 222 focused Release tests passed, with zero failures or skips. Added tests cover row-major layout, scalar conversion bit patterns, missing and nonfinite input rejection, empty input, queued cancellation, view lifetime and final-owner cleanup. Existing regression workflow tests now exercise direct construction. Behavior and standards reviews found no actionable issues.

All 60 measured workers passed the independent analytic oracle. Maximum absolute error was `4.76837158203125e-7`, below the fixed `1e-4` bound. Output and learned-parameter hashes matched across modes and repetitions. Every returned batch matched within its worker.

Every worker reported zero reservations and zero MLX active bytes after owner cleanup. Explicit cache clearing returned MLX cache bytes to zero. Prepared Double batches and prediction outputs were still alive during post-close memory snapshots. These checks establish the measured ownership release, not complete return of process memory to the operating system. MLX active bytes overlap imported external buffer storage and must not be added to the explicit payload count.

The full SwiftSci suite and sanitizers were not rerun. This is a deterministic local trial, not a formal performance baseline or evidence for arbitrary datasets.

## Reproduction and evidence

Hardware was Apple M4 Max with 128 GiB unified memory, running macOS 27.0 build 26A428. The arm64 binary targets macOS 14. No macOS 14 runtime was tested. MLX Swift remains pinned to fork revision `4657976edcdd2c60642424985d474b45ddddb390`.

The benchmark used the executable produced by the passing Release test build. Coverage was disabled and the Mach-O guard confirmed no coverage instrumentation. The saved build command uses safe Metal math, precise FP32 functions and fast math disabled.

Binary SHA-256: `1671e0c8710a9a701764223cc2a94f82f99ecb6535f3fa392b2465755dc6e6a5`.

Replay instructions are in `Benchmarks/RetainedGPUTrial/README.md` on the implementation branch. Local build commands, logs and the test bundle are in `~/local-ai/spl/swiftsci/retained-gpu-direct-pack-20261007/`. The final measurements are in `comparison`; `smoke` is preliminary.

Archived evidence includes the [summary](../archive/2026-10-07/direct-gpu-packing/summary.json), [samples](../archive/2026-10-07/direct-gpu-packing/samples.json), and [source and binary fingerprints](../archive/2026-10-07/direct-gpu-packing/provenance.json).
