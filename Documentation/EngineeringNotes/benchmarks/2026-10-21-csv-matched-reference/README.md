# Matched CSV comparison on original reference files

This compares local SwiftSci commit `a5f6e78a751365ec360efdd4ae8f028db04b441b` with pandas 3.0.6, Polars 1.44.2, and DuckDB 1.5.6. It measures resource use after the compact-record, numeric-inference, and explicit-date-format work. It does not claim to represent an unmodified upstream main or every possible configuration of the reference libraries.

SwiftSci uses less CPU than the reference engines on the two station controls. Polars uses less CPU and memory on the large energy file. Explicit date conversion is the largest remaining cost in SwiftSci; this comparison supports optimizing that path next.

The same bytes, column order, null rules, numeric widths, date convention, and materialized output values are required from every engine. All 56 preflight workers and all 96 measurement workers pass exact per-column hashes and null counts. No invalid output contributes to these results.

## Workload and execution contract

The original UCI energy file has 2,075,259 rows and nine columns. It runs twice: Date and Time as text, and Date converted to midnight UTC with Time retained as text. The two measured Beijing station files each have 35,064 rows and eighteen columns. All twelve station files are checked in preflight. These are the same two station controls used in the preceding repair evaluation, selected before timing. They do not establish the performance of all twelve files or arbitrary CSV workloads.

Every reader receives the complete column schema, delimiter, and null-token set. There is no numeric type-inference contest. Energy nulls are empty fields and `?`; station nulls are empty fields and `NA`. All measurement columns are binary64, and station identifier/calendar columns are Int64. The date contract is the same Gregorian calendar day. The validator encodes it as midnight UTC. Swift returns Date values; the references return native 64-bit, timezone-naive datetime columns interpreted as UTC by the validator. Storage and timestamp units can differ. This does not establish equivalence for timezone-sensitive downstream operations. String values and row order must match exactly.

| Engine | Ingestion contract |
| --- | --- |
| SwiftSci | Public `DataFrame(csv:options:)`, complete type overrides, explicit `d/M/yyyy` where Date is parsed |
| pandas | C CSV reader, complete non-date dtypes, default null list disabled, round-trip float conversion, explicit `%d/%m/%Y` date format and date cache enabled |
| Polars | Complete schema and null list; date text converted with strict, exact `%d/%m/%Y` parsing into a 64-bit datetime column inside the measured operation; date cache enabled |
| DuckDB | Complete columns, automatic detection disabled, explicit timestamp format and null list, row-order preservation enabled; Arrow materialization included in measured operation |

[Polars documents that a complete schema avoids inference](https://docs.pola.rs/api/python/stable/reference/api/polars.read_csv.html). [pandas documents its date-format, caching, and float-conversion controls](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html). The installed API behavior and every resulting value were also checked locally. DuckDB's Python wrapper uses `na_values`, not the SQL-style `nullstr` spelling; the initial wrapper setup error was corrected before preflight and measurement.

The machine is an Apple M4 Max with 128 GiB memory, macOS 27.0.1, Swift 6.4, and Xcode 27.0. AC power was confirmed at the start, before each round, and at the end. Power mode was automatic. Every engine uses CPU execution and native parallelism under the existing `production-default` environment policy. No CPU affinity or P-core/E-core placement is forced. Configured worker pools do not establish the number or type of cores actually active.

Each case has six fresh-process rounds, one read per worker. Three engine orders and their reverses give every pair equal before/after positions. Imports, library initialization, the DuckDB connection, and schema preparation occur before measurement. We explicitly read the source file outside each round to warm the normal filesystem cache. This measures first-call ingestion in a prepared runtime with cached input, not process launch or cold-disk I/O. No builds or additional benchmarks run alongside the measurement; ordinary desktop activity remains.

Timing covers the eager public read, required date conversion/materialization, and output release. Validation occurs between read and release and is excluded from both CPU and elapsed time. Memory is captured before validation. There are no repeated reads or warmups inside a worker, so process high-water memory cannot include a preceding validation pass. Every sample is retained.

## Results

Values are medians of six workers. CPU time is process user plus system time, not FLOPs, energy, or elapsed time. Added retained RSS is the process RSS with its result held minus RSS before reading. It includes allocator-retained memory and runtime work; it is not just the logical column payload. Peak RSS is total process high-water memory through read completion and includes the prepared runtime. Python workers also preload NumPy for validation, so absolute process peaks are not standalone engine deployment footprints. Read the baseline and RSS growth alongside those peaks. The archive also records each process's baseline and full ranges.

| Case | Engine | Elapsed ms | CPU ms | Added retained RSS MiB | Peak process RSS MiB |
| --- | --- | ---: | ---: | ---: | ---: |
| Energy, dates as text | SwiftSci | 100.06 | 476.52 | 586.86 | 720.16 |
| Energy, dates as text | pandas | 1,156.86 | 1,153.78 | 308.56 | 406.37 |
| Energy, dates as text | Polars | 24.44 | 312.75 | 339.30 | 407.20 |
| Energy, dates as text | DuckDB | 73.83 | 646.38 | 496.41 | 571.58 |
| Aotizhongxin | SwiftSci | 6.36 | 13.94 | 16.59 | 25.77 |
| Aotizhongxin | pandas | 37.21 | 36.79 | 18.08 | 116.00 |
| Aotizhongxin | Polars | 2.98 | 20.67 | 15.72 | 80.11 |
| Aotizhongxin | DuckDB | 18.68 | 36.52 | 20.34 | 95.52 |
| Wanliu | SwiftSci | 6.22 | 13.64 | 16.60 | 25.62 |
| Wanliu | pandas | 36.37 | 36.07 | 17.34 | 115.12 |
| Wanliu | Polars | 2.91 | 19.85 | 15.83 | 80.28 |
| Wanliu | DuckDB | 18.59 | 35.99 | 19.77 | 94.81 |
| Energy, dates parsed | SwiftSci | 87,361.34 | 87,578.76 | 828.73 | 962.03 |
| Energy, dates parsed | pandas | 1,378.56 | 1,376.99 | 442.66 | 649.87 |
| Energy, dates parsed | Polars | 38.70 | 349.37 | 250.10 | 410.48 |
| Energy, dates parsed | DuckDB | 78.59 | 695.31 | 461.62 | 536.80 |

### Paired CPU ratios against Polars

Ratios compare SwiftSci with Polars within each round. Below one means less SwiftSci CPU time. Ranges include all six rounds.

| Case | Median CPU ratio | Minimum to maximum |
| --- | ---: | ---: |
| Energy, dates as text | 1.529 | 1.377 to 1.547 |
| Aotizhongxin | 0.670 | 0.649 to 0.680 |
| Wanliu | 0.689 | 0.610 to 0.707 |
| Energy, dates parsed | 254.915 | 230.142 to 272.785 |

## CPU and memory decisions

The station files show why CPU work and elapsed time need separate treatment. SwiftSci uses less CPU than Polars on these inputs, while Polars finishes earlier. Retained RSS growth is close; the much smaller Swift process peak also reflects its smaller prepared runtime and the Python benchmark imports. This is not evidence of uniformly smaller column payloads.

The large energy file with text dates exposes a remaining resource gap against Polars. SwiftSci uses more CPU, takes longer, and grows process memory more. SwiftSci uses less CPU than pandas and DuckDB on that case, but more memory. That is a tradeoff, not an unqualified efficiency win.

Parsed dates dominate the current SwiftSci read. The explicit-format feature fixes the source-contract problem, but does not yet make the conversion competitive. This does not justify replacing the compact parser: source review shows that the date path invokes Foundation's formatter for each field. pandas and Polars can reuse parsed values under their configured caches. The benchmark itself does not isolate every source of the timing difference.

The energy file contains 1,442 distinct date strings and 1,442 consecutive date runs across 2,075,259 observations. There are 2,073,817 adjacent repeats, or 99.9305% of rows. These counts were computed after timing from the original file. Reusing a preceding conversion is therefore a concrete, constant-storage candidate for this workload. It still needs mixed-format, invalid-date, high-cardinality, and shuffled-input checks before production use. A more specialized date parser is a separate candidate; these measurements do not establish which design should ship.

The large unquoted reader also retains its full-width flat field-index path, and `CSVColumnBuilder` produces `TypedColumn` arrays of optional values. Those are visible storage choices worth profiling. The RSS results alone cannot assign the observed memory to the field index, output arrays, allocator caches, or temporary Foundation objects. That attribution remains open.

The next experiment should isolate date-conversion reuse with a bounded amount of state, retain the existing default behavior, and measure CPU plus memory on repeated and non-repeated dates. Keep numeric/quoted CSV storage work separate so each change has attributable evidence. No production code was changed during this comparison.

## Limits and evidence

Six fresh-process measurements per engine/case are a useful local baseline, not a universal performance ranking. The reference libraries return their native eager tables, and DuckDB includes its Arrow export. These output contracts deliberately expose real implementation differences rather than normalize every library through an extra shared conversion. Validation checks exact values, widths, row order, and null positions outside timing.

The date contract here is whole-day UTC interpretation, not arbitrary timezone, fractional-second, or malformed-source behavior. The two Date modes use the same original file but ask for different outputs, so they are separate workloads. Filesystem cache, ordinary scheduling, prepared runtimes, and the selected API paths limit generalization. CPU temperature and unrelated desktop load were not controlled; all observed variation is retained. CPU seconds do not isolate instruction count, core type, or clock frequency. No GPU/NPU, energy, cache-miss, allocation-count, or hardware-core placement measurements were taken.

- [Verification summary](verification.json)
- [Measurement summary data](summary.json)
- [Evidence archive](evidence.tar.gz)
- [Archive member hashes](evidence-manifest.json)
- [Explicit date-format feature](../2026-10-21-csv-date-format/README.md)
- [Original data provenance and earlier comparison](../2026-10-21-csv-reference/README.md)

The evidence stays on `codex/engineering-notes`. It contains the pinned Swift build receipt, Python worker, exact engine options, original-data input fingerprints, 56 preflight outputs, all 96 measurement outputs, power records, date-characteristic scan, summarizer, and verifier. It excludes datasets, binaries, and compiler caches. Scripts record local paths and require the pinned source, dependency cache, and benchmark virtual environment. Replay uses a fresh directory and runs preparation, build, preflight, measurement, summarization, post-run characterization, and verification in that order. This is a recorded experiment, not a newly published standard benchmark profile.
