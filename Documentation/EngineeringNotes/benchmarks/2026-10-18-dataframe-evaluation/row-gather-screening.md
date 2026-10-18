# Row-partitioned gather screening

2026-10-18. S1 trial, based on implementation commit `d23bf7cac92fe9f9c10bd98046ca8ade354b5a3c`. Trial branch `codex/dataframe-row-partition-gather-trial`. This plan precedes candidate measurements.

The hypothesis is that large narrow dataframes leave useful CPU parallelism unused because each column is one task. Partitioning each destination column by row range may reduce complete gather and sorting time. It may also lose time to dispatch, destination initialization or memory bandwidth. This experiment does not change the sort permutation algorithm or public column representation.

The baseline and candidate use one frozen public-API harness. Generate the same input before timing. Time either `DataFrame.gathered(at:)` with a prepared stable permutation or complete `sortBy`. Retain the complete output through the end timestamp. Afterward check all columns, order, types, null counts and Double bit patterns against the reference permutation. Do not time reference sorting, validation or source construction.

The candidate partitions only sufficiently large selections. Small inputs retain the existing gather. Its initial target is at least 32,768 rows per task, with total logical tasks bounded by available CPU count across columns. This is an initial scheduling hypothesis, not a measured cache boundary or active thread count. Borrow source and permutation buffers, write disjoint ranges in a single final column allocation, join before ending the borrow, and aggregate per-partition null counts. No chunk payload arrays, final concatenation, extra permutation or change to integer precision is permitted. Existing custom column conformers keep their current gather implementation.

Screen these inputs with five paired fresh-process rounds, counterbalanced baseline/candidate order, two warmups and five timed samples. Use native CPU scheduling on AC power and run one process at a time.

- Protected inputs: 129, 4,096 and 32,768 rows, widths 1, 2, 4 and 16.
- Primary inputs: 100,000 and 1,000,000 rows, widths 1, 2, 4 and 16, random finite numeric columns.
- Semantic controls: 100,000-row repeated keys, ascending and descending runs, nulls and sparse validity; 100,000-row mixed String/Bool columns at widths 2 and 4.
- Run isolated gather and complete sorting. Public CSV-stream and wine/scientific controls follow if the candidate remains promising.

Retain each process median, paired ratios, full range and raw samples. Whole-process peak RSS includes construction and validation, so report it separately from the algorithm-visible allocations. Source and final payload sizes are unchanged. Added algorithm-visible state consists of borrowed-pointer metadata and at most one Int null counter per logical task. GCD may allocate internally; this accounting is not an allocation trace. Keep the largest source-plus-destination case below 1 GiB and run serially. No energy claim is possible from elapsed time or RSS.

This is screening, with no default-policy promotion. A candidate proceeds to held-out confirmation only if a primary complete-sort case has a consistent absolute saving beyond its paired process variation, protected cases show no repeatable slowdown, and ownership checks pass. Choose usefulness and memory bounds for confirmation from the pilot before collecting confirmation. Different row counts, widths and data distributions must be reserved for confirmation. If the candidate has no useful complete-operation benefit, preserve the evidence and reject it without adding a production dispatcher.

## Specialization control

The first protocol-witness candidate failed the primary performance screen. Its 100,000-row narrow complete sorts were about 2.57 to 3.18 ms against 1.61 to 1.74 ms for the baseline; the corresponding million-row cases also regressed. Screening stopped after this clear failure, so its unrun wide and semantic timing cases are not passing evidence. Correctness and sanitizer results remain separately recorded.

The first object file contains a generic `TypedColumn.gathered(at:partitions:)` loop with metadata-dependent strides and indirect calls. Replacing the new internal protocol with a concrete-type switch produces explicit specializations in the object file. This removes the speculative protocol while retaining the generic source implementation and all public interfaces. Preserve both variants and compare the specialized candidate against the original baseline.

Also build a specialized serial control. Its source differs only by replacing the row `concurrentPerform` loop with a serial task loop. It retains the same partition ranges, output initialization, counters and concrete dispatch. Column-level scheduling remains as before. This contrast includes compiler differences caused by the dispatch boundary; it does not measure pure hardware parallelism independently of generated code. Use it on primary narrow numeric and mixed cases after the main screen, with the same paired process repetitions. The temporary control source is saved with its build receipt; the trial branch retains the row-parallel implementation.
