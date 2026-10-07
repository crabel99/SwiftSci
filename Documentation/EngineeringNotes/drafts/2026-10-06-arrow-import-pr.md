Arrow imports repeatedly search chunk boundaries for each row. With Arrow 21.0.0, empty chunks can also crash that lookup. Date32 import requests the wrong generic array type, and the dependency's date accessor reads signed days as unsigned values.

Traverse each chunk once through Arrow's existing accessors, preserving owned TypedColumn values and per-type null policies. Import canonical date32 arrays through the signed Int32 accessor and widen before converting days to seconds. The related [Arrow correction](https://github.com/apache/arrow-swift/pull/194) is merged upstream; this change retains Arrow 21.0.0.

## Dependency and review scope

Depends on #60. Merge that prerequisite first. Until then, GitHub's main-based comparison includes its dependency and LLM compatibility commits. The [Arrow-only diff](https://github.com/crabel99/SwiftSci/compare/409e6ee545b88c22b83520845660c27ec584125d...c8e4629018f1cebcecfc018cd715701400c8ebdf) contains two commits and three files: ArrowTableBridge.swift and two regression-test files.

The public API and owned-copy semantics remain unchanged. Retained Arrow storage, date64 support, and the broader memory-kernel work are outside this PR.

## Validation

- Full local Release suite on exact head `c8e4629018f1cebcecfc018cd715701400c8ebdf`: **1,156 passed, zero failed, 2 skipped**. Counts are test definitions, including parameterized tests. The skips require the optional pinned tokenizer fixture.
- Regressions cover empty and all-empty chunks, different chunk boundaries, integer limits and values above 2^53, NaN versus null, signed zero, infinities, Boolean values, Unicode, all null strategies, signed date32 extremes, producer mutation, and source-buffer release.
- The empty-chunk and canonical date32 regressions failed before the corresponding fixes. Existing dataframe, Arrow, Feather, matrix, CSV, JSON and Parquet tests are included in the passing suite.
- Independent standards and behavior reviews found no issues. Hosted CI for this PR is pending.

## Performance evidence

The previously completed matched comparison used normal Release builds on Apple M4 Max, 128 GiB RAM, macOS 27 and Swift 6.4. Both workers used official MLX Swift 0.32.3; only ArrowTableBridge.swift differed in production code. The current bridge is byte-identical to the measured implementation.

Median of three fresh-process runs per workload, alternating before/after order. Each worker imports four numeric columns, selects rows, gathers values and constructs a checked Double matrix. Timing excludes fixture creation, memory sampling and correctness checks. All 42 complete outputs matched the deterministic oracle.

| Workload | Before, ms | After, ms | Speedup |
| --- | ---: | ---: | ---: |
| 1k rows, one chunk | 0.198 | 0.060 | 3.33× |
| 100k rows, no nulls | 17.924 | 4.607 | 3.89× |
| 1M rows, one chunk | 178.749 | 47.254 | 3.78× |
| 1M rows, 32 chunks | 813.501 | 47.737 | 17.04× |
| 1M rows, 32 chunks, sparse selection | 796.604 | 42.053 | 18.94× |
| 100k rows, five matrix extractions | 33.093 | 5.062 | 6.54× |
| 1M rows, ten matrix extractions | 221.200 | 84.545 | 2.62× |

One-million-row import allocation was 64,029,856 bytes in both versions. These measurements establish speed improvements for this owned-import pipeline, not reduced allocation or whole-library performance. Float, Boolean, String and date compatibility have test coverage but no new timing survey.

Historical benchmark fingerprints are preserved: upstream base `0d0de4bea8e892dc1abc32be7878160d7f777109`, measured patched head `cd6b8218b1adcebd0a43d0382270623e902a125e`, and ArrowTableBridge.swift SHA-256 `af067255f6eb8ca9a39b244306465e579babc1c20ba44106f95bbfdc7944eac4`. These are prior measurements, not a new benchmark run on the final PR head.
