# Filter storage experiment

Standalone Double prototype. It measures predicate evaluation, selection allocation, and materializing every output column. It compares ordinary optional arrays with compact values and validity bits, and compares selected indices with a full bitmap and nonempty 64-row blocks.

Run only when other timing work is idle:

```sh
swiftc -O -whole-module-optimization main.swift -o probe
python3 run.py --rows 1000000 --widths 1,3,12 --repeats 5
```

Each process has two warmups. Cases are deterministically shuffled. Every result is checked outside timing against an independently generated row-wise checksum, selected-row count, and null count. Small boundary checks include nil, infinities, NaN, and signed zero. A null predicate value is excluded. Other columns preserve nulls, exact Double bit patterns, and row order.

The matrix varies selected percentages 0, 1, 10, 50, 90, 100; null percentages 0, 1, 30; clustered and shuffled selection; and column counts. Requested percentages apply before predicate null exclusion. Default shuffled selections use an independent hash stream from null placement.

Memory fields distinguish actual malloc live bytes, process high-water RSS, and calculated buffer payload. Selection payload excludes capacity slack. The current index implementation reserves half the input row count regardless of selectivity, matching SwiftSci. Bitmap and blocks reserve by input word count. Actual output heap deltas are allocator-sensitive and do not include the transient selection after it has been released. RSS includes fixture construction and reference checking. Do not interpret payload sizes as whole-process savings.

This is a storage experiment, not a SwiftSci public filter benchmark. It uses serial gather for every representation. It does not measure copying into the current optional-backed TypedColumn interface. The compact variant models a fully compact consumer pipeline. Adapting its output to existing TypedColumn requires another allocation and scan; that cost must be included before proposing partial integration.

Two additional variants account for compatibility costs. `packed_materialized` starts with a compact input, filters to compact output, and materializes the public optional output inside timing. `optional_roundtrip` starts with the current optional input, converts all columns to compact storage, filters, and materializes optional outputs inside timing. The latter tests whether a filter-only storage substitution pays its own conversion costs. Both preserve bit patterns and missingness.

The optional baseline skips gathered-null counting for null-free fixture columns, as production does. These probes still use one controlled append-based gather implementation for all selection representations. SwiftSci's production Double gather uses a preinitialized output buffer and pointer writes, and its integer gather uses `map`. The prototype isolates selection/storage tradeoffs; any winning alternative must be integrated and measured in production before committing it.
