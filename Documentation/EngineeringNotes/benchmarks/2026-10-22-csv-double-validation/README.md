# Concrete Double validation in the CSV reader

The candidate keeps the Double decoder concrete inside the inferred-value loop. It uses the existing parser, null matcher, typed builder, record views, and fallback rules. The change adds no retained storage or scheduling policy.

The implementation is `c8c56d1eb25f51afa27c452c6f656cb79dec73a6` on local branch `codex/csv-double-validation`, based on `277d1792d34e280a50744bd7419848d1c16b8655`. That parent is the [count-only scanner experiment](../2026-10-22-csv-count-row-events/README.md). The original control remains `dba26e1562503e1594194250d914327830d8f58d`. One private source file changes, with 43 added lines and four removed. Nothing is pushed.

## A decoder boundary inside the value loop

The frozen reproduction fails on 100000-row numeric inference, with about 14.6% more process CPU than the original reader. The wider explicit-schema Beijing input is below the review threshold in this run. Reducing the numeric input to one column isolates inferred Double conversion. That column uses about 21% more CPU than the original, while its explicit-schema control is about 4% higher. The one-batch control is close to the original.

The initial trials test direct writes into the typed builder, a borrowed record view for type planning, and larger row batches. Direct writes and borrowed planning do not consistently improve the regression. Larger batches help but increase temporary memory, so they remain a separate policy experiment.

Matched native sampling and emitted Apple Silicon code reveal an indirect protocol decoder call inside the parent's inferred Double loop. The call passes decoder metadata and its witness table for each field. The original loop calls the byte parser directly. Sampling identifies the active path. It does not establish CPU ratios from sample counts.

Inlining the outer append method or inner shared loop does not recover the gain. Moving the loop into the decoder protocol's default batch method also leaves the overhead. A concrete Double loop removes it and improves both null-free and null-heavy input. The direct-builder trial did not recover the gain. The emitted-code diagnosis points to the decoder boundary rather than result transport alone. The final pinned binary replaces the indirect call with a direct byte-parser call. `verify-dispatch.py` checks the retained instruction excerpts and binary identities.

## Keep the narrow implementation

The finalist comparison includes the initial concrete diagnostic, a smaller concrete inferred-only loop, and a shared callback-loop design. All preserve output contracts. The shared design recovers much of the numeric gain but adds CPU cost to Date and explicit-schema controls. The candidate therefore keeps the narrow inferred-Double loop. Explicit Double schemas delegate to the existing path. Other decoder types retain their existing loops.

Rejection cleanup is shared. An invalid field still records its original absolute source offset and discards the partial typed builder. The small concrete loop retains the same record lookup, nil handling, classified decoder, and early rejection as the generic loop. It duplicates no numeric parser or null-matching implementation. The [independent reviews](reviews.md) assess this limited loop duplication against the compiler evidence and rejected alternatives.

This is a compiler-boundary optimization, not a change chosen for a particular input size or dataset. It does not add a cache, index, padding, public option, deployment requirement, or worker pool. Batch size, exact output capacity, native optional storage, and joined worker ownership remain unchanged.

## Eager resource comparison

| Input and mode | Original CPU ms | Parent CPU ms | New CPU ms | CPU vs parent | CPU vs original | Peak RSS MiB, original → new | Elapsed ms, original → parent → new |
|---|---:|---:|---:|---:|---:|---:|---:|
| bike-day known | 1.051 | 0.697 | 0.697 | +0.0% | -33.7% | 7.81 → 7.71 | 0.498 → 0.416 → 0.390 |
| bike-hour known | 8.184 | 5.536 | 5.530 | -0.1% | -32.4% | 17.71 → 15.75 | 1.598 → 2.164 → 2.077 |
| unique-shuffled known | 7.673 | 6.277 | 6.301 | +0.4% | -17.9% | 15.83 → 12.31 | 4.878 → 5.568 → 5.574 |
| Aotizhongxin known | 12.531 | 12.927 | 12.822 | -0.8% | +2.3% | 25.78 → 23.07 | 4.716 → 5.238 → 5.292 |
| energy known | 464.742 | 359.810 | 356.256 | -1.0% | -23.3% | 720.21 → 422.32 | 102.031 → 178.009 → 178.227 |
| energy infer | 449.127 | 388.939 | 361.673 | -7.0% | -19.5% | 720.25 → 421.58 | 102.943 → 173.601 → 178.658 |
| energy-date-full known | 466.495 | 372.690 | 367.097 | -1.5% | -21.3% | 720.22 → 421.58 | 98.005 → 169.872 → 171.043 |
| late-bool infer | 7.367 | 7.508 | 7.442 | -0.9% | +1.0% | 10.60 → 9.98 | 7.370 → 7.512 → 7.448 |
| late-text infer | 14.537 | 9.238 | 9.068 | -1.8% | -37.6% | 19.00 → 16.86 | 13.300 → 9.254 → 9.076 |

## Streaming resource comparison

| Input and mode | Original CPU ms | Parent CPU ms | New CPU ms | CPU vs parent | CPU vs original | Peak RSS MiB, original → new | Elapsed ms, original → parent → new |
|---|---:|---:|---:|---:|---:|---:|---:|
| date-100000-1 known | 4.541 | 4.511 | 4.676 | +3.7% | +3.0% | 8.51 → 8.58 | 4.583 → 4.557 → 4.702 |
| bike-hour known | 5.470 | 5.516 | 5.416 | -1.8% | -1.0% | 12.85 → 13.06 | 2.068 → 2.050 → 2.045 |
| unique-shuffled known | 5.639 | 5.614 | 5.769 | +2.8% | +2.3% | 9.36 → 9.48 | 4.990 → 4.986 → 5.116 |
| Aotizhongxin known | 12.501 | 12.457 | 12.483 | +0.2% | -0.1% | 15.70 → 15.71 | 4.738 → 4.615 → 4.641 |
| energy known | 334.891 | 330.834 | 325.467 | -1.6% | -2.8% | 138.82 → 138.88 | 154.101 → 155.414 → 155.466 |
| energy-date-full known | 349.117 | 342.641 | 341.308 | -0.4% | -2.2% | 138.78 → 138.96 | 150.941 → 149.355 → 150.140 |

## Null-heavy resource comparison

| Null fraction and mode | Original CPU ms | Parent CPU ms | New CPU ms | CPU vs parent |
|---|---:|---:|---:|---:|
| 0% infer | 2.595 | 2.913 | 2.688 | -7.7% |
| 50% infer | 3.434 | 3.601 | 3.170 | -12.0% |
| 50% known | 2.958 | 3.078 | 3.136 | +1.9% |
| 90% infer | 3.829 | 3.498 | 3.287 | -6.0% |
| 90% known | 3.085 | 3.280 | 3.387 | +3.2% |

The final candidate reduces process CPU by 7.7%, 12.0%, and 6.0% on the 0%, 50%, and 90% inferred numeric controls. Their elapsed times improve by about 10%, 16%, and 9%. The large inferred power read uses 7.0% less CPU, while its elapsed median is 2.9% higher. That CPU-versus-latency result is retained explicitly. Peak eager RSS remains about 421 to 422 MiB versus about 720 MiB originally.

No final case exceeds the 10% CPU-review threshold against the parent. Some controls are slightly worse. Explicit null-heavy CPU medians increase by 1.9% and 3.3%, and the Date-only stream increases by 3.7%. These measured costs are retained rather than attributed to an unproven mechanism.

In the full final comparison, no case exceeds the CPU-review threshold against the original. The previously failing null-free inferred numeric case is now 3.6% above it. A separate rerun of the original two-case reproduction confirms numeric inference at 3.4% above the original, so that subcase is green.

The supplemental two-case command still exits with failure because wider explicit-schema Beijing input measures 10.2% above the original. The same input is 2.3% above the original in the full final run. Both records are retained. The candidate is 0.8% below its parent on this case in that full run, and it delegates explicit Double schemas to the existing path. The broader reader still needs work on the wider-input cost and its variability. A passing final table does not erase the supplemental red result.

Keep the focused Double-validation commit. Do not treat it as clearance to promote the entire bounded reader. The next investigation should examine a bounded, explicit batch-memory policy and the wider-file coordination cost. Larger batches remain an unpromoted trial because their memory cost must remain a caller-visible tradeoff.

## Validation and measurement limits

All 383 SwiftDataFrame tests pass in Release, Debug, and Release with Address Sanitizer, without failures or skips. The accepted receipts pin source hashes to this candidate. Existing tests cover exact large integers, decimal rounding, numeric-looking and Unicode nulls, non-finite values, ragged records, whole-column validation, late candidate rejection, original-token fallback, and batch boundaries. No tests change in this commit.

The public byte-parser differential still matches all 30720 raw-byte fixtures. The standard production-default `tabular-smoke` suite passes all 190 SwiftSci and pandas samples, and its certificate audit passes. These results validate the declared tabular contracts. They do not certify every numerical algorithm or the full MLX-dependent library.

Final resource evidence contains 162 eager workers, 108 streaming workers, and 90 null-control workers, plus 18 streaming correctness preflights. The input bytes, selected columns, native types, values, null positions, and output order match within each comparison. Native output metadata is checked across eager implementations. Streaming checks every per-column value hash in an untimed repeat.

The three implementations run in six balanced-order rounds with fresh processes and warm input pages. AC power is required, with native CPU parallelism. This task runs no builds, tests, or profiler sessions alongside accepted resource measurements. No outliers are trimmed. CPU is process user plus system time. Elapsed time is separate. Peak memory is captured before validation. RSS includes resident mappings and allocator behavior. These are not energy, allocation-count, or cache-efficiency measurements.

## Retained experiments and reproduction

The first, inlining, dispatch, and finalist pilots each retain 192 validated workers. A separate control pilot retains 144 workers for Date, String, explicit-schema, null-heavy, and late-fallback cases. These diagnostic pilots are separate from final acceptance measurements. Sources and receipts preserve every trial. None of the rejected trials appears in the implementation branch.

Raw profiles and disassemblies are compressed without changing their contents. Build receipts pin source, command, dependency, and binary identities. `standardized-artifacts.tar.gz` preserves the standard-suite records. `diagnostic-inputs-and-trials.tar.gz` preserves the input reductions and trial sources. `source-change.patch.gz` contains the focused production diff. `artifact-sha256.json` verifies retained files.

Scripts use local frozen paths and require matching restored sources before reuse. The parent source is `/private/tmp/swiftsci-csv-count-row-events-control-20261022`. The original source remains `/private/tmp/swiftsci-csv-scoped-simd-20261021`. Use a fresh output directory for another run. Final controllers refuse to overwrite prior outputs. The verification driver now rejects whitespace errors before starting a test run.

This report belongs to `codex/engineering-notes` and must stay out of implementation PRs. All changes remain local. Keep any remaining CPU, elapsed-time, and memory tradeoffs visible before promoting the broader bounded reader.
