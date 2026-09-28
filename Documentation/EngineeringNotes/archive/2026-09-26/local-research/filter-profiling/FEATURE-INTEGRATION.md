# Selective feature adoption for SwiftSci

This plan accompanies the local `codex/optimize-filter-null-count` candidate. It is a design assessment, not a commitment to merge entire libraries or implement every item. The public SwiftSci API should remain the main interface while internal performance improvements are measured independently.

## What each library contributes

| Library | Useful strengths observed | What to retain or adopt |
|---|---|---|
| SwiftSci | Existing typed columns, statistics and forecasting modules, Arrow integration, native Swift interfaces | Keep the scientific modules and improve their shared dataframe implementation. |
| pandas | Type-specific compiled selection kernels, explicit dtype controls, well-defined indexing and result behavior | Use it as a differential reference for selected behaviors, and adopt type-specific execution without reproducing its entire index system. |
| Kiraa SwiftPandas | Specialized numeric buffers, separate validity bitmap, structured lazy predicates, validated CSV reads, resident CLI datasets | Adopt the ideas individually where measurements or user workflows justify them. |

The new Int64 gather is an example of this approach. It extends SwiftSci's own existing Double specialization with a concrete integer helper. No pandas or Kiraa implementation code was copied.

## Proposed order

### 1. Finish and upstream the measured numeric fast paths

The current candidate keeps Int64 data exact, including values beyond Double's exact integer range. Existing public callers continue to use `gathered`, `filter` and `filterFast`. The new helper is private.

Before adding more type-specific paths, profile Int32, Float, sorting and aggregation separately. Every new path should preserve ordered values, null positions, duplicate indices and type metadata. Compare narrow and wide frames, empty/all/sparse selections, and nullable inputs. Avoid multiplying kernels merely because another library has one.

Success means a measured improvement through the public API with the same output and passing Debug/Release tests. An isolated kernel improvement that disappears in a real pipeline is insufficient.

### 2. Strengthen CSV contracts before tuning the parser

SwiftSci already has `CSVReadOptions.columnTypeOverrides`, a byte-oriented parser and parallel column conversion. Those features do not need to be added again.

The inspected override paths can turn failed conversions into nil. Kiraa distinguishes a parse report from a validated read that throws; pandas also exposes explicit dtype and conversion behavior. A useful SwiftSci addition would be an explicit invalid-value policy with column and row diagnostics. Preserve existing behavior as an explicit compatibility choice while allowing callers to require strict parsing.

Tests should cover integers above 2^53, overflow, missing tokens versus malformed tokens, quoted delimiters/newlines, escaped quotes, UTF-8 and inconsistent row lengths. A future speed comparison must declare the same output types in every library. Kiraa's default numeric CSV inference produced floating-point ID columns in our first benchmark, while pandas kept integer IDs.

After that, profile scanning, type inference and column construction independently. Kiraa's flat field offsets and chunked scanning are useful candidates. SwiftSci already parallelizes column conversion, so adding threads indiscriminately is not the next step.

### 3. Make lazy filters inspectable

SwiftSci's query plan currently stores arbitrary row closures and merges consecutive filters. Its inspected optimizer preserves selection nodes in sequence; despite its comment mentioning projection pushdown, it cannot generally infer which columns an opaque closure needs.

Kiraa uses a structured predicate tree with referenced-column information. SwiftSci could add a typed single-column predicate path using its existing FilterCondition vocabulary, while retaining closure filters. The optimizer could then combine predicates and move column selection earlier when all required columns remain available.

Keep closures in order unless their behavior is explicitly constrained. Tests should compare optimized and unoptimized execution, including nulls, missing columns and selection before/after filters. Benchmark complete read-filter-select-group pipelines so reduced intermediate copying is visible.

### 4. Decide result semantics explicitly

Two observed differences deserve decisions and tests:

- SwiftSci's empty gather returns `DataFrame.empty`, losing the original schema. A typed empty result would help pipelines continue without guessing column types.
- SwiftSci turns group keys into string columns; Kiraa uses string index labels. Value agreement with pandas does not establish type compatibility. Preserve numeric group-key types where that is the intended contract.

Treat these as separate behavior changes, with issue discussion and regression tests, rather than hiding them inside a performance patch. Include ordering, null-versus-NaN behavior and copy/value semantics in each decision.

### 5. Prototype storage changes only when needed

Kiraa separates numeric buffers from validity bits and has fast paths for all-valid data. SwiftSci's measured Optional<Int64> and Optional<Double> stride is 16 bytes on this Mac. A numeric buffer plus bitmap could reduce memory and repeated null work.

However, SwiftSci already exposes `[T?]` through TypedColumn.values and supports concrete TypedColumn downcasts. Replacing storage outright can introduce materialization costs or break callers. Its existing Arrow bridge and retained-owner buffers are a better starting point for a prototype than introducing a second unrelated storage system.

Compare an Arrow-backed or bitmap-backed implementation behind AnyColumn against current storage. Measure construction, filtering, joins, missing-value operations, slicing and conversion back to public values, including retained memory and ownership lifetimes. Decide from end-to-end results; the current Int64 speedup shows that a storage rewrite is not required to remove the dominant filter overhead.

### 6. Keep resident datasets in a separate tool layer

Kiraa's load/pipe/save daemon is relevant to repeated local-agent jobs because it can retain a dataset between requests. A similar tool could call SwiftSci's dataframe, statistics and forecasting modules without re-reading CSV for every operation.

Keep that lifecycle outside the core dataframe module. Establish dataset ownership, explicit drop/eviction, resource limits and stable result handles before exposing long-lived data to agent workflows. This is a distinct product feature from numeric kernel optimization.

## Source and licensing record

The inspected SwiftSci checkout carries an MIT license, the installed pandas distribution carries BSD-3-Clause, and the inspected Kiraa fork carries Apache-2.0. Those are distinct licenses. This plan uses implementation ideas and independently written SwiftSci changes. Any future literal code port should record its source revision and the applicable license/notice requirements before publication.

## Evidence and source locations

- [Filtering profile report](/Users/LOCAL_USER/local-ai/spl/swiftsci/filter-profiling/results/20260925T220711Z/REPORT.md)
- [SwiftSci column implementation](/Users/LOCAL_USER/Documents/src/SwiftSci/Sources/SwiftDataFrame/Columns/TypedColumn.swift)
- [SwiftSci CSV options](/Users/LOCAL_USER/Documents/src/SwiftSci/Sources/SwiftDataFrame/IO/CSVReadOptions.swift)
- [SwiftSci CSV parsing](/Users/LOCAL_USER/Documents/src/SwiftSci/Sources/SwiftDataFrame/IO/CSVReader.swift)
- [SwiftSci lazy optimizer](/Users/LOCAL_USER/Documents/src/SwiftSci/Sources/SwiftDataFrame/Lazy/QueryPlan.swift)
- [SwiftSci Arrow buffer](/Users/LOCAL_USER/Documents/src/SwiftSci/Sources/SwiftDataFrame/Internal/ArrowDataBuffer.swift)
- [Kiraa lazy optimizer](/Users/LOCAL_USER/Documents/src/kiraa-swift-pandas/Sources/SwiftPandas/Lazy/QueryOptimizer.swift)
- [Kiraa validated CSV reads](/Users/LOCAL_USER/Documents/src/kiraa-swift-pandas/Sources/SwiftPandas/IO/CSV/CSVReaderStrict.swift)
- [Kiraa resident server](/Users/LOCAL_USER/Documents/src/kiraa-swift-pandas/Sources/SwiftPandasCLI/Server/Handlers.swift)
