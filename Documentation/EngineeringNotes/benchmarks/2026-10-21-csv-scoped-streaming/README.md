# Scoped CSV streaming resource results

Scoped record batches and existing SIMD scans reduce CPU work and peak memory for the checked streaming workloads. They also increase elapsed time on several workloads. The implementation keeps the public streaming interface and owned output columns. It is a local implementation, not a submitted or merged change.

## Source progression and decision

| Revision | Local branch | Purpose |
| --- | --- | --- |
| `85f240ef707e59486f87177103928786b36db56e` | `codex/csv-ingestion` | Prepared dates and three correctness repairs; original full-index streaming control |
| `762650aadb1bc6baa16e7a451fdcb32fdeac5386` | `codex/csv-scoped-streaming` | Scoped scalar framing, consumer-driven CSV cursor, and composed pull transformations |
| `dba26e1562503e1594194250d914327830d8f58d` | `codex/csv-scoped-simd` | Existing SIMD structural scanning reused for general record discovery |

The first scalar prototype lowers the full energy stream's peak RSS from about 440 to 139 MiB. Its first controlled experiment raises CPU work by 10–11%, crossing the review threshold recorded before timing. The [scalar experiment](stream-measurement) is preserved. It motivates a separate SIMD trial rather than a claim that lower elapsed time or lower memory proves efficiency.

The SIMD trial reuses `CSVStructuralScanner`, including its 16-byte loads. It finds structural positions in the existing quote/framing state machine. Searches stop at 64 KiB windows so a long field without separators still reaches cancellation checkpoints. Escaped quote pairs skip their second structural position, including at vector and search-window boundaries. No thread pool, converted-value cache, dependency, or memory manager is added.

Keep the SIMD version as the preferred local streaming candidate. It reduces CPU work in every paired round across all five workloads, while preserving the scalar prototype's memory reduction. The eager materializing reader remains available. It still creates a full-file index, and it remains a different operation from consuming a stream without retaining every frame.

## Complete stream measurements

Each value is the median of six fresh processes. The original, scalar, and SIMD engines all consume one public stream without retaining returned chunks. Peak RSS is captured before validation. Exact native types, row order, missing positions, and all column values are checked in a separate untimed repeat in every worker.

| Workload | Original CPU ms | Scalar CPU ms | SIMD CPU ms | Original peak MiB | SIMD peak MiB | Original elapsed ms | SIMD elapsed ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| bike-hour | 7.343 | 5.938 | 4.963 | 17.797 | 12.812 | 1.517 | 2.066 |
| unique-shuffled | 7.149 | 7.521 | 5.553 | 13.430 | 9.375 | 4.600 | 4.899 |
| Aotizhongxin | 12.883 | 14.025 | 11.089 | 20.344 | 15.719 | 6.211 | 4.653 |
| energy | 466.142 | 487.913 | 323.599 | 439.406 | 138.984 | 91.085 | 151.299 |
| energy-date-full | 462.704 | 516.236 | 345.934 | 439.469 | 138.617 | 93.613 | 149.568 |

On the full date-converting energy file, CPU work falls 25.2% and peak RSS falls 68.5% relative to the original stream. Elapsed time increases from 93.6 to 149.6 ms, about 60%. On the numeric and text energy control, CPU work falls 30.6% and peak RSS falls 68.4%. Small workloads also use less CPU, but elapsed time does not improve in every case.

This is a resource tradeoff with measured CPU and memory benefits, not a universal latency improvement. The checked streaming workload has no hard latency requirement. A caller that requires the lowest latency for full materialization still needs a separate operation-level comparison. These measurements do not prove application throughput or energy savings, and CPU time is not a FLOP count.

The [full table](simd-stream-measurement/table.md), [raw 90-worker measurements](simd-stream-measurement/workers.jsonl), and [summary ranges](simd-stream-measurement/summary.json) retain every result. The full energy input has 2,075,259 rows. Bike Sharing and Beijing observations are original reference data. The shuffled unique-date file is a derived diagnostic control. Input bytes, schemas, date formats, and independent output hashes are pinned in the [timing plan](simd-stream-measurement/plan.json) and [prepared-date input contracts](../2026-10-21-csv-prepared-dates/inputs).

The machine and environment match the [prepared-date experiment](../2026-10-21-csv-prepared-dates/README.md). All calls run on the CPU with native engine parallelism and AC power. Six balanced permutations put each engine before each other engine three times. Inputs are read outside each timed round to favor a warm filesystem cache. Ordinary user workflows continue; this task runs no builds or tests during the controlled timings. No sample is removed. Fifteen engine/workload combinations pass preflight before the final 90-worker experiment.

## Ownership and behavior

`CSVReadCursor` owns a mapped source, headers, byte position, and remaining row limit. Its lock protects state and the complete synchronous read. Each request borrows source bytes, discovers one requested row chunk, converts columns with the shared builder, and returns an owned `DataFrame`. Borrowed pointers never cross an `await`, and all concurrent column workers join before the borrow ends.

The public stream uses the native unfolding initializer. Reading starts with consumer demand. EOF, errors, and direct cursor cancellation clear retained input. A weak-owner test also proves that native unfolding cancellation releases the source owner while the stream and iterator remain retained. The test accepts the stream's native nil-on-cancellation behavior; it does not require the producer closure to run on a pre-cancelled request. [Swift's unfolding implementation](https://github.com/swiftlang/swift/blob/main/stdlib/public/Concurrency/AsyncThrowingStream.swift) explains that producer-closure cleanup.

`ChunkedDataFrame` now owns transformation state in each iterator. `filter`, `select`, `mapChunk`, and supported joins advance upstream only when another output is requested. The four producer-task loops are removed. Tests check exact request counts, skipped empty filter results, mapping failure, and unsupported joins on empty sources. Terminal iterator state drops its owned upstream. A deliberately retained external source supplied by a caller remains caller-owned.

Headers, row limits, quoted records, CRLF, permissive EOF behavior, null tokens, native output types, chunk-local inference, and source order retain their established contracts. A positive chunk size is required. Returned strings and arrays remain usable after the source is removed. Compact batch offsets are relative to each borrowed source slice, even when the file's virtual range exceeds two or four GiB. Oversized batches retry with full-width fields.

The cursor still maps the source file. A row limit is not a byte limit: wide rows, large fields, retained outputs, and expanding joins can exceed an ordinary working set. `collect()` intentionally materializes all results. This implementation does not add byte-budget admission or guarantee a hard RSS bound.

## Validation

| Check | Scalar scoped head | SIMD scoped head |
| --- | ---: | ---: |
| Complete DataFrame Debug tests | 365 passed | 367 passed |
| Complete DataFrame Release tests | 365 passed | 367 passed |
| AddressSanitizer DataFrame tests | 365 passed | 367 passed |
| Standard tabular production-default samples | 190 passed | 190 passed |
| Certificate audit | Passed | Passed |

All completed test suites have zero failures or skips. The standardized profile contains 19 cases across SwiftSci and pandas in five process rounds. It qualifies tabular behavior and numerical handoff; its timings are not part of the controlled streaming comparison. Each head has its own built worker and source receipt. The full MLX-dependent library test suite is outside this validation scope.

Reviewed Debug coverage covers 214 of 224 added executable lines in the combined scoped/SIMD source diff relative to `85f240ef70`. [Per-file coverage](simd-coverage/patch-coverage.json) preserves the uncovered lines. These include invariant failures and the oversized-offset retry path; representation boundaries and large virtual ranges have separate checks. No production guard is removed to inflate coverage. Test fixtures cover quote alignment at 34 vector offsets, long escaped UTF-8 fields, and both sides of the cancellation-window boundary.

Independent standards review finds no actionable violation or code smell. Independent specification review finds and resolves an exact-alignment cancellation weakness in the scalar draft, then finds no remaining issue in either committed candidate. Historical failed launches remain in the local experiment directory. One ownership test initially retained the cursor itself and expected native cancellation to call it; that failed assertion tested the wrong ownership arrangement. Direct cancellation and weak-owner release are now separate checks.

Build receipts preserve Release flags, source hashes, linked dependency hashes, and executable hashes. Native measurement executables pass the repository's uninstrumented-binary check. Test bundles, machine binaries, mapped data, and prepared datasets are not added to production commits. The [archive manifest](SHA256SUMS.json) checks the retained evidence files. The [complete standardized run archives](qualification) keep their original certificate checksums. Their machine and path metadata remain intact so the extracted runs can be audited. Both archives pass the certificate audit after extraction.

## Integration status

The [ingestion strategy](../../research/2026-10-21-csv-ingestion-strategy.md) now has verified prepared conversion, scoped record discovery, and consumer-driven streaming through built-in transforms. These are committed locally in separate reviewable units. Production branches contain source, tests, and API documentation only; this report stays on `codex/engineering-notes`.

Eager bounded inference and late-type replay remain the next integration gate. The eager path still uses the full-file index. A direct compact numerical-output experiment and a broader native column-storage change remain conditional follow-ons. The existing direct matrix preparation is preserved. No blanket claim is made that the full architecture or every CSV workload is optimized.
