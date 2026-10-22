# CSV count-only discovery and rejected-token pruning

The local prototype removes most of the late-type fallback penalty and keeps the earlier large-file memory reduction. It still fails the gate for replacing the default reader. Beijing eager CPU is 17.5% above the original reader, and the broader branch has streaming CPU regressions that predate this change. Do not hide those costs in an average.

## Source and implementation

The final local head is `297ebd36ef979cf1a5dfafa3f419c052165f2d1e` on `codex/csv-count-only-scan`. It builds on `33bd8ce78588d8027443e421ea918b9c4a704ab9`, the [exact-sizing prototype](../2026-10-21-csv-eager-batches/README.md). The original control is `dba26e1562503e1594194250d914327830d8f58d`. Each measurement plan records exact source and binary identities. Nothing was pushed or submitted.

The count-only specialization uses the existing framing state machine. Its compile-time output mode removes field and row-coordinate storage from counting. Normal indexing keeps local arrays. This avoids a second quote parser and the per-field sink mutation that regressed the first trial.

An inferred conversion now retains the offset of its first rejecting original token. Before a replay, the plan tests that token against later eligible candidates through the existing decoders. A token such as `true` already disproves Double, so replaying the entire prefix as Double cannot help. A surviving candidate still validates every original row. The plan never admits a type excluded by the original sample.

Offsets refer to the retained source. The eager reader rebases each batch's rejecting offset once. Indexed streaming uses the same pruning within its public chunk. The rejection record retains no source pointer, converted numeric text, or column-wide field index.

Public API, optional column storage, deployment target, ordered first-1000-row eligibility, explicit override invalid-to-null behavior, and streaming chunk-local inference remain unchanged. JSON retains its own caller. Record batches remain 16384 rows. That row bound is not a hard byte or memory limit.

## Diagnosis and rejected alternatives

The frozen-binary reproduction exited nonzero with late Boolean CPU 18.0% above the original. The Beijing input was 10.6% above it. Four smaller Boolean fixtures reproduced the trend around the internal eager batch boundary.

Process CPU profiling separated counting, framing, conversion, setup, and finalization. Beijing counting cost about 1.3 ms. Late Boolean framing ran 21 times because integer, Double, and Boolean each attempted seven batches. Setup and finalization were small, so builder destruction was not the main explanation.

The first generic sink trial passed correctness but increased ordinary framing cost. Its 162-worker measurement is retained in `count-only-measurement`. It is a rejected design. The compile-time output-mode pilot is in `output-mode-pilot`. It reduced large-file work modestly but did not resolve fallback. The final measurement includes rejected-token pruning.

The initial count-test compile failure came from a throwing expression inside a test macro. The corrected test binds the typed result before its assertion. It was a test construction repair, not a parser defect. No diagnostic overlay is present in production source.

## Final eager comparison

| Input and contract | Original CPU ms | Previous prototype CPU ms | New CPU ms | New vs original | Peak RSS MiB, original → new | Elapsed ms, original → new |
|---|---:|---:|---:|---:|---:|---:|
| bike-day known | 0.871 | 0.721 | 0.747 | -14.2% | 7.81 → 7.66 | 0.380 → 0.406 |
| bike-hour known | 7.649 | 5.629 | 5.670 | -25.9% | 17.73 → 15.72 | 1.506 → 2.297 |
| unique-shuffled known | 7.400 | 7.467 | 7.407 | +0.1% | 15.78 → 12.25 | 4.889 → 6.727 |
| Aotizhongxin known | 12.115 | 13.857 | 14.238 | +17.5% | 25.73 → 23.02 | 4.616 → 5.550 |
| energy known | 467.400 | 418.238 | 412.420 | -11.8% | 720.17 → 422.20 | 102.803 → 187.668 |
| energy infer | 446.738 | 430.586 | 415.324 | -7.0% | 720.22 → 422.28 | 101.879 → 186.794 |
| energy-date-full known | 465.083 | 477.702 | 456.939 | -1.8% | 720.23 → 421.69 | 96.801 → 211.323 |
| late-bool infer | 6.559 | 7.643 | 6.713 | +2.3% | 10.56 → 9.66 | 6.596 → 6.729 |
| late-text infer | 14.040 | 14.819 | 8.741 | -37.7% | 18.94 → 16.81 | 12.842 → 8.763 |

There are 162 validated fresh workers, six balanced-order rounds for nine configurations and three frozen binaries. The full input contracts, raw workers, and plans are retained. The final candidate lowers late Boolean CPU 12.2% and late text CPU 41.0% relative to the previous prototype. Relative to the original, those changes are +2.3% and -37.7% respectively.

The power references retain a peak near 422 MiB instead of 720 MiB, about 41% lower. Their elapsed times are still about twice the original. The memory improvement is real, but it does not erase the CPU or latency costs elsewhere.

## Streaming regression check

| Input | Original CPU ms | Previous CPU ms | New CPU ms | New vs previous | New vs original |
|---|---:|---:|---:|---:|---:|
| bike-hour | 5.280 | 5.824 | 5.812 | -0.2% | +10.1% |
| unique-shuffled | 5.548 | 6.827 | 6.875 | +0.7% | +23.9% |
| Aotizhongxin | 11.986 | 12.795 | 13.331 | +4.2% | +11.2% |
| energy | 327.163 | 367.194 | 365.440 | -0.5% | +11.7% |
| energy-date-full | 344.342 | 394.202 | 408.849 | +3.7% | +18.7% |

The streaming comparison has 90 validated workers plus 15 exact-output preflight workers. Each timed pass consumes and releases public 10000-row chunks immediately. A separate untimed pass checks all native types, values, null positions, and output order. Both passes use identical selected records and schemas across the three binaries.

The current change is within 4.2% CPU of the previous prototype on these five inputs. The earlier shared-conversion prototype was already slower than the original streaming reader. The final branch is 10.1% to 23.9% above the original on these inputs. This is an additional blocker for promoting the whole branch. Similar peak RSS does not compensate for added CPU work in streaming.

## Validation

- final-pruned-release: 382/382 passed, no failures or skips.
- final-pruned-debug: 382/382 passed, no failures or skips.
- final-pruned-asan: 382/382 passed, no failures or skips.

All three frozen parser implementations agree on 30720 deterministic raw-byte fixtures, including custom delimiter and quote overlaps, ragged rows, quoted newlines, escaped quotes, and permissive EOF cases. Count-contract tests compare counting with discovery and cover limits, cancellation, and long quoted records.

Fallback tests protect original-sample eligibility, original lexical text, earlier contradictions in a surviving candidate, unaffected completed columns, null values, and a rejecting token beyond the first batch. The new test files have 64 and 61 source lines. Large fixtures use generated repeated records rather than large literals.

The standard `tabular-smoke` run passes all 190 SwiftSci and pandas samples in production-default mode, and its certificate audit passes. This covers declared tabular workloads and the SwiftDataFrame test target. It does not establish full numerical certification or validate every MLX-dependent library module.

Two independent reviewers found no actionable standards or specification defects. The final small cleanup derives `rejected` from the recorded field instead of maintaining duplicate state. The final source also adds the cross-batch offset test.

## Measurement boundaries

Both resource comparisons use CPU backends with native parallelism, identical input bytes and schema contracts, AC power checks, warm input pages, and balanced process order. No builds or tests from this task run during accepted resource timings. Every timing worker validates its output. Validation is outside measured CPU and elapsed time, and memory is captured before validation. No outliers are trimmed.

CPU means process user plus system time. RSS includes resident mappings and allocator behavior. Neither metric is an allocation count or energy measurement. Native optional result storage is unchanged. No SRAM, SLC, processor-affinity, or hardware energy claim follows from these results.

Build receipts retain commands, source hashes, binary hashes, and dependency identities. Scratch binaries and full local test bundles remain in `/private/tmp/swiftsci-csv-cpu-profile-20261021`. The reproduction scripts contain local worktree and input paths. Restore equivalent paths or adjust them before rerunning elsewhere. Reference dataset provenance remains with the [prepared-date evaluation](../2026-10-21-csv-prepared-dates/README.md).

## Decision and next gate

Keep the local commits and the measured memory improvement. Do not open a PR to replace the default reader yet. The next investigation must isolate ordinary per-cell conversion and per-batch scheduling against the original implementation, including streaming. Wide numeric and repeated-date reference data are required controls. Promote a change only if it lowers CPU work without losing bounded discovery, native values, null behavior, or the measured memory benefit.

This record belongs to `codex/engineering-notes`. Implementation PRs must not include it or the benchmark artifacts.
