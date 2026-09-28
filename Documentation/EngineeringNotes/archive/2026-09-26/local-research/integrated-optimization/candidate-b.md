# Candidate B: bounded ingestion and delayed materialization

This is a competing design, not an implementation claim. It is grounded in [CSV source tracing](csv-grounding.md), the current optional-array column contract, and the existing lazy executor, which presently materializes each operation. The candidate belongs mainly on `codex/compact-column-storage`; two ingestion pieces can land earlier without changing public storage.

## Usage, caller's view

Existing eager callers keep their code and receive ordinary `TypedColumn<T>` values:

```swift
let frame = try await DataFrame(csv: url, options: options)
let sorted = try frame.sortBy("value", ascending: false)
let groups = sorted.groupBy("site", "period")
```

Existing streaming callers keep receiving independent DataFrames that remain valid after the source closes:

```swift
for try await batch in DataFrame.readCSVStream(contentsOf: url, chunkSize: 10_000) {
    consume(batch)
}
```

An experimental extension to the lazy API would let one query retain a selection and permutation until its result is requested. This is proposed syntax, not functionality that exists today:

```swift
let result = try await DataFrame.lazyCSV(url: url, options: options)
    .whereColumn("value", .greaterThan(500))
    .sortBy("value", ascending: false)
    .groupBy("site", "period")
    .sum("value")
    .collect()
```

The user never coordinates file mappings, validity buffers, factorization or gather operations. The existing closure filter remains supported as an explicit materialization boundary because arbitrary closures cannot be analyzed for column dependencies or reordered safely.

## Problem

A fast individual CSV parser, sorter and grouper can still perform unnecessary work when composed. Today, eager filtering gathers every column, sorting gathers again, and grouping then scans the copied results. Ingestion holds a whole-file token grid before building eager optional arrays. The candidate reduces the total number of materializations across a query rather than only making each materialization faster.

The load-bearing compatibility constraint is `TypedColumn.values: [T?]`, a public stored property. Changing it to a computed compact-buffer decode would keep much source syntax but would change cost and storage behavior. Returning different column implementations could also break clients that cast columns to `TypedColumn<T>`. This candidate therefore does not silently swap the public eager representation.

## Shape

Keep one private execution owner, `ExecutionTable`, behind the lazy evaluator. It owns immutable typed column storage, a row domain and per-execution group metadata. CSV scan state owns the mapping and partial record; it emits bounded batches. A selection or permutation maps logical rows directly to immutable physical rows. Composition flattens that mapping rather than creating nested views.

Sketch, not compiled code:

```swift
// Private to SwiftDataFrame execution.
struct ExecutionTable {
    let columns: ExecutionColumns
    let rows: RowDomain
    func selecting(_ condition: TypedCondition) -> ExecutionTable
    func sorted(by key: ColumnID, ascending: Bool) -> ExecutionTable
    func grouped(by keys: [ColumnID]) -> ExecutionGroups
    func materialized() throws -> DataFrame
}

enum RowDomain {
    case all(count: Int)
    case positions(OwnedRowPositions)
}

struct PrimitiveBuffer<T> {
    let values: OwnedBuffer<T>
    let validity: Validity
}

enum Validity {
    case allValid(count: Int)
    case bitmap(OwnedBitmap)
}

struct ExecutionGroups {
    let table: ExecutionTable
    let rowGroupIDs: OwnedGroupIDs
    let representativeRows: OwnedRowPositions
    func sum(_ value: ColumnID) -> AggregateResult
}

struct CSVScanState {
    mutating func nextBatch() throws -> ParsedBatch?
}
```

`OwnedRowPositions` and `OwnedGroupIDs` have separate types because a group number cannot serve as a row index. Their constructors validate external or computed boundaries once; hot loops operate within that invariant. `PrimitiveBuffer` owns value and validity lengths together. A null bit is separate from every valid value, including NaN, zero, and integer extrema.

Do not make a public storage protocol from this sketch. Dispatch concrete type once per column and keep the representation switch in `ExecutionColumns`. A public `AnyColumn` adapter belongs only at materialization. That avoids a new per-value virtual call and prevents CSV, grouping and sorting from independently deciding bitmap rules.

CSV numeric columns build typed values in bounded batches. With a fixed schema, each field parses directly into its final primitive buffer. With current inferred semantics, the scanner buffers the initial sample, chooses the same type policy, then continues; preserving current behavior means later conversion failures still follow the current policy until a separate inference correction lands. An improved promotion policy must be explicit. Stream batches cannot retroactively change the type of a batch already delivered.

Sorting returns a stable row permutation. Equal keys retain their order in the incoming logical row domain. Null placement and present NaN ordering retain the established comparator. Exact integers never become Double keys. A comparison sort or radix specialization can implement this contract, but the representation change does not require choosing radix now.

Grouping resolves typed keys against the row domain and assigns first-seen IDs. Dictionary or bounded-domain algorithms remain internal alternatives. Factorization caches live only within an immutable execution and identify both column storage and row domain. Reusing a code array from a different selection would be wrong. Floating zero and NaN canonicalization follows current grouping identity, with null distinct. Output labels keep the current public representation when materialized.

Source grounding: [public column values](/Users/LOCAL_USER/Documents/src/SwiftSci/Sources/SwiftDataFrame/Columns/TypedColumn.swift:19), [eager storage](/Users/LOCAL_USER/Documents/src/SwiftSci/Sources/SwiftDataFrame/Core/DataFrame.swift:10), [current lazy execution](/Users/LOCAL_USER/Documents/src/SwiftSci/Sources/SwiftDataFrame/Lazy/LazyDataFrame.swift:61), [AnyColumn protocol](/Users/LOCAL_USER/Documents/src/SwiftSci/Sources/SwiftDataFrame/Columns/AnyColumn.swift:1).

## Module boundary and lifetime

- CSV code owns dialect interpretation, field boundaries, schema policy, malformed-input reporting and byte-pointer lifetime. Consumers receive owned batches, never dangling mapped slices.
- Execution storage owns immutable values, validity and row mapping. Selection, sorting and grouping consume its concrete buffers. They do not know CSV syntax.
- `collect()` owns conversion into current public DataFrame/TypedColumn results. Eager APIs continue to use their existing kernels unless a measured benefit justifies routing a complete operation through execution storage.

A row view retains its underlying buffers. A one-percent selection can therefore keep the whole input alive. A planner can choose to gather when that reduces retained memory, but the first prototype should expose that cost in measurements rather than hide a guessed threshold. No shared global caches or mutable dictionaries are needed.

Bounded token batches do not by themselves guarantee bounded streaming memory: the current `AsyncThrowingStream` can queue yielded DataFrames. Backpressure requires a pull-driven producer or a documented buffering contract that never drops rows. That API/lifetime issue belongs in the experimental stream work, not in a flat-index patch.

## Synthesis position

Candidate A, flat ragged offsets plus eager typed columns and bounded grouping specialization, should be the base for the next production optimization. It preserves current ownership and public behavior and attacks a measured allocation cost. Candidate B is a long-term architecture to test on the compact-storage branch. Its value depends on reducing whole-query allocation enough to compensate for indirect gathers and final materialization.

Adapt bounded field batches and correct mapped-pointer scope from B when the production scanner can retain existing semantics. Do not graft selection views into the eager `TypedColumn` API as an incidental performance fix.

## Tradeoffs accepted

- We accept indirect access through row IDs in exchange for avoiding intermediate copies across several operations. It can lose on dense sequential scans and isolated operations.
- We accept one final optional-array conversion to preserve public eager columns. Savings must cover that cost.
- We accept private execution-specific types in exchange for hiding ownership and validity rules from users. We do not accept a wrapper layer that merely forwards each eager operation and adds no retained-work benefit.
- We accept retained base-buffer memory for views. Benchmarks must include low-selectivity queries and long-lived results.
- We accept stable sorting work when a later operation consumes its order. Grouped floating sums can depend on input order, so removing a sort before aggregation is not automatically valid even when only aggregate values are returned.

## Alternatives considered

Direct streaming into current `[T?]` builders reduces token memory and preserves public types. It cannot avoid later filter/sort copies, but is a viable production follow-on after the flat scanner.

Changing `TypedColumn` itself to compact storage would let all eager operations benefit, but its public `.values` property and client casts make conversion/caching behavior observable. This requires an explicit compatibility design rather than a concealed implementation substitution.

GPU parsing or sorting is not selected. Unified memory removes some transfer requirements but not command, synchronization or representation costs. No evidence here supports an end-to-end win over CPU kernels.

## Open questions and risks

Can the measured compact-buffer benefit survive final `[T?]` materialization on actual SPL query chains? How much original storage remains live for sparse selections? Should inference changes become an explicit schema mode? Can typed lazy predicates be added without exposing private plan representation through the existing public `QueryPlan`? Are users relying on the concrete type of columns returned by streaming ingestion?

These questions can be resolved through read-only client searches and isolated prototypes before expanding the production API. None blocks Candidate A.

## Next implementation step

On the compact-storage branch, prototype the existing CSV → filter → stable sort → group workload with private owned buffers and one flattened row permutation, compare full values and order against production, and measure total time, peak memory, retained memory and final materialization cost separately.
