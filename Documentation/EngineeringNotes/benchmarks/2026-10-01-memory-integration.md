# Memory integration after the prototype

This is a proposal for SwiftSci's numerical data path, based on the October 1 prototype. It belongs to `codex/engineering-notes`. It does not change the production interface or imply upstream approval. The [experiment report](2026-10-01-memory-sequence.md) contains the measurements and qualifications.

The best supported first change is to retain numerical selections and prepare the consumer's matrix once. Whole-column storage remains the default candidate. Chunked storage has a measured role for localized edits and append builders. Metal-backed storage belongs at an explicit device-consumer seam.

## Existing interfaces determine the first integration

The inspected production sources are those inherited by `codex/unified-memory-prototype` from `f9e13de32e492b0a49eb0c6647a2136e9ccf6aa4`. No production source changed during this sequence.

| Existing code | Observed behavior | Proposed integration |
|---|---|---|
| `TypedColumn.values` | Public immutable `[T?]` storage | Preserve this interface in the first contribution. A storage replacement needs a separate compatibility decision. |
| `DataFrame.prepareNumericBatch` | Converts supported numeric columns into compact Double columns | Use this existing preparation seam first. Measure direct compact ingestion later. |
| `PreparedNumericBatch.selectingRows` | Gathers values and preserves original row indices | Add a package-private retained-selection representation for internal consumers. Keep the existing public return contract. |
| `StandardScaler.fit` and `transform` on a prepared batch | Uses vDSP and preserves the established row-width division order | Read selections through retained owners. Keep training order and arithmetic order unchanged. |
| `PreparedNumericMatrix` | Owns a public `[Double]`, layout and original row identities | Let internal consumers borrow a checked matrix representation. Materialize the public array when that interface is requested. |
| `LinearRegression.fit` and `LogisticRegression.fit` | Accept nested rows; GPU paths flatten and convert them to Float | Add prepared-input overloads after the internal representation is qualified. Route existing callers through the same implementation without changing their declared numerical behavior. |
| `DataBuffer` and `ArrowDataBuffer` | Existing byte-access abstractions; the inspected typed-column path does not use them | Reconcile or replace these abstractions during storage integration. Avoid adding another general buffer protocol alongside unused ones. |
| `ArrowTableBridge.toDataFrame` | Expands Arrow columns into optional Swift arrays | Treat Arrow borrowing as separate work. The presence of `ArrowDataBuffer` does not make this conversion zero-copy. |
| `ChunkedDataFrame` | Streams whole dataframes | Keep streaming chunks distinct from copy-on-write blocks inside one column. Their purposes and lifetimes differ. |

A retained selection needs an immutable owner, a validated row mapping and the validity information for the same snapshot. Selection composition must preserve duplicates, order and original row identities. Values and validity cannot refer to different generations.

The internal matrix representation needs dtype, dimensions, element strides, layout, missing-value treatment and an owner. A raw pointer alone is insufficient. CPU consumers borrow the owner for the call. Device consumers retain it until work completes, even if a caller stops awaiting the result.

## Storage choices follow the workload

Retained row indices avoid repeated gathers and preserve memory for other work. A gathered snapshot costs memory once and benefits repeated fitting over the same selected rows. The prototype measures both choices with the original table still retained. It does not establish an automatic crossover threshold.

The mutation experiment supports fixed-size blocks for localized edits under retained snapshots. Scattered edits can touch nearly every block and copy nearly the whole column. Ordered dense edits still favor the contiguous column after removing dictionary grouping overhead. Indexed scans also favor the contiguous column. A production block implementation would need block-aware numerical loops rather than a division and lookup for every element.

The append comparison uses exact-size allocations. It does not compare against a contiguous builder with spare capacity. An append builder should therefore remain an explicit experiment until it competes with amortized growth, multiple batch sizes and realistic snapshot retention. Chunking every column now would trade proven read throughput for a benefit that depends on edit locality.

The first implementation should use explicit internal choices for retained selection and gathered reuse. A later policy may choose between them from measured reuse and memory constraints. Such a policy must account for the cost of changing representation and must not alternate representations on every operation.

## Precision and placement are separate decisions

Compact storage preserves the declared element type and keeps validity separate from values. A valid NaN remains different from a missing value. Exact integer storage remains exact until a requested conversion.

The scientific CPU path keeps Double values and the existing precision policy. A Float32 device export is a lossy conversion. It must honor the caller's precision requirement and preserve the source. The device trial measures rounding for its fixture; it does not qualify arbitrary scientific inputs for Float32.

Missing-value handling remains part of the operation contract. The prototype's workflow explicitly filters complete rows before fitting. That does not authorize a new implicit complete-case policy in `StandardScaler`. Existing prepared-batch scaling treats missing numerical payloads as NaN. Compatibility tests must preserve that behavior unless a separate interface explicitly requests another policy.

The same applies to stable sorting, duplicate selections, empty input, constant columns, training-only fitting, overflow and numerical reduction order. Repacking data must not silently change any of them.

## Unified memory still requires ownership and synchronization

The direct C MLX adapter proves buffer sharing for page-aligned, contiguous Float32 allocations with page-aligned extents. The adapter rejects null imports. A checked copying path handles an extent that does not meet the managed-import restriction. Arbitrary strides, slices, foreign Arrow buffers and concurrent writers remain unqualified.

The input owner remains alive while the GPU reads it. A host edit detaches if a shared import still retains that owner. Sharing therefore avoids a copy for read-only consumption but can defer the copy to a later writer. Import time alone is not the workflow cost.

The output handoff waits for MLX evaluation, wraps the completed allocation in a Metal buffer and retains the MLX array through Metal completion. Independent queues need an explicit ordering contract. A cancelled task must not release memory that a submitted command still uses. The current checks cover an abandoned lazy graph and completed submitted work, not cancellation of running commands.

The pinned mlx-swift 0.31.6 Swift managed initializer fails owner-release qualification. The [dependency report](2026-10-01-mlx-managed-finalizer.md) records the reproducer. The explicit C callback adapter passes release checks but remains tied to the pinned dependency. Production integration should use a qualified upstream wrapper or retain copying as the fallback.

A lock protects the prototype's allocation counters because a foreign callback can release an owner on another thread. That lock does not make mutable columns Sendable. Production concurrency needs immutable published snapshots, exclusive mutation, and a reviewed foreign-callback lifetime contract. `@unchecked Sendable` alone would not provide those guarantees.

## Contributions can remain small and reviewable

The proposed implementation order is:

1. Add package-private retained numerical selections and direct matrix preparation. Keep public arrays and existing arithmetic behavior. Qualify complete workflows, null semantics and snapshot lifetimes.
2. Add prepared-input model overloads and remove repeated nested-row conversion from those implementations. Preserve the old entry points and compare identical algorithms, devices and dtypes.
3. Compare direct compact CSV and Parquet builders with the current optional-array ingestion path. Account for parser time, conversion, peak RSS and malformed-input behavior.
4. Develop chunked mutation and append builders separately. Require workload-level gains over contiguous storage with spare capacity before choosing any automatic policy.
5. Integrate a qualified MLX adapter after resolving the pinned wrapper's lifetime fault. Add cancellation, concurrent-reader, slice, allocation-failure and repeated-model-cycle tests before exposing shared imports to callers.

None of these steps requires raising the declared minimum Swift or macOS version for the first retained-selection contribution. The prototype builds with the existing Swift 6 package manifest and macOS 14 deployment target on the current toolchain. Runtime testing occurred on the current Apple silicon host, not on macOS 14. Newer Metal compiler configuration has an availability-guarded fallback. New language lifetime features can be evaluated later without becoming a prerequisite for the initial contribution.

## Acceptance before a production contribution

The prototype evidence is narrower than production readiness. Promotion requires existing Debug and Release tests, numerical conformance with unchanged tolerances, old-caller compilation, persistence checks and the established benchmark controller. Historical benchmark fingerprints must remain attached to their original source states.

Storage qualification must include NaN and infinity, bitmap and block boundaries, repeated and invalid edits, retained values plus validity, failed allocation paths, and exact integer conversion limits. Device qualification must include owner release across repeated lifecycles, rejected layouts, callback execution, stream ordering and cancellation after submission.

Performance comparisons must charge parsing, conversion, materialization, synchronization and output access where the workload requires them. Cold-file I/O, memory pressure, external datasets, string columns, joins, full model training and tensor caches remain outside this sequence. No GPU kernel timing here is a claim that a whole model runs faster.
