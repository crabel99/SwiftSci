# Prepared GPU packing default qualification

Date: 2026-10-07

## Decision

Use 16-by-16 blocked packing as the shared prepared-input default on the local memory trial branch. Keep row-wise packing and 32- and 64-element tiles as explicit comparison controls. The results support a common bulk conversion boundary for scoped and retained inputs. They do not establish a universal tile optimum or a size threshold for choosing between the two ownership lifetimes.

Tile qualification commit: `41c5bd585a96f38a0fc4d074bb30d50d0cdad125`.
Default implementation commit: `a4449211543d089a4c37bc8476f9d525a223190e`.
Branch: `codex/retained-memory-accounting-trial`. Neither commit was pushed. This report and raw evidence belong to `codex/engineering-notes` and must remain outside implementation PRs.

## Structure

`PreparedFloatPacking.defaultStrategy` owns the default. Public prepared regression prediction, scoped batch import, generic retained batch construction and schema-owning retained construction all use it. Review caught a literal default in the typed retained factory; the committed implementation carries the strategy as an associated value and derives its default from the central policy.

The blocked loop reads short contiguous runs from each column and writes the corresponding row-major positions. It uses no staging array. Float conversion, validation, feature-name checks, CPU behavior and the generic row-array path retain their previous contracts. Finite Double inputs can still overflow Float32; this change does not tighten the conversion policy.

Allocation, padding, MLX import, synchronization and reservation ownership remain separate from conversion. Changing the packing default neither adds a pool nor changes lifetime selection. Both lifetimes use the same packing code, so their comparison is less affected by different conversion implementations.

## Evidence and selection

The first experiment compared row-wise, 16-, 32- and 64-element tiles across widths 1, 8, 17, 32, 33, 63, 64, 65, 127 and 128. Each width used 65, 4,096 and 65,536 rows, one and sixteen predictions, and three rotated rounds. All 720 fresh-process workers passed. Tile winners varied by shape. Sixteen-element tiles performed well across the wider cases and became the candidate for actual-default qualification.

The final comparison used widths 1, 8, 17, 64, 65 and 128; the same three row counts and two prediction counts; and five rotated rounds. Its five modes were explicit scoped row-wise, actual public default, scoped 32-tile control, explicit retained row-wise and actual retained default. All 900 fresh-process workers passed.

Three small cases had noisy medians, so widths 1, 17 and 128 at 65 rows and sixteen predictions were repeated with twenty rounds and the same five modes. All 300 workers passed. Several timing differences changed direction between runs, with overlapping ranges. These data do not establish a consistent small-input regression or gain. This is a qualification of the wider-input benefit with small-case uncertainty, not a claim that every shape improves.

## Validation

The final Release integration run passed 839 tests, with zero failures and two skips. Xcode reports 1,028 successful test executions when parameterized cases are included. The nine selected targets were SwiftDataFrame, SwiftStats, SwiftPreprocessing, SwiftML, SwiftCluster, SwiftOptimize, SwiftExplain, SwiftNLP and SwiftSciBenchmarkSupport.

The two skipped tests require `SWIFTSCI_LLAMA_TOKENIZER_JSON`, which was not provided. An existing MNIST test also returns early when a developer-specific NPZ file is absent and is recorded as passed by XCTest. That pass does not establish MNIST fixture coverage. These gaps are unrelated to the changed packing paths but limit the integration claim. This was not the full library suite or a sanitizer run.

Packing tests check exact Float bit patterns, signed zero, underflow, overflow, irregular widths, partial tiles, page edges and destination guard elements. Prediction tests cover explicit row-wise and all blocked controls. Existing schema, ownership and cleanup tests ran against the selected default.

All 1,200 final comparison workers matched full prediction and learned-parameter hashes across modes and met the fixed `1e-4` analytic-oracle bound. Maximum observed oracle error was `9.5367431640625e-07`. Each worker reported zero reservation bytes after close, zero active MLX bytes after close, and zero cache bytes after explicit clearing. These checks do not prove complete RSS reclamation or absence of every possible leak.

## Measurement contract

Every worker fits a scaler and CPU ordinary least squares model on 512 generated training rows, then uses independent held-out rows without refitting. All modes use the same GPU prediction kernel. Total workflow timing includes held-out transformation, input preparation and completed predictions. Fixture generation, training, warmup, verification, snapshot overhead and cleanup are outside timing. Every returned Double prediction array stays alive through the measured snapshot.

The driver runs one worker at a time, rotates mode order, checks memory pressure before launch and gives each worker a 90-second timeout. No test or other benchmark launched by this task ran concurrently. Other activity on the workstation was not controlled. The records retain ranges and individual samples.

The explicit scoped row-wise mode calls the package strategy overload. The public-default mode calls the public API without an override. The retained-default mode invokes the typed factory without an override. Thus the default modes test the paths users would actually select, including their call boundaries.

## Large-input timing

All cases below have 65,536 held-out rows. Times are median milliseconds. SR is scoped row-wise; SD is the actual scoped default; S32 is the scoped 32-tile control; RR is retained row-wise; RD is the actual retained default.

| Columns | Predictions | SR ms | SD ms | S32 ms | RR ms | RD ms |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 1 | 1.699 | 1.670 | 1.617 | 2.073 | 1.988 |
| 1 | 16 | 12.084 | 10.655 | 10.051 | 8.721 | 7.771 |
| 8 | 1 | 2.800 | 2.757 | 2.804 | 3.235 | 3.252 |
| 8 | 16 | 19.429 | 18.648 | 18.310 | 8.491 | 9.229 |
| 17 | 1 | 5.281 | 4.531 | 4.647 | 5.983 | 4.913 |
| 17 | 16 | 40.485 | 30.181 | 29.794 | 12.789 | 10.673 |
| 64 | 1 | 20.393 | 14.864 | 15.638 | 20.701 | 15.363 |
| 64 | 16 | 165.950 | 85.968 | 96.213 | 26.679 | 21.496 |
| 65 | 1 | 18.878 | 13.871 | 14.370 | 20.122 | 14.948 |
| 65 | 16 | 168.937 | 90.223 | 91.763 | 27.816 | 20.291 |
| 128 | 1 | 58.117 | 33.878 | 35.439 | 57.741 | 34.883 |
| 128 | 16 | 498.185 | 179.635 | 200.801 | 60.186 | 40.829 |

At 64 columns and sixteen predictions, the scoped default reduced median time from 165.950 to 85.968 ms, about 1.93 times faster. Retained input reduced 26.679 to 21.496 ms, about 1.24 times faster. At 128 columns, the corresponding changes were 498.185 to 179.635 ms and 60.186 to 40.829 ms, about 2.77 and 1.47 times faster.

These are within-run controls using the same final binary. Earlier reports used different binaries and measurement sessions; their numbers are historical evidence, not interleaved before/after controls.

## Memory

Median process high-water memory before validation, in MiB, for the same cases:

| Columns | Predictions | SR MiB | SD MiB | S32 MiB | RR MiB | RD MiB |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 1 | 26.00 | 26.02 | 25.98 | 26.33 | 26.31 |
| 1 | 16 | 33.84 | 33.89 | 33.83 | 34.14 | 34.17 |
| 8 | 1 | 35.09 | 35.09 | 35.08 | 35.45 | 35.44 |
| 8 | 16 | 42.92 | 42.92 | 42.94 | 43.28 | 43.22 |
| 17 | 1 | 46.94 | 46.94 | 46.97 | 47.36 | 47.30 |
| 17 | 16 | 54.80 | 54.81 | 54.81 | 55.09 | 55.09 |
| 64 | 1 | 107.88 | 107.88 | 107.86 | 108.20 | 108.16 |
| 64 | 16 | 115.69 | 115.69 | 115.70 | 115.97 | 115.95 |
| 65 | 1 | 109.41 | 109.39 | 109.42 | 109.66 | 109.64 |
| 65 | 16 | 117.25 | 117.22 | 117.23 | 117.45 | 117.53 |
| 128 | 1 | 190.92 | 190.91 | 190.91 | 191.25 | 191.33 |
| 128 | 16 | 198.72 | 198.78 | 198.70 | 199.03 | 199.03 |

The packing change did not materially alter peak RSS within each lifetime in these samples. Retained storage and MLX active memory overlap while the shared import exists and must not be added together. Budget reservations are admission estimates, not a process-memory cap. Caller-owned prepared columns and returned outputs remain separate allocations.

## Small-input timing

Ratios below divide explicit row-wise median time by default median time. Values above one favor the default. Near-one ratios are inconclusive, and the repeated small-case results below show why single medians should not drive routing policy.

| Columns | Rows | Predictions | Scoped ratio | Retained ratio |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 65 | 1 | 1.02 | 1.05 |
| 1 | 65 | 16 | 0.74 | 1.38 |
| 1 | 4096 | 1 | 0.97 | 0.94 |
| 1 | 4096 | 16 | 1.10 | 1.23 |
| 8 | 65 | 1 | 1.06 | 1.02 |
| 8 | 65 | 16 | 1.07 | 1.21 |
| 8 | 4096 | 1 | 0.97 | 0.98 |
| 8 | 4096 | 16 | 0.96 | 1.18 |
| 17 | 65 | 1 | 1.03 | 0.95 |
| 17 | 65 | 16 | 0.76 | 1.07 |
| 17 | 4096 | 1 | 1.03 | 1.06 |
| 17 | 4096 | 16 | 0.95 | 0.95 |
| 64 | 65 | 1 | 1.01 | 1.13 |
| 64 | 65 | 16 | 1.05 | 1.41 |
| 64 | 4096 | 1 | 1.22 | 1.08 |
| 64 | 4096 | 16 | 1.29 | 1.12 |
| 65 | 65 | 1 | 0.98 | 1.01 |
| 65 | 65 | 16 | 0.88 | 1.21 |
| 65 | 4096 | 1 | 1.13 | 1.11 |
| 65 | 4096 | 16 | 1.44 | 0.88 |
| 128 | 65 | 1 | 1.03 | 0.97 |
| 128 | 65 | 16 | 1.16 | 0.85 |
| 128 | 4096 | 1 | 1.40 | 1.25 |
| 128 | 4096 | 16 | 1.73 | 1.39 |

Independent twenty-round repeat at 65 rows and sixteen predictions, in milliseconds:

| Columns | Mode | Median | Minimum | Maximum |
| ---: | --- | ---: | ---: | ---: |
| 1 | workflow-scoped | 7.316 | 4.689 | 15.008 |
| 1 | workflow-default | 7.438 | 3.987 | 21.841 |
| 1 | workflow-scoped-blocked | 6.647 | 4.314 | 16.294 |
| 1 | workflow-direct | 4.574 | 3.609 | 10.533 |
| 1 | workflow-retained-default | 5.472 | 3.422 | 9.000 |
| 17 | workflow-scoped | 9.172 | 5.447 | 16.753 |
| 17 | workflow-default | 7.834 | 4.826 | 23.412 |
| 17 | workflow-scoped-blocked | 7.980 | 5.477 | 12.914 |
| 17 | workflow-direct | 5.245 | 3.585 | 9.330 |
| 17 | workflow-retained-default | 5.628 | 3.905 | 9.007 |
| 128 | workflow-scoped | 7.415 | 4.308 | 11.119 |
| 128 | workflow-default | 7.244 | 5.400 | 11.669 |
| 128 | workflow-scoped-blocked | 8.188 | 4.210 | 13.140 |
| 128 | workflow-direct | 4.650 | 3.344 | 10.221 |
| 128 | workflow-retained-default | 4.772 | 3.655 | 9.427 |

## Limits and next question

This trial measures a generated, training-only preprocessing and linear-regression prediction workflow. It covers multiple widths and reuse counts but not all callers, distributions, models or Apple-silicon generations. It cannot establish that 16-by-16 tiles fit every cache hierarchy best. Narrow inputs show little dependable benefit; the strongest evidence concerns larger, wider inputs.

The next architectural question is import and padding policy. Scoped import retains its copy fallback for unaligned extents; retained construction pads storage and verifies sharing. Any proposed change should be measured independently while keeping the same packer, numerical kernel and output lifetimes. No automatic CPU/GPU or scoped/retained size threshold is justified by this experiment.

Hardware was Apple M4 Max with 128 GiB unified memory, running macOS 27.0 build 26A428. The Release arm64 binary has a macOS 14 deployment target; no macOS 14 runtime was tested. The MLX Swift fork remains pinned to `4657976edcdd2c60642424985d474b45ddddb390`. The saved build command selects safe Metal math and precise FP32 functions. The binary guard rejected coverage instrumentation before measurements.

Final binary SHA-256: `664d814f8b8e8c55d068a9e237128b54d5967f05ea4bbc379479a2ef10346ad3`.

Local commands, logs and test bundles are under `~/local-ai/spl/swiftsci/gpu-packing-default-20261007/`. The archive retains all summaries, all 1,920 measured worker records, source and binary fingerprints, and compact test outcomes. Replay options are documented in the implementation branch's `Benchmarks/RetainedGPUTrial/README.md`.

- [Tile qualification, 64 columns](../archive/2026-10-07/gpu-packing-default/tiles-64/summary.json)
- [Default comparison, 64 columns](../archive/2026-10-07/gpu-packing-default/default-64/summary.json)
- [Default comparison, 128 columns](../archive/2026-10-07/gpu-packing-default/default-128/summary.json)
- [Small-input repeat, 17 columns](../archive/2026-10-07/gpu-packing-default/small-repeat-17/summary.json)
- [Test outcomes and known fixture gaps](../archive/2026-10-07/gpu-packing-default/validation.json)
