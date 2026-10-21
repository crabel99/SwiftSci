# Prepared CSV date conversion

Prepared byte conversion removes the dominant Foundation date cost on these declared numeric-date workloads. It reduces CPU work and held memory without a value cache. The numeric and text controls stay within the review thresholds recorded before timing. This supports shipping the date change independently of the streaming prototype.

The comparison uses baseline `a5f6e78a751365ec360efdd4ae8f028db04b441b` and candidate `85f240ef707e59486f87177103928786b36db56e` on local branch `codex/csv-ingestion`. Neither branch is pushed. Keep this report and its evidence on `codex/engineering-notes`.

## Implementation and compatibility

Each column prepares its numeric format once. Recognized ASCII year, month, and day fields convert directly from CSV bytes. A checked Gregorian calculation constructs the UTC `Date`, with no intermediate field String. The direct subset admits years 1600 through 9999 and formats composed of one four-digit year and one month and day component, separated by slash, hyphen, or period.

Unsupported forms keep Foundation conversion, including short years, historical dates, alternate separators accepted by Foundation, Unicode digits, timestamps, and format directives outside this subset. The fallback formatter is created only when needed. Default parsing and its month-first ambiguity rule are unchanged. Null matching occurs before conversion. Explicit invalid conversions still become null.

Separate commits repair three reproduced defects before the optimization: streaming row limits, streaming header normalization, and generated header-name collisions. Contract tests also retain chunk-local inference, late-value validation, and the existing direct numerical handoff. The independent [standalone date diagnostic](date-parity) checks 6,720 Foundation comparisons, including 4,264 direct conversions.

## Matched resource results

These are medians from six fresh processes per engine and workload. CPU is process user plus system time for one public eager read and output release. Held RSS growth is measured before value validation, relative to that process before the call. It is not an allocation count or payload measurement.

| Workload | Before CPU ms | Prepared CPU ms | Before held RSS growth MiB | Prepared held RSS growth MiB |
| --- | ---: | ---: | ---: | ---: |
| bike-day | 39.047 | 1.449 | 3.89 | 1.27 |
| bike-hour | 819.294 | 11.153 | 14.80 | 10.09 |
| unique | 3987.225 | 6.778 | 21.82 | 7.62 |
| unique-shuffled | 3957.685 | 7.614 | 21.88 | 7.55 |
| energy | 482.447 | 496.512 | 586.84 | 586.84 |
| Aotizhongxin | 14.001 | 13.507 | 16.57 | 16.63 |
| Wanliu | 13.498 | 13.637 | 16.56 | 16.62 |
| energy-date-full | 82638.276 | 488.654 | 828.70 | 586.85 |

The full date-converting energy read drops from 82.64 CPU seconds to 0.489. Every paired unique-date and shuffled-date round improves without a cache. The full numeric and text energy control changes from 482.45 to 496.51 CPU ms, about 2.9% by the ratio of medians. This stays below the predeclared 10% review threshold. The other numeric controls remain close to their baseline. No control exceeds the held-RSS review threshold of 5% plus 8 MiB.

The [complete comparison table](measurement/table.md) includes pandas 3.0.6, Polars 1.44.2, and DuckDB 1.5.6. On the full date-converting energy file, prepared SwiftSci uses 489 CPU ms, Polars 370, DuckDB 707, and pandas 1,367. SwiftSci's held RSS growth is still 587 MiB, versus 249 for Polars, 461 for DuckDB, and 443 for pandas. Date conversion is much cheaper, but the full index and optional output arrays remain material memory costs. These results do not establish that the entire CSV architecture is finished.

All five engines receive the same original bytes, complete declared native types, matching null tokens, and explicit date interpretation. All 240 timed workers pass column order, row count, native type, null-position, and per-column value hashes. Forty unique engine/workload preflight combinations pass; eight final candidate checks repeat after its build is frozen. The additional checks close a build/preflight scheduling overlap and are retained separately.

## Workloads and measurement conditions

Original reference files include the complete UCI household energy file and both Beijing air-quality stations. The separately selected [UCI Bike Sharing dataset](https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset), DOI 10.24432/C5W894, supplies daily and hourly observations. Its original files and provenance were pinned before implementation. The daily file has 731 distinct source dates. The hourly file has 17,379 records. See [reference provenance](reference/provenance.json) and the [input contracts](inputs).

`unique` and `unique-shuffled` are derived diagnostic controls with 100,000 distinct dates. The shuffled order uses seed 81471. They diagnose cheap conversion independently of repetition; they do not replace the original-data results. The `energy` control preserves dates and times as text. `energy-date-full` converts the original date field using its day-first source convention.

The machine is an Apple M4 Max with 128 GiB, on AC, macOS 27.0.1, Swift 6.4, and Xcode 27. Each engine uses its native CPU parallelism under the repository's production-default policy. No claim is made about equal worker budgets, energy, FLOPs, affinity, or CPU cache misses.

Six balanced cyclic and reversed orders put each engine before each other engine three times. Inputs are read outside the timed call before each round to favor a warm filesystem cache. Ordinary user workflows continue. This task runs no builds or tests during timing. All samples and their ranges remain in [raw measurements](measurement/workers.jsonl) and [summary statistics](measurement/summary.json); no outlier is removed. AC is checked before each round and at completion.

Python package imports and connection setup precede timing. Native output materialization, date conversion, and release are inside each measured call. Exact output validation is outside timing, and peak/held memory is captured before it. Absolute process peaks include each runtime and its imports. File cache residency can still vary with host activity.

## Validation and evidence

The complete DataFrame Release suite passes 354 tests with no failures or skips. AddressSanitizer passes the same 354 tests at candidate head `85f240ef70`. Debug coverage at `38f962f98b` covers all 112 executable date-helper lines and all 22 added reader lines. The final candidate removes one redundant matcher initialization after that coverage run; the coverage receipt is not relabeled as a measurement of the later source. This report does not claim a rerun of the full MLX-dependent library suite.

The [build verification](build-vcs-verification.json) checks every SwiftDataFrame source against its commit and records both uninstrumented executable hashes. [Build receipts](build) retain commands, compiler settings, and linked dependency hashes. The [timing plan](measurement/plan.json) records the acceptance thresholds before timing. The local host label and test device identifiers are omitted from this archive; benchmark values and source fingerprints are preserved.

A separate instrumented sample of the baseline follows `NSDateFormatter` through `CFDateFormatter` into ICU parsing. [The sample](baseline-sample.txt) supports the cost diagnosis. Its resource result is excluded from the acceptance timings.

`prepare-bench.py`, `build.py`, `preflight.py`, `run.py`, and `summary.py` preserve the local experiment. Their paths and build dependency locations describe this machine; the original input contracts and file hashes identify the portable data requirements. The archive's [SHA256 manifest](SHA256SUMS.json) checks its evidence files.

## Decision

Keep the prepared-date change. Defer a converted-value cache because cheap unique-value conversion already meets this stage's resource goal. Continue the scoped-record and demand-driven streaming experiment against this frozen candidate, charging its framing, scheduling, retained state, and source release. Eager bounded inference and replay remain a separate integration gate in the [ingestion strategy](../../research/2026-10-21-csv-ingestion-strategy.md).
