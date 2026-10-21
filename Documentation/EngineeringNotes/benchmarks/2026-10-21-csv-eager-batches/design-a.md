# Scoped eager CSV assembly

## Problem

The eager reader currently indexes every field in the file before it converts any column. The replacement must bound parser metadata to one batch while preserving the exact eager inference contract: the first 1,000 selected data rows admit candidates in `Int64`, `Double`, `Bool`, `Date`, `String` order; an all-null sample chooses `String`; every admitted non-string candidate must validate every selected row; and a failure retries the next candidate admitted by the original sample against original source bytes. Overrides still turn invalid values into nil, `inferTypes == false` still yields strings, and streaming keeps its existing chunk-local inference. The mapped input and final column arrays remain whole-read owners. Only record metadata becomes scoped.

## Usage, caller's view

Public call sites do not change:

```swift
var options = CSVReadOptions()
options.columnTypeOverrides = ["Date": .date32, "power": .float64]
options.columnDateFormats = ["Date": "d/M/yyyy"]

let frame = try await DataFrame(csv: url, options: options)
let power = frame[column: "power", as: Double.self]!.values
```

```swift
var options = CSVReadOptions()
options.inferTypes = false
options.maxRows = 25_000
let frame = try await DataFrame(csv: url, options: options)
```

Streaming retains its existing cursor and one inference decision per public chunk:

```swift
for try await chunk in DataFrame.readCSVStream(
    contentsOf: url, chunkSize: 10_000, options: options
) {
    consume(chunk)
}
```

`CSVReader.read(url:options:)`, `CSVReader.buildFrame`, `CSVReadOptions`, and returned `TypedColumn.values` remain unchanged at the module boundary.

## Recommended shape

Keep the change inside the existing IO module. Delete eager use of `SystemsCSVParser.parseIndex` and the repeated type-specific row loops in `buildIndexedColumn`. Reuse `SystemsCSVParser.scanBatch` and the existing byte parsers, null matcher, date parser, record views, and typed column builder.

The eager coordinator owns the mapped `Data`, headers, selected row limit, replay start offset, and column states:

```swift
private struct EagerCSVPlan {
    let headers: [String]
    let dataStartOffset: Int
    let maximumRows: Int?
    let options: CSVReadOptions
}

private struct InferenceEligibility: OptionSet {
    let rawValue: UInt8
    static let int64  = Self(rawValue: 1 << 0)
    static let double = Self(rawValue: 1 << 1)
    static let bool   = Self(rawValue: 1 << 2)
    static let date   = Self(rawValue: 1 << 3)
}

private struct SampleDecision {
    let eligible: InferenceEligibility
    let sawNonNull: Bool

    var orderedCandidates: [InferredKind] { /* fixed order, then string */ }
}

private enum InferredKind { case int64, double, bool, date, string }

private enum Parsed<Value> {
    case missing
    case value(Value)
    case invalid
}

private protocol CSVScalarCodec {
    associatedtype Value: SupportedType
    static func parse(
        buffer: UnsafeBufferPointer<UInt8>,
        offset: CSVFieldOffset,
        context: inout Context
    ) -> Parsed<Value>
    associatedtype Context
}

private final class ColumnAttempt<Codec: CSVScalarCodec>: @unchecked Sendable {
    let columnIndex: Int
    let name: String
    var context: Codec.Context
    private var builder: CSVColumnBuilder<Codec.Value>
    private(set) var rejected = false

    init(columnIndex: Int, name: String, context: Codec.Context)

    func appendBatch<Records: CSVRecordAccess>(
        buffer: UnsafeBufferPointer<UInt8>,
        records: Records,
        rowCount: Int,
        invalidPolicy: InvalidPolicy
    )

    func finish() -> any AnyColumn
}

private enum InvalidPolicy { case appendNil, rejectCandidate }

private enum ColumnWorker {
    case int64(ColumnAttempt<Int64Codec>)
    case double(ColumnAttempt<DoubleCodec>)
    case bool(ColumnAttempt<BoolCodec>)
    case date(ColumnAttempt<DateCodec>)
    case string(ColumnAttempt<StringCodec>)

    mutating func appendBatch(
        buffer: UnsafeBufferPointer<UInt8>,
        records: CSVRecordIndex,
        rowCount: Int
    )

    var rejected: Bool { get }
    func finish() -> any AnyColumn
}

private struct EagerCSVAssembler {
    let parser: SystemsCSVParser
    let plan: EagerCSVPlan
    let sample: [SampleDecision]
    var workers: [ColumnWorker]
    var finished: [Int: any AnyColumn]

    mutating func collect(buffer: UnsafeBufferPointer<UInt8>) throws -> DataFrame
    mutating func runReplayPass(buffer: UnsafeBufferPointer<UInt8>) throws
    mutating func advanceRejectedWorkers()
}
```

`ColumnAttempt` is a reference owner on purpose. Switching over `ColumnWorker` copies a small reference, not the builder's Array value, so appending cannot trigger a full copy merely because an enum still holds the prior value. Each worker retains one builder for the length of its attempt. A rejected attempt releases that builder before the next one starts. A successful attempt moves its column into `finished`; later replay passes do not touch it.

The enum switch happens once per column per batch. The generic `appendBatch` loop is specialized for its codec and calls no closure or existential for each cell. `Parsed` keeps missing and invalid distinct. Explicit overrides use `.appendNil`; inferred candidates use `.rejectCandidate`. The string codec decodes the original token bytes and applies the existing decoded-string null policy. Numeric codecs keep the existing `CSVNullMatcher` ordering and fallbacks. The inferred date codec uses `Date.parse`; only an explicit date codec owns `CSVDateParser` with `columnDateFormats[name]`.

`CSVColumnBuilder` should gain a zero or estimated-capacity initializer rather than receiving a known total row count:

```swift
internal init(minimumCapacity: Int = 0)
```

Do not count the file first. Swift Array growth supplies amortized linear append cost. An optional estimate may use the first batch's rows-per-byte ratio, capped to a modest value, but correctness and allocation behavior must not depend on it.

## Data flow

`CSVReader.read` maps the file once and keeps that mapping alive through all passes. It calls `scanBatch(maximumRows: 1)` to decode or synthesize headers and record the exact data start offset. `maxRows == 0`, empty input, and header-only input exit at the same boundary as today.

The sample pass starts at `dataStartOffset`, scans at most 1,000 selected data rows in scoped batches, and updates one `SampleDecision` per column. Missing fields, zero-length offsets, and configured decoded nulls do not count as sample values. Eligibility tests are independent and stop only after all four typed candidates fail. This pass stores no field offsets after each batch and never builds output.

The assembler then creates one worker per column. Overrides pick a fixed worker with `.appendNil`. `inferTypes == false` picks `String`. An all-null inferred sample also picks `String`. Other inferred columns pick the first eligible candidate in fixed order.

Each replay pass resets only a byte cursor and selected-row counter to `dataStartOffset`. It repeatedly calls `scanBatch` with the lesser of the private batch row target and remaining `maxRows`, dispatches the resulting batch to unfinished workers, joins all column work, advances by `nextOffset`, then drops the batch. Batch offsets remain relative to the rebased buffer. No offset or compatibility array survives dispatch.

At end of pass, successful workers seal their columns. Failed inferred workers discard their typed owners and advance to the next candidate from their immutable `SampleDecision`. Another replay reads original source tokens from the same mapped `Data`. At most five conversion passes occur, and only columns that still need validation participate in later passes. String is terminal. Headers, quoting, ragged fields, CRLF and permissive EOF remain owned by `scanBatch`; row limits are applied to data records, not headers.

Column work may remain parallel within a batch. One task owns one worker for that dispatch, all tasks join before batch metadata expires, and passes are serial. Mutable date formatter state stays inside its column attempt. Begin with the current column concurrency policy; a worker-count change is a separate measured decision.

`CSVReader.buildFrame` remains the streaming assembly path and can use the same `ColumnAttempt` and codec loops against its already scoped public chunk. It must not adopt eager sampling across chunks or carry candidate state between calls. `CSVReader.inferColumn` remains because JSON calls it.

## Signatures and caller changes

The eager entry point becomes a thin owner:

```swift
static func read(url: URL, options: CSVReadOptions) async throws -> DataFrame {
    // map once, derive plan, sample, collect through EagerCSVAssembler
}
```

The duplicated conversion implementation is replaced by these private operations:

```swift
private static func makePlan(
    buffer: UnsafeBufferPointer<UInt8>, options: CSVReadOptions
) throws -> EagerCSVPlan?

private static func sampleColumns(
    buffer: UnsafeBufferPointer<UInt8>, plan: EagerCSVPlan
) throws -> [SampleDecision]

private static func makeWorkers(
    plan: EagerCSVPlan, sample: [SampleDecision]
) -> [ColumnWorker]
```

Streaming calls a revised batch-local builder with no semantic change:

```swift
internal static func buildFrame(
    buffer: UnsafeBufferPointer<UInt8>,
    records: CSVRecordIndex,
    startRow: Int,
    rowCount: Int,
    headers: [String],
    options: CSVReadOptions
) throws -> DataFrame
```

It derives sample decisions from that supplied range, then runs workers over that same range. Since the complete chunk metadata already exists, failed candidates can replay the range without rescanning bytes. This preserves chunk-local inference and removes the duplicated loops without forcing eager orchestration into streaming.

## Module map

- `CSVReader.swift`: public-entry orchestration, eager plan and assembler, batch-local `buildFrame`, worker dispatch.
- `CSVColumnBuilder.swift`: typed Array ownership and final column creation; add unknown-capacity construction only.
- New `CSVColumnConversion.swift`, if `CSVReader.swift` becomes unwieldy: `Parsed`, codecs, `SampleDecision`, `ColumnAttempt`, and `ColumnWorker`. These form one conversion module because they share candidate and null-policy knowledge.
- `SystemsCSVParser.swift` and `CSVRecordIndex.swift`: unchanged grammar and scoped batch metadata.
- `CSVReadCursor.swift`: unchanged cursor and public chunk boundaries; it continues to call `buildFrame`.

Do not add a public type, cache, thread pool, full-file schema object, count prepass, source-offset index, or legacy compatibility arrays.

## Synthesis decision

The chosen design combines replay waves with reference-owned typed accumulators. Replay waves keep parser metadata bounded and preserve original-token retries. Reference owners solve the Swift Array copy-on-write hazard without exposing an accumulator protocol or allocating a type-erased closure per cell. The conversion enum concentrates the only runtime type dispatch at the batch boundary.

I rejected a row-major multi-type staging buffer. It could scan each row once, but retaining original tokens or decoded strings until schema settles recreates whole-input temporary storage and makes lexical string fallback expensive or incorrect. I also rejected one independent scanner per column. It gives each typed worker a simple loop but multiplies framing work for every column and duplicates quote/header/row-limit policy across workers.

## Tradeoffs accepted

- We accept a 1,000-row sample pass and rare whole-range replay passes in exchange for batch-scoped metadata and exact candidate fallback.
- We accept geometric Array growth without an exact reserve count in exchange for avoiding a full-file count pass.
- We accept one enum switch per column per batch in exchange for concrete, specialized cell loops and explicit ownership.
- We accept retaining the mapped source for the eager read in exchange for stable original-token replay without reopening a mutable path.
- We accept that eager memory remains proportional to returned rows in exchange for preserving `[T?]` column storage and the public API.

## Alternatives considered

### Pass-owned accumulators

Each replay pass could own value-type builders in local arrays and return successes. This looks simpler, but enum extraction can retain a second Array reference and trigger full copies during append. Avoiding that trap would require fragile move discipline throughout orchestration. Reference-owned attempts make the ownership rule local.

### Per-column complete scans

Each column could sample and validate itself from the mapped source. Typed loops would be simple, but every column would repeat CSV framing and structural scans. It also scatters row-limit and malformed-record behavior. The interface is shallow because callers inside `CSVReader` must coordinate parsing and conversion policy repeatedly.

### Retained token batches until schema settles

A coordinator could parse the file once and retain token ranges or copied strings for retry. This hides replay CPU but restores metadata proportional to all fields or string storage proportional to input. It violates the reason for the change.

## Risks and checks

- Does rebasing the input buffer for every `scanBatch` preserve `nextOffset` and compact-offset fallback for records larger than the private batch target?
- Does cancellation between passes and batches release rejected builders without retaining mapped-buffer borrows?
- Does the current `concurrentPerform` arrangement guarantee that one worker is never mutated by two tasks in the same dispatch?
- Do characterization tests confirm zero-length sample fields remain skipped even when `""` is absent from `nullValues`, while conversion still follows the existing null policy?
- Do late `1` then `true`, late integer-to-double, exact large integers, numeric-looking nulls, quoted fields, ragged rows, CRLF, EOF, headers and `maxRows` match the full-index control exactly?
- Does allocation profiling show no whole-column copy when a batch appends to an existing worker?

## Next implementation step

First extract `Parsed`, specialized codecs, and the reference-owned `ColumnAttempt` from the repeated `buildIndexedColumn` loops, then prove exact behavior against the current full-index reader before changing eager orchestration.
