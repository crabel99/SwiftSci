# Selecting CSV storage once per column

Selecting the index representation once per column, then borrowing its storage during conversion, removes the measured large-unquoted CPU penalty while retaining compact-index memory savings. Keep this as the leading prototype. Original reference-file comparisons remain required before closing the segment or recommending production integration.

This follows the [broader-input qualification](../2026-10-21-csv-diverse/README.md). All variants start from production reference `546510bb7df19fc87a664bded5947c738011ee1d`. The existing packed candidate is byte-identical to that previous experiment. No production checkout, public API, default, dependency, or GitHub branch changed. These records belong only to `codex/engineering-notes`.

## Results against production

CPU percentages are medians of five paired ratios for the public read plus output release. Peak and held memory come from separate fresh workers.

| Input | Paired CPU change | Peak RSS MiB, reference to candidate | Held heap MiB, reference to candidate |
| --- | ---: | ---: | ---: |
| Unquoted numeric, 1,000,000 × 4 | −5.3% | 159.39 → 159.45 | 61.08 → 61.08 |
| Unquoted numeric, 1,000,000 × 2 | −3.1% | 87.05 → 87.05 | 30.55 → 30.55 |
| Quoted numeric, 1,000,000 × 4 | −6.1% | 241.36 → 149.83 | 70.31 → 61.08 |
| Quoted numeric, 1,000,000 × 2 | −0.6% | 116.17 → 86.81 | 39.78 → 30.55 |
| Quoted numeric, 131,071 × 7 | −6.7% | 63.97 → 37.17 | 15.17 → 14.13 |
| Quoted numeric, 75,001 × 13 | −33.3% | 66.98 → 38.64 | 15.05 → 15.05 |
| Nullable numeric, 250,000 × 8, inferred schema | −16.9% | 127.41 → 71.78 | 32.94 → 30.64 |
| Same nullable input, supplied schema | −15.3% | 127.42 → 71.77 | 32.94 → 30.64 |

Every pair for the large unquoted cases uses less CPU, including four additional shapes. The million-row four-column ratios span 0.934–0.957. This fixes the measured penalty in the previous compact candidate on those synthetic workloads without adding a material memory cost.

The million-row quoted four-column CPU result is favorable but has a range of 0.916–1.003, so one pair is near parity. The quoted two-column case is near parity overall, with ratios spanning 0.946–1.007. Their memory savings remain large. The thirteen-column quoted case improves in every pair, with ratios spanning 0.660–0.714; it is a specific workload result, not an expected universal speedup.

Both nullable eight-column modes use less CPU in every pair. Peak RSS falls about 44%. Missing values are covered by the validation, but this does not isolate missingness as the cause of the improvement.

Small inputs remain near parity. The 1,000-row unquoted case changes by +0.3%, with ratios spanning 0.938–1.063. Mixed-type cases have positive CPU medians but ranges crossing one, so no consistent improvement is established. Long-text and date cases remain near parity. Their conversion and output storage costs still dominate.

Full paired results:

- [Primary numeric shapes](scoped-primary/RESULTS.md)
- [Additional unquoted shapes](scoped-flat/RESULTS.md)
- [Small and wider quoted shapes](scoped-heldout/RESULTS.md)
- [Mixed types, nulls, long text, and dates](scoped-diverse/RESULTS.md)
- [Direct comparison with the earlier packed candidate](packed-to-scoped/RESULTS.md)

The direct packed-to-scoped comparison uses less CPU in every pair for all five primary shapes. Median reductions range from 3.9% to 10.2%, with unchanged memory. This separates the new lookup improvement from the memory change already demonstrated by compact storage.

## Implementation and ownership

The scanner, compact field format, block allocation policy, numeric conversion routines, inference rules, and public APIs are unchanged from the earlier compact candidate. This experiment changes the column builder's access to the index:

1. Choose the flat or compact representation once when starting a column.
2. Borrow the flat field buffer or outer compact-block buffer, together with the row-start buffer, using nested `withUnsafeBufferPointer` calls.
3. Run the existing typed column-building implementation against a concrete view. The generic implementation remains a single source definition for all thirteen conversion and inference loops.
4. Return the independently owned column before either borrowed buffer scope ends.

Each concurrent column builder creates its own read-only view. The owning arrays remain alive for the entire synchronous call. No view is stored in the returned column, sent to another task, or retained across an asynchronous suspension. Compact inner block arrays remain ordinarily owned Swift arrays. The full-width blocked representation above the compact range limit uses the existing owning-index fallback; large-file performance for that path has not been measured here.

The views preserve the existing row and ragged-column checks. Valid field offsets originate in the parser. Borrowing does not copy the index or change parsed numeric precision. These are internal prototype types, not a new public borrowed-memory API.

## Compiler evidence and controls

The first borrowed-flat prototype specialized the column builder but left thirteen calls to each lookup method. It did not remove the resource penalty. Inlining the small lookup methods removed those calls and improved the unquoted case, but the quoted path still used more CPU than production.

Adding a concrete compact view lets the compiler specialize that path too. The final scoped variant has distinct flat, compact, and owning-fallback machine-code implementations, with no branch relocations to the selected lookup methods in the recorded object. The per-field storage-enum choice is absent from the flat and compact views. Twelve storage-getter calls remain in the owning fallback specialization; their relocation addresses fall before the flat specialization begins. These are not calls from the flat or compact conversion loops. [Code-generation evidence](codegen.json) records object hashes, specialized symbols, lookup-call relocations, and code-section sizes. It does not prove a particular cache or processor-counter mechanism.

An [ordinary-array control](array-control/RESULTS.md) uses the same selected views and inline lookups but holds arrays instead of borrowed buffers. Compared directly with scoped buffers, it uses 5.4% more CPU for million-row unquoted input, 6.2% more for million-row quoted four-column input, and 8.8% more for million-row quoted two-column input. All five pairs are more expensive in those three cases. Memory is unchanged. This supports retaining scoped access on the tested toolchain; it does not establish that every array access or bounds check is intrinsically expensive.

The module's machine-code section grows from 554,696 bytes for the packed candidate to 581,624 bytes for scoped access, about 26.3 KiB or 4.9%. Compared with production, the increase is about 32.6 KiB or 6.1%. These are object-section sizes, not total application memory. There is no duplication of the typed loops in source, but specialization does produce additional machine code. The array control is slightly larger again at 583,544 bytes.

Preserved alternatives:

- [Borrowing the flat path without forcing inlining](borrowed-primary/RESULTS.md)
- [Inlining the flat-path and owning-index lookups](inlined-primary/RESULTS.md)
- [Ordinary arrays instead of scoped buffers](array-control/RESULTS.md)

## Validation and measurement boundaries

All six variants passed seven explicit public CSV fixtures, 2,022 parser parity cases with identical result hashes, and eight broader full-read workloads with exact type and value checks. Each also passed eight public streaming workloads in 257-row chunks, checking 4,176,384 fields against independently validated full reads.

The leading scoped candidate additionally passed:

- Sixteen existing tests in four CSV suites covering null matching, null counts, numeric conversion, and numeric null fast paths.
- 349,650 flat borrowed-versus-owning lookup checks under AddressSanitizer, including empty and ragged rows and exclusion of compact storage from the flat view.
- 505,836 compact/full-width/automatic/borrowed comparisons across sixteen inputs, including block boundaries, escaped fields, ragged rows, and unfinished input.
- Integer representation and automatic range selection checks below and above 2 GiB and above 4 GiB. The range checks use sparse virtual mappings, touch only short payloads, and release them afterward. They are not multi-gigabyte public-read benchmarks.
- Nine public-read workloads with the SwiftDataFrame module and measurement program built under AddressSanitizer: all eight broader inputs and the million-row unquoted input. Every result passed validation, with no sanitizer diagnostics. Cached third-party dependency objects were not rebuilt with instrumentation. These sanitizer runs are excluded from timing results.

The eight paired comparison sets contain 688 fresh workers, 2,150 timing samples, and 258 separate memory samples. Every timing worker warms up twice and measures five reads. Each memory worker performs one read without warmup and captures peak RSS before validation. Timing includes public API work and output release; validation and fixture creation are excluded.

Input bytes, schema mode, output contract, Release settings, dependency objects, and measurement program match within each pair. Native CPU parallelism remains enabled. Each set records AC power at both ends. Pair order alternates under normal desktop activity; no valid slow measurement is removed.

CPU is summed process user-plus-system time, not energy or FLOPs. Peak RSS is process high-water memory. Held heap is the change in malloc bytes in use while retaining the result. Allocation counts, hardware cache misses, bandwidth, energy, and P-core/E-core residency were not measured. This is focused CSV validation, not the complete SwiftSci suite or hosted CI.

## Evidence and next gate

The [audit](audit.json) and [audit program](audit.py) check source and binary identities, fixture hashes, full worker inventories, paired summaries, code-generation object hashes, and validation receipts. The [raw archive](evidence.tar.gz) and [archive/member hashes](evidence-sha256.json) preserve the evidence. Patches for [packed](packed.patch), [borrowed](borrowed.patch), [inlined](inlined.patch), [scoped](scoped.patch), and [array-control](arrays.patch) variants apply to the pinned production reference.

[Replay preparation](replay.py) exports the reference, applies patches, regenerates inputs, and verifies source and fixture identities. Builds require the recorded Xcode installation and cached dependency objects. Fresh replay preparation matched all source and fixture hashes; see the [verification receipt](replay-verification.json). That preparation check did not rebuild or repeat benchmarks. New measurements are new evidence, not identical historical timings.

Proceed with the scoped candidate to the [actual reference-data closeout gate](CLOSEOUT.md). Original UCI energy and air-quality files must be tested without changing their quoting or layout to select a preferred path. Record CPU, elapsed time, peak RSS, held heap, and correctness for each original file. No actual reference files have been downloaded or timed in this experiment. The segment remains open until that comparison and the final integration review are complete.
