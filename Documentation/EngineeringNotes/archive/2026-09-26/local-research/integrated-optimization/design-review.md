# Review of integrated optimization candidates

Reviewed Candidate A and Candidate B against SwiftSci `2694d303f8` and the sorting source evidence. This is a design review, not performance validation. No production edits or benchmarks were made.

## Decision

Use Candidate A for the production optimization branch. Retain Candidate B as the architecture experiment on `codex/compact-column-storage`. Both candidates agree on this division, and the source supports it. A removes specific allocation and hashing costs without changing the public eager DataFrame contract. B can remove whole intermediate frames, but it introduces ownership, schema, row-domain, and cache-lifetime decisions that need independent evidence.

Do not merge every proposed A component automatically. CSV, grouping, and sorting have separate correctness obligations and should earn separate commits and measurements. A faster parser does not justify a radix sorter that loses on common inputs.

## Correctness and compatibility

The flat CSV index is the strongest production change in either candidate. It preserves ragged row boundaries while eliminating per-row field-array reservation. Keep one scanner implementation. The public `parse` wrapper can materialize the old nested representation for actual public callers, while internal readers use the flat representation. Pointer lifetime must cover all synchronous parsing and conversion work; joined parallel workers must complete inside `withUnsafeBytes`. Do not let slices that borrow mapped bytes escape into a returned frame.

A's bounded grouping helper also fits the current design. Its domain and prefix table must use reporting-overflow arithmetic before allocation. Include the optional null slot in the checked product. IDs must be assigned while traversing the current input order, and fallback must preserve exact typed equality. The range scan and table allocation can lose when few rows span a broad domain, so applicability should account for rows, slot count, and bytes. This remains a private policy.

Both sort candidates preserve stable row positions and exact integers. Tighten the wording around NaNs. The old fallback is a compatibility behavior, not a valid total order. It uses IEEE comparisons that do not satisfy strict weak ordering with NaN. Keep it unchanged for this pass, including the regression test, and do not promise that NaNs sort last. That promise would require an explicit semantic correction.

Floating radix keys must canonicalize positive and negative zero for ordering while leaving source payloads intact. NaNs must reject the new path before performing radix scatter. Infinities and subnormals need explicit boundary tests. Descending order must invert numeric order keys, not reverse the final permutation, because reversing output would reverse equal-key row order. Nil remains last in both directions.

B correctly treats arbitrary closure filters as materialization boundaries. It also correctly scopes factorization caches to both immutable storage and row domain. A sorted selection changes first-seen group order and reduction order, even when group membership is identical. Removing that sort is not an algebraically safe rewrite for the existing API.

## Interface depth and ownership

A keeps read, sort, and group policies behind their existing owners. This is the right amount of sharing for the current branch. A common vocabulary of typed values and row positions does not require a public execution protocol.

B's private `ExecutionTable` can be a useful owner if it actually retains work across operations. Avoid adding it as a forwarding wrapper around the current eager calls. The proposed `ColumnID`, owned positions, group IDs, and validity buffers are justified only where they prevent mixing incompatible domains or centralize a real lifetime invariant.

B identifies the important compatibility issue. Public `TypedColumn.values` is a stored `[T?]` array, and clients can cast columns to `TypedColumn<T>`. A computed decode or replacement concrete column type changes observable costs or behavior. Keep that redesign on the compact branch, with materialization and client compatibility measured explicitly.

## Memory traffic and implementation risks

A's CSV field index reduces estimated offset storage from about 408 bytes per three-field row to about 80 bytes, before capacity overhead. This is an allocation model, not a measured peak-memory guarantee. The mapped source, output arrays, conversion scratch, and allocator behavior remain live. The flat index still grows with the complete input.

Bounded grouping replaces dependent hash probes with direct addressing, but still requires a domain scan and an ID pass. A 9,700-entry Int table is about 77.6 KB; that figure does not identify an Apple cache boundary. Measure allocation, domain-product fallback, and sparse input costs.

Sorting layouts should remain explicit experiments:

- Two arrays of `(UInt64 key, Int row)` records use about 32 bytes per valid row before null positions and final index extraction. They move both fields on every active byte pass.
- A fixed UInt64 key array plus two Int permutation buffers uses about 24 bytes per valid row before null positions and any final concatenation. It scatters only row IDs but indirectly loads keys on later passes.
- The existing tuple comparison sort has adaptive behavior and cached values. A near-sorted frame can favor it even if radix wins on random input.

These are conservative structural estimates to check with `MemoryLayout.stride` and allocations. Compiler lifetime shortening and Array capacity can change peak live bytes. Avoid uninitialized-pointer tricks in the first candidate; they make correctness harder to establish before showing that initialization costs matter.

B can eliminate several output gathers, but sparse views retain their full base storage. A one-percent result is not a one-percent-memory result. Its final `[T?]` conversion must be inside end-to-end measurements. B also correctly notes that an unbounded queued `AsyncThrowingStream` defeats a bounded scanner's memory promise. A pull-driven implementation or explicit nondropping backpressure is required before claiming bounded streaming memory.

## Acceptance gates

Before timing, compare every value and row position against the current public operation or an independent exact reference. Cover signed-zero payload preservation, Int extrema, adjacent integers above 2^53, duplicate ties, both directions, nil, NaN fallback, all-null and empty inputs. Add sorted, reversed, constant, random, and duplicate-heavy distributions around any size threshold. CSV and group tests must preserve the separately documented ragged-row and typed-key semantics.

Measure key preparation, permutation, gather, and complete sort separately. Public `sortBy` and filter-sort-group timings are decisive. Include narrow and wide frames, low and high null density, and peak scratch memory. Use serial alternating Release runs, inference idle, fixed inputs, and the same build and thread settings. A candidate passes only if gains exceed ordinary run-to-run variation and does not create an unexplained regression outside its selected applicability range.

Do not select a universal size cutoff from one million-row random data. Gather may dominate wide frames; allocating radix scratch may dominate small ones. An identity-permutation optimization, as used by pandas, is a separate opportunity after preserving value semantics and checking caller expectations.

Run the descending Release regression and full package suite after integrating accepted changes. Keep the prior production comparison as a before/after reference, with corrected Kiraa grouping extraction if needed. The performance result and correctness result must refer to the same output contract.

## Smallest safe sorting prototype

Start with a private, standalone Double permutation helper in the experiment package. Double is the key type in the measured bottleneck, so this gives the smallest test of the main hypothesis. Leave production `AnyColumn`, `DataFrame.sortBy`, gathering, other key types, and current NaN behavior unchanged during candidate selection.

Use a UInt64 normalized-key buffer and two Int permutation buffers. Scan `[Double?]` once to collect valid row positions, missing rows, and ordered keys. Reject NaNs and report fallback. Canonicalize zero keys. Perform stable eight-bit LSD counting passes, skipping bytes that have one bucket. Complement the ordered key for descending. Return the final source-row permutation with missing rows appended stably. Keep this helper allocation-owning and synchronous, with ordinary Swift arrays initially.

Compare against the current tuple comparator on exactly the same optional arrays, then use the resulting permutation through production `gathered` for whole-operation timing. Test both correctness and footprint before adding a size gate. If indirect key loads dominate, add the two-record-buffer variant as the second candidate; do not preemptively generalize storage. Broaden to Float and exact integer widths only after the Double hypothesis wins, using their own key widths and boundary tests.

This prototype establishes whether changing the sort algorithm is worthwhile. It does not force the compact-storage branch to adopt its temporary key buffers; that branch can later pass an already compact numeric representation into the same permutation contract.
