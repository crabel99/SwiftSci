# CSV validation modes and the Date conversion regression

The local change recovers the Date conversion regression while preserving the bounded eager reader's memory savings. It does not finish the whole CSV prototype. Wider eager input and some numeric streaming cases still use more CPU than the original reader.

The candidate is `a5856aa40f8de2bbcc3653976419202a41222190` on `codex/csv-validation-modes`, based on `297ebd36ef979cf1a5dfafa3f419c052165f2d1e`. That prior prototype is the [count-only and fallback experiment](../2026-10-21-csv-cpu-discovery/README.md). The original control remains `dba26e1562503e1594194250d914327830d8f58d`. All changes remain local.

## Why two decoding contracts

An explicit schema maps both missing and invalid fields to nil. Inference must distinguish them because an invalid token rejects a candidate. The previous shared loop transported that distinction for every field, including explicit schemas.

The new loop chooses the validation contract once per batch. Inference keeps the existing classified result. Explicit schemas request an optional value. Most decoders derive that optional from their classified result. Date returns the parser's optional directly, avoiding an additional generic result tag. Neither Date parsing nor numeric arithmetic changes.

The change adds 31 lines and removes 3 in one private implementation file. It adds no public API, deployment requirement, cache, allocation policy, worker pool, or core-affinity rule. Native optional output storage and existing joined workers remain unchanged.

## Evidence and rejected trials

The frozen-binary reproduction was red for a two-column date stream and wider eager Beijing input. Reductions to one Date column retained the regression. Boundary measurements showed single-column conversion at about 5.36 ms of process CPU versus 4.06 ms originally, while framing was slightly cheaper. This ruled against framing as the primary cause of that Date regression.

Sampling showed extra `CSVDecodedValue` tag routines in the prior explicit-Date path. A matched final sample uses the same null policy and input bytes on both heads. Those routines no longer appear in its new explicit-Date samples. Sampling supports the diagnosis; the paired whole-operation measurements below establish the benefit. Sample counts are not elapsed-time ratios or energy measurements.

Forced inlining and moving the builder into a local variable did not give consistent gains. Separating the value and invalid flag into another generic result structure also did not help. Removing classified results for every decoder improved Date work but made 90%-missing inferred numeric input 18.4% more CPU-expensive in the retained retest. That trial was rejected. The final mode split keeps the classified inference path and avoids that repeated-null-classification penalty.

Two early null pilots reused an output filename. Their superseded raw records are unavailable. The optional-only alternative was rerun into a distinct retained record and reproduced the regression. The final production null comparison is retained separately. No final acceptance statement depends on the overwritten records. The retained controllers now use distinct destinations and refuse to overwrite prior measurements. Executed controller snapshots preserve the commands that produced the evidence.

## Final eager comparison

| Input and mode | Original CPU ms | Prior prototype CPU ms | New CPU ms | CPU vs prior | CPU vs original | Peak RSS MiB, original → new | Elapsed ms, original → new |
|---|---:|---:|---:|---:|---:|---:|---:|
| bike-day known | 0.920 | 0.751 | 0.714 | -5.1% | -22.5% | 7.83 → 7.73 | 0.383 → 0.408 |
| bike-hour known | 7.622 | 5.872 | 5.577 | -5.0% | -26.8% | 17.77 → 15.78 | 1.518 → 2.121 |
| unique-shuffled known | 7.456 | 7.538 | 6.352 | -15.7% | -14.8% | 15.78 → 12.31 | 4.899 → 5.663 |
| Aotizhongxin known | 12.183 | 14.127 | 13.726 | -2.8% | +12.7% | 25.70 → 23.06 | 4.772 → 5.614 |
| energy known | 445.468 | 415.732 | 405.672 | -2.4% | -8.9% | 720.20 → 422.35 | 100.501 → 195.264 |
| energy infer | 457.519 | 419.279 | 412.991 | -1.5% | -9.7% | 720.23 → 422.41 | 101.882 → 197.442 |
| energy-date-full known | 484.864 | 457.668 | 423.067 | -7.6% | -12.7% | 720.24 → 421.58 | 97.351 → 184.877 |
| late-bool infer | 6.684 | 6.577 | 6.867 | +4.4% | +2.8% | 10.56 → 9.72 | 6.708 → 6.889 |
| late-text infer | 13.911 | 8.829 | 8.836 | +0.1% | -36.5% | 18.92 → 16.86 | 12.732 → 8.853 |

## Final streaming comparison

| Input and mode | Original CPU ms | Prior prototype CPU ms | New CPU ms | CPU vs prior | CPU vs original | Peak RSS MiB, original → new | Elapsed ms, original → new |
|---|---:|---:|---:|---:|---:|---:|---:|
| date-100000-1 known | 4.617 | 5.857 | 4.413 | -24.7% | -4.4% | 8.51 → 8.55 | 4.712 → 4.433 |
| bike-hour known | 5.282 | 5.870 | 5.415 | -7.8% | +2.5% | 12.79 → 12.88 | 1.974 → 1.962 |
| unique-shuffled known | 5.614 | 6.984 | 5.559 | -20.4% | -1.0% | 9.38 → 9.44 | 4.952 → 4.914 |
| Aotizhongxin known | 12.200 | 13.012 | 12.788 | -1.7% | +4.8% | 15.63 → 15.48 | 4.613 → 4.577 |
| energy known | 327.183 | 365.957 | 375.777 | +2.7% | +14.9% | 139.06 → 138.65 | 149.302 → 151.181 |
| energy-date-full known | 346.298 | 409.714 | 391.228 | -4.5% | +13.0% | 139.08 → 139.21 | 144.859 → 144.843 |

Date-only streaming is now about 4% below the original reader's CPU work, and the two-column date stream is about level with it. The full explicit-date eager read is about 13% below the original's CPU work and retains peak RSS near 422 MiB instead of 720 MiB. Its elapsed time remains substantially higher than the original. The table keeps that cost visible.

The wider eager Beijing case remains about 13% above the original's CPU work. Power-data streaming also remains above it. No weighted average or Date-specific win clears those remaining blockers.

## Null-heavy comparison

| Null fraction and mode | Original CPU ms | Prior CPU ms | New CPU ms | New vs prior |
|---|---:|---:|---:|---:|
| 0% infer | 2.473 | 2.966 | 2.966 | +0.0% |
| 50% infer | 3.268 | 3.693 | 3.648 | -1.2% |
| 50% known | 2.829 | 3.493 | 3.342 | -4.3% |
| 90% infer | 3.667 | 3.602 | 3.598 | -0.1% |
| 90% known | 2.909 | 3.556 | 3.515 | -1.2% |

These controls contain 100000 rows with native Int64 and Double columns and deterministic 0%, 50%, and 90% null distributions. They check inferred and explicit schemas without changing selected values, types, null positions, or row order between implementations. The new implementation has no CPU regression above the 10% review limit versus its parent across the final eager, streaming, and null controls. Several inherited costs remain above the original reader.

## Validation and measurement boundaries

All 382 SwiftDataFrame tests pass in Release, Debug, and Address Sanitizer, with no failures or skips. Test-source and implementation hashes match the final head. The parser differential still matches all 30720 deterministic raw-byte fixtures. No parser source changed in this commit.

The standard production-default `tabular-smoke` run passes all 190 SwiftSci and pandas samples, and its certificate audit passes. This validates the declared tabular cases. It does not establish full numerical certification or cover every MLX-dependent module. The independent [standards and specification reviews](reviews.md) found no actionable defects.

Final resource evidence contains 162 eager workers, 108 streaming workers, and 90 null-control workers, plus 18 streaming correctness preflights. The three implementations run in six balanced-order rounds. Native types, values, null positions, and output order are checked. Validation runs outside measured CPU and elapsed intervals, with peak memory captured before validation. No builds or tests from this task run concurrently with these accepted comparisons. AC power and native CPU parallelism remain the policy. Input pages are warm, and no outliers are trimmed.

CPU is process user plus system time. RSS includes resident mappings and allocator behavior. Neither is an energy reading or an allocation count. No GPU, NPU, cache-capacity, or SRAM-efficiency conclusion follows from these CPU experiments.

## Reproduction and next step

Plans and raw worker records accompany the tables. Build receipts preserve commands, source hashes, binary hashes, and dependency identities. The raw standard suite is in `standardized-artifacts.tar.gz`. Diagnostic inputs and trial source files are in `diagnostic-inputs-and-trials.tar.gz`. The retained original and parent modules remain under `/private/tmp`, with the parent source restored at `/private/tmp/swiftsci-csv-count-only-control-20261021`. Scripts use local paths and require equivalent restored checkouts before reuse. Trial reconstruction uses the restored parent source. Final validation uses the candidate head. Choose a fresh output directory for another run.

Keep the focused validation-mode commit. Do not promote the broader bounded reader to the default or open its implementation PR yet. Next isolate numeric and String conversion on the wider reference data, separating per-cell work from per-batch scheduling. Preserve the Date recovery, original-token fallback, and peak-memory reduction while testing that next change.

This record belongs to `codex/engineering-notes` and must stay out of implementation PRs.
