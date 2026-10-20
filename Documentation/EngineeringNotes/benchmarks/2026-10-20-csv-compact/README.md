# Compact CSV field index experiment

An eight-byte field entry substantially reduces peak memory for quoted CSV input. The thirteen-column case also uses less CPU. Other shapes still show CPU costs, including unquoted input that gains no memory benefit. Preserve the compact design as a memory-focused candidate; do not change the production default from these results alone.

This follows the [block-storage](../2026-10-20-csv-blocks/README.md) and [field-traversal](../2026-10-20-csv-cursor/README.md) experiments. Every variant starts from `546510bb7df19fc87a664bded5947c738011ee1d`. Production source is unchanged. This report belongs to `codex/engineering-notes`.

## Representation and boundary

The quoted fallback parser can store a field in eight bytes:

- A `UInt32` starting offset.
- An `Int32` length, complemented when escaped quotes are present.

The parser selects this representation once when the range's absolute end offset is at most `Int32.max`, or 2,147,483,647 bytes. It checks the absolute end, not merely the range length. This conservative bound covers both offsets and lengths without inspecting each field for overflow. Integer conversions remain checked. Above the bound, the same scanner uses full-width fields. The scanner and bounded-block builder are generic over the field representation, so the quote-state logic is not duplicated.

The block size remains 16,384 fields. Compact blocks hold 128 KiB of element storage instead of 256 KiB. This is an allocation bound, not a claim that the size matches an Apple cache. Row starts remain full-width integers. The parallel unquoted scanner still builds its original full-width flat index; it receives no compact-storage benefit in this experiment.

The public decoded field and the resulting DataFrame remain unchanged. Compact metadata does not reduce the precision of CSV values.

## End-to-end results

The final variant returns the existing two-integer packed payload from index storage, then decodes it in one common place. CPU percentages use medians of five paired ratios. Displayed CPU times are medians of worker medians; their ratio need not equal the paired result.

| Input | CPU ms, production → candidate | Paired CPU change | Peak RSS MiB, production → candidate | Held heap MiB, production → candidate |
| --- | ---: | ---: | ---: | ---: |
| Quoted, 250,000 × 4 | 12.28 → 12.45 | +1.4% | 65.11 → 40.64 | 17.63 → 15.33 |
| Quoted, 1,000,000 × 4 | 48.09 → 48.21 | +0.1% | 241.31 → 149.75 | 70.31 → 61.08 |
| Quoted, 1,000,000 × 2 | 23.07 → 24.40 | +6.5% | 116.14 → 86.73 | 39.78 → 30.55 |
| Quoted, 131,071 × 7 | 11.92 → 11.96 | −0.1% | 63.92 → 37.14 | 15.17 → 14.13 |
| Quoted, 75,001 × 13 | 19.06 → 14.93 | −20.3% | 66.97 → 38.58 | 15.05 → 15.05 |
| Unquoted, 1,000,000 × 4 | 42.30 → 43.97 | +3.8% | 159.39 → 159.33 | 61.08 → 61.08 |

The million-row four-column CPU ratios span 0.987–1.039, consistent with near parity in this run. Peak RSS falls about 38%. The thirteen-column CPU ratios span 0.730–0.833, and peak RSS falls about 42%. This wider case improved in both earlier compact comparisons as well. It warrants further investigation, but no cache counters were collected to identify the hardware mechanism.

The narrower million-row input remains a tradeoff. Its CPU ratios span 0.993–1.130. Every large unquoted pair uses more CPU, spanning 1.024–1.045, with no memory saving. Small unquoted input also shows a cost, about 7.1% or roughly 0.02 ms in its comparison. Do not hide these cases behind the wider-input gain.

The smaller index is temporary. Held output heap is unchanged relative to the previous block prototype. The retained-heap improvement against production comes from avoiding reuse of oversized discarded parser allocations, as established in the earlier experiment. Peak-memory reduction is the additional benefit of narrower index entries.

Full measurements:

- [Final payload layout against production](packed-RESULTS.md) and [held-out shapes](heldout-packed-RESULTS.md)
- [Initial compact layout against production](compact-RESULTS.md) and [held-out shapes](heldout-RESULTS.md)
- [Initial compact layout against full-width blocks](compact-active-reference-RESULTS.md) and [held-out shapes](heldout-active-reference-RESULTS.md)
- [Forced-inline trial against production](inlined-RESULTS.md)
- [Direct held-out comparison of return layouts](return-layout-heldout/RESULTS.md)

## Compiler investigation

Adding a third storage case changed the initial lookup result from the existing packed payload to a decoded offset. The compiled object contains 12 branch relocations to a separate lookup getter. The earlier full-width block object contains none. This is evidence of changed generated code, not proof that those calls explain the CPU difference.

Forcing the getter inline removes those calls but does not improve the primary comparison against production. Keep that trial as rejected evidence. The final variant instead shares the decoding step and returns the smaller packed payload. Its object also contains no separate lookup calls. A direct held-out comparison between the two compact return layouts has CPU ratio ranges crossing one for all five cases; it does not establish a general speed benefit from the return-layout change alone.

The module's machine-code section is 550,024 bytes for the earlier block prototype, 552,836 for the initial compact variant, 552,168 for forced inlining, and 554,696 for the final payload layout. The final layout therefore adds about 0.85% to this section relative to full-width blocks. These are object-section sizes, not deployed application sizes. [Code-generation evidence](codegen.json) records object hashes, commands, symbols, and relocations.

## Validation

Both compact return layouts passed:

- Seven explicit public-reader fixtures and 2,022 parser parity cases.
- 505,836 compact, full-width, and automatically selected field comparisons across 16 inputs, including ragged rows, unfinished rows, wide rows, and block boundaries.
- Layout and integer-boundary checks, including escaped lengths at the signed 32-bit boundary and full-width offsets above 4 GiB.
- Actual automatic scanner selection for ranges below 2 GiB, above 2 GiB, and above 4 GiB. A test-only wrapper calls the existing private range entry point. Sparse virtual mappings touch only the short payload pages and are released after each check. This validates address handling without scanning a multi-gigabyte file; it is not a full public-API benchmark of such a file.
- Sixteen existing tests in four CSV suites covering column null counts, null matching, numeric conversion, and numeric null fast paths. These run in separate Release builds with internal test access. This is not the full SwiftSci test suite.

Every timed numeric result passed independent shape and value validation. The audited study contains 640 full-API worker processes, 2,000 timing samples, and 240 separate memory samples. Timing includes the CSV read and output release; validation runs outside the clock. Memory workers do not warm up, and record process peak RSS before validation. Timing workers warm up twice and then measure five reads. Native CPU parallelism remains enabled. All accepted runs record AC power at both ends.

Input bytes, inferred schemas, Release settings, harness bytes, and dependency object bytes match within each pair. CPU time is summed user-plus-system time. Peak RSS and held malloc bytes describe different memory boundaries. Energy, allocation counts, bandwidth, and cache misses were not measured.

## Evidence integrity and replay

An early derived runner reused a held-out output label. Its existing-worker guard stopped new workers, but ran after writing a plan. That overwrote the original plan. The original 80 worker records are preserved under `excluded-heldout` in the archive and excluded from the audited results. The compact held-out comparison was rerun with a matching plan. No measurements were discarded because they were slow.

The replacement [paired runner](run-pair.py) separates fixture selection from result labels and creates a new output directory exclusively before writing any evidence. A [guard check](runner-guard-check.json) verifies that an existing plan remains byte-for-byte unchanged and no workers start when a directory already exists. The runner also completed the direct return-layout comparison successfully. Replay uses this runner rather than the copied per-variant scripts.

The [audit](audit.json), [audit program](audit.py), [raw evidence archive](evidence.tar.gz), and [archive hashes](evidence-sha256.json) preserve identities, commands, accepted and excluded records, and test receipts. Patches for [full-width blocks](active.patch), [initial compact storage](compact.patch), [forced inlining](inlined.patch), and [the final payload layout](packed.patch) apply to the pinned baseline.

Use [replay preparation](replay.py) with a checkout containing the baseline commit and a new output directory. It requires this machine's Xcode installation and the cached dependency objects referenced by `build.py`. Follow the printed commands. New timing results are new evidence, not a reproduction of identical historical timings.

## Next decision

Keep the memory improvement. Before production integration, determine how to preserve the unquoted path's CPU behavior and qualify the candidate with mixed types, long text, sparse values, and wider real files. If the CPU cost remains, expose the storage choice through an explicit resource policy rather than silently choosing one resource tradeoff for every caller. Do not infer a universal CPU-versus-memory exchange rate from this study.
