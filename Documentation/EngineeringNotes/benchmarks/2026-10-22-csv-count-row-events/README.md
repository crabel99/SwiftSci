# Count-only CSV scanning without field events

The candidate skips field-delimiter events while counting records for eager column capacity. It retains quote and row-boundary processing. Indexed discovery, conversion, inferred type selection, allocation capacity, and scheduling are unchanged.

The implementation is `277d1792d34e280a50744bd7419848d1c16b8655` on local branch `codex/csv-count-row-events`, based on `5375f261c28c5cb1ee94f6c0892ba6d830e4312a`. That parent is the [explicit numeric decoding experiment](../2026-10-21-csv-numeric-decode/README.md). The original reader control remains `dba26e1562503e1594194250d914327830d8f58d`. The change adds 13 lines and removes one across the scanner and its existing count-parity test file. Nothing is pushed.

## Count rows without discovering every field

The bounded eager reader first discovers one batch, then counts remaining records to reserve exact output capacity. The parent uses a count specialization of the shared grammar scanner. Although that specialization allocates no field coordinates, its structural scanner still reports every comma to the state machine.

Counting needs quotes and row boundaries. The candidate substitutes LF for the scanner's delimiter event only in count mode. The existing grammar still applies its quote, delimiter, and newline precedence. At EOF, one check restores the existing behavior for a final unquoted delimiter. That delimiter leaves the final row unfinished, so the indexed parser does not retain that row. A delimiter inside an unfinished quote remains part of a field. The optimization preserves both behaviors.

This removes per-delimiter processing from counting without adding a separate grammar, cache, index, allocation policy, thread pool, or public option. The new test uses six trailing-field patterns after a 64 KiB prefix and compares limited and unlimited counts with real indexed discovery. It adds one parameterized test, keeping the suite file small.

## Reproduction and competing trials

A frozen-binary reproduction still fails the 10% CPU-review limit on wider eager Beijing input and inferred two-column numeric input. The initial ratios are 1.105 and 1.190 versus the original. Reduction across 1000, 16384, 16385, and 100000 rows shows that the numeric cost becomes clearer across several batches. Inputs, native types, selected values, nulls, and output order remain matched.

The investigation tests three ranked explanations. The count trial removes delimiter events only. The batch trial increases the private batch limit from 16384 to 65536 rows only. The view trial borrows the coordinate storage view once per batch instead of once per column. Its joined ownership and scheduling remain unchanged. Each trial starts at the same parent.

The pilot retains 192 validated workers across six cases and four implementations in balanced orders. On the large eager power input, the count trial uses about 5% less CPU and 9% less elapsed time, with the same peak RSS. Wider eager input and the small explicit numeric input also improve. Streaming acts as an unchanged-path control.

Larger batches reduce CPU on several eager cases but increase peak RSS by about 2.3 MiB on the small numeric input and 10 MiB on the large power input. They are retained as a separate resource tradeoff rather than silently promoted. Borrowing the coordinate view once per batch does not consistently help. The focused commit contains neither trial.

## Eager resource comparison

| Input and mode | Original CPU ms | Parent CPU ms | New CPU ms | CPU vs parent | CPU vs original | Peak RSS MiB, original → new | Elapsed ms, original → parent → new |
|---|---:|---:|---:|---:|---:|---:|---:|
| bike-day known | 0.993 | 0.808 | 0.794 | -1.8% | -20.0% | 7.80 → 7.72 | 0.403 → 0.437 → 0.405 |
| bike-hour known | 7.490 | 5.362 | 5.338 | -0.4% | -28.7% | 17.77 → 15.78 | 1.447 → 2.050 → 2.027 |
| unique-shuffled known | 7.645 | 6.175 | 6.049 | -2.0% | -20.9% | 15.78 → 12.31 | 4.982 → 5.518 → 5.372 |
| Aotizhongxin known | 11.477 | 12.871 | 12.441 | -3.3% | +8.4% | 25.78 → 23.11 | 4.558 → 5.637 → 5.174 |
| energy known | 449.420 | 372.280 | 349.383 | -6.2% | -22.3% | 720.21 → 420.84 | 102.225 → 190.880 → 175.442 |
| energy infer | 448.997 | 403.216 | 392.418 | -2.7% | -12.6% | 720.22 → 421.57 | 101.785 → 191.321 → 175.427 |
| energy-date-full known | 462.637 | 381.998 | 367.861 | -3.7% | -20.5% | 720.21 → 422.37 | 97.402 → 183.730 → 168.799 |
| late-bool infer | 6.500 | 6.599 | 6.653 | +0.8% | +2.4% | 10.56 → 9.67 | 6.576 → 6.655 → 6.710 |
| late-text infer | 14.270 | 8.764 | 8.816 | +0.6% | -38.2% | 18.92 → 16.88 | 13.042 → 8.809 → 8.873 |

## Streaming resource comparison

| Input and mode | Original CPU ms | Parent CPU ms | New CPU ms | CPU vs parent | CPU vs original | Peak RSS MiB, original → new | Elapsed ms, original → parent → new |
|---|---:|---:|---:|---:|---:|---:|---:|
| date-100000-1 known | 4.498 | 4.374 | 4.394 | +0.4% | -2.3% | 8.52 → 8.58 | 4.540 → 4.401 → 4.447 |
| bike-hour known | 5.378 | 5.384 | 5.242 | -2.6% | -2.5% | 12.81 → 12.95 | 2.002 → 1.977 → 2.015 |
| unique-shuffled known | 5.661 | 5.588 | 5.551 | -0.6% | -1.9% | 9.38 → 9.49 | 5.024 → 4.970 → 4.938 |
| Aotizhongxin known | 12.563 | 12.225 | 12.380 | +1.3% | -1.5% | 15.61 → 15.78 | 4.620 → 4.580 → 4.597 |
| energy known | 337.477 | 321.778 | 323.413 | +0.5% | -4.2% | 138.90 → 138.82 | 152.611 → 145.675 → 151.617 |
| energy-date-full known | 347.094 | 336.973 | 341.187 | +1.3% | -1.7% | 139.16 → 138.98 | 146.728 → 143.283 → 143.475 |

## Null-heavy resource comparison

| Null fraction and mode | Original CPU ms | Parent CPU ms | New CPU ms | CPU vs parent |
|---|---:|---:|---:|---:|
| 0% infer | 2.506 | 2.996 | 2.849 | -4.9% |
| 50% infer | 3.195 | 3.607 | 3.505 | -2.8% |
| 50% known | 2.821 | 3.159 | 3.041 | -3.7% |
| 90% infer | 3.608 | 3.603 | 3.473 | -3.6% |
| 90% known | 2.948 | 3.292 | 3.178 | -3.5% |

The null controls contain 100000 rows with native Int64 and Double output. Their deterministic missing positions cover 0%, 50%, and 90% null distributions. The final parity guard checks actual native output metadata between implementations, in addition to the per-worker value and null checks.

Large eager reads use 2.7% to 6.2% less CPU than the parent and finish about 8% sooner. Wider eager Beijing input uses 3.3% less CPU and finishes 8.2% sooner. The synthetic numeric controls use 2.8% to 4.9% less CPU. Large eager peak RSS remains about 421 to 422 MiB versus about 720 MiB originally. The candidate does not increase the retained-memory policy.

No final case exceeds the 10% CPU-review threshold against the parent. The unchanged streaming path varies by about -2.6% to +1.3% in CPU, with one large-stream elapsed median about 4.1% higher. That result is retained rather than described as an improvement. The count-only optimization does not run in streaming.

One case remains above the 10% CPU-review threshold against the original: null-free two-column numeric inference uses 13.7% more CPU. Wider eager Beijing input remains 8.4% above the original, and 50%-missing numeric inference remains 9.7% above it. Those near-threshold results still matter. Crossing a review threshold is not proof that all overhead has disappeared. The broader eager prototype also retains an elapsed-time cost against the original on several cases. The tables preserve that tradeoff.

Keep this focused improvement. The next investigation is the remaining small inferred-numeric cost across batches. The larger-batch trial gives evidence of a coordination tradeoff, but its extra temporary memory needs an explicit policy before production use. Do not promote that trial or change inference semantics to make a benchmark pass.

## Correctness and measurement boundaries

All 383 SwiftDataFrame tests pass in Release, Debug, and Release with Address Sanitizer, without failures or skips. Receipts pin their source hashes to this implementation. The new EOF test supplements existing random-byte, custom delimiter, custom quote, search-window, maximum-row, and cancellation coverage.

A direct scanner driver compares count-only results with actual indexed discovery for 30729 fixtures and five unlimited or limited count checks per fixture. Both the frozen parent and final source pass all 153645 checks. The separate public parser differential still matches all 30720 raw-byte fixtures. [Independent standards and specification reviews](reviews.md) report no actionable defects. The specification review explicitly checks delimiter-equals-quote, delimiter-equals-LF, and quote-equals-LF precedence.

The standard production-default `tabular-smoke` suite passes all 190 SwiftSci and pandas samples, and its certificate audit passes. This validates the declared tabular cases. It does not certify the full numerical or MLX-dependent library.

Final resource evidence contains 162 eager workers, 108 streaming workers, and 90 null-control workers, plus 18 streaming correctness preflights. Each comparison uses six balanced-order rounds and fresh processes. Input pages are warm. AC power is required, and CPU parallelism remains native. This task runs no builds or tests alongside accepted measurements. No outliers are trimmed.

Within each comparison, the selected bytes, schema contract, native output types, values, nulls, and output order match. Validation runs outside the measured operation. Streaming validates all per-column hashes in a separate untimed repeat. Peak memory is captured before validation. CPU is process user plus system time. Elapsed time is reported separately. RSS includes resident mappings and allocator effects. None of these measurements is an energy reading, allocation count, or hardware-cache measurement.

## Reproduction and ownership

Plans, raw workers, summaries, test receipts, build identities, and input contracts accompany this report. `standardized-artifacts.tar.gz` preserves the standard-suite results. `diagnostic-inputs-and-trials.tar.gz` preserves reductions and trial sources. `source-change.patch.gz` contains the focused implementation and test diff. `artifact-sha256.json` verifies the retained files.

Scripts refer to frozen local sources, modules, and input paths. The parent source is restored at `/private/tmp/swiftsci-csv-numeric-decode-control-20261022`. The original source remains at `/private/tmp/swiftsci-csv-scoped-simd-20261021`. Restore matching sources and dependencies before rebuilding. Use a fresh output directory for another run. Final controllers refuse to overwrite prior outputs.

This record belongs to `codex/engineering-notes` and must stay out of implementation PRs. All changes remain local. Retain any remaining CPU or latency costs explicitly before considering the broader bounded eager reader for default use.
