# Compact storage, mutation, and Apple silicon constraints

Research date: 2026-09-26. Source checkout: `/Users/crabel/Documents/src/SwiftSci`, commit `4c5bb953547ba5d84c7fd86bf868b1680c5f1811`. Installed compiler reports Apple Swift 6.4, arm64. This note reviews code and primary documentation; it makes no new benchmark claims and changes no production code.

## Finding

A fixed-width compact numeric column can support cheap point updates. With exclusive ownership, changing a present `Double` needs one value store; changing its validity also modifies one bitmap word and the cached null count. There is no inherent need to rebuild a column or decompress anything. The expensive cases are shared snapshots that require copying, growth beyond capacity, physical insertion or deletion, maintaining sorted order, variable-length payload replacement, and synchronization with outstanding consumers.

Our prototype is compact, not compressed. It stores ordinary fixed-width `Double` values and validity words. Arguments about expensive updates in compressed, clustered database storage do not transfer wholesale to this representation. The design question is which access and mutation guarantees we promise to callers.

## What the existing code establishes

- `Sources/SwiftDataFrame/Columns/TypedColumn.swift:5` defines a value type. Its public `values: [T?]` at line 21 and cached null count are immutable. Its initializer taking `[T]` converts all entries to optional values. `nonNullValues` at line 329 materializes another array. A new compact representation must migrate these consumers, not add a hidden conversion before every operation.
- `Sources/SwiftDataFrame/Core/DataFrame.swift:647` gathers into new columns. `mapColumn` at line 707 constructs a new values array. Current users receive functional transformations, not a mutable shared table.
- `Benchmarks/CompactStorage/results/20260926T021523Z/main.swift:22` defines `PackedColumn` with immutable `[Double]` plus `[UInt64]`. Empty validity means all present. The prototype constructs a dense Float batch, normalizes values, imputes missing entries as zero, and calls `cblas_sgemv` at line 230. It therefore exercises an important table-to-matrix path, but does not implement mutation, snapshots, external leases, or asynchronous device access.
- The later storage experiment uses the same basic representation. Its recorded 1,728 cases demonstrate lower resident storage, but bitmap/block selection and packed filtering did not win broadly. The optional-to-packed-to-optional round trip was slower in every million-row case. These are standalone prototype results, not production API timings. See [recorded report](/Users/crabel/local-ai/spl/swiftsci/filter-optimization/storage-experiment/REPORT.md).
- `Sources/SwiftML/Core/MLP.swift:19` already has flat row-major mutable `[Double]` weights. `LayerAdamState` at line 43 owns first and second moments. Lines 281–286 update moments and weights in place. Lines 357 and 705 save best-layer snapshots through array value semantics. A storage rewrite must preserve those snapshots. Replacing arrays with freely shared mutable pointers would silently corrupt early-stopping restoration.

These sources support a separation between nullable tabular storage and dense training tensors. They can share allocation and lifetime machinery, but they need different shape, missing-value, and mutation rules.

## Established language and hardware constraints

Swift `Span` can expose borrowed contiguous storage without transferring ownership. `MutableSpan` models an exclusive mutable borrow with bounded lifetime, and prevents its owner from being accessed while that borrow exists. Both are implemented starting with Swift 6.2. This is useful for synchronous kernels; it does not by itself represent an asynchronous foreign consumer that holds a pointer after the Swift call returns. [SE-0456](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0456-stdlib-span-properties.md), [SE-0467](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0467-MutableSpan.md).

A custom copy-on-write container can use `isKnownUniquelyReferenced`, but the function is not a lock. Apple explicitly requires appropriate synchronization when the object may be accessed from multiple threads. An outstanding unsafe pointer or foreign lease also needs its own ownership accounting. [Swift uniqueness checking](https://developer.apple.com/documentation/swift/isknownuniquelyreferenced(_:)-98zpp).

Swift Collections provides noncopyable `UniqueArray` and fixed-capacity `RigidArray`. They are candidates for predictable builders and working buffers, not automatic replacements for every public value type. Pin and inspect the package version and API availability before adoption. The installed compiler is newer than SwiftSci's declared Swift tools version of 6.0; new language APIs need an explicit minimum-toolchain decision. [Swift Collections](https://github.com/apple/swift-collections), [SwiftSci manifest](/Users/crabel/Documents/src/SwiftSci/Package.swift:1).

Metal shared storage gives CPU and GPU access to the same system-memory resource. CPU writes must finish before dependent GPU reads, and GPU writes must finish before CPU reads or writes. Unified physical memory removes a required device transfer for compatible buffers; it does not remove data hazards or lifetime rules. [MTLStorageMode.shared](https://developer.apple.com/documentation/metal/mtlstoragemode/shared), [resource synchronization](https://developer.apple.com/documentation/metal/resource-synchronization).

Apple's no-copy buffer example allocates page-aligned backing memory and wraps that allocation in an `MTLBuffer`. Do not assume an arbitrary Swift array allocation is suitable for no-copy Metal import. Choose an owning allocator deliberately, check the actual API requirements, and retain it through device completion. [Apple no-copy compute example](https://developer.apple.com/documentation/metal/selecting-device-objects-for-compute-processing).

Accelerate accepts regular strides in many vector routines. Apple recommends unit stride for most vDSP functions. Irregular selected-row indices are not a regular stride and normally need gather, a custom kernel, or materialization. A column view and a matrix view must report their actual layout. [vDSP stride guidance](https://developer.apple.com/documentation/accelerate/controlling-vdsp-operations-with-stride).

## Proposed ownership and mutation contract

This section is a design proposal, not functionality present in SwiftSci.

Use an owned numeric allocation with explicit element type, initialized count, capacity, alignment, and allocator. Keep validity and cached null count with the column owner. A missing validity allocation means all entries are present. Nullable column views carry a bit offset as well as a values offset; slices need not begin at a word boundary.

Public table values can retain snapshot semantics. A mutation session first establishes exclusive ownership of the affected column or chunk. It copies only when another snapshot or read lease needs the old content. It then amortizes uniqueness checks, bounds validation, and cache invalidation over an entire edit batch.

Useful conceptual operations are:

- Borrow immutable numeric values and validity for synchronous reading.
- Borrow mutable values without allowing changes to validity or count.
- Edit nullable entries through a writer that maintains validity and null count together.
- Append a validated batch after reserving both value and validity capacity.
- Produce a snapshot or consume a uniquely owned builder into a finished column.
- Export an immutable retained buffer lease with an explicit release callback.
- Transfer exclusive ownership to a mutable foreign/device lease, returning it only after completion.

Do not expose independent unrestricted mutable pointers to both validity and values through the ordinary API. That makes cached null count and invariants the caller's problem. Trusted internal bulk writers may use both, but must provide a final validity count or reduce local counts before publication.

A read lease keeps its buffer version alive. While leased, a normal table edit creates a new version instead of changing the exported bytes. A write lease excludes reads, snapshots, resize, and competing mutation until it ends. Structural changes never invalidate a live external pointer silently. Returning a copy, waiting, or rejecting an unsupported mutable export are valid policies; the API must identify which one applies.

A GPU lease owns the `MTLBuffer`, its backing allocation, operation metadata, and completion state. Host access resumes after the completion event. A scoped pointer closure must not launch work that outlives the closure unless a separate retained owner takes responsibility. Use command completion or shared events to release or return ownership. [CPU/GPU shared events](https://developer.apple.com/documentation/metal/synchronizing-events-between-a-gpu-and-the-cpu).

### Point updates and nullable transitions

For a unique fixed-size column, a point update remains bounded work. The first null in an all-valid column is the exception: allocating and initializing validity for the existing rows is linear unless validity capacity already exists. Preserve an allocated all-valid bitmap internally after edits if dropping and rebuilding it causes churn; logical all-valid status and physical capacity need not be the same state.

Set and clear validity with the matching null-count transition. Preserve the distinction between NaN and missing. Decide whether invalid value slots contain initialized arbitrary values or a canonical zero. Before exporting raw buffers, canonicalization may be desirable because a consumer can inspect masked bytes even though they are semantically null. Do not let an optimization expose uninitialized memory.

### Batched scatter and parallel editing

A batch can validate indices once, establish uniqueness once, and group writes by target chunk or contiguous run. Grouping is an optional optimization with a cost. Preserve duplicate-index semantics explicitly, such as last assignment in input order. An accumulation scatter needs a separate reduction contract; reordering floating-point additions changes results.

Disjoint row indices are insufficient for parallel validity writes. Rows 0 and 1 share the same UInt64 word. Two ordinary read-modify-write operations can lose one update. Assign whole validity words to a worker, use per-worker masks followed by a merge, or use correctly synchronized atomic updates. Per-worker null-count deltas avoid a shared counter. Distinct words can still share a cache line, so partition larger contiguous regions for throughput. Correctness comes before tuning the partition size.

### Append, insert, delete, and sort

Reserve numeric and validity capacity together. Append batches amortize allocation; growth must not occur while pointers are borrowed. All columns must reach the same row count before publishing a dataframe. Build unpublished buffers and commit a validated batch rather than leave a half-appended table after an error.

Middle insertion into one contiguous column shifts a suffix. Repeating it is inherently a poor fit. Append-oriented chunks, row-order indirection, or a small edit buffer can avoid repeated shifting. Physical deletion can likewise be deferred through a selection or tombstone view, but every subsequent consumer then pays indirection or selection cost until compaction.

Sorting can retain an immutable permutation over base columns. Repeated comparisons or display of sorted data may benefit; repeated dense math may justify gathering once. Keep row order separate from physical storage and make materialization explicit. Never substitute a bitmap for a permutation when order or duplicate rows matters.

## Tradeoffs to measure

| Representation or policy | Suits | Main cost or constraint |
|---|---|---|
| Unique contiguous numeric column | Point updates, normalization, dense kernels, small tables | Growth copies; middle insertion shifts; no concurrent snapshot of mutated bytes |
| Contiguous copy-on-write column | Read-heavy snapshots, familiar Swift semantics | First mutation after sharing can copy a whole column |
| Chunked copy-on-write column | Sparse edits to large shared tables, append streams | Chunk lookup and metadata; dense consumers may need several calls or packing |
| Immutable base plus edit buffer | Frequent small edits with long-lived snapshots | Every scan must merge updates; later compaction costs; increasing implementation complexity |
| Base columns plus selection/permutation | Filter, sort, train/validation splits without immediate payload copying | Irregular access; mutable-view aliasing; export may require gathering |
| Dense mutable tensor workspace | Weights, gradients, moments, iterative numerical solvers | Nullable table semantics need resolution before entry; snapshots still need copies or versions |
| Metal-backed shared allocation | Repeated compatible GPU/CPU operations | Allocation/alignment rules, synchronization, device data-type capabilities; not every API accepts it |

Start with unique contiguous storage and column-level snapshots. Add chunking only after snapshot-and-edit workloads show unacceptable copy amplification. The simple representation matches existing Accelerate consumers and gives a clear baseline. No chunk size or switching threshold is justified by the current evidence.

## Research precedent and its limits

The X100 work argues for processing cache-sized vectors through operator pipelines instead of choosing between one-row dispatch and materializing whole intermediate columns. Its relevance here is bounded batches and fused pipelines. Its historical measurements do not predict Apple silicon speedups. [Boncz, Zukowski, and Nes, MonetDB/X100](https://ir.cwi.nl/pub/16497/16497B.pdf).

Héman and colleagues studied positional update structures over read-optimized column stores, maintaining differences and merging them during scans. This gives a concrete option if we need many snapshots and scattered edits. Their database setting includes compressed, ordered disk storage and transaction management. A mutable in-memory numeric Swift column does not need that machinery merely because it is columnar. [Positional update handling in column stores](https://ir.cwi.nl/pub/16172/16172D.pdf).

## Acceptance workloads

Evaluate complete workflows, not just mutation loops. Vary row count, column width, null density and clustering, selected-row order, mutation rate, and snapshot lifetime. Include sizes below and above cache capacity, and runs near realistic memory pressure. Keep a held-out workload set.

1. Unique point writes, contiguous batch writes, random scatter, and repeated duplicate indices. Measure first-null creation separately from steady nullable updates.
2. Snapshot then modify 1, 0.1%, 1%, and 50% of entries. Hold one and several snapshots. Measure copied bytes, peak live allocation, latency, and unchanged snapshot checksums.
3. Reserve-and-append batches versus one-at-a-time append, boundary growth, empty batches, and allocation failure. Include all-valid to nullable transitions at rows 63, 64, and 65.
4. Filter then sort then normalize then matrix operation. Compare gathered output with retained selection and one final batch materialization. Include repeated epochs so one packing cost is not charged unfairly on every epoch.
5. Existing MLP fitting with early stopping. Check that saved weights remain unchanged after later optimizer updates and that restoring the best model yields the same predictions.
6. Simultaneous readers, independent mutable columns, and disjoint-row edits in the same validity word. Run race detection and exact null-count checks. Use a deterministic duplicate scatter reference.
7. Sliced columns with nonzero values and bitmap offsets. Test overlapping source/destination copies, non-unit stride, invalid indices, and empty buffers.
8. Export to a synchronous Accelerate call, retained read-only foreign view, and asynchronous GPU operation. Attempt edit, append, destruction, cancellation, and resize while leases exist. Prove either a safe copy, excluded access, or explicit rejection.
9. Mixed payload tables with strings and categories. Numeric compactness must not be presented as a solution to variable-length UTF-8 mutation or dictionary remapping.

Report total workflow time, time spent packing and synchronizing, bytes copied, peak live and resident memory, allocation count, and semantic parity. Monitor memory pressure and device utilization when evaluating GPU paths. Smaller resident data can be worthwhile even when a single kernel is no faster, but quantify the increased usable workload size rather than assume it.

## Recommended decision

Treat the current performance branch as an optimized implementation of the existing API. The next storage branch should first establish ownership, snapshot, null, shape, and export contracts. Build a compact numeric column that supports efficient unique mutation and a dense batch adapter that current SwiftSci numerical code can consume. Validate one full preprocessing-to-ML workflow and its snapshot behavior before replacing all columns or building a general plugin system.

The architectural boundary should describe what a consumer requires and what an owner guarantees. It should not promise that every dataframe can become every tensor with zero copies. Null handling, dtype conversion, permutation, layout, and asynchronous ownership can each make a copy necessary.
