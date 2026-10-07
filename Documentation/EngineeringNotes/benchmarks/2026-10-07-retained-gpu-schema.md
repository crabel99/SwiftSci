# Owned schema for retained GPU prediction

Date: 2026-10-07

## Decision and implementation

Keep the typed input adapter in the local trial. Retained prediction now accepts `RetainedPreparedGPUInputTrial`. This object owns feature names, order, row count and packed Float32 storage derived from the same immutable prepared batch. The factory is the only way to construct it. Callers cannot attach a different set of names to an arbitrary GPU allocation.

Implementation commit `6e8ad19ca037fd4b7bbb2b7717428427b6975f6b` is on `codex/retained-memory-accounting-trial`, based on `dc2d23df38a96f398faba718d0e581e7e5fc2ff9`. Existing public prediction APIs are unchanged. No branch was pushed.

The adapter keeps the generic retained owner private. It exposes no reshape or generic view operation, forwards read completion and close to the existing owner, and releases that owner when dropped. Borrowed MLX arrays remain subject to the package's read-only scope contract. This is not a Swift type-system guarantee against a malicious internal callback that mutates or exports an alias.

Prediction no longer takes a separate column-name argument. It checks the adapter's ordered names against training names where those exist and always checks column count. Models initialized from coefficients alone have no training schema and continue to use positional matching. Parameter snapshots are still captured before awaiting the input actor.

Direct construction is the default. The staged-reference mode preserves the earlier Float-array construction as an explicit benchmark control. Both modes validate missing and nonfinite Double input. Conversion to Float32 follows the existing behavior, including overflow from finite Double values. The adapter does not claim every converted value is finite.

## Verification

All 224 focused Release tests passed, with zero failures or skips. Tests cover real reordered input batches, positional width mismatch, unfitted and closed models, cancelled and concurrent predictions, refitting, mutation of the source after packing, invalid input, repeated close and release on drop. Both packing modes exercise snapshot and release checks. The existing generic storage tests continue to cover views, queued admission and completion ownership.

Behavior review and standards review found no actionable issues. All retained-prediction callers in this trial use the typed adapter; none supplies names independently.

The full SwiftSci suite and sanitizers were not rerun. This package-only experiment has not been integrated into public callers or declared production-ready.

## Workflow comparison

The comparison retains the previous protocol. Fit StandardScaler and CPU ordinary least squares on 512 training rows with 64 features, then score independent held-out inputs with training-only preprocessing. Use one or sixteen predictions for 64 or 65,536 rows. Keep all returned Double arrays alive through the measured memory snapshot.

Times include held-out transformation, input preparation and completed predictions. They exclude fixture creation, fitting, full validation, measurement overhead and cleanup. Five fresh serial workers per mode and case produce 60 samples, with rotating mode order, memory-pressure checks and per-worker timeouts. The budget estimates remain unchanged.

| Rows | Predictions | Mode | Preparation ms | Workflow ms | Workflow range ms | Peak RSS MiB |
| ---: | ---: | --- | ---: | ---: | --- | ---: |
| 64 | 1 | Scoped | 0.021 | 0.784 | 0.710 to 1.168 | 24.83 |
| 64 | 1 | Staged retained | 0.465 | 1.184 | 1.086 to 1.202 | 25.25 |
| 64 | 1 | Direct retained | 0.480 | 1.097 | 1.006 to 1.155 | 25.11 |
| 64 | 16 | Scoped | 0.021 | 11.262 | 8.510 to 14.033 | 24.86 |
| 64 | 16 | Staged retained | 0.499 | 7.377 | 4.891 to 8.028 | 25.27 |
| 64 | 16 | Direct retained | 0.631 | 9.069 | 4.600 to 10.335 | 25.22 |
| 65,536 | 1 | Scoped | 10.178 | 23.655 | 22.985 to 26.920 | 107.94 |
| 65,536 | 1 | Staged retained | 31.191 | 32.467 | 30.965 to 33.505 | 148.31 |
| 65,536 | 1 | Direct retained | 21.981 | 23.337 | 22.102 to 24.467 | 108.55 |
| 65,536 | 16 | Scoped | 10.363 | 213.465 | 209.863 to 226.530 | 116.02 |
| 65,536 | 16 | Staged retained | 31.649 | 40.515 | 38.413 to 58.489 | 153.86 |
| 65,536 | 16 | Direct retained | 21.891 | 30.320 | 29.325 to 32.891 | 116.48 |

For the large input and sixteen predictions, direct retention took 30.320 ms versus 213.465 ms for scoped prediction, a 7.04-fold ratio. Median peak RSS was 116.48 MiB versus 116.02 MiB. The staged control took 40.515 ms and peaked at 153.86 MiB. These results preserve the earlier repeated-prediction benefit after schema ownership is added. They do not isolate the adapter's overhead from between-run variation or establish a universal speedup.

All 60 workers passed the analytic oracle with maximum absolute error `4.76837158203125e-7`, below the fixed `1e-4` bound. Full prediction and fitted-parameter hashes matched across modes and repetitions. Every worker returned its reservations and MLX active bytes to zero after owner cleanup; explicit cache clearing returned cache bytes to zero.

Process RSS includes caller-owned prepared batches and returned predictions. MLX active bytes overlap imported external buffer storage. Neither these snapshots nor budget estimates imply a cap on all process memory or complete reclamation of resident pages.

## Evidence and remaining boundary

The test-build executable was used for measurement. Coverage was disabled and checked in the binary. Saved build settings request safe Metal math, precise FP32 functions and fast math disabled. Hardware was Apple M4 Max with 128 GiB unified memory and macOS 27.0 build 26A428. The arm64 macOS 14 deployment target does not constitute testing on a macOS 14 runtime. MLX remains pinned to `4657976edcdd2c60642424985d474b45ddddb390`.

Binary SHA-256: `40cc49cff74b1206a58b63ad61a7043ab5365e7c02a961e7af0efd481fec63ff`.

Logs, the build command and the test bundle are under `~/local-ai/spl/swiftsci/retained-gpu-schema-20261007/`. Replay instructions are in `Benchmarks/RetainedGPUTrial/README.md` on the implementation branch. Archived evidence includes the [summary](../archive/2026-10-07/retained-gpu-schema/summary.json), [samples](../archive/2026-10-07/retained-gpu-schema/samples.json), and [fingerprints](../archive/2026-10-07/retained-gpu-schema/provenance.json).

The caller still reserves prediction scratch and returned outputs separately. The next integration decision is an explicit reusable prediction session that ties this prepared input to that work budget and a caller-controlled lifetime. Retention should remain opt-in until its public contract and broader validation are complete. Small single-call workloads do not justify automatic retention.
