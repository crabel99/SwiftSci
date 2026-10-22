# Explicit numeric CSV decoding

The candidate adds direct optional Int64 and Double decoding for explicit schemas. Inference keeps its classified result and its existing parsing contract. This is a focused continuation of the [validation-mode experiment](../2026-10-21-csv-validation-modes/README.md).

The implementation is `5375f261c28c5cb1ee94f6c0892ba6d830e4312a` on local branch `codex/csv-numeric-decode`, based on `a5856aa40f8de2bbcc3653976419202a41222190`. The original reader control remains `dba26e1562503e1594194250d914327830d8f58d`. The change adds 18 lines in `Sources/SwiftDataFrame/IO/CSVColumnConversion.swift` and changes no other production file. Nothing is pushed.

## A smaller decoding contract for explicit schemas

An explicit schema maps missing and invalid fields to nil. Inference needs to distinguish missing from invalid because invalid tokens reject a candidate type. The parent chooses that contract once per batch but its numeric decoders still produce a classified result before converting it to an optional.

The new numeric methods return the parser's optional directly. They preserve the exact null-check order, byte parsers, and String fallback. They add no cache, worker pool, allocation policy, public API, or deployment requirement. Native optional column storage, scheduling, and classified inference remain unchanged.

Existing tests cover numeric-looking null tokens, Unicode null equivalence, infinity and NaN tokens, exact large integers, decimal rounding, quotes, ragged rows, and missing values. Both independent [code reviews](reviews.md) found no actionable defects. Reviews check source contracts. The executed validations below check behavior on this head.

## Red reproduction and reduction

The retained reproduction exits with failure because the parent uses more CPU than the original on wider explicit-schema Beijing input and inferred two-column numeric input. Its initial CPU ratios are 1.176 and 1.203. This is a performance regression reproduction, not a correctness failure.

Reducing real Beijing data to individual columns distinguishes the costs. The larger Double-column stream uses about 10% more CPU than the original, while integer and String controls are close. The larger Double eager read uses about 12% more CPU. The complete records retain the smaller inputs too.

The investigation compares three hypotheses: repeated scheduling cost, mutation through a heap-owned builder, and unnecessary classified results for explicit numeric fields. Each first-round trial changes one factor. A second round compares the direct decoder against shared-adapter inlining and a combined local-builder and inlining trial. Each pilot runs 192 validated workers in balanced orders, using six cases and four implementations. The pilots are diagnostic evidence, separate from final acceptance measurements.

Serial scheduling saves about 22% of CPU work on the wider input but approximately doubles elapsed time. It remains a measured tradeoff, with no silent default change. Moving the builder into a local variable does not consistently help ordinary inputs. Inlining the shared adapter does not recover the direct numeric decoder's gain. The final change therefore keeps the two small numeric methods and adds none of the trial scheduling or ownership machinery.

Those comparisons locate a useful implementation change. They do not prove a specific cache, false-sharing, or compiler mechanism. No hardware-counter evidence was collected.

## Eager resource comparison

| Input and mode | Original CPU ms | Parent CPU ms | New CPU ms | CPU vs parent | CPU vs original | Peak RSS MiB, original → new | Elapsed ms, original → parent → new |
|---|---:|---:|---:|---:|---:|---:|---:|
| bike-day known | 0.887 | 0.737 | 0.716 | -2.9% | -19.3% | 7.81 → 7.72 | 0.441 → 0.520 → 0.508 |
| bike-hour known | 7.513 | 5.318 | 5.357 | +0.7% | -28.7% | 17.77 → 15.78 | 1.447 → 2.050 → 2.071 |
| unique-shuffled known | 7.728 | 6.394 | 6.423 | +0.5% | -16.9% | 15.83 → 12.36 | 4.967 → 5.637 → 5.743 |
| Aotizhongxin known | 11.395 | 13.675 | 13.024 | -4.8% | +14.3% | 25.77 → 23.10 | 4.558 → 5.634 → 5.641 |
| energy known | 447.594 | 395.236 | 360.755 | -8.7% | -19.4% | 720.21 → 420.88 | 100.419 → 187.757 → 188.133 |
| energy infer | 446.620 | 401.103 | 398.818 | -0.6% | -10.7% | 720.22 → 422.37 | 100.631 → 190.743 → 191.028 |
| energy-date-full known | 461.394 | 416.070 | 376.155 | -9.6% | -18.5% | 720.20 → 421.34 | 95.908 → 181.481 → 183.524 |
| late-bool infer | 6.452 | 6.889 | 6.849 | -0.6% | +6.2% | 10.56 → 9.72 | 6.482 → 6.913 → 6.874 |
| late-text infer | 14.147 | 8.927 | 8.985 | +0.6% | -36.5% | 18.93 → 16.88 | 13.046 → 8.974 → 9.007 |

## Streaming resource comparison

| Input and mode | Original CPU ms | Parent CPU ms | New CPU ms | CPU vs parent | CPU vs original | Peak RSS MiB, original → new | Elapsed ms, original → parent → new |
|---|---:|---:|---:|---:|---:|---:|---:|
| date-100000-1 known | 4.494 | 4.446 | 4.389 | -1.3% | -2.3% | 8.52 → 8.58 | 4.525 → 4.469 → 4.460 |
| bike-hour known | 5.245 | 5.567 | 5.231 | -6.0% | -0.3% | 12.77 → 12.88 | 1.969 → 2.023 → 2.097 |
| unique-shuffled known | 5.560 | 5.543 | 5.465 | -1.4% | -1.7% | 9.36 → 9.45 | 4.905 → 4.897 → 4.823 |
| Aotizhongxin known | 12.191 | 12.982 | 12.230 | -5.8% | +0.3% | 15.52 → 15.75 | 4.498 → 4.613 → 4.564 |
| energy known | 334.353 | 371.749 | 320.719 | -13.7% | -4.1% | 138.49 → 138.12 | 151.993 → 150.131 → 151.521 |
| energy-date-full known | 344.026 | 391.123 | 333.005 | -14.9% | -3.2% | 138.86 → 138.15 | 146.699 → 144.598 → 143.500 |

## Null-heavy resource comparison

| Null fraction and mode | Original CPU ms | Parent CPU ms | New CPU ms | CPU vs parent |
|---|---:|---:|---:|---:|
| 0% infer | 2.546 | 2.962 | 3.003 | +1.4% |
| 50% infer | 3.204 | 3.466 | 3.631 | +4.8% |
| 50% known | 2.808 | 3.261 | 3.110 | -4.7% |
| 90% infer | 3.696 | 3.705 | 3.590 | -3.1% |
| 90% known | 2.977 | 3.454 | 3.257 | -5.7% |

The synthetic null controls contain 100000 rows and native Int64 and Double columns. Missing positions follow deterministic 0%, 50%, and 90% distributions. They cover inference and explicit schemas without changing input bytes, native output types, values, null positions, or output order between implementations.

The numeric power read uses 8.7% less CPU than the parent, and the explicit-date power read uses 9.6% less. Peak eager RSS remains about 421 MiB versus about 720 MiB originally, a reduction of about 41%. Large streaming reads use 13.7% and 14.9% less CPU than the parent. Their CPU costs are now about 4.1% and 3.2% below the original reader. Wall time remains approximately level with the parent on those reads. The eager path still has an elapsed-time cost relative to the original, shown in the tables.

No final case exceeds the 10% CPU-review threshold versus the parent. This does not mean every case improves. Small cases vary, and 50%-missing inferred numeric input uses 4.8% more CPU in this run even though its classified decoder is unchanged.

Four comparisons still exceed that threshold versus the original. Wider eager Beijing input uses 14.3% more CPU. The two-column numeric controls use 17.9% more with no nulls and inference, 13.3% more with 50% nulls and inference, and 10.7% more with 50% nulls and an explicit schema. The focused commit helps, but the broader reader is not ready for default promotion. These remaining results point to batch coordination and inferred conversion costs as the next investigation. They do not justify changing the inference contract.

## Validation and limits

All 382 SwiftDataFrame tests pass in Release, Debug, and Release with Address Sanitizer, with no failures or skips. Source hashes in each test receipt match this candidate. The raw-byte parser differential still matches all 30720 fixtures. No scanner or byte-parser code changes in this commit.

The production-default `tabular-smoke` suite passes all 190 SwiftSci and pandas samples, and its certificate audit passes. That establishes the declared tabular contracts. It does not certify every numerical algorithm or the full MLX-dependent library.

Final resource evidence contains 162 eager workers, 108 streaming workers, and 90 null-control workers, plus 18 streaming correctness preflights. Each comparison uses six fresh-process rounds with balanced implementation order. The controllers check all selected values and nulls. A separate parity guard rejects differences in actual native output types and column metadata between eager implementations. Streaming checks native types and all per-column value hashes in an untimed repeat.

The measurements use the same input bytes, selected columns, row order, and schema contract within each comparison. Input pages are warm, AC power is required, and CPU parallelism remains native. This task runs no builds or tests alongside accepted resource measurements. No outliers are trimmed. Whole-operation CPU is process user plus system time, and wall time is reported separately. Peak and held RSS include resident mappings and allocator behavior. These are not energy readings or allocation counts.

## Reproduction and evidence ownership

The plans and raw workers accompany the tables. Build receipts preserve commands, source hashes, binary hashes, and dependency identities. Raw standard-suite artifacts are in `standardized-artifacts.tar.gz`. Input reductions and trial sources are in `diagnostic-inputs-and-trials.tar.gz`. The implementation diff is in `source-change.patch.gz`. `artifact-sha256.json` covers every retained artifact except itself.

The scripts refer to frozen local binaries and input paths. Restore the corresponding sources and dependencies before rebuilding. The parent source is restored at `/private/tmp/swiftsci-csv-validation-modes-control-20261021`. The original source remains at `/private/tmp/swiftsci-csv-scoped-simd-20261021`. Use a fresh output directory for another run. Controllers refuse to overwrite final outputs.

This report belongs to `codex/engineering-notes` and must stay out of implementation PRs. The focused numeric commit is local. Keep any remaining resource regressions visible before considering the broader bounded CSV reader for default use.
