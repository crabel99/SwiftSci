# Grouping design grounded in SwiftSci, pandas and Kiraa

Reviewed 2026-09-26. SwiftSci `2694d303f86f`, Kiraa `fc5d957401f7`, installed pandas 3.0.6 source. This is a source review and design proposal, not a new performance measurement. Production files were not changed. Apply the research and unslop skills.

## What the measured gap contains

The million-row production fixture reports SwiftSci 49.50 ms, pandas 10.61 ms and Kiraa 36.62 ms for two-key grouping. It has two integer keys with 100 and 97 distinct values, yielding 9,700 observed combinations. Timing includes key processing, aggregation of two numeric value columns, and result construction. It does not isolate hashing. [Benchmark report](/Users/LOCAL_USER/local-ai/spl/swiftsci/production-comparison/results/20260926T033814Z/REPORT.md)

The report's statement that Kiraa drops composite key columns is incorrect for the recorded source revision. `fastAggregate` appends each original grouping column gathered at first representative rows. Composite index labels are ordinal strings, but the actual columns retain the keys and physical types. Both CPU and GPU output paths do this. The benchmark adapter overwrites those columns using reconstructed input keys, which weakens its parity check unnecessarily. The parent agent has been notified and is correcting the adapter/report. [CPU output](/Users/LOCAL_USER/Documents/src/kiraa-swift-pandas/Sources/SwiftPandas/DataFrame/DataFrame.swift:1808), [ordinal labels](/Users/LOCAL_USER/Documents/src/kiraa-swift-pandas/Sources/SwiftPandas/DataFrame/DataFrame.swift:1931), [GPU output](/Users/LOCAL_USER/Documents/src/kiraa-swift-pandas/Sources/SwiftPandas/Metal/MetalGroupBy.swift:155), [adapter](/Users/LOCAL_USER/local-ai/spl/swiftsci/production-comparison/Sources/KiraaBench/main.swift:64).

## SwiftSci's current execution

`DataFrame.groupBy` captures a frame and key names. Each aggregation or transform then calls `buildGroups` again. `GroupIndex` stores one native-width group ID per input row, a representative row per group, and group row counts. `append` assigns first-seen identity independently of dictionary iteration. [Entry point](/Users/LOCAL_USER/Documents/src/SwiftSci/Sources/SwiftDataFrame/Core/DataFrame.swift:556), [index and builder](/Users/LOCAL_USER/Documents/src/SwiftSci/Sources/SwiftDataFrame/Core/GroupedDataFrame.swift:211).

A single Int, Int32 or Int64 key uses a bounded-domain lookup when its checked value span fits at most 65,536 slots and no more slots than input rows. Otherwise it uses a typed dictionary. With multiple keys, even the first integer key bypasses that existing optimization. Each column instead builds a new typed dictionary keyed by either the optional value or `(priorGroupID, optionalValue)`, and a new GroupIndex. [Dispatch](/Users/LOCAL_USER/Documents/src/SwiftSci/Sources/SwiftDataFrame/Core/GroupedDataFrame.swift:232), [refinement](/Users/LOCAL_USER/Documents/src/SwiftSci/Sources/SwiftDataFrame/Core/GroupedDataFrame.swift:264), [bounded lookup](/Users/LOCAL_USER/Documents/src/SwiftSci/Sources/SwiftDataFrame/Core/GroupedDataFrame.swift:378).

After grouping, each numeric value column gets its own sequential reduction over row IDs. Sum and mean preserve compensated Double arithmetic. `sumChecked` has separate exact integer accumulation. Result key columns are formatted only for representative rows, into String columns. Preserving that output is a compatibility requirement for this optimization. [Output](/Users/LOCAL_USER/Documents/src/SwiftSci/Sources/SwiftDataFrame/Core/GroupedDataFrame.swift:415), [reduction](/Users/LOCAL_USER/Documents/src/SwiftSci/Sources/SwiftDataFrame/Core/GroupedDataFrame.swift:510).

For two keys, the implementation reads both key columns, writes two row-ID arrays and reads the first ID array during refinement. It also updates group counts twice and builds two dictionaries. Only the final counts and representatives survive. These are source-derived traffic observations. Whether hashing, allocation, bounds checks, or memory stalls dominate needs phase timing or CPU sampling.

An arm64 native Int ID array costs 8 bytes per row before allocator overhead. Two live million-row ID arrays therefore account for about 16 MB. Optional numeric strides must be measured with MemoryLayout for the actual type and compiler; `[Int64?]` is not equivalent to an eight-byte value array plus bitmap. Narrowing IDs to UInt32 could reduce their traffic, but introduces range checks and conversion to native array indices. It belongs in a measured prototype, not an assumed win.

## What pandas does differently

The installed `Grouping._codes_and_uniques` factorizes each component with the requested missing-value policy. `BaseGrouper._ob_index_and_ids` combines component codes, compresses observed IDs, and constructs a MultiIndex from the original levels and codes. Cached grouping properties support repeated aggregations. [Factorization](/Users/LOCAL_USER/local-ai/spl/swiftsci/benchmark/.venv/lib/python3.14/site-packages/pandas/core/groupby/grouper.py:621), [result IDs](/Users/LOCAL_USER/local-ai/spl/swiftsci/benchmark/.venv/lib/python3.14/site-packages/pandas/core/groupby/ops.py:880).

`get_group_index` computes mixed-radix codes only for a prefix whose cardinality product fits Int64. It compresses the partial result before combining more components when necessary. Missing codes can become their own valid category or remain excluded. `compress_group_index` has a linear sorted-input path, otherwise an Int64 hash table; ordering can then be restored separately. [Installed source](/Users/LOCAL_USER/local-ai/spl/swiftsci/benchmark/.venv/lib/python3.14/site-packages/pandas/core/sorting.py:121), [compression](/Users/LOCAL_USER/local-ai/spl/swiftsci/benchmark/.venv/lib/python3.14/site-packages/pandas/core/sorting.py:675), [upstream source](https://github.com/pandas-dev/pandas/blob/main/pandas/core/sorting.py).

The useful idea is explicit integer codes with checked composition and separate output ordering. pandas' missing-key and NaN behavior must not replace SwiftSci's own contract. Nor should we assume pandas' multiple full-array passes are universally faster than SwiftSci's refinement. The current fixture has small dense domains that favor direct addressing.

## What Kiraa does differently

Kiraa's GroupBy initializer eagerly factorizes all keys, combines codes, compacts observed groups, and stores first representative rows. Subsequent aggregates reuse those fields. Numeric factorization reads separate values and validity; its dictionary emits first-occurrence codes and -1 for invalid rows. Composite grouping combines codes through `oldCode * nUnique + componentCode`, then a final Int dictionary compresses those codes. [Initializer](/Users/LOCAL_USER/Documents/src/kiraa-swift-pandas/Sources/SwiftPandas/DataFrame/DataFrame.swift:1527), [numeric factorization](/Users/LOCAL_USER/Documents/src/kiraa-swift-pandas/Sources/SwiftPandas/Core/Array/NullableArray.swift:921).

Several details are unsuitable for direct adoption:

- Cardinality multiplication and code multiplication at lines 1601 and 1603 use unchecked-by-design ordinary Int arithmetic. Swift overflow traps rather than providing a safe high-cardinality fallback. A thousand rows with seven independently 1,000-valued key columns already have a hypothetical Cartesian product of 10^21, even if only a thousand combinations occur. This is a source-derived overflow risk, not an executed Kiraa failure in this review.
- CPU grouping excludes null key rows. SwiftSci includes null as an explicit component. SwiftSci also canonicalizes NaN payloads and signed zeros; generic Float dictionary factorization does not establish the same contract.
- Single-key output is sorted by key, while multi-key output retains first-seen order. SwiftSci's first-seen rule must remain consistent.
- Numeric CPU aggregation converts value columns through `asDouble` and uses ordinary addition. It is not equivalent to SwiftSci's compensated sums or exact checked integer sums.
- GPU multi-key factorization joins formatted components with tabs and treats text `NA` as missing. That can conflate different tuples or real strings. GPU reductions convert values to Float32. This path must not become SwiftSci's scientific default. [GPU factorization](/Users/LOCAL_USER/Documents/src/kiraa-swift-pandas/Sources/SwiftPandas/Metal/MetalGroupBy.swift:388), [Float32 conversion](/Users/LOCAL_USER/Documents/src/kiraa-swift-pandas/Sources/SwiftPandas/Metal/MetalGroupBy.swift:245).

Kiraa's default GPU grouping gates are 10 million rows and 100,000 groups. Our million-row, 9,700-group fixture is below both. The measured difference is not evidence of GPU advantage. The GPU entry point can refactor keys on the CPU before its group-cardinality rejection; that duplication is another reason to share exact factorization rather than copy this dispatch structure. [Thresholds](/Users/LOCAL_USER/Documents/src/kiraa-swift-pandas/Sources/SwiftPandas/Metal/MetalDispatch.swift:99), [late cardinality gate](/Users/LOCAL_USER/Documents/src/kiraa-swift-pandas/Sources/SwiftPandas/Metal/MetalGroupBy.swift:107).

Kiraa StringArray factorization uses a flat probing table with cached FNV hashes of raw UTF-8. This illustrates a locality improvement, but raw-byte hashes must agree with equality. It checks full-hash equality before Swift String equality. Swift String treats canonically equivalent composed/decomposed Unicode as equal, although those strings have different bytes. No normalization is visible in the inspected path. Preserve SwiftSci's existing String semantics, and add a composed/decomposed Unicode case before experimenting with byte hashing. [String hash and comparison](/Users/LOCAL_USER/Documents/src/kiraa-swift-pandas/Sources/SwiftPandas/Core/Array/StringArray.swift:318).

## Recommended prototypes

### Bounded integer refinement

First reuse `buildIntegerGroups` for the first composite integer key. Then allow each later integer component to refine existing prefix IDs through a checked domain lookup:

1. Scan valid values for a bounded exact min/max range. Use reporting-overflow subtraction and exact Int conversion. Allocate an extra distinct slot for null when present.
2. Check `prefixCount * componentSlotCount` for overflow and against an explicit byte budget. Distinct group count is not the same as value range.
3. For each input row, compute a checked-by-construction slot from its prior ID and exact component offset. The table stores a final group ID or -1.
4. On first encounter, call GroupIndex.append with the next dense ID. Preserve representatives and ordering from input traversal.
5. Fall back to existing typed dictionary refinement for sparse/extreme ranges or oversized products.

For the measured 100 by 97 domains, this needs 9,700 slots, about 77,600 bytes for native Int entries. It removes dictionary work from both components without changing column storage or numerical reductions. The pre-scan and table initialization have costs, so measure smaller inputs and sparse ranges. Do not set a larger limit merely to make this fixture pass.

### General factorization plus code refinement

For strings and sparse numeric domains, factorize each component independently, then combine its dense codes with prior prefix IDs. Use direct addressing only when the checked dense product fits the budget; otherwise hash pairs of integer codes. This can reduce repeated long-string hashing but adds a component code array and a pass. Compare it to the existing typed-prefix dictionary at varying string lengths and cardinalities before choosing it.

### Representative-row hash table

A single composite table can store representative row indices and cached hashes. Hashes choose candidates, and typed component equality resolves collisions. This avoids per-column ID passes and per-row heap tuples. It also introduces probe growth, heterogeneous comparison dispatch and capacity invariants. It is a credible alternative for many keys or high cardinality, but has more proof and maintenance cost than bounded refinement. Keep it an isolated prototype until evidence favors it.

DuckDB documents linear probing, separate payload storage, cached hashes and hash fragments to reduce expensive candidate comparisons. It also explains why local tables and radix partitions are preferable to a single contended mutable table for parallel aggregation. These are useful design choices, not measured M4 results. [DuckDB primary explanation](https://duckdb.org/2022/03/07/aggregate-hashtable).

## Integration and branch boundary

The common mechanism across CSV, sorting and grouping is typed columns plus row positions. CSV should produce typed buffers without per-cell strings where grammar and inference allow. Sorting should produce an exact stable permutation. Grouping should consume exact typed keys and produce first-seen IDs. Reusing this mechanism must not silently reorder arithmetic or change key equality.

On the current production branch, keep GroupIndex private, add bounded refinement, remove provably unused intermediate metadata if measured worthwhile, and maintain the existing public output. Avoid persistent caches for now. Built-in TypedColumn is immutable, but AnyColumn only promises Sendable and read access; it does not guarantee immutable snapshot semantics for custom reference types. Eager caching also shifts work from aggregation to groupBy construction. A cache ownership and invalidation contract is a separate design decision. [Column protocol](/Users/LOCAL_USER/Documents/src/SwiftSci/Sources/SwiftDataFrame/Columns/AnyColumn.swift:3).

On the compact-storage branch, investigate reusable categorical codes, validity bitmaps, selection/permutation views, and buffer ownership across parsing and MLX. Dictionary codes can be reused for grouping but do not automatically encode sorting order. A sort needs ranks of unique keys with a specified comparator. Filtering or permutation must map codes with row selection and keep the correct first representative. Byte-backed strings also require explicit Unicode equality and lifetime rules.

The X100 paper shows why dispatch per element is expensive and why whole-column intermediate traffic can become the next limit. Its cache-sized execution approach supports testing fused selection plus grouping, but fusion should follow measured need. A preceding sort cannot simply be deleted: SwiftSci exposes first-seen group order, first/last reductions, and compensated sums whose result depends on addition order. [X100 paper](https://www.cidrdb.org/cidr2005/papers/P19.pdf).

## Verification before selecting a design

Use an independent tuple-equality reference and preserve null versus literal text, signed zero/NaN policy, full-width integers, first-seen order, transform row alignment and output key columns. Add overflow products, sparse extreme ranges, all-null components, reversed key order, composed/decomposed Unicode and deliberately colliding hashes. Preserve checked integer overflow behavior and compensated floating arithmetic.

Measure key scanning/factorization, ID refinement, reduction and output separately, then run public end-to-end operations. Cover low/medium/near-row-count cardinality; one/two/many keys; random/skewed/clustered ordering; 0/1/50 percent nulls; short/long Unicode strings; repeated aggregates; and wide frames. Record allocation or incremental peak memory in addition to whole-process RSS. Avoid concurrent benchmark processes. Use CPU samples to distinguish hash/probe latency, Swift specialization and memory traffic before calling a path bandwidth-bound or adding parallelism.
