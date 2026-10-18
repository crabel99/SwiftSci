# Candidate B: bounded stable chunk sort and merge

## Problem

The public operation already has the right shape: callers ask a column for a stable row permutation through `sortedIndices`, and `DataFrame.sortBy` gathers every column with that permutation. The experiment should change only how a disordered `Double` column produces that permutation when the input has at least 131,072 rows. Small inputs, sparse inputs, and inputs accepted by the existing run-adaptive scan keep their serial paths. NaN keeps the generic comparator fallback. The design must preserve stable ties, including `-0.0` and `+0.0`, append null rows in source order in both directions, retain the source payload unchanged, and finish all concurrent work before borrowed buffers leave scope.

## Usage (caller's view)

The caller sees no new type, option, or scheduling policy.

```swift
let ascending = try frame.sortBy("measurement")
let descending = try frame.sortBy("measurement", order: .descending)

let permutation = try frame["measurement"].sortedIndices(order: .ascending)
```

These calls keep the current behavior:

```swift
// Equal numeric values retain source order. Signed-zero payloads survive gathering.
let stable = try frame.sortBy("measurement", order: .ascending)

// Missing values remain last in both directions and preserve their source order.
let descendingWithNulls = try frame.sortBy("measurement", order: .descending)

// A Double column containing NaN uses the existing generic comparison path.
let compatibleNaNResult = try frame.sortBy("measurement")
```

The only intended behavioral difference is elapsed time on large, disordered, non-NaN Double inputs.

## Shape

### Dispatch stays private

Keep `TypedColumn.sortedIndices` and `DataFrame.sortBy` unchanged. Extend the existing private Double dispatcher at its last decision point, after the adaptive scan has rejected the serial comparison route and after a complete preparation scan has proved that every valid value is non-NaN.

```swift
private func sortIndicesDouble(
    _ values: [Double?],
    order: SortOrder
) -> [Int]

private enum PreparedDoubleSort {
    case radix(
        keys: [UInt64],
        validIndices: [Int],
        missingIndices: [Int]
    )
    case comparatorFallback
}

private func prepareDoubleSort(
    _ values: [Double?],
    order: SortOrder
) -> PreparedDoubleSort
```

`prepareDoubleSort` is a private sketch, not a request to add a lasting enum if the existing radix preparation already expresses the same branch cleanly. Per subtract-before-you-add, reuse that scan and its owners before introducing another representation. Its job is to establish three facts once: no NaN entered the optimized path, transformed keys encode the requested direction while mapping both signed zeros to one key, and `validIndices` plus `missingIndices` preserve source order.

Parallel dispatch is narrow:

```swift
private let minimumParallelDoubleRows = 131_072
private let minimumValidRowsPerWorker = 65_536

private func parallelWorkerCount(
    totalCount: Int,
    validCount: Int,
    activeProcessorCount: Int
) -> Int {
    guard totalCount >= minimumParallelDoubleRows else { return 1 }
    return max(1, min(activeProcessorCount, validCount / minimumValidRowsPerWorker))
}
```

Use the parallel path only when the result exceeds one worker. Read `ProcessInfo.processInfo.activeProcessorCount` once at the private dispatch boundary. Do not expose it as public policy and do not build a scheduler abstraction.

### Core data and signatures

The recommended prototype sorts contiguous ranges of the existing `validIndices` buffer, then merges those ranges through one equally sized scratch buffer. The immutable key array provides comparisons. A range carries stability provenance because lower ranges always contain earlier source positions.

```swift
private struct StableIndexRun {
    let range: Range<Int>
}

private func parallelStableChunkSortDouble(
    keys: borrowing [UInt64],
    validIndices: consuming [Int],
    missingIndices: borrowing [Int],
    workerCount: Int
) -> [Int]

private func stableSortChunks(
    indices: UnsafeMutableBufferPointer<Int>,
    keys: UnsafeBufferPointer<UInt64>,
    runs: borrowing [StableIndexRun]
)

private func mergePass(
    source: UnsafeBufferPointer<Int>,
    destination: UnsafeMutableBufferPointer<Int>,
    keys: UnsafeBufferPointer<UInt64>,
    runs: borrowing [StableIndexRun]
) -> [StableIndexRun]

private func stableMerge(
    source: UnsafeBufferPointer<Int>,
    destination: UnsafeMutableBufferPointer<Int>,
    keys: UnsafeBufferPointer<UInt64>,
    left: Range<Int>,
    right: Range<Int>,
    output: Range<Int>
)
```

These signatures show ownership intent. Actual Swift 6 syntax should follow what the package compiler accepts. The implementation may keep ordinary private array parameters if explicit ownership modifiers trigger a compiler issue. The non-negotiable part is the lifetime: both index buffers and the key buffer remain alive and borrowed across every synchronous `concurrentPerform`, and no closure escapes.

Each initial range is contiguous and deterministic. Divide `validCount` into `workerCount` ranges with sizes differing by at most one. No range is empty. Worker `i` sorts only its range in place using a stable comparison over transformed keys. For equal keys, it retains input order. Since `validIndices` entered each range in source order, this preserves ties within a run.

```swift
with borrowed keys and mutable validIndices {
    concurrentPerform(iterations: runs.count) { runID in
        stable-sort validIndices[runs[runID].range]
        compare keys[validIndices[position]]
        choose left element when keys are equal
    }
}
```

Do not call an unstable standard sort with row index as an explicit tiebreaker unless measurement shows the stable local routine is untenable. That changes the algorithm being compared and risks making signed-zero stability depend on a second ordering rule. The prototype should use the same stable comparison helper as the serial cached-value path if it can operate on index ranges without allocating pair arrays. Otherwise, add one private range sorter beside this algorithm, not a public sorter or framework.

Merge passes pair adjacent runs. Each pair owns one disjoint destination range, so a `concurrentPerform` iteration writes no byte touched by another iteration. An unpaired run copies to the identical destination range. `stableMerge` chooses from the left run when keys compare equal. That one rule preserves global source order because the left run always precedes the right run in the original valid-index sequence.

```swift
var source = validIndicesBuffer
var destination = scratchBuffer
var runs = initialRuns

while runs.count > 1 {
    let jobs = adjacentPairs(runs)
    concurrentPerform(iterations: jobs.count) { jobID in
        let job = jobs[jobID]
        if job has two runs {
            stableMerge(source, destination, job.left, job.right, job.output)
        } else {
            copy source[job.output] to destination[job.output]
        }
    }
    swap(&source, &destination)
    runs = mergedRuns(jobs)
}

if source is scratchBuffer {
    swap array ownership, rather than copy V indices
}
append missingIndices to the final owner
```

`concurrentPerform` is synchronous. The caller does not append missing indices, swap owners, or end any pointer borrow until it returns. The closures capture immutable job metadata and raw buffer addresses only. If Swift rejects capturing mutable buffer-pointer values as `Sendable`, pass addresses through an integer representation as the existing gather does, reconstruct pointers inside the closure, and document the disjoint-write proof at that line.

### Scratch and source lifetime

The chunk design reuses the preparation data already needed by radix ordering:

- transformed keys: approximately `8N` bytes;
- valid row indices: logical `8V` bytes, with the existing implementation possibly reserving `8N`;
- missing row indices: `8M` bytes;
- merge scratch: `8V` bytes;
- run and merge-job metadata: `O(W)` records, where `W` is the bounded worker count.

There are no per-worker copies of keys or indices. A local stable range sorter must not allocate `O(chunk size)` scratch on top of the shared merge buffer. It should use the shared destination slice if its algorithm permits that, or use an in-place stable routine for the initial chunks. This is the design's sharpest implementation constraint. If the available stable range sorter requires full-size scratch per worker, reject that implementation rather than hiding a second `8V` or worse peak.

The source `[Double?]` remains borrowed through preparation only. The concurrent algorithm reads transformed keys and row indices, not Optional payloads. This keeps source lifetime simple and prevents parallel reads from becoming entangled with array representation. Gathering later reads the unchanged original column, which preserves finite payloads, infinities, subnormals, nulls, and signed-zero bits exactly.

### Edge behavior

- All-equal valid values pass through the existing adaptive run scan and should remain on the serial stable route. If they reach the prototype because thresholds change, chunk sorts and left-biased merges return the original valid-index order.
- All-missing or very sparse inputs keep the existing comparison route. Worker selection also returns one when `validCount < 131,072`, because two workers require at least 131,072 valid rows under the 65,536 rule.
- NaN discovered anywhere in the full preparation scan returns `comparatorFallback` before concurrent mutation starts. No partial permutation can escape.
- Signed zeros map to the same transformed key. Stable sort and left-biased merge retain their source order. Gathering copies the original payload bits.
- Nulls never enter a chunk or merge. Append `missingIndices` after all valid rows in both directions.
- Descending order remains encoded in the transformed key. Never reverse an ascending permutation.
- Count arithmetic must use checked construction of ranges and `Int` indices. Avoid `2 * width` loop arithmetic that can overflow. Build the next pass by advancing through the current run array in pairs. Array allocation failure remains the runtime's failure behavior; the prototype should not add speculative recovery.

### Compiler and release-build hazards

The package has a recorded Swift 6.4 Release miscompile around separated generic ascending and descending closures. This design avoids direction-specific concurrent comparator closures by transforming keys once and using one concrete UInt64 comparison everywhere. Keep `stableMerge` concrete and non-generic for the prototype.

Swift's concurrency checker does not prove that two raw-pointer slices are disjoint. A compile-time `Sendable` success is not the safety proof. The proof comes from deterministic non-overlapping ranges, one writer per destination range, read-only source buffers, and synchronous completion. Put that proof beside each `concurrentPerform`, where a future edit can invalidate it.

Optimization can expose aliasing mistakes that Debug masks. Test Release directly. In particular, source and destination must never name the same allocation during a merge pass; reconstructed addresses must keep their owners alive with `withExtendedLifetime`; and an ownership swap must happen only after all merge jobs return. Avoid nested `concurrentPerform`, since it complicates scheduling and adds no required capability.

### Module map and interface depth

Keep all new definitions private beside the current Double sorting helpers in `TypedColumn.swift`, unless file size alone justifies a private extension file. `DataFrame`, `AnyColumn`, gather code, and package-level interfaces do not change.

This is a deep private module behind an unchanged public call. It hides worker calculation, range partitioning, key transformation, stable chunk sorting, buffer ownership, merge scheduling, and null handling. Callers still provide only a column and direction. There is no pass-through scheduler object, policy enum, or public choice between radix and merge.

## Synthesis decision

Candidate B recommends stable parallel chunk comparison plus merge as the first bounded prototype. It changes less of the ordering representation than parallel radix and gives every concurrent writer one contiguous, disjoint output range. The design borrows radix's best structural property: prepare transformed direction-aware UInt64 keys once, normalize signed zeros there, and reject NaN before parallel work. It rejects a generic parallel sorting framework and per-stage public configuration because this experiment has one caller and one narrow input class.

## Tradeoffs accepted

- We accept `O(V log W)` merge traffic after local sorts in exchange for simple disjoint writes and an auditable stability proof.
- We accept one `8V` merge buffer in exchange for parallel merges with no locks and no in-place merge complexity.
- We accept comparison work inside chunks in exchange for fewer global passes than a six-pass LSD radix sort when worker-local sorting and cache behavior are favorable.
- We accept private concrete Double and UInt64 helpers in exchange for avoiding the known generic Release-compiler hazard.
- We accept idle cores when there are fewer than 65,536 valid rows per worker in exchange for bounded scheduling overhead and predictable scratch use.

## Alternatives considered

### Stable parallel LSD radix

Give each worker a contiguous source range and a private 2,048-bin histogram for each active 11-bit digit. Reduce histograms in worker order to compute disjoint bucket offsets, then let each worker scatter its source range into its assigned subrange of every bucket. Swap source and destination buffers after the synchronous pass. Worker-order offsets plus source-order traversal preserve stability. This shape has deterministic linear work and handles repeated keys well, but every active digit adds a global histogram reduction and a full `V` scatter. Six passes are possible. It also carries more offset arithmetic and a larger proof surface than chunk merge, while exposing no extra caller capability. It is the strongest competing prototype and should be measured, not dismissed.

### Parallel local sorts followed by a serial merge

This keeps local writes disjoint but leaves an increasingly dominant serial tail. Its interface is equally small, yet it hides less useful parallel capability and is unlikely to falsify the claim that permutation generation can scale on large inputs.

### A public sort policy or generic scheduler

This would let callers choose radix, merge, or worker count. It leaks experimental internals into `sortedIndices`, makes callers learn memory and stability details, and creates policy that current usage does not need. Reject it.

## Open questions and risks

- Can the existing stable cached-value sorter operate on borrowed index slices without allocating pair arrays, or does the prototype need one concrete private range-sort routine?
- Does the shared merge buffer suffice for local stable sorting, or does the chosen local algorithm add scratch that raises peak memory beyond parallel radix?
- At what valid count does parallel chunk merge beat the current serial adaptive/radix path in Release on the target Apple silicon machines?
- Does the merge-pass barrier and `O(V log W)` traffic erase gains at two workers, making the 131,072 total-row gate too low?
- Does Swift 6 Release preserve the pointer ownership and left-biased merge behavior under full optimization across repeated runs and thread counts?

## Testing seam and measured falsifier

The simplest testing seam is one private, test-visible entry that accepts precomputed transformed keys, source-ordered valid indices, missing indices, and an explicit worker count, then returns the permutation. Production computes the worker count and calls the same function. Tests can force one, two, and the maximum bounded worker count without adding public policy or mocking `ProcessInfo`.

Compare its exact permutation against the existing serial result for both directions across threshold boundaries, uneven chunk sizes, duplicate-heavy inputs, all equal values, signed-zero mixtures with bit-pattern checks, infinities, subnormals, null-heavy inputs, and NaN at the first, middle, and final source positions. Run these checks in Release and repeat enough times to expose races. Separately record permutation-only elapsed time, full `sortBy` elapsed time, and peak resident memory.

The measured falsifier is blunt: reject chunk merge if, on the target Apple silicon Release benchmark at 131,072, 1,048,576, and the largest representative row count, it fails to beat both the serial baseline and the parallel LSD radix candidate on median permutation time at any size where the parallel dispatcher selects it, or if its peak resident memory exceeds radix by more than the one documented `8V` merge buffer. Any permutation mismatch, nondeterminism, source-bit change, null-order change, NaN-path change, or Thread Sanitizer finding rejects it regardless of speed.

## Next implementation step

Prototype the test-visible precomputed-key chunk sorter with two deterministic runs and one left-biased parallel merge, then prove its exact permutation and buffer lifetime in Release before adding more workers or benchmark plumbing.
