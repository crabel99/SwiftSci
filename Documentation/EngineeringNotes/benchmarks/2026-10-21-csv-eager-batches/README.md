# Eager CSV batches and exact output sizing

This is an implemented local experiment. The candidate preserves values and types but does not pass the default-reader resource gate. No upstream PR is planned yet. Late Boolean replay exceeds the CPU review limit at +16.2%. The wider Beijing input is also near the limit at +10.0%.

## Source and scope

The control is `dba26e1562503e1594194250d914327830d8f58d`, the validated scoped-SIMD streaming head. Its eager path still builds the complete field index. The final candidate is `33bd8ce78588d8027443e421ea918b9c4a704ab9` on `codex/csv-eager-count-probe`, based on `codex/csv-eager-batches`. All work remains local. Engineering records stay on `codex/engineering-notes`.

Public API, native optional column storage, deployment target, first-1000-row eligibility, original-token fallback and public chunk-local inference remain unchanged. JSON keeps its own inference caller. Public offset-grid parsing remains available.

See the [strategy](../../research/2026-10-21-csv-ingestion-strategy.md), [source trace](ground.md), [design A](design-a.md), [design B](design-b.md), [independent judgment](judgment.md) and [synthesis](synthesis.md).

## What changed

Shared generic conversion replaces repeated explicit and inferred loops. Each column attempt owns one typed builder. Dispatch occurs per column per batch. Synchronous workers join before borrowed coordinates expire. Failed inferred candidates discard their output and share replay waves over the original mapping. Successful columns stay complete. The first batch supplies the original sample and conversion input.

The original geometric-growth prototype passed correctness but did not lower large-file peak RSS. Fixed typed chunks removed repeated growth, but final contiguous output assembly still left high resident memory. Those adverse results are retained. The first 36-worker geometric pilot is diagnostic only because its original build receipt was not separately retained before rebuilding; it is excluded from final acceptance evidence.

Exact sizing counts selected records after the retained first batch, using the same scanner and bounded metadata. It then reserves final arrays once. This measured alternative departs from the initial preference to avoid a count pass. The extra work buys a material large-file RSS reduction, but smaller and replay-heavy CPU costs still need resolution. A 65536-row batch did not remove those costs and used more scratch than 16384 rows. The final experiment uses 16384.

The count and conversion passes retain at most two batches during initial sizing. A row budget is not a hard byte or RSS cap. Quoted large fields can exceed normal batch storage. Final eager output remains proportional to selected rows.

## Validation

- counted-release: 375/375 passed, 0 failed, 0 skipped.
- counted-debug: 375/375 passed, 0 failed, 0 skipped.
- counted-asan: 375/375 passed, 0 failed, 0 skipped.

Independent spec and standards reviews found no actionable source defects, including the exact-count delta. Tests cover late Int-to-Double and Int-to-Bool fallback, original lexical text, exact large Int64 values, all-null samples, custom null policies, quotes, ragged rows, row limits and batch boundaries. The new fixture files contain 65 and 60 source lines; larger row sets come from repeated strings.

Standard `tabular-smoke` validation passed all 190 samples across SwiftSci and pandas in production-default mode, and its certificate audit passed. Results are recorded in [the runner output](standardized-run.log) and [audit output](standardized-audit.log). They cover their declared tabular cases, not the full MLX-dependent library suite or numerical certification generally.

## Final paired resource comparison

| Input / mode | CPU ms, indexed → candidate | Peak RSS MiB | Elapsed ms |
|---|---:|---:|---:|
| bike-day / known | 0.982 → 0.731, -25.6% | 7.80 → 7.67 | 0.400 → 0.442 |
| bike-hour / known | 7.561 → 5.812, -23.1% | 17.78 → 15.73 | 1.489 → 2.318 |
| unique-shuffled / known | 7.445 → 7.639, +2.6% | 15.77 → 12.23 | 4.826 → 6.985 |
| Aotizhongxin / known | 12.237 → 13.457, +10.0% | 25.77 → 23.03 | 4.552 → 5.851 |
| energy / known | 467.447 → 420.203, -10.1% | 720.20 → 422.23 | 101.611 → 206.363 |
| energy / infer | 470.294 → 430.753, -8.4% | 720.23 → 423.68 | 102.367 → 208.028 |
| energy-date-full / known | 489.035 → 469.779, -3.9% | 720.22 → 423.67 | 98.081 → 229.723 |
| late-bool / infer | 6.482 → 7.532, +16.2% | 10.56 → 9.69 | 6.519 → 7.550 |
| late-text / infer | 14.114 → 15.402, +9.1% | 18.93 → 16.80 | 12.910 → 15.437 |

The final comparison contains 108 validated fresh workers, six balanced-order rounds for nine configurations. Every worker checks native types, column and row order, values and null positions against independent input contracts. Reference CSVs include original UCI power, Beijing and Bike Sharing records. Shuffled distinct dates and late-type failures are synthetic controls. Provenance for reference inputs remains with the [prepared-date evaluation](../2026-10-21-csv-prepared-dates/README.md).

Both paths use CPU native parallelism and the same source bytes and schema contracts. AC is checked. Input pages are read outside timing. This task runs no builds or tests during resource measurement. Correctness validation is excluded from measured CPU and elapsed work; memory is captured before validation. Timings include the public read and release. No outliers are trimmed.

CPU means process user plus system time. RSS includes resident mappings and allocator behavior; it is not live heap, allocation count or energy. Held live heap for the full explicit-date output is approximately 285 MiB for both paths, as expected for unchanged public storage. Reduced peak RSS does not alone prove higher sustained application throughput.

Plans, worker records, input hashes, receipts and summaries are retained alongside this report. The raw local test bundles and executable snapshots remain at `/private/tmp/swiftsci-csv-eager-checks-20261021`. Reproduction scripts name the original worktree and input paths; restore equivalent paths or edit them before rerunning elsewhere.

## Decision and next gate

Keep the experiment isolated. Do not waive the CPU review limits or average away the adverse cases. Next profile framing/counting, compact-record access and per-batch scheduling independently on the wider and late-replay cases. A count-only scanner must share the existing grammar rather than introduce a second quote parser. Any retained-index versus replay choice needs an explicit memory bound and workload evidence. No cache-capacity or hardware-affinity claim follows from these timings.
