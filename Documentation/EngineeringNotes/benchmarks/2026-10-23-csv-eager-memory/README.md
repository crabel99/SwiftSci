# Eager CSV memory accounting

The eager CSV result, rather than an oversized parser buffer, is the main private allocation in this sample. Seven numeric optional arrays and two string optional arrays account for almost all 285 MiB of held heap. The input contributes another 126.8 MiB of clean file-backed pages during the read. Those pages disappear when the public read returns.

This is a memory diagnosis, not a new performance comparison. Production source is unchanged at `5d1f89a961106104757f2d8d0b8faba79487d100`. All profiling processes are owned by this experiment. No unrelated processes are stopped.

## Why this investigation follows the comparison

The [strict external comparison](../2026-10-23-csv-external-resources/README.md) measured lower Swift CPU time but higher eager read-associated peak RSS than Polars on the household reference file. RSS combines allocations, file mappings, and resident allocator storage. That measurement cannot identify which structure to change.

The source file contains 2,075,259 observations in 132,960,755 bytes. Every reader uses the same complete schema and eleven declared null tokens in the `energy-common` contract. Its numeric `?` marker is explicitly included. This is not the ten-token Swift default configuration.

## Evidence separates the four hypotheses

| Ranked hypothesis before instrumentation | Observation | Consequence |
|---|---|---|
| The mapped input accounts for much of the peak above held output. | Both diagnostic worker policies show the complete 126.8 MiB input region resident with zero dirty bytes before return. That region is absent after return. | Treat input mapping separately from private output storage. |
| Optional-value arrays dominate held output. | Native heap inspection finds seven `Double?` array objects totalling 232,472,576 bytes and two `String?` arrays totalling 66,420,736 bytes. | Numeric representation is a justified candidate for a storage experiment. |
| Excess capacity or large temporary copies dominate. | Each array contains 2,075,259 values with capacity 2,075,646. Total unused element capacity is 55,728 bytes, about 54.4 KiB. Only nine large array objects remain at completion. | Shrinking capacity or adding a final compaction pass addresses little of this case. Smaller earlier transient allocations are not excluded. |
| Released output remains owned by SwiftSci. | Live heap falls to about 0.22 MiB. The nine large array objects disappear. Native region inspection classifies their former regions as `Malloc Large (empty)`, although their pages remain resident. | Persistent RSS alone is not evidence of retained SwiftSci output. |

These observations apply to this build and input. They do not establish the absence of every possible leak or describe the allocator's undocumented reclamation policy.

## Lifecycle results

Representative serial lifecycle using the actual production module:

| Checkpoint | Live heap, MiB | Process RSS, MiB | Peak process RSS, MiB |
|---|---:|---:|---:|
| Before the read | 0.091 | 6.516 | 6.516 |
| Result held, before validation | 285.253 | 297.625 | 423.984 |
| Result released, after validation | 0.222 | 298.328 | 423.984 |
| After diagnostic allocator pressure relief | 0.220 | 298.375 | 423.984 |

The explicit pressure-relief request reports zero bytes relieved in each lifecycle run. Adding allocator flushing to production is not justified by this experiment. Release remains important for ownership even when RSS does not fall immediately.

The frozen diagnostic module pauses after the full frame is constructed while the input is still mapped. Native physical footprint is 291.1 MiB there and 291.5 MiB after return in the serial run. The clean input mapping explains why peak RSS and charged physical footprint differ. Neither measure alone is total system memory saved, nor should they be added together. Native tools and in-process counters have different accounting scopes.

The parallel actual-module run holds the same 285.253 MiB live heap. Its peak RSS is 424.281 MiB. This investigation does not measure an allocation advantage from changing column-conversion scheduling.

Seven lifecycle reads pass exact type, column order, row count, null position, and per-column SHA256 checks. Four of those runs receive 36 native snapshots in total, using `vmmap` and `heap`. Three runs omit native snapshots, including the smaller air-quality input. Two additional repeated-read processes complete eight reads each. Six post-warmup records per policy retain less than 0.12 MiB live heap after release. Those original probes retain a small statistics dictionary per record, so their few-KiB growth is not a clean test of zero residual allocation. They do exclude accumulation of a 285 MiB live output per read.

## The representation cost is explicit

On the measured toolchain:

- `Double` occupies 8 bytes. `Double?` has size 9 and stride 16 because array elements must respect alignment.
- `String?` has stride 16. These short date and time strings do not create millions of individually allocated string objects in the native heap snapshot.
- The nine optional arrays have a logical payload of 284.993 MiB. Including their observed capacity and array object headers gives 285.047 MiB, accounting for more than 99.9% of the 285.253 MiB held live heap.

The reader reserves the counted row capacity once. `CSVColumnBuilder.column` transfers its array into `TypedColumn` and clears the builder. The snapshot contains one large array per output column, rather than an additional complete builder copy.

Relevant source boundaries, recorded at `5d1f89a961106104757f2d8d0b8faba79487d100`:

- `Sources/SwiftDataFrame/IO/CSVReader.swift`: maps the file for `CSVEagerReader.read`, then releases the mapping on return.
- `Sources/SwiftDataFrame/IO/CSVEagerReader.swift`: scans bounded record batches but retains completed output values.
- `Sources/SwiftDataFrame/IO/CSVColumnBuilder.swift`: builds `[T?]` directly with reserved capacity.
- `Sources/SwiftDataFrame/Columns/TypedColumn.swift`: exposes `public let values: [T?]`; its typed subscripts and operations depend on this storage.
- `Sources/SwiftDataFrame/Core/DataFrame.swift`: typed column lookup casts to `TypedColumn<T>`. A separate opaque compact column does not automatically preserve that API.
- `Sources/SwiftDataFrame/Internal/ArrowDataBuffer.swift`: already provides owner-retaining Arrow buffer access.
- `Sources/SwiftDataFrame/Internal/ArrowTableBridge.swift`: currently copies Arrow values into optional arrays. Routing CSV through this bridge would still materialize the larger output representation.

## Next experiment and acceptance boundary

Prototype dense numeric values with a separate validity bitmap, using existing ownership and buffer facilities where they fit. Build this representation directly during decoding. Converting a completed optional array afterward would introduce both an extra full pass and a period with two representations alive.

For this particular schema, replacing only the seven numeric optional arrays with 8-byte values and one validity bit per row would reduce logical output payload from **284.99 MiB to 175.89 MiB**, a calculated difference of **109.10 MiB, or 38.28%**. This is an illustrative layout calculation. It excludes allocation granularity, metadata, bitmap alignment, public-API materialization, and compute costs. It is not a measured improvement.

A storage experiment must retain exact null semantics. NaN cannot substitute for null because valid NaN and missing data are distinct. It must also preserve the typed lookup boundary, define the cost of requesting `[T?]`, and avoid retaining both representations by default. Cover filtering, gathering, sorting, joining, and matrix extraction so a cheaper CSV result does not move the cost into every later operation.

Evaluate total CPU time, live retained bytes, peak footprint, and end-to-end downstream costs on the household and air-quality references plus mixed small, null-free, nullable, and long-string cases. Keep native CPU scheduling unchanged. Promote only demonstrated resource improvements. Streaming remains the bounded-output choice when the caller does not require a complete resident frame.

## Reproduction and artifacts

- [Summary](summary.json) contains lifecycle counters, per-column capacities, native region excerpts, and the illustrative layout calculation.
- [Audit](audit.json) records the completed checks.
- [Source receipt](source-receipt.json) records the source commit and all 50 Swift source hashes.
- [Experiment archive](experiments.tar.gz) includes controllers, probes, build receipts, compiler module-loading logs, the original source snapshot, the diagnostic-only patch, input contracts, and raw native snapshots.
- [Artifact hashes](artifact-sha256.json) cover every delivered artifact except the manifest itself.

The module build uses optimized whole-module compilation for `arm64-apple-macos14.0` on the recorded machine. Every newly linked client emits module-loading diagnostics and asserts that the loaded `SwiftDataFrame` interface matches its linked object. The actual client links the existing production object. The diagnostic client links a frozen copy with a single checkpoint inside the mapping lifetime. No production worktree file is edited.

The archived controllers use absolute paths for the recorded machine and its existing dependency products. To reproduce elsewhere, restore the input file with its recorded SHA256, rebuild the pinned source and dependencies, and update those roots. Native binaries, build caches, and the large reference CSV are excluded. `profile.py` owns each child, acknowledges bounded checkpoints, captures only those child processes, and terminates its own child on failure. `summarize.py` audits all captures. No profiled elapsed or CPU value is accepted as a benchmark result.
