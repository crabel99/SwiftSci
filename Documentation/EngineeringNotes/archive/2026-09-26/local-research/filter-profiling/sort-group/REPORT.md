# Sorting and grouping optimizations

Branch: `codex/dataframe-optimizations`. Changes are committed locally.

## Commits

- `f067438b29` caches numeric value/index pairs, collects missing rows once, and stable-sorts the pairs. It dispatches on typed columns and removes the discarded Double value sort. NaN uses the existing optional-comparison path.
- `309da17ee4` uses typed optional integer keys for grouping by a single Int64, Int32 or Int column. Group order remains first-seen, result keys remain strings, and aggregation code is unchanged.

## Diagnosis

The baseline million-row probe measured sorting at 207.047 ms and grouped summation at 273.703 ms. Both missed the exploratory targets of 120 ms and 60 ms. Grouped row counts took 254.604 ms, showing that most grouped-sum time was spent building groups. Native samples showed comparison closures at the top of sorting stacks and dynamic casts, text formatting and string work in grouping. Samples are retained in this folder.

## Alternating comparisons

Each operation ran in three batches with alternating executable order, two warmups per process and fifteen measured iterations. The table reports medians of 45 samples. Full output checks passed. Raw samples, executable paths and hashes are retained in the JSON files.

| Operation | Before, ms | After, ms | Speedup |
|---|---:|---:|---:|
| sort | 213.743 | 68.419 | 3.12x |
| argsort | 206.714 | 59.168 | 3.49x |
| group | 249.548 | 22.548 | 11.07x |
| group_count | 246.600 | 18.894 | 13.05x |

The sorting result measures the combined sort patch; it does not separately attribute the gain to cached keys, typed dispatch or removal of the unused value sort.

## Validation

273 scoped tests pass in Debug and Release. Coverage includes stable ties and null placement, exact Int64 extrema and values beyond Double precision, infinities, signed zero, NaN compatibility, first-seen group order, null-only groups, empty inputs, all numeric aggregations, transforms, multiple-key fallback and high-cardinality integer groups. This is the dataframe, statistics, forecasting and independent-check suite, not every SwiftSci module.

The final matched comparison passed all output-value checks at 100,000 and 1,000,000 rows. Million-row results:

| Operation | SwiftSci, ms | Kiraa, ms | pandas/NumPy, ms |
|---|---:|---:|---:|
| Filter | 3.300 | 2.977 | 2.268 |
| Sort | 65.671 | 59.883 | 29.281 |
| Group | 21.052 | 9.285 | 4.711 |

[Complete matched benchmark report](/Users/crabel/local-ai/spl/swiftpandas/benchmark/results/20260926T001725Z/REPORT.md)

## Scope and remaining work

The grouping fast path covers a single integer key. Strings, floating-point keys and multiple-key grouping retain their prior implementation and semantics. Grouped sums still build row-index arrays and return Double aggregates. Numeric sorting still uses a comparison sort and allocates value/index pairs. Packed numeric storage, validity bitmaps and aggregation over dense group IDs remain candidates for separate measured changes.

Measurements are local CPU results on a shared Mac. The matched benchmark report records library versions, source and executable hashes, type differences and memory-measurement limits.
