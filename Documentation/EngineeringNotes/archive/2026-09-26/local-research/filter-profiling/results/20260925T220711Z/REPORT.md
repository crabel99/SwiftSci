# Filtering API and native profile comparison

This investigation profiles the existing local optimization candidate. It makes no further production edits. The repeatable probes live outside both source repositories.

At one million rows, the optimized SwiftSci filter takes 32.55 ms, Kiraa takes 2.94 ms, and pandas takes 2.11 ms without an extra deep copy. The primary remaining SwiftSci bottleneck is gathering its two Int64 columns through the generic TypedColumn path.

## Matched workload and method

The inputs reproduce the earlier workload: two Int64 columns, one optional Double column, 100 groups, one missing value every 101 rows, and value > 500. Exactly 494,981 rows pass. Eleven measured iterations follow two warmups. Each operation runs in a fresh process, sequentially. BLAS thread limits are one where honored. Both Swift builds use Release optimization. Timings exclude setup, result validation and JSON output.

Each stage checks its result against an independently constructed expected selection. Native macOS sample profiles run separately from timing, after setup, warmup and the initial correctness check. The sampled process repeats the operation; the driver terminates it after the three-second sample. Sampling overhead therefore does not contaminate the timing table.

## Stage measurements

| Stage | SwiftSci ms | Kiraa ms | pandas ms |
|---|---:|---:|---:|
| Full filter | 32.549 | 2.940 | 2.114 |
| Selection | 1.641 | 0.615 | 0.194 |
| Gather all three columns | 29.983 | 1.841 | 1.501 |
| Gather one Int64 column | 15.090 | 0.355 | 0.219 |
| Gather the optional Double column | 0.542 | 1.122 | 0.220 |

Selection is not identical work: SwiftSci returns row indices directly; Kiraa and pandas return Boolean masks. pandas converts the mask to indices in another 0.37 ms. Kiraa filter(mask:) takes 2.27 ms including mask-to-index conversion and all column gathers. Gather-only stages start with precomputed indices. Separate medians should not be treated as exact additive accounting.

The old pandas benchmark included an unnecessary explicit `.copy()`. With that copy it takes 2.328 ms; without it, 2.114 ms. Copying the already-selected frame alone takes 0.169 ms. This correction strengthens pandas slightly and does not explain the large SwiftSci gap.

## What each implementation does

- SwiftSci: filter(column:where:) finds row indices, then gathers every column through AnyColumn. Double has a concrete vGather implementation. Int64 uses the generic T implementation, initializes an optional array, copies generic values, and constructs a new column that scans again to count nulls.
- Kiraa: a Column enum dispatches once to its concrete Double or Int64 storage. Values live in native typed buffers; validity lives in a separate bitmap. Its take routine has an all-valid fast path and the native profiles show specialized NullableArray.take and NativeArray.take functions.
- pandas: Boolean selection calls mask.nonzero(), then DataFrame.take. The manager copies dtype-specific blocks via array_algos.take_nd, which allocates a typed output and dispatches to compiled Cython functions. Native samples show take_2d_axis0_float64_float64, take_2d_axis1_int64_int64, memmove and PyArray_Nonzero. Python coordinates those operations; it does not compare and copy every row in Python bytecode.

The exact installed pandas API was inspected locally. Its dtype blocks, shapes and strides are saved in timings.json. The current upstream [Cython take template](https://github.com/pandas-dev/pandas/blob/main/pandas/_libs/algos_take_helper.pxi.in) corroborates the typed-kernel design; it is not a version-pinned substitute for the installed 3.0.6 code or sampled binary.

## Evidence for specialization as the next target

SwiftSci spends about 30 ms in the gather stage. Each integer column alone costs about 15 ms; the Double column costs about 0.54 ms. Native samples locate the integer cost in generic copying, optional metadata handling, array access and TypedColumn initialization. The predicate itself takes only about 1.64 ms.

A diagnostic frame storing the same small integer-valued IDs and group labels in Double columns runs the full filter in 3.295 ms. Both Double? and Int64? have a measured 16-byte stride here. That control strongly implicates the generic-versus-specialized execution path; reducing the element width was not responsible. These fixture integers are exactly representable as Double. Converting real IDs to floating point is not the proposed fix.

Direct construction from one million optional values takes 18.73 ms for Int64 and 18.71 ms for Double. The fast Double gather shows that the compiler can optimize the same column construction in a concrete context. Kiraa's takingInt64s constructor is approximately O(1) for this input because it can share the existing array and mark validity as all-valid; its 0.001 ms result is not an equal-work null-scan comparison. Converting optional Double values to Kiraa's storage takes 3.63 ms.

A focused next experiment is to give Int64 gathering a concrete implementation, like the existing Double gather, while preserving Int64 storage and all null behavior. Measure that through the public DataFrame filter API, then rerun the full-value comparison and Debug/Release checks. The current evidence does not justify a wholesale bitmap-storage rewrite or a GPU implementation.

## Limits and reproducibility

These are CPU timing and stack-sampling profiles. They do not count heap allocations, measure memory bandwidth or identify exact instruction costs. The samples support generic runtime overhead as the dominant remaining issue; they do not prove a particular compiler optimization will be applied to a new implementation. The synthetic workload has roughly 50% selectivity and only three columns. Further candidates should also be checked with no matches, all matches, nullable integers, sparse/dense nulls and wider frames.

The source repositories remain at their prior states. SwiftSci retains the uncommitted null-count/type-dispatch optimization and three correctness tests. Kiraa remains clean. No upstream code was copied into SwiftSci.

Run these probes with:

```sh
cd "/Users/LOCAL_USER/local-ai/spl/swiftsci/filter-profiling"
swift build -c release --arch arm64 -j 8
/Users/LOCAL_USER/local-ai/spl/swiftsci/benchmark/.venv/bin/python run.py
```

Sources inspected:

- [SwiftSci column gathering](/Users/LOCAL_USER/Documents/src/SwiftSci/Sources/SwiftDataFrame/Columns/TypedColumn.swift:110)
- [SwiftSci frame gathering](/Users/LOCAL_USER/Documents/src/SwiftSci/Sources/SwiftDataFrame/Core/DataFrame.swift:647)
- [Kiraa frame filtering](/Users/LOCAL_USER/Documents/src/kiraa-swift-pandas/Sources/SwiftPandas/DataFrame/DataFrame.swift:553)
- [Kiraa typed take](/Users/LOCAL_USER/Documents/src/kiraa-swift-pandas/Sources/SwiftPandas/Core/Array/NativeArray.swift:258)
- [Kiraa validity handling](/Users/LOCAL_USER/Documents/src/kiraa-swift-pandas/Sources/SwiftPandas/Core/Array/NullableArray.swift:355)
- [Installed pandas dispatch snapshot](/Users/LOCAL_USER/local-ai/spl/swiftsci/filter-profiling/installed-pandas-take.py)

Raw timings, native samples, executable hashes and the candidate source diff are stored beside this report. Source and harness hashes are recorded in metadata.json.
