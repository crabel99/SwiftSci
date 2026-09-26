# SwiftSci hardware and Swift constraints

Read-only review on 2026-09-26. Repository inspected at `3387fd4189`, branch `codex/dataframe-optimizations`. No benchmarks ran in parallel with the implementation work. Recommendations below distinguish documented behavior from hypotheses needing measurements.

## What the hardware evidence supports

Apple specifies M4 Max at up to 128 GB unified memory and up to 546 GB/s memory bandwidth. This is a chip specification, not a guarantee that one CPU thread, or this algorithm, can sustain that rate. The local machine's exact SKU must be recorded before treating the maximum as its specification. Do not infer cache sizes from the product name. [Apple M4 Pro and M4 Max announcement](https://www.apple.com/newsroom/2024/10/apple-introduces-m4-pro-and-m4-max/)

A useful bound for a streaming pass is elapsed time >= bytes transferred / achieved bandwidth. Algorithmic bytes counted from arrays are useful traffic estimates, not measurements of DRAM traffic. Caches, write allocation, repeated loads, allocation, and dependency chains change the relationship. Measure a matching streaming baseline before claiming that filtering saturates bandwidth. A scalar grouping loop with dependent hash probes may be latency limited even while total bandwidth use is low.

Apple's CPU Counters distinguish instruction delivery, instruction processing and discarded work. Branch misprediction contributes to discarded work; long-latency loads can contribute to processing stalls. These give us a way to distinguish the competing explanations instead of calling every speedup a cache optimization. Correlate them with Time Profiler or signposted stages. [Addressing CPU bottlenecks](https://developer.apple.com/documentation/xcode/addressing-cpu-bottlenecks)

## What Swift contributes

Generic source code can compile to concrete specialized code when type and implementation are visible. Whole-module optimization exposes implementations across source files; an existential or an `Any` conversion inside every row is a different cost from one dispatch per column. Avoid introducing new compiler-only specialization attributes into a package declaring Swift tools 6.0. First arrange ordinary generic helpers and explicit concrete dispatch so supported compilers can specialize them. [Swift whole-module optimization](https://www.swift.org/blog/whole-module-optimizations/)

Apple explains how a homogeneous generic array permits dense storage and specialization, while heterogeneous protocol elements carry per-element dynamic types. Array copies ordinarily retain the existing buffer until mutation requires copying. Therefore renaming an immutable column can preserve its buffer and cached null count; recounting values has no semantic benefit. [Explore Swift performance, WWDC24](https://developer.apple.com/videos/play/wwdc2024/10217/)

Use `MemoryLayout<T>.stride`, not `size`, for array element traffic. Do not inspect the Optional tag through an assumed byte offset. Optional representation can use spare bit patterns, and a numeric optional can require padding. The Swift collections maintainer gives `Int` stride 8 and `Int?` stride 16 as an example and describes value buffers plus validity bitmaps, including the extra lookup on cold access. Re-measure all supported numeric types on each tested toolchain. [MemoryLayout.stride](https://developer.apple.com/documentation/swift/memorylayout/stride), [Swift collections maintainer on Optional storage](https://forums.swift.org/t/ticket-map/47244/12)

Compact storage remains a separate branch because public `TypedColumn.values: [T?]` is an observable API. This branch can reduce instruction count and redundant passes without changing that representation.

## Findings tied to the current source

- `TypedColumn.filteredIndices` handles only Double, Int64 and String. Float, Int32 and native Int fall through despite being supported numeric types. Complete concrete dispatch and retain one typed loop per column. Validate threshold conversion before the loop; never truncate a floating threshold to an integer or round an integer through Double merely to obtain a faster path.
- `sortedIndices` has Float, Double, Int32 and Int64 specialization but omits Int. Use the existing integer comparator for Int. Preserve stable ties and null placement, and keep the existing compiler-workaround comparator structure.
- `renamed` calls the public initializer, rescanning an unchanged buffer. Pass the existing `_nullCount` to the private initializer. This changes rename from a full data pass to metadata work.
- Ordinary grouped aggregation omits typed native Int dispatch. Complete numeric type coverage rather than routing native integers through per-row existential conversion.
- String grouping maps nil to a real string, `__null__`. Composite grouping concatenates descriptions separated by `||`. Both can merge distinct keys. Equality must be structural, with a distinct missing case. Hashes accelerate lookup but cannot replace equality.
- A fixed two-integer key can be a small Hashable struct. Arbitrary-width keys can use typed component IDs or typed components, but avoid allocating a new boxed object graph per row. This is a candidate to measure, not proof that a custom hash table is necessary.

The bounded integer lookup already present trades a bounded allocation and range scan for direct indexed lookups. Its 65,536-entry cap is a software policy, not a documented Apple cache boundary. Preserve fallback behavior for sparse and overflowing spans; tune only with measured cardinality/range distributions.

## SIMD, Accelerate and GPU boundaries

Accelerate provides CPU vector implementations selected for the available processor. Its presence does not establish that a function named `vGather` executes a vector kernel; the current `vGather` implementation is an indexed typed loop. A SIMD comparison followed by scalar per-lane appends can still be dominated by selection and stores. Additional conversion and packing passes count against any vector speedup. Compare the whole operation, including allocation. [Accelerate overview](https://developer.apple.com/documentation/accelerate)

Apple GPU shared resources let CPU and GPU access the same system memory, but shared memory does not remove synchronization. Private resources are GPU-only, and CPU consumption of GPU results needs the appropriate ordering. Therefore offloading a short filter is a separate hypothesis requiring command submission, packing and synchronization costs to be measured. It is more promising when several operations keep the same buffers on the GPU. No GPU or Neural Engine benefit is established by these CPU changes. [Apple GPU storage modes](https://developer.apple.com/documentation/metal/choosing-a-resource-storage-mode-for-apple-gpus?changes=_2&language=objc), [Metal synchronization, WWDC22](https://developer.apple.com/videos/play/wwdc2022/10101/)

## Integration and acceptance constraints

1. Target modern Apple Silicon, as clarified by the user after this research. The existing package minimum is inherited, not a user design constraint. Keep public optional arrays, stable sort ties, first-seen group order, and explicitly documented missing-value behavior. Any correction to a previously ambiguous comparison rule needs explicit tests and documentation.
2. Establish correctness at integer extrema and around 2^53 before timing. Include fractional thresholds, missing values, NaN/infinity, literal null sentinel strings, delimiter collisions, and multi-column tuples.
3. Test filter selectivity 0%, 1%, 50%, 99%, 100%; null density 0%, 1%, 50%, 100%; sorted and random inputs. Group tests need low/high cardinality, skew, dense ranges, sparse ranges, and composite keys.
4. Report Release latency separately for selection, gather and aggregation, plus end-to-end time, peak/live memory, allocations when actually measured, and effective algorithmic bytes per second. Do not label algorithmic traffic as measured DRAM bandwidth.
5. Inspect hot-loop SIL or assembly after timing if a generic helper remains slow. Look for per-row casts, witness calls, retain/releases and bounds checks rather than adding unsafe code indiscriminately.
6. Run performance measurements serially with local inference idle. Record model, OS/compiler, thread policy, size, distribution and warmup. Preserve corrected semantics even when a faster numerical shortcut exists.
