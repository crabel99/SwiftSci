# Candidate A: bounded parallel stable radix

## Problem

Speed up permutation generation only for disordered `Double` columns with at least 131,072 input rows. The public `sortedIndices` and `sortBy` calls, ordering rules, storage, and gather path stay unchanged. The new path must preserve stable ties, signed-zero payloads, nulls last in both directions, and the current generic comparator fallback for any NaN. Smaller inputs and inputs accepted by the run-adaptive serial path remain serial.

## Usage (caller's view)

Callers see no new policy or type:

```swift
let ascending = try column.sortedIndices(ascending: true)
let descending = try frame.sortBy(column: "reading", ascending: false)
```

The existing Double dispatcher performs its sparse/small checks and adaptive scan. Only after that scan proves the input disordered and the complete radix preparation scan proves it NaN-free may it select the bounded parallel implementation.

```swift
// Existing private dispatch, with one deeper decision.
private func sortIndicesDouble(_ values: [Double?], ascending: Bool) -> [Int]
```

## Shape

Keep one private Double-sorting module rather than adding a scheduler or public policy. Its dominant structure is immutable transformed keys indexed by source row, two alternating valid-row index buffers, source-ordered missing rows, and per-worker histogram/offset slabs. The module derives worker count once:

```swift
private func parallelWorkerCount(validCount: Int) -> Int {
    min(ProcessInfo.processInfo.activeProcessorCount,
        validCount / 65_536)
}

private func parallelRadixIndicesDouble(
    _ values: [Double?],
    ascending: Bool,
    workerCount: Int
) -> [Int] // sketch only
```

Return to the existing serial radix function when `workerCount < 2`. Gate on total input rows at 131,072 as specified, but size workers from valid rows. This retains the sparse route and prevents tiny valid partitions.

Preparation is serial and transactional. In one complete source-order scan, build transformed `UInt64` keys, valid source indices, and missing indices. Normalize both signed zeros to one key. Complement transformed keys for descending order. If any value is NaN, discard all private preparation buffers and invoke the unchanged generic comparison fallback. Nothing has written to the returned permutation yet.

Each radix pass uses three synchronous `DispatchQueue.concurrentPerform` phases:

```swift
// workerRanges are fixed contiguous slices of the current source index buffer.
parallel workers: count digits into histogram[worker][bucket]
serial coordinator: prefix by bucket, then worker number
parallel workers: scatter their source slice into disjoint destination ranges
swap source and destination borrows
```

Prefixing bucket totals in worker order is the stability proof. Every worker reads its contiguous input slice in increasing position order. Its assigned interval for a bucket starts after all earlier workers' contributions to that bucket. No two workers write the same destination slot. Skip constant digits using the existing differing-bit mask. Six 11-bit passes still cover the key, with nine meaningful bits in the last pass.

Borrow both alternating buffers and keys across the full pass sequence. `concurrentPerform` is synchronous, so no closure outlives a borrow or array owner. Pass raw addresses through the same integer-address technique already used by gather if Swift's sendability checking rejects captured typed pointers. Keep that unsafe adaptation inside this function and document the disjoint-write proof beside it. Do not capture a mutable Swift `Array` in concurrent closures.

Approximate logical payload is the current `8N` key capacity, `8N` valid-index capacity, `8V` alternate index buffer, and `8M` missing indices, plus `workers * 2,048 * MemoryLayout<Int>.stride` for worker histograms and one 2,048-entry coordinator offset slab. At 16 workers the added histogram payload is about 256 KiB. Final output reuses the correct alternating owner when possible, then appends missing indices in source order. The input column remains alive and immutable until the synchronous function returns, so original signed-zero and all other Double bits survive later gather unchanged.

All-equal valid values never reach parallel radix if the adaptive check works as today. If they do, the differing mask skips every pass and returns source order. All-missing and very sparse inputs stay on existing comparison routes. Count products and offsets use checked `Int` arithmetic at allocation boundaries; if histogram sizing or prefix totals cannot be represented, use the existing serial route before launching workers. NaN always falls back before parallel mutation. Missing rows always append last, independent of `ascending`.

Swift Release builds are a design constraint. Keep `ascending` as the actual `Bool` API and form keys in one non-generic function. Do not split direction into generic comparator closures, given the recorded Swift 6.4 optimizer fault. Keep pointer lifetimes within explicit buffer-borrow scopes. Compile and test both Debug and Release because exclusivity, sendability, and optimizer behavior differ here.

This is a deep private module behind an unchanged public call. It hides worker selection, buffer ownership, digit planning, stability, and fallback. Callers learn nothing about radix passes or concurrency. Subtraction comes first: reuse the existing dispatcher, transforms, adaptive scan, fallback, and serial route; add only the parallel kernel and its narrow selection rule.

## Synthesis decision

Candidate A recommends bounded parallel radix as the first prototype. It preserves the current algorithm's cached-key, stable-scatter structure and adds one ownership idea: workers share reads but receive disjoint destination intervals. Prototype the chunk comparison-and-merge alternative separately under the same private dispatch seam so measurement, rather than a new public option, chooses between them.

## Tradeoffs accepted

- We accept three barriers per active radix digit in exchange for deterministic writes without locks or atomics.
- We accept per-worker 2,048-bin histograms in exchange for one stable global scatter per digit.
- We accept a serial full preparation scan in exchange for rejecting NaN before parallel mutation and preserving exact compatibility fallback.
- We accept parallel work only above a coarse threshold in exchange for leaving proven small and run-adaptive routes alone.

## Alternatives considered

The viable structural alternative is stable parallel chunk comparison sorting followed by balanced stable merges. Prepare contiguous `(UInt64 key, Int row)` records only after the full scan rejects NaN. Sort each contiguous chunk once with `UnsafeMutableBufferPointer.sort`, comparing cached keys and then row index, then merge adjacent runs into one shared scratch buffer with left-on-equal selection. Each merge level assigns disjoint input pairs and output ranges through synchronous `concurrentPerform`; swap source and scratch after each level. This has a clean ownership proof and fewer global radix barriers. It may also cost roughly 16 bytes per valid row for records, another record buffer for merging, and undocumented temporary storage inside the standard-library sort. That cost should be reported, not hidden behind a same-space claim the prototype cannot prove.

Chunk sort and merge lost as the recommendation because comparison work remains `O(V log V)`, the standard-library local sort's allocation behavior is not part of our contract, and the merge record buffers raise peak memory beside dataframe gathering. It remains the right measured control: its sequential key access may beat indirect radix traffic on some Apple silicon sizes.

A generic parallel sorting framework was rejected. It would expose scheduling concepts, broaden the affected types, and make this experiment harder to remove.

## Open questions and risks

- Does parallel radix reduce permutation time and full `sortBy` time at 131,072, 262,144, 1M, and 10M rows on the target Apple silicon, after counting barriers and memory bandwidth?
- Does chunk sort plus merge win for any tested size or disorder distribution despite its comparisons and extra record storage?
- Does peak RSS stay acceptable when radix scratch overlaps final dataframe gather allocations?
- Do Debug, Release, Thread Sanitizer, Address Sanitizer, and repeated exact-permutation tests confirm the pointer lifetime and disjoint-write proof?
- Does checked histogram sizing need an explicit serial fallback on 32-bit platforms, or can package platform constraints make that unreachable?

## Testing seam and measured falsifier

Use the existing private Double permutation function as the seam. Add an internal test-only strategy override with three values, serial radix, parallel radix, and chunk merge, without threading it into public APIs. Generate the same prepared inputs and compare each forced strategy's exact permutation against the existing serial result. Cover both directions, active-digit counts, duplicates, signed zeros with copied bit patterns, nulls, all equal, all missing, infinities, extreme finite values, NaN at the first and last positions, threshold edges, and worker-boundary ties.

Benchmark permutation generation separately from full `sortBy`. Reject parallel radix if its median permutation time does not improve by at least 20 percent at 1M disordered, mostly valid rows on the target Apple silicon, or if it raises peak RSS by more than the measured scratch accounting predicts by 10 percent. Also reject it if chunk merge is faster at both 1M and 10M with no correctness or RSS regression. These are prototype falsifiers, not a permanent dispatch policy.

## Next implementation step

Build the test-only forced-strategy seam and exact permutation oracle first, then implement the radix kernel with one digit and two workers before extending it to all active digits.
