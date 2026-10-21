# Explicit CSV date formats

Local branch `codex/csv-explicit-date-format`, commit `a5f6e78a751365ec360efdd4ae8f028db04b441b`, adds a source-format choice on top of numeric-inference repair `548a783f02678c95c027a733e3cbd51df363dc47`. The branch is unpushed. This report and its evidence belong only to `codex/engineering-notes`.

## Corrected diagnosis

The earlier reports called the UCI date mismatch a parser defect. That classification was incorrect. `Date.parse(from:)` documents month-first precedence for ambiguous slash dates, and `DateTimeTests.testAmbiguousDates` tests it. UCI household energy dates use day/month/year. For example, the library's default reads `1/2/2007` as January 2, while this source means February 1.

The historical diagnostic still fails its day-first oracle under the default, with identical column hashes to the numeric-repair head. It remains excluded from successful performance comparisons. We preserve that evidence and correct its interpretation. The separate loss of 398 fractional air-quality measurements was a genuine numeric-inference defect, addressed on the parent branch.

## Caller-controlled format

```swift
var options = CSVReadOptions()
options.columnTypeOverrides["Date"] = .date32
options.columnDateFormats["Date"] = "d/M/yyyy"
```

`columnDateFormats` supplies Foundation date-format patterns for explicitly typed date columns. Entries on inferred or non-date columns do nothing. An explicit date column without a format keeps the existing parser. Invalid dates become null, matching explicit conversion behavior.

The implementation uses a Gregorian calendar, POSIX locale, and UTC. It creates one formatter per converted column, or per column in each streaming chunk, and reuses it for every field. Each concurrent column has its own formatter. It adds no global cache, new parser, dependency, or numeric-inference work. Both existing date-conversion paths share the factory. Source text cleaning reuses the existing helper.

The production diff contains two source files and one 49-line test file: 73 insertions and two deletions. `Date.parse(from:)` and its ambiguity tests are unchanged. Format selection is a separate feature, not a changed default.

## Validation

| Check | Result |
| --- | --- |
| Test before implementation | New date-convention test fails for quoted and unquoted inputs through full, streaming, and internal string reads; 343 pass, one test fails |
| Complete DataFrame Debug suite | 344 pass, no failures or skips |
| Complete DataFrame Release suite | 344 pass, no failures or skips |
| Added executable source lines | 15/15 covered, including the options initializer |
| Standard tabular smoke | 190 validated samples, 19 cases across SwiftSci and pandas in five process rounds; certificate audit passes |
| Original energy-file prefix | All nine columns match the independent oracle across 25,000 rows |
| Original complete energy file | All nine columns match across 2,075,259 rows, including every date and 25,979 nulls in each measurement column |
| Default date diagnostic | Unchanged; its sole mismatch with the UCI oracle is the Date column |

The first test launch had a new test's argument order wrong and did not compile. That setup failure is retained as `red-format`. After correction, `red-behavior` fails against the parent reader with the new option declaration present but unused. The passing tests exercise the same test source after the reader uses the format. The evidence verifier checks those source fingerprints.

The tests also cover independent day-first and month-first columns, invalid calendar dates, configured nulls, format entries that do not change inference or text columns, and streaming with inference disabled. Existing tests retain the default ambiguity contract. LLVM coverage comes from the actual Debug test executable and profile; the report does not rely on Xcode's aggregate source-file listing.

The UCI audit uses the unchanged original file, whose bytes and provenance are recorded in the [reference-data report](../2026-10-21-csv-reference/README.md). An independent Python standard-library CSV reader constructs Gregorian UTC dates and hashes every output value and null position. It recomputes all nine column hashes. Full-file hashes for the eight non-date columns must also equal the earlier oracle. Time remains source text; this feature does not combine Date and Time into timestamps.

## Scope and limits

These are correctness results. The single-call audit includes resource counters, but it is not a controlled throughput experiment and supports no performance claim. In particular, the differently interpreted default cannot be used as a valid speed baseline for this source. A future comparison must give every library the same date convention, output types, null rules, and input bytes.

The standard smoke suite checks existing tabular workflows and does not independently certify this new format option. Its new-option evidence comes from the focused tests and full original-file oracle. We did not repeat the full all-module test suite, Address Sanitizer, or hosted CI. The parent sanitizer results belong to that parent. The reference executable targets macOS 14; local validation does not establish compatibility with a different hosted compiler.

## Evidence and replay

- [Verification summary](verification.json)
- [Evidence archive](evidence.tar.gz)
- [Archive member hashes](evidence-manifest.json)
- [Numeric inference repair](../2026-10-21-csv-inference/README.md)
- [Compact parser integration](../2026-10-21-csv-integration/README.md)

The archive contains the production patch, test and compiler receipts, coverage text, independent oracle, original-data audit outputs, standard benchmark requests and responses, and certificate. It excludes source datasets, executables, module caches, and Xcode result bundles. Every archive member is hash-verified.

Scripts preserve the local cache paths used for this experiment. Replay requires the recorded parent and feature commits, resolved dependencies, existing benchmark Python environment, and original UCI file. Adjust the scratch paths, then run `verify.py` for Debug with coverage and Release, `coverage.py`, `reference/date-oracle.py`, `reference/build.py explicit`, and `reference/audit.py`. Build the standard worker, prepare and certify `tabular-smoke` for SwiftSci and pandas, audit its certificate, and run `verify-evidence.py`. Use a fresh evidence directory; the runners reject existing result bundles. This is recorded local validation, not a new portable benchmark command.

## Matched reference comparison

The subsequent [CSV resource comparison](../2026-10-21-csv-matched-reference/README.md) measures this exact head against pandas, Polars, and DuckDB with matching source schemas. All outputs pass. Date conversion remains expensive, and the report identifies bounded reuse as the next experiment. The correctness results above remain unchanged.
