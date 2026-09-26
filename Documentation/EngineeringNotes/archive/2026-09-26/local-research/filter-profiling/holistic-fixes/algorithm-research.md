# Grouping and filtering research for SwiftSci

Research checked 2026-09-26. This is a design recommendation, not a measured performance claim. No repository files changed.

## Recommendation

Keep the existing flat `GroupIndex` and specialized integer grouping. Replace textual composite identities with typed equality. The smallest general implementation is incremental group refinement: scan one typed key column at a time and assign first-seen IDs to `(previousGroupID, currentValue)` pairs. This needs two row-ID buffers and a dictionary, avoids per-row strings and tuple arrays, and works for any number of columns without multiplying key cardinalities.

This extends the current branch's execution improvements. Persistent dictionary encoding, selection views, compact validity storage, model adapters and cache-sized pipelines belong on the compact-storage branch.

## Evidence from research and working systems

| Source | Relevant result | Application to SwiftSci |
|---|---|---|
| Boncz, Zukowski and Nes, *MonetDB/X100: Hyper-Pipelining Query Execution*, CIDR 2005 | Tuple-at-a-time interpretation hides independent work from the compiler. Full-column intermediates can instead saturate memory bandwidth. Cache-sized vector processing balances these costs. | Move type dispatch outside element loops. Avoid formatting, boxing and temporary arrays in common typed paths. Profile the actual loops before adding threads or SIMD. The paper's historical processor timings are not Apple M4 measurements. [Paper](https://www.cidrdb.org/cidr2005/papers/P19.pdf) |
| Abadi, Myers, DeWitt and Madden, *Materialization Strategies in a Column-Oriented DBMS*, ICDE 2007 | Passing positions and delaying tuple construction can save work, but late materialization can lose when it forces expensive rescans. Selectivity and execution structure matter. | Reuse selected row positions and gather only required output columns. Measure both sparse and dense selections. A selection view is a later API/storage design, not necessary for completing typed filtering now. [Paper](https://www.cs.umd.edu/~abadi/papers/abadiicde2007.pdf) |
| Mühleisen and Raasveldt, DuckDB *Parallel Grouped Aggregation*, 2022 | Hash matches require key equality checks. Linear probing benefits from locality. Independent local tables and radix partitions enable parallel aggregation without one shared mutable table. | Keep equality authoritative. Retain deterministic first-seen IDs independently of dictionary iteration. Parallel aggregation needs ordered representative reconciliation and a numerical reproducibility policy before adoption. [Implementation explanation](https://duckdb.org/2022/03/07/aggregate-hashtable) |
| pandas `get_group_index` implementation | pandas combines already-factorized column labels into integer IDs. It checks product size and compresses partial IDs before overflow. | Per-column codes can remove repeated string hashing. Never multiply cardinalities unchecked or use a combined hash as the actual group identity. Our incremental-pair design avoids Cartesian-product arithmetic altogether. [Source](https://github.com/pandas-dev/pandas/blob/main/pandas/core/sorting.py) |
| DuckDB perfect aggregate hash table | Bounded integral domains permit array-addressed grouping instead of a general hash lookup. | Keep bounded integer lookup, but use a memory budget and checked span arithmetic. Small distinct count does not imply small value range. A sparse pair of distant integers needs hashing. [Source](https://github.com/duckdb/duckdb/blob/main/src/execution/perfect_aggregate_hashtable.cpp) |
| Kuiper, Boncz and Mühleisen, *Robust External Hash Aggregation in the Solid State Age*, ICDE 2024 | Fixed-size local aggregation and partitioning address cache pressure, high cardinality and spilling. Cardinality and skew change the best execution strategy. | Benchmark tiny, moderate and near-row-count group cardinalities, skew and clustered order. A spill-capable or parallel hash engine is beyond the minimal in-memory fix. [Paper](https://duckdb.org/pdf/ICDE2024-kuiper-boncz-muehleisen-out-of-core.pdf) |
| Williams, Waterman and Patterson, *Roofline*, Berkeley report 2008, CACM 2009 | Throughput depends on work per byte as well as available compute and memory bandwidth. | Count bytes moved and temporary storage, not only arithmetic operations. Hash workloads also have dependency/latency limits, so a floating-point roofline alone will not explain them. [Primary report](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2008/EECS-2008-134.pdf) |
| Do, Graefe and Naughton, *Efficient sorting, duplicate removal, grouping, and aggregation*, revised 2022 | Sorted input supports efficient streaming aggregation. Hash versus sort choices depend on sizes, ordering and downstream use. | Do not replace all grouping with sorting based on one benchmark. Radix sorting needs a defined total key order, extra buffers and a plan to restore first-seen output. Consider it after profiling high-cardinality cases. [Paper](https://arxiv.org/abs/2010.00152) |

## Two implementation alternatives

### A. Hash complete row keys

Use a fixed typed pair for common two-column cases or a private hash table that stores representative row indices and compares original columns when hashes match. This can read each key once per row and keep auxiliary storage proportional to groups plus the existing row IDs.

A dynamically allocated `[AnyHashable]` for every row is a poor first implementation. It replaces string allocation with another allocation and dynamic dispatch. A custom representative-row table avoids this but brings table growth, probe behavior, equality dispatch and capacity correctness into the patch. Specialized typed pairs scale badly across every type combination.

Choose this later if high-cardinality composite benchmarks show that repeated ID-buffer passes dominate. Hashing alone never establishes equality.

### B. Refine groups one column at a time

Start with the first column's exact groups. For each subsequent column, scan rows in input order and look up a fixed `RefinedKey<T: Hashable>` containing the prior group ID and the current optional value. Create a new ID on first occurrence. Replace the old IDs after that column. At the final pass, derive representatives and counts in input order.

Expected work is O(rows × key columns); live row-ID storage is O(rows), plus the current dictionary. The generic loop specializes once per column. No per-row array is required. Equivalence follows by induction: equal refined IDs mean equal prefixes and equal current values. Different hashes improve speed; dictionary equality guarantees correctness even when hashes collide.

The tradeoff is multiple ID-buffer passes and repeated hashing of common strings. Full per-column dictionary encoding can help repeated operations, but storing all code arrays costs O(rows × key columns). Reuse codes only with a clear invalidation/ownership contract. For this branch, choose refinement and benchmark it against a fixed-pair reference.

## Equality requirements before implementation

- `nil` is its own component value. Empty strings, `"null"`, `"__null__"` and delimiter-containing strings remain ordinary distinct strings. A tuple boundary must not depend on delimiter escaping.
- Preserve first appearance for group order and representatives. Do not expose randomized dictionary order.
- Preserve exact native integers and Int64 values, including adjacent values above 2^53. Do not convert grouping keys through Double.
- A hash collision is two unequal keys landing at the same hash. A serialization collision is two unequal tuples converted to the same text. Swift Dictionary handles the former; it cannot repair the latter.
- Decide float semantics explicitly. Recommended grouping policy: positive and negative zero group together; all NaN payloads group together; nil remains distinct from NaN; infinities retain sign. Canonicalize only dictionary identity and retain the original first representative for output. This is a proposed semantic correction because the current string conversion distinguishes signed zero. Ordinary floating-point equality cannot itself provide NaN reflexivity.
- Scientific libraries differ. pandas treats NaN as missing for grouping, whereas DuckDB treats NaN as an equal, ordered numeric category. Neither silently determines SwiftSci's contract. [pandas null grouping](https://pandas.pydata.org/docs/user_guide/groupby.html), [DuckDB numeric rules](https://duckdb.org/docs/current/sql/data_types/numeric).
- Canonical Float/Double keys can use unsigned bit patterns, mapping zero to one pattern and NaN to one pattern. Keep validity separate. Use the same semantics in typed and erased paths.
- `SupportedType` is Hashable, but `AnyColumn.value(at:) -> Any?` does not guarantee hashability or equality. Built-in runtime values can use typed/canonical dispatch. Arbitrary custom Hashable values can use AnyHashable, with a runtime type tag where type identity is part of equality. Arbitrary non-Hashable custom values cannot be grouped exactly through the current protocol. String descriptions are insufficient. This is an API limitation that must be documented or solved through an equality/grouping hook, not hidden behind a supposedly universal fast path.
- Existing group key output is `TypedColumn<String>` built from representatives. Internal exact grouping can improve while preserving that output format. Changing output dtypes is a separate compatibility decision.

## Required checks and measurements

Correctness cases: null versus literal sentinel, empty strings, delimiter collisions, repeated tuples, reversed column order, signed zeros, several NaN bit patterns, infinities, Int limits, Date precision, Bool, custom Hashable values with intentionally constant hashes, and custom AnyColumn fallback behavior. Verify aggregate/transform output and first-seen representatives, not just group count.

For timing, vary rows, key count, cardinality, selectivity, null density, string length, skew, clustering and numeric width. Record group-ID construction separately from aggregation and result construction. Report peak and temporary memory alongside time. Typed filtering should cover Float, Int32 and native Int without converting all keys to Double. Preserve SwiftSci's existing null and comparison semantics.

A useful first commit sequence is native Int correctness, typed filtering completeness, null-count reuse for rename, then exact grouping with an independent reference implementation. Cache-sized execution, persistent factorization and storage layout changes can follow on the compact-storage branch.
