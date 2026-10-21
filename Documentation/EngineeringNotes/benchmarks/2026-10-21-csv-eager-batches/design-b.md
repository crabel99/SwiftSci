# Eager CSV: typed column groups with replay sweeps

## Problem

The eager reader retains offsets for every field to give column workers random access. The replacement must retain only one batch of offsets. It must preserve first-1,000-row candidate eligibility and validate candidates against all selected rows. A late failure must replay original tokens; it cannot promote converted numbers. This design uses concrete typed column groups rather than an enum holding each column's growing output.

## Usage

Public calls and storage stay unchanged:

```swift
let frame = try await DataFrame(csv: file, options: options)
let integers = frame[column: "id", as: Int64.self]!.values
```

A streaming caller still gets inference within each requested public chunk:

```swift
for try await chunk in DataFrame.readCSVStream(
    contentsOf: file, chunkSize: 10_000, options: options
) { consume(chunk) }
```

Internally the reader obtains headers and samples without a full-file prepass, then delegates whole-file assembly:

```swift
return try mappedData.withUnsafeBytes { raw in
    let source = raw.bindMemory(to: UInt8.self)
    return try CSVReader.collectBatches(source: source, options: options)
}
```

Streaming's existing `buildFrame` uses the same prepared decoders and generic append loop, but with a fresh local group for one chunk. It does not acquire whole-file schema state.

## Shape

Pseudocode; bodies are not implementations:

```swift
// Five eligible flags, fixed once from the original sample.
struct CSVTypeCandidates {
    let eligible: /* compact ordered candidate set */
    func next(after: CSVConversionKind?) -> CSVConversionKind
}

// A parser result distinguishes invalid from the configured null value.
enum CSVFieldValue<Value> { case value(Value), missing, invalid }

protocol CSVFieldDecoder {
    associatedtype Value: SupportedType
    mutating func decode(
        buffer: UnsafeBufferPointer<UInt8>, offset: CSVFieldOffset
    ) -> CSVFieldValue<Value>
}

// Concrete decoders hold prepared null/date state; no any CSVFieldDecoder.
struct CSVIntegerDecoder: CSVFieldDecoder { /* existing numeric policy */ }
struct CSVDoubleDecoder: CSVFieldDecoder { /* existing numeric policy */ }
struct CSVBooleanDecoder: CSVFieldDecoder { /* decoded null/string policy */ }
struct CSVInferredDateDecoder: CSVFieldDecoder { /* Date.parse */ }
struct CSVExplicitDateDecoder: CSVFieldDecoder { /* CSVDateParser */ }
struct CSVStringDecoder: CSVFieldDecoder { /* decoded null/string policy */ }

struct CSVTypedSink<Decoder: CSVFieldDecoder> {
    let ordinal: Int
    let name: String
    let rejectInvalid: Bool
    var decoder: Decoder
    var values: CSVColumnBuilder<Decoder.Value>
    var rejected: Bool

    // Dispatch on rejectInvalid once outside the specialized cell loop.
    mutating func append<Records: CSVRecordAccess>(
        buffer: UnsafeBufferPointer<UInt8>, records: Records,
        startRow: Int, rowCount: Int
    ) // not implemented
}

struct CSVTypedGroup<Decoder: CSVFieldDecoder> {
    private var columns: [CSVTypedSink<Decoder>]
    mutating func append<Records: CSVRecordAccess>(
        buffer: UnsafeBufferPointer<UInt8>, records: Records,
        startRow: Int, rowCount: Int
    ) // Mutate columns[index] in place; never copy a sink out.
    mutating func finish(into: inout [(any AnyColumn)?])
    func failedOrdinals() -> [Int]
}

struct CSVEagerAssembly {
    // Concrete properties, not an existential array of groups.
    var integers: CSVTypedGroup<CSVIntegerDecoder>
    var doubles: CSVTypedGroup<CSVDoubleDecoder>
    var booleans: CSVTypedGroup<CSVBooleanDecoder>
    var inferredDates: CSVTypedGroup<CSVInferredDateDecoder>
    var explicitDates: CSVTypedGroup<CSVExplicitDateDecoder>
    var strings: CSVTypedGroup<CSVStringDecoder>
    var completed: [(any AnyColumn)?]
    let candidates: [CSVTypeCandidates]
    // Type choice is column-level; original eligibility remains immutable.
}

extension CSVReader {
    static func collectBatches(
        source: UnsafeBufferPointer<UInt8>, options: CSVReadOptions
    ) throws -> DataFrame // not implemented
}
```

The coordinator scans headers once and gathers at most the first 1,000 selected data rows. Sampling retains the exact current rules, including skipping zero-length fields regardless of the configured empty-token null policy. All-null samples select String. Explicit overrides bypass inference and invalid values become nil.

Build the first groups from that fixed sample. Append the retained sample metadata, discard it, then advance through scoped `scanBatch` results. For each batch, call the six concrete groups. Each group iterates its columns and runs a generic specialized row loop against flat/compact views. Missing ragged fields append nil. No type switch, closure or existential sits inside a cell loop.

On an inferred invalid token, discard that column's partial builder immediately and mark its sink rejected; do not append further values to it. Other sinks complete normally. At the end, move successful columns into their ordinal output slots. Rebuild groups only for failed ordinals, selecting their next originally eligible candidate, and rescan the same borrowed source range. Each replay sweep frames once for all pending columns, rather than once per failed column. Repeat until all output slots are filled. String terminates the sequence. At most five conversion sweeps occur for any column, and there is no unconditional count/inference sweep. Full-file schemas are unchanged by internal batch boundaries.

The source owner is the original mapped `Data`. Save only the data-start byte offset and the selected-row limit; do not reopen the pathname or keep source-wide record offsets. Replay starts from that byte offset and applies the same row budget. Header framing uses the existing scanner so quoted newlines, CRLF, extra fields and permissive EOF behavior stay authoritative. Batch records and pointer views expire before scanning the next batch. Mapping borrow never crosses a suspension.

Array ownership is explicit. append mutates `columns[index]` through Swift's in-place modify access, not `for var column in columns`, associated-value extraction or a returned sink snapshot. No observer retains a copy of the group array. Failed builders are replaced with empty builders, which releases their accumulated buffers. Completed outputs are never appended again. This removes the enum-associated-Array copy trap. If implementation needs to extract an owning sink, revise the shape rather than relying on optimizer CoW elimination.

The public interface stays unchanged. CSVReader owns schema, source replay and output assembly. The generic decoder boundary consolidates current explicit/inferred conversion loops and their invalid/null distinction; SystemsCSVParser remains the record grammar owner. Only CSVReader plus one internal conversion file need describe this flow. `inferColumn` stays for its JSON caller. No new public schema mode, storage type, cache, scheduler or thread pool is introduced.

## Synthesis decision

Pending parent comparison. This candidate's distinguishing feature is a small fixed collection of concrete typed groups and shared replay sweeps, instead of an array of per-column enum accumulators or a separate scan per column.

## Tradeoffs accepted

- Accept serial batch framing and column-group iteration initially in exchange for bounded field metadata and straightforward exclusive output ownership. Existing column parallelism must not be claimed preserved; benchmark CPU, latency and RSS before adoption.
- Accept rescanning complete records for failed columns in exchange for retaining original tokens without a source-wide index. Grouping failures into sweeps limits repeated framing when many columns fail together.
- Accept geometric final-array growth because row count is unknown without a prepass. Peak RSS must include growth reallocations and all completed columns retained during replay.
- Accept six internal concrete group properties in exchange for no per-cell erased dispatch and no enum-associated output extraction. Date modes are separate because inferred Date.parse and explicit prepared formats have different semantics.
- Accept small column-index/candidate arrays proportional to column count; these are schema metadata, not compatibility token arrays.

## Alternatives considered

Per-column range cursors make the generic conversion routine especially small and eliminate heterogeneous state, but rescan every record for every column even with complete schemas. That multiplies structural CPU work by width and is a poor default for this resource-first objective.

Per-column enum accumulators hide heterogeneous builders behind one array, but require careful move-out/move-back mutation to avoid CoW, a sentinel state or reference owners. This typed-group design encodes the concrete storage shape directly and permits one specialized append implementation.

A full-file count/sample pass permits exact reservations, but adds mandatory structural work even for declared schemas and maxRows-limited reads. Retain it only as a measured alternative if geometric output growth dominates real workloads.

## Open questions and risks

- Will six group traversals versus source-column order lose meaningful cache locality for wide mixed schemas? Measure a wide mixed fixture as well as narrow reference inputs.
- Will removal of column concurrency exceed latency constraints even when aggregate CPU and RSS improve? Preserve the immutable full-index control and report all three metrics.
- Can generic decoder methods compile to direct specialized calls under the existing Release build? Inspect emitted specialization or a focused profiler sample; do not infer this solely from generic source spelling.
- Does geometric array growth consume more peak memory than the removed metadata on narrow numeric data? If so, compare bounded capacity estimates from observed batches, without a new full count pass.

## Next implementation step

Extract the existing parsing/null policies into concrete decoders and one specialized append loop, prove unchanged current reader results, then add typed-group scoped collection and late-candidate replay fixtures.
