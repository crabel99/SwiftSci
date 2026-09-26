# Sorting, gathering, and shared dataflow

Read-only analysis on 2026-09-26. SwiftSci revision `2694d303f86fd1e71e32ab1633542408b669b90e`, Kiraa revision `fc5d957401f70e9d3b6b07270f7f300d488fd39f`. No performance runs or production edits were made for this note.

## What the measured result actually compares

The production benchmark sorts Float64 `value` descending, requires stable ties and missing values last, then gathers every output column. The recorded million-row medians were SwiftSci 65.40 ms, pandas 29.98 ms, and Kiraa 59.34 ms. These are complete public operations, not isolated sorting kernels. Source calls are in `production-comparison/python_bench.py:34`, `Sources/SciBench/main.swift:38`, and `Sources/KiraaBench/main.swift:39` beside this research directory. The saved report and metadata are in `../production-comparison/results/20260926T033814Z`.

The strongest next experiment is a private stable numeric permutation kernel, with the existing public `sortBy` and gather boundary unchanged. The public result, including all gathered columns, must decide whether it wins. A comparison-sort baseline remains useful for ordered data and small inputs. Compact persistent storage should remain on its separate branch.

## SwiftSci's current path

[DataFrame.swift:546](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftDataFrame/Core/DataFrame.swift:546) resolves the key column once, calls `sortedIndices`, and calls `gathered` with that permutation. [TypedColumn.swift:211](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftDataFrame/Columns/TypedColumn.swift:211) dispatches Double, Float, Int64, Int32, and Int to a specialized generic helper.

The helper at [TypedColumn.swift:325](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftDataFrame/Columns/TypedColumn.swift:325) scans the optional source into an array of `(index: Int, value: T)` plus missing row indices. It stably sorts these tuples, maps them into a new index array, then appends missing rows. This caches non-null key values and avoids optional handling during every comparison. It also moves the index and value together during the comparison sort, then allocates the final index array. There is an eager `Array(0..<values.count)` before the numeric dispatch at line 212. Whether Release removes that unused numeric-path allocation needs an allocation trace or optimized-code inspection before claiming its cost.

A non-null Double tuple is 16 bytes on the observed arm64 ABI when both fields are eight bytes. Use `MemoryLayout.stride` to verify this and each other type in the actual candidate executable. A million such tuples occupy roughly 16 MB before capacity and allocator overhead. Tuple movement and merge scratch are separate costs from the final 8 MB index array and source optional values. These are structural byte estimates, not measured resident memory or DRAM traffic.

[DataFrame.gathered:647](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftDataFrame/Core/DataFrame.swift:647) materializes all columns. At four or more columns and 10,000 or more selected rows, it gathers columns concurrently. Below that it gathers sequentially. [TypedColumn.gathered:116](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftDataFrame/Columns/TypedColumn.swift:116), [vGather:409](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftDataFrame/Columns/TypedColumn.swift:409), and [gatheredNumeric:632](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftDataFrame/Columns/TypedColumn.swift:632) use typed indexed copies and preserve cached null counts. Despite its name, `vGather` currently calls no Accelerate gather kernel. Random source accesses remain after a faster sort.

The current NaN escape at line 333 rebuilds an index array and calls the old optional comparator. IEEE `<` with NaN does not provide the strict weak ordering expected by sort. Existing `NumericSortTests.swift:51` deliberately compares this fallback with the same historical behavior. Preserve that fallback in this optimization pass, and put NaN placement into a separate semantic change if the project wants to define it. Do not describe the existing NaN order as scientifically well-defined.

## What Kiraa does

[DataFrame.sortValues:787](/Users/crabel/Documents/src/kiraa-swift-pandas/Sources/SwiftPandas/DataFrame/DataFrame.swift:787) pattern-matches a column once. With an all-valid mask, it calls [NativeArray.argsort:474](/Users/crabel/Documents/src/kiraa-swift-pandas/Sources/SwiftPandas/Core/Array/NativeArray.swift:474). This sorts integer row positions against compact contiguous values. It does not construct `(row,value)` tuples. With missing values it first separates valid and missing row positions, sorts valid positions against the raw buffer, and appends the missing positions.

[DataFrame.takeRows:611](/Users/crabel/Documents/src/kiraa-swift-pandas/Sources/SwiftPandas/DataFrame/DataFrame.swift:611) then gathers columns sequentially. [NativeArray.take:258](/Users/crabel/Documents/src/kiraa-swift-pandas/Sources/SwiftPandas/Core/Array/NativeArray.swift:258) gathers raw values; [NullableArray.take:355](/Users/crabel/Documents/src/kiraa-swift-pandas/Sources/SwiftPandas/Core/Array/NullableArray.swift:355) gathers validity bits separately and creates an all-valid bitmap when appropriate. It still allocates output and scans row positions. The default row index avoids per-row string label copying.

Kiraa also has a `VectorOps.sort` that invokes `vDSP_vsortD`. That is a value-only numeric sort. The benchmark DataFrame path above never invokes it. It cannot supply a stable row permutation by itself, and its internal algorithm or stability must not be inferred from Kiraa's source comments. The modest 65.4 versus 59.3 ms difference is consistent with both programs using a Swift comparison sort plus full materialization. It does not establish which individual cost dominates.

## What installed pandas and NumPy do

The benchmark uses pandas 3.0.6 and NumPy 2.5.3. The installed [pandas frame.py:8372](/Users/crabel/local-ai/spl/swiftsci/benchmark/.venv/lib/python3.14/site-packages/pandas/core/frame.py:8372) calls `nargsort`; line 8390 gathers blocks through the manager. Lines 8380 onward return a shallow copy when the result is an identity permutation. This is a useful optimization to evaluate independently for already-sorted frames.

Installed [pandas sorting.py:372](/Users/crabel/local-ai/spl/swiftsci/benchmark/.venv/lib/python3.14/site-packages/pandas/core/sorting.py:372) creates a missing-value mask, separates valid values and source positions, calls NumPy `argsort(kind='stable')` on the valid values, then appends missing positions. Descending order reverses both valid inputs before sorting and reverses the resulting permutation afterward. Both reversals together preserve original ordering among ties. Reversing only an ascending result would break stability.

The exact NumPy source revision is `dd88c0c19b54ad9ed3533224221285bf0873249a`, reported by the installed `numpy.version.git_revision`. Exact source files were retrieved through GitHub's content API and saved in `source-evidence/numpy-npysort_methods.cpp`, `numpy-timsort.hpp`, and `numpy-radixsort.hpp`. Older `.cpp` paths returned 404 because the current implementation uses headers.

[Exact NumPy dispatcher, lines 100-132](https://github.com/numpy/numpy/blob/dd88c0c19b54ad9ed3533224221285bf0873249a/numpy/_core/src/npysort/npysort_methods.cpp#L100) selects radix only for bool and signed or unsigned 8-bit and 16-bit integers. Float64, Float32, Int32, and Int64 use indirect Timsort in this build. The old dtype function table at lines 204-227 agrees. Local `nm -C` confirms Float64 `atimsort_impl` symbols in the installed binary. Thus the measured pandas advantage is not evidence that pandas used radix sorting for this Float64 workload. Generic NumPy documentation says integer stable sorting uses radix more broadly; the pinned implementation is the stronger evidence for our installed version.

[NumPy's indirect Timsort](https://github.com/numpy/numpy/blob/dd88c0c19b54ad9ed3533224221285bf0873249a/numpy/_core/src/npysort/timsort.hpp#L487) detects natural runs, reverses strictly descending runs, extends short runs by insertion sorting, and merges row positions. It gallops to trim already-ordered ends before merging at lines 704-747 and allocates scratch for the smaller run. The main indirect loop is lines 824-862. This avoids moving a key alongside every row index. Do not call the entire merge loop galloping; its boundary trimming is the part explicitly observed here.

[NumPy's radix helper](https://github.com/numpy/numpy/blob/dd88c0c19b54ad9ed3533224221285bf0873249a/numpy/_core/src/npysort/radixsort.hpp#L148) is still a useful design reference. It flips the sign bit for signed integer ordering, counts byte histograms, skips constant bytes, converts counts to offsets, and stably scatters indices into an auxiliary buffer for each active byte. It returns early for ordered input. This is reference material, not a claim that a direct port will beat Swift on M4 Max.

## Candidate designs and correctness constraints

Keep the public result as `[Int]`, and isolate any new algorithm behind the numeric helper. This avoids a new policy flag or exposing buffer ownership to DataFrame callers.

| Candidate | Expected advantage | Cost to measure |
|---|---|---|
| Existing tuple comparison sort | Cached optional-free keys, adaptive to ordered runs | Tuple movement, scratch, final index extraction |
| Indirect stable comparison sort with a plain key buffer | Moves eight-byte indices, closer to pandas and Kiraa | Indexed key loads, materializing compact keys from `[T?]` |
| Stable LSD radix on `(orderedKey,row)` records | Sequential key access and histogram work, fewer comparisons | Two record buffers, full record writes on each active byte |
| Stable LSD radix on indices plus separate keys | Eight-byte scatter writes and shared key buffer | Indirect key loads each pass, auxiliary index buffer, key normalization |

Radix requires an order-preserving key. Signed integers flip the sign bit without conversion through Double, preserving all Int64 values. Descending can complement the ordered key while retaining stable scatter. Floating finite numbers and infinities can map bits by complementing negative values and flipping the sign bit on nonnegative values. Normalize both signed zeros to one key so their input order remains stable. Preserve their original payload in the source, since only the order key should normalize. Keep NaNs on the existing fallback and append nil rows in their original order. Never reverse an already-sorted stable permutation to get descending order.

Check every candidate on empty/all-null arrays; duplicate ties; positive and negative zero; infinities; subnormals; Int extrema and adjacent values above 2^53; both directions; and arrays containing NaN to verify fallback parity. Add sizes near candidate thresholds and distributions with sorted, reversed, constant, duplicate-heavy, and random keys. Any histogram sum, index narrowing, or buffer sizing must be overflow-safe. A fixed UInt32 row index is not a valid universal replacement for Int.

## Hardware and integration

The current target is modern Apple Silicon. Compare data traffic, dependent loads, branch work, and output materialization on the actual M4 Max. An advertised memory bandwidth does not tell us the achieved bandwidth of a dependent indexed-load loop. Apple CPU Counters can distinguish discarded branch work and long-latency processing stalls; use them when wall-clock measurements cannot separate candidate explanations. [Apple CPU bottleneck guidance](https://developer.apple.com/documentation/xcode/addressing-cpu-bottlenecks)

Swift's standard sort guarantees stable ordering and currently uses adaptive merge sorting. Generic specialization and contiguous homogeneous buffers can remove dynamic dispatch without adding C. [Swift sorting contract](https://developer.apple.com/documentation/swift/array/sorted()), [Swift source](https://github.com/swiftlang/swift/blob/main/stdlib/public/core/Sort.swift), [Swift specialization](https://www.swift.org/blog/whole-module-optimizations/)

For scientific data, distribution matters. Natural-run algorithms adapt to ordered input, while fixed-width radix replaces comparison work with repeated scans and scatters. The comparative experiment should include both types of workload. Research on natural merge sorts gives run-sensitive bounds, but does not select the winner for a specific memory layout and processor. [Buss and Knop, Strategies for Stable Merge Sorting](https://arxiv.org/abs/1801.04641)

CSV parsing should eventually produce typed buffers without redundant string materialization, but this branch must retain `[T?]` public compatibility. A private sort-key normalization pass is allowed without committing to compact persistent storage. The compact-storage branch can later supply the same permutation helper with raw values and a validity bitmap, removing conversion rather than adding another algorithm.

Grouping and sorting can share a row-selection representation eventually. In the current pipeline `filter -> sort -> group`, each public operation materializes its output. A later query plan could compose selections and permutations, then let grouping read original typed columns in that row order. Do not remove sorting before grouping without proof. First-seen group order, first/last reductions, floating summation order, and output order can all change. A faster group index alone does not justify changing observable pipeline behavior.

Measure key preparation, permutation creation, and output gathering separately, then accept on complete `sortBy` and pipeline results. Include allocation and peak memory measurements. Perform serial Release runs with inference idle and keep the previous production fixture alongside more varied inputs. Confirm the original descending Release regression still passes. Run the full production comparison after accepting a kernel, because a local sort gain can disappear when gathering wide rows or changing downstream group order.

## Recommendation

Compare the two radix layouts against the existing implementation, with a plain-key indirect comparison sort as a reference if the radix variants have no broad win. Keep thresholds evidence-based, retain the old NaN fallback, and avoid public storage changes. The decision should account for correctness, complete operation time, auxiliary memory, and behavior on already-ordered data. The largest architectural gain may eventually come from avoiding repeated materialization across filter, sort, and group, but that belongs behind an explicit execution plan with the current eager API as the correctness reference.
