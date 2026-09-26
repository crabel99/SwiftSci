# Filtering selection and storage experiments

Keep selected indices as the general production representation. A bitmap or nonempty-block representation reduces selection memory, but neither gives a broad time improvement. Compact numeric storage keeps its substantial memory benefit; converting into and out of it inside one filter generally costs more than it saves.

## Scope

This standalone Release Swift prototype measures the full predicate, selection allocation, and serial gather of every column. It measures output null counting as well. All 1,728 cases passed independent selected-row, null-count, and bit-pattern checksum checks. Small boundary checks cover nil, NaN, infinities, and signed zero.

The matrix covers selected percentages 0, 1, 10, 50, 90, 100; null percentages 0, 1, 30; shuffled and clustered selections; widths 1, 3, 12; and 100,000 or 1,000,000 rows. Percentages apply before null predicate exclusion. Nulls in other output columns are preserved.

- `screening-100k.json`: 432 cases, three timed repetitions, two warmups. Uses `main-v1.swift`.
- `confirmation-1m.json`: 432 cases, five timed repetitions, two warmups, three columns. Uses `main.swift`.
- `widths-100k.json`: 864 cases, three timed repetitions, two warmups, one or twelve columns. Uses `main.swift`.

The second version hoists compact storage's null-free validity checks out of its loops. Matrix cases run serially in deterministic shuffled order. Other team benchmark runs were paused during these measurements.

This prototype deliberately controls gather logic. It is not the exact production SwiftSci filter. Production Double gather initializes an output buffer and writes through pointers; native integers use `map`. This experiment uses append-based serial gather consistently to compare storage and selection mechanisms. Timings are evidence for accepting or rejecting prototypes, not claimed production speedups.

## Million-row results

Each ratio is candidate elapsed time divided by the optional-array/index-vector baseline for the same case. Below 1 is faster. The median column is the median of 36 case ratios, not a pooled elapsed-time ratio. Cases below baseline are descriptive counts, not statistical significance claims.

| Storage and output | Selection | Median ratio | Range | Cases below baseline |
|---|---|---:|---:|---:|
| optional | indices | 1.000 | 1.000 to 1.000 | 0/36 |
| optional | bitmap | 1.056 | 0.830 to 1.288 | 12/36 |
| optional | blocks | 1.064 | 0.299 to 1.239 | 13/36 |
| packed | indices | 1.617 | 0.975 to 8.776 | 2/36 |
| packed | bitmap | 1.139 | 0.597 to 9.340 | 12/36 |
| packed | blocks | 1.152 | 0.291 to 8.980 | 8/36 |
| packed_materialized | indices | 2.162 | 0.942 to 8.859 | 2/36 |
| packed_materialized | bitmap | 1.744 | 1.011 to 9.217 | 0/36 |
| packed_materialized | blocks | 1.814 | 1.047 to 9.030 | 0/36 |
| optional_roundtrip | indices | 4.760 | 2.346 to 31.760 | 0/36 |
| optional_roundtrip | bitmap | 4.222 | 1.817 to 32.316 | 0/36 |
| optional_roundtrip | blocks | 4.245 | 1.817 to 32.517 | 0/36 |

`packed_materialized` includes conversion of compact output back to public optional arrays. `optional_roundtrip` includes converting the input optional columns to compact storage, filtering, and constructing optional outputs. This is the relevant conversion cost for inserting compact storage only inside the current filter API.

At 100,000 rows, optional bitmap and block median ratios were 1.040 and 1.047 for one column, and 1.071 and 1.052 for twelve columns. The mixed result survives changing table width.

## Run structure matters

For clustered 50% selection at one million rows, block selection takes 0.338 times the index baseline with no nulls, 0.609 times with 1% nulls, and 1.061 times with 30% nulls. Complete 64-row blocks use a sequential gather loop. Nulls break those blocks.

Shuffled 50% selection has a median block/index ratio of 1.035. Shuffled 1% selection has a ratio of 1.162. An adaptive policy based only on selectivity would choose badly. Any later adaptive range-copy experiment should measure contiguous run structure, include its detection cost, and repeat the missing-value matrix.

## Memory

At one million rows and three Double columns:

- Optional input malloc usage is 45.8 MiB. Compact input uses 22.9 MiB without nulls and 23.3 MiB with validity bitmaps.
- For shuffled 50% selection without nulls, optional output payload is 22.88 MiB and compact output payload is 11.44 MiB.
- For that case, actual process peak RSS was 78.45 MiB for optional indices and 40.59 MiB for compact bitmap. The latter uses compact inputs and outputs throughout. It is not an achievable drop-in saving for the existing public interface.
- An index selection stores about 4 MB at 50% selection. A full bitmap stores 125,000 bytes. Nonempty 64-row blocks use about 250,000 bytes when every source block has a match. Sparse index selections can be smaller than a full bitmap.

Calculated payload sizes exclude capacity slack and allocator overhead. Actual malloc counters measure live allocations. Process peak RSS includes fixture construction and correctness checks. Per-process output heap deltas exclude the transient selection after its release. The raw result fields keep these categories separate.

## Integration boundary

Current `AnyColumn.filteredIndices` returns `[Int]` and `gathered(at:)` takes `[Int]`. A bitmap cannot replace only the selector and retain its benefit if the next step immediately rebuilds indices. A measured selection-aware path must include DataFrame dispatch and each supported column gather.

Current `TypedColumn.values` is a public stored `[T?]`. Typed access expects `TypedColumn<T>`, and sorting, reductions, comparison, serialization, and mapping consume its optional values. Compact storage needs coordinated migration of those consumers. The separate compact branch currently contains a pipeline prototype rather than a migrated production column implementation.

No production files or existing compact-storage artifacts were changed in this experiment. Keep the current general index path. Preserve the compact prototype for a full storage-and-consumer migration, and retain these block results as evidence for a later run-aware gather experiment.
