# Eager CSV batch grounding

Source inspected at `dba26e1562503e1594194250d914327830d8f58d` in `/private/tmp/swiftsci-csv-scoped-simd-20261021`. This is a source trace, not new measurement or a proposed implementation.

## Existing callers and ownership

`CSVReader.read` maps one `Data`, borrows its bytes synchronously, calls `SystemsCSVParser.parseIndex` for the complete file, decodes headers, then converts columns. `maxRows` limits conversion after indexing. `buildFrame` joins `DispatchQueue.concurrentPerform` before the borrow ends. Workers read immutable bytes/index and write disjoint column slots. Returned `TypedColumn` arrays own values independently of the mapping.

`CSVReadCursor` already owns the source between streaming requests. It frames one header row, then calls `scanBatch` on a rebased byte range for each public chunk. Each batch contains relative field offsets and `nextOffset`. It calls the same `CSVReader.buildFrame`; inference therefore applies independently to each public chunk. Do not change that schema contract while changing eager assembly.

`SystemsCSVParser.scanBatch` is the reusable framing operation. It scans complete records, normally uses compact offsets and retries full-width offsets when necessary. Its SIMD scanner checks cancellation between bounded search windows. It preserves current quote, CRLF and permissive EOF behavior. A row target is not a byte or RSS cap. A wide row or long field can exceed ordinary scratch expectations. The public `SystemsCSVParser.parse` still requests a full offset grid and must remain supported.

## Conversion contract

`buildColumn` selects borrowed flat/compact record access once, then calls generic `buildIndexedColumn`. That function combines inference selection and conversion. It repeats nearly identical append loops for explicit types, inference candidates and final text. Those loops are the principal subtraction opportunity. Existing byte parsers, null matcher, prepared date parser and typed builder should retain their responsibilities.

Explicit overrides take precedence over `inferTypes`. Integer widths produce `Int64`; floating widths produce `Double`. Invalid explicit conversions become nil. Explicit dates use `CSVDateParser` and the configured format. Inferred dates use `Date.parse`; configured date formats do not affect inference. Text and Bool use decoded-token null matching. Numeric parsing checks numeric-looking null tokens before its byte fast path when needed, then falls back to String parsing. Reuse that exact policy.

For inferred eager columns, the first `min(totalRowsToRead, 1000)` rows determine eligible candidates. Missing fields and zero-length offsets are skipped. Zero-length offsets are skipped even if the caller removed the empty token from `nullValues`. Configured decoded null strings are skipped too. The remaining sample independently tests Int64, Double, Bool and Date. Sampling can stop once all four fail.

Candidates are attempted in order Int64, Double, Bool, Date, then String. A candidate must convert every selected row. A missing field or configured null remains nil; any other failed conversion rejects the candidate. Only candidates admitted by the original sample may be attempted. The sample is not updated after a late failure. A sample containing no non-null value forces the whole column to String, even when later rows are numeric.

A late `true` after a sample of `1` values can require Int64 failure, Double failure, then Bool success. A generic Int-to-Double-to-String promotion chain would silently change behavior. Final text must decode original source tokens, preserving lexical forms such as leading zeros and integers beyond exact Double precision. Converted values cannot reconstruct these tokens.

## Assembly boundary and state risks

The next change concerns eager orchestration and conversion state, not public `DataFrame` storage. `CSVColumnBuilder<T>` owns `[T?]`, tracks null count and currently receives an exact total-row capacity. Scoped eager assembly will not know that capacity without a count pass. An unconditional full-file count/inference pass is additional work, not an established requirement. Compare its cost explicitly if considered.

One retained mapped source can support replay without reopening a mutable pathname. Batch metadata and borrowed views must expire before advancing or suspending. Keep completed columns while replaying a failed column, and account for those retained output arrays in the peak memory result. Final eager output is inherently proportional to all selected rows.

An enum containing typed builders needs careful mutation. Extracting an associated builder into a local variable while the enum still retains the same Array can trigger a full copy on append. Repeated whole-output copies would erase the metadata savings. Likewise, per-cell type-erased closure dispatch can replace known concrete inner loops with overhead. Candidate implementations should show their mutation ownership and dispatch point explicitly.

A prepared date parser contains formatter state. It may belong to one worker/column; sharing mutable formatter state across concurrent workers is not justified by the current design. `CSVNullMatcher` can be prepared per column/read without rebuilding it per appended batch. Invalid conversion must remain distinguishable from missing data for inferred candidates.

`CSVReader.inferColumn` has a production JSON caller. It cannot be deleted just because CSV conversion moves. The separate whole-String CSV parser has different ragged-row handling and is not an independent oracle for all file-reader behavior.

## Verification targets

Characterize sample boundaries, all-null/empty sample behavior, late Bool promotion, late Double promotion, failed-candidate replay, original text preservation, exact Int64 values, numeric-looking nulls and explicit failure-as-null. Exercise headerless/ragged/quoted/CRLF/EOF data, `maxRows`, empty/header-only files, and rows crossing internal batches. Internal batches must not alter eager whole-column types or streaming public-chunk types.

Keep the current full-index reader as the immutable CPU/RSS comparison control. Measure complete loads and independent native-value validation. Report CPU work, elapsed time and peak/held RSS separately. More scanning on rare replay paths may be an acceptable measured tradeoff, but it cannot be hidden behind a smaller index or faster elapsed result.

Approved strategy owner: `/Users/crabel/Library/Caches/SwiftSci/engineering-evaluation-20261018/Documentation/EngineeringNotes/research/2026-10-21-csv-ingestion-strategy.md`, particularly "Schema and replay", "Memory, demand and hardware", and "Subtraction and compatibility work".
