# Candidate A: eager typed operations with bounded intermediates

Design sketch only. No production changes. Grounding is in [CSV](csv-grounding.md) and [grouping](group-grounding.md), plus the current numeric permutation implementation in TypedColumn.swift. Architect phases Ground and Sketch are complete for this candidate. Synthesis, implementation and possible redesign belong to the parent task.

## Usage

The caller continues to use the existing eager DataFrame API. Each call returns a complete value with current null, ordering and numerical semantics. No new execution mode or memory-lifetime rules reach callers.

```swift
import SwiftDataFrame

let observations = try await DataFrame(csv: inputURL)
let byOutput = try observations.sortBy("output", ascending: false)
let totals = observations.groupBy("site", "year").sum()
let checkedTotals = try observations.groupBy("site", "year").sumChecked()
```

A filter/sort/group pipeline remains explicit. Optimizing its individual operations must preserve the first-seen group order and ordered floating arithmetic induced by the sort. The implementation does not remove that sort merely because group membership is unchanged.

## Problem

The three measured costs have related causes but different contracts. CSV retains a separately reserved field array for every row. Composite grouping repeatedly hashes typed prefixes even for small dense integer domains. Numeric sorting uses comparison sorting over cached values and row indices. The solution should reduce allocation and per-element overhead while preserving full-width integers, stable equal-key ordering, missing values, exact checked sums, and compensated sums. Apple Silicon is the target; API compatibility with the current public column representation remains useful independently of any Intel support question.

## Shape

Keep each algorithm with the code that owns its semantics. Share the concept of exact typed values and row positions; do not introduce a universal execution protocol merely because all three algorithms scan arrays. This keeps interface depth high: existing read, sort and group calls hide representation, budget, dispatch and fallback decisions.

The sketches below show intended signatures and invariants, not compilable patches.

### CSV field ownership

Inside `IO/SystemsCSVParser.swift`, add one internal flat ragged index:

```swift
internal struct CSVFieldIndex: Sendable {
    private(set) var fields: [CSVFieldOffset]
    private(set) var rowStarts: [Int] // Starts at 0; includes terminal offset.

    var rowCount: Int { /* rowStarts.count - 1 */ }
    func field(row: Int, column: Int) -> CSVFieldOffset? {
        /* nil if this ragged row lacks the requested field */
    }
    func row(_ row: Int) -> ArraySlice<CSVFieldOffset> {
        /* fields[rowStarts[row]..<rowStarts[row + 1]] */
    }
}

extension SystemsCSVParser {
    internal func parseIndex(buffer: UnsafeBufferPointer<UInt8>) -> CSVFieldIndex {
        /* Existing scanner grammar, appending to flat fields and rowStarts. */
    }
    // Existing public API retained, using the same scanner.
    public func parse(buffer: UnsafeBufferPointer<UInt8>) -> [[CSVFieldOffset]] {
        /* Materialize rows from parseIndex only for public legacy callers. */
    }
}
```

The scanner alone constructs valid boundaries. File and stream readers consume this index directly. Internal column conversion takes the index and byte slice while synchronously joined workers stay inside `Data.withUnsafeBytes`. No pointer escapes the closure. This is boundary discipline applied to mapped input, and it removes one existing lifetime violation.

Ragged rows retain distinct boundaries; a rectangular multiplication would change their behavior. The measured field stride is 24 bytes. Three fields plus an eight-byte row boundary need about 80 bytes per row, before capacity slack, compared with roughly 408 bytes of reserved field payload per row in the current scanner. Both forms still grow with file size. True incremental tokenization is a separate design.

A later private ASCII null matcher may bypass String construction for ordinary numeric tokens. Escaped or non-ASCII custom null tokens use the existing normalization path. Implement the flat index first to attribute its effect independently. Keep integer-overflow and trailing-delimiter fixes in separate regression commits.

### Integer group refinement

Keep `GroupIndex`, typed equality and reductions in `Core/GroupedDataFrame.swift`. Add a checked descriptor and bounded refinement helper:

```swift
private struct BoundedIntegerDomain<T: FixedWidthInteger> {
    let lower: T
    let validSlotCount: Int
    let nullSlot: Int?    // Distinct from all valid integer values.
    var slotCount: Int { /* validSlotCount plus optional null slot */ }

    init?(values: [T?], maximumSlots: Int) {
        /* Reporting-overflow span, exact conversion, fixed capacity bound. */
    }
    func slot(for value: T?) -> Int {
        /* Offset proven in range by construction, or nullSlot. */
    }
}

private func refineBoundedIntegerGroups<T: FixedWidthInteger>(
    prefixes: GroupIndex, values: [T?], maximumTableBytes: Int
) -> GroupIndex? {
    /* Domain scan, checked prefixCount * slotCount, then direct lookup.
       Return nil before allocation if unsupported or over budget.
       Traverse input order and assign IDs with GroupIndex.append. */
}
```

A failed applicability check selects existing typed dictionary refinement; it is not a data error. The first composite integer column reuses the current single-key bounded builder. At each later component, check the domain product and byte budget before allocating. Null consumes its own slot. No conversion through Double, wrapping arithmetic, or unchecked Cartesian product is allowed.

For the existing two-key fixture, 9,700 native Int lookup slots occupy about 77.6 KB. The algorithm still makes a range pass and an ID pass, but replaces per-row hash lookup with checked-by-construction addressing. It remains adaptive to sparse/extreme keys through the existing fallback. Parameterize the private budget for prototypes; select one conservative constant only after measuring domain width and input size, rather than exposing a public tuning option.

Keep output key formatting, ordinary sum semantics and sumChecked unchanged. Do not add persistent caches to GroupedDataFrame in this candidate. AnyColumn does not require immutable reference snapshots, and eager caching would change when groupBy pays its cost.

### Stable numeric permutations

Keep `AnyColumn.sortedIndices(ascending:)` and DataFrame.gathered unchanged. Implement one private numeric candidate below TypedColumn's existing dispatch:

```swift
private func stableRadixIndices<T>(
    values: [T?], ascending: Bool,
    orderedBits: (T) -> UInt64?
) -> [Int]? {
    /* Return nil for a NaN or rejected size/memory gate.
       Build ordered keys and row positions for non-null values.
       Stable counting passes over eight-bit digits.
       Append null row positions in original order. */
}

private func integerSortBits(_ value: Int64) -> UInt64 {
    /* UInt64(bitPattern: value) ^ (1 << 63) */
}
private func floatingSortBits(_ value: Double) -> UInt64? {
    /* NaN -> nil; canonicalize both zeros; negative bits inverted,
       nonnegative bits xor sign bit. */
}
```

Use concrete dispatch so Int32, Int64, native Int, Float and Double have exact type-appropriate transforms. Float widening to Double is exact but requires measuring extra key width; a 32-bit variant may be preferable. Descending order reverses the numeric key mapping before stable passes, not the final row array. That preserves original order for equal keys and signed-zero ties. Nulls remain last. NaNs route to the current comparison path, whose behavior is already part of the production contract.

This is a prototype candidate, not a chosen replacement. A naive two-buffer radix implementation holds two key arrays and two row arrays, about 32 bytes per non-null row, plus null indices and final output. Eight key-byte passes can move more data than an adaptive comparison sort on nearly sorted input. Benchmark thresholds, duplicate-heavy inputs and existing runs. Retain comparison sorting if radix does not win on the target workload or memory budget. Test integer extrema and both directions in Release because this branch already worked around a compiler-sensitive comparator.

No new public types are required. CSV's index is internal because two reader paths use it. Grouping and sorting helpers remain private. The public legacy CSV wrapper serves a real compatibility boundary, rather than creating a second parser.

## Synthesis decision

Pending parent comparison with the streaming/lazy candidate. Recommend this candidate as the near-term production base if phase profiles show its removed allocation and hash work dominate. Accept only measured components; a useful CSV or grouping improvement does not justify an unmeasured radix rewrite.

## Tradeoffs accepted

- We accept whole-file CSV offsets in exchange for a contained change that preserves current file and stream behavior. This does not claim bounded-memory parsing.
- We accept optional-array storage and eager gathers in exchange for a focused production patch. Compact storage and reusable selections remain viable on their branch.
- We accept range pre-scans and a bounded lookup table in exchange for eliminating hashes on suitable integer domains. Existing dictionary refinement handles the rest.
- We accept a comparison fallback in exchange for preserving NaN behavior and good performance on workloads where radix traffic loses.
- We accept repeated group construction across separate aggregate calls in exchange for avoiding a premature cache lifetime contract.

## Alternatives considered

A streaming parser plus deferred query plan can bound temporary input memory, push projections into parsing and avoid intermediate gathers. It hides more execution complexity, but requires clear schema promotion, cancellation, buffer ownership and ordering contracts. That is a stronger long-term shape for the compact-storage branch, especially repeated or wide pipelines.

A universal row-index executor for read/filter/sort/group would share signatures while leaking unrelated CSV, equality and ordering policies into one abstraction. Reject it unless actual duplicated code establishes a stable common operation. Shared vocabulary is sufficient here.

A custom composite hash table may improve high-cardinality grouping with fewer full-column passes. It needs representative-row equality, table-growth tests and probe controls. Retain it as a measured alternative to bounded/refined grouping, not part of the initial implementation.

## Open questions and risks

- Which input size and table-byte limits yield repeatable wins across low, skewed and near-row-count cardinality without excessive allocation?
- Does radix beat the current stable comparison sort once final gathering and destruction are included, and does its additional scratch memory remain acceptable?
- Should documented inherited CSV parsing defects be corrected in this branch before measuring, so the baseline and candidate process the same complete records?
- Will later compact storage expose a column-owned row-selection operation, allowing these algorithms to reuse exact representations without adding public execution controls?

These are measurement and design questions for the ongoing task, not reasons to stop for user approval.

## Next implementation step

Correct the benchmark's Kiraa key extraction, then build the flat CSV index and bounded integer refinement as independent tested prototypes against the existing public API before selecting a sorting algorithm.
