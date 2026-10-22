# CSV conversion work and ownership

Grounded in `/private/tmp/swiftsci-csv-count-only-scan-20261021`. This trace covers the byte reader path. This checkout has `CSVReader.buildIndexedColumn`, not a `convertColumn` function.

`CSVColumnPlan` owns the candidate type list and immutable conversion options. `CSVColumnConversion` selects a typed `CSVColumnAttempt` reference. The attempt owns one immutable decoder, a validation flag, the growing `CSVColumnBuilder`, and the first rejected field. Readers supply bytes and record coordinates for each append; attempts do not retain those inputs.

## What capacity means

`CSVColumnPlan.conversion(type:capacity:)` passes capacity unchanged into `CSVColumnAttempt.init`. The attempt passes it to `CSVColumnBuilder.init`, which calls the Swift array's `reserveCapacity`. Capacity reserves output storage. It does not limit append work, supply a sample, or change decoder selection in the current code. `append` receives its actual row count separately.

| Caller | Capacity supplied | Actual conversion work |
| --- | --- | --- |
| `CSVEagerReader.begin` | Initial selected rows plus `SystemsCSVParser.countRecords` over the remaining bytes, bounded by remaining `maxRows` when present | All selected data records, appended in batches |
| `CSVEagerReader.read` after rejection | The same `initial.capacity` | The new candidate replays the selected data records from byte offset zero |
| `CSVReader.buildIndexedColumn` | `dataRowsToRead` | That exact requested indexed row range, once per candidate attempt |
| `CSVColumnPlan.nextCandidate` | `1` | One original rejected token, represented as one synthetic record |

The eager value is the total selected data-row count, not the first batch size. `begin` scans at most 16,384 initial rows, then counts the remaining records without retaining their coordinates. For `maxRows == 0`, it scans one row for structure but sets selected rows and capacity to zero. `countRecords` returns zero immediately when its limit is zero. Headers are outside the data source counted here.

For streaming, `CSVReadCursor.read` requests `min(chunkSize, remainingRows)` from `scanBatch`. It sends the batch's actual `records.count` to `CSVReader.buildFrame`. That count becomes `dataRowsToRead` and capacity in `buildIndexedColumn`, even for a short final chunk. It is the chunk's selected row count, not total remaining file rows or the configured chunk size.

A retry probe's capacity of one describes only the probe. If a later candidate accepts that token, the eager reader creates a separate full-capacity attempt, or `buildIndexedColumn` creates a separate chunk-capacity attempt. The probe's builder and decoder are not reused for the full conversion.

## Decoder lifetime and batches

`CSVColumnPlan.init` samples at most the first 1,000 rows of its supplied range. Overrides produce one nonvalidating candidate. Disabled inference produces UTF-8. Inference records the eligible candidates in priority order and always ends with UTF-8. `nextCandidate` can eliminate later candidates with the rejected token, but cannot add a type excluded by the original sample.

`CSVEagerReader.begin` creates the plans and first attempts, then appends the initial batch. `read` keeps those same attempt references while scanning later batches. `CSVColumnConversion.appendIndexed` selects flat, compact, or general record access and dispatches to the existing attempt. `CSVColumnAttempt` stores `decoder` as `private let`; batch appends reuse that decoder. The small-string versus general-string choice is also fixed when `conversion` creates the attempt.

An inferred invalid value rejects the attempt, records the original source field offset, and clears its builder. Later appends return immediately for that attempt. The eager reader advances the candidate, creates a new attempt, resets its scan offset and row count, and replays the source for rejected columns. Successful columns finish and leave the active list. A decoder is therefore stable across batches within one eager attempt, but rejection replaces the attempt and decoder.

Streaming retains only mapped data, headers, byte offset, and remaining row limit between requests. Each `read` calls `buildFrame`, which creates new plans and attempts for that chunk. No decoder or inferred candidate list persists between chunks. Within a chunk, `buildIndexedColumn` retries candidates against that chunk's entire indexed range.

The eager batch helper assigns each column to one joined worker. The mapped bytes and immutable record index remain valid until the workers return. Attempts retain typed output across batches; batch record coordinates can then leave scope. `CSVColumnBuilder.column` returns the final typed column and resets the builder.

## Unused null matcher construction

`CSVColumnPlan.conversion` creates `CSVNullMatcher(nullValues)` before switching on type. Integer, double, and date decoders retain it. Boolean uses the original `Set<String>` directly. Both UTF-8 branches also use string null tokens directly through `CSVSmallStringDecoder` or `CSVStringDecoder`. For boolean and UTF-8 conversions, the newly constructed matcher is unused. This is a source-level observation; no build or measurement established whether optimization removes that work.

## Source map

- `Sources/SwiftDataFrame/IO/CSVColumnConversion.swift`, `CSVColumnPlan.init`, `nextCandidate`, `conversion`, `CSVColumnConversion`, and `CSVColumnAttempt`.
- `Sources/SwiftDataFrame/IO/CSVEagerReader.swift`, `read`, `begin`, and batch `append`.
- `Sources/SwiftDataFrame/IO/CSVReader.swift`, `buildFrame`, `buildColumn`, and `buildIndexedColumn`.
- `Sources/SwiftDataFrame/IO/CSVReadCursor.swift`, `read` and stored `Input`.
- `Sources/SwiftDataFrame/IO/CSVColumnBuilder.swift`, `init` and `column`.
- `Sources/SwiftDataFrame/IO/SystemsCSVParser.swift`, `scanBatch` and `countRecords`.
- `Sources/SwiftDataFrame/IO/CSVNullMatcher.swift`, `init`.
