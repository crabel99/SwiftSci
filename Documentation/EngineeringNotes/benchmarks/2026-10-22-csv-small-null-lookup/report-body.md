# Bounded String null lookup in CSV reads

## Decision

Use direct native String equality comparisons for nonempty null sets containing at most two tokens. Empty sets and sets with more than two tokens retain hashed lookup, including the default ten-token set.

The local implementation is commit `680ac74b96ab6c6968d83a9511ebdce69d30093b` on `codex/csv-small-null-lookup`. Its frozen parent is `46a9b9bf951918cd2eb281dadf554efb30c7b0a0`, the [vector mask reduction](../2026-10-22-csv-vector-mask-reduction/README.md).

FINAL_DECISION

This change adds a private immutable lookup representation inside the existing String decoder. It changes no public API, numeric conversion, CSV grammar, batch size, concurrency policy, or retained data cache. The implementation branch contains one source change and one 69-line test file. This report and the experiments remain on `codex/engineering-notes`.

## What the profile showed

The parent profile validates complete native output before repeating reads. Each DataFrame leaves scope through a separate async function. The wide driver completes 1,000 reads and 35,064,000 rows. The household driver completes 30 reads and 62,257,770 rows. Both processes exit. These diagnostic samples are not accepted timings.

Three initial hypotheses concerned numeric digit checks, overhead around column conversion, and decimal-scale lookup. Production disassembly already removes per-digit buffer bounds checks and loads decimal powers from constant storage. The named `CSVColumnAttempt.appendRows` hotspot maps to String conversion and null membership, where the decoder hashes each parsed String even for a two-token null set. Double parsing remains visible in the profile, but this patch does not change it.

String output still requires String construction. The opportunity is to avoid hash computation when one or two equality checks can answer the same membership question. The implementation uses Swift's String equality, preserving canonical Unicode behavior. It does not assume that equal Strings have identical UTF-8 bytes or lengths.

## Rejected alternatives

The first matrix records 1,056 validated public reads across the parent and three single-factor trials. Delaying construction of the byte matcher does not show a consistent overall CPU benefit. Both linear lookup through sixteen tokens and a representation with extra one- and two-token cases improve several two-token reference reads. Their wider linear threshold performs badly on the default ten-token controls. Low-null text data uses about 43–62% more CPU. That design is rejected.

The second matrix records 1,188 validated reads. Both candidate representations limit direct comparison to at most two tokens and retain hashed lookup above that count. The array form is simpler and shows less overhead on large custom sets than the representation with separate one- and two-token cases. The final candidate also keeps empty sets on their original hashed path.

The pilots include two empty-set density labels with identical data and semantics. Both observations remain preserved. The final controller removes that duplicate byte/schema/null contract before timing. The all-String contracts are added after the pilots to expose String lookup costs independently of numeric null matching.

A third trial moves selection to the column/batch boundary using the existing generic decoder framework. It records 756 validated reads. A follow-up records 2,052 additional validated reads across the original parent, the committed candidate, and that trial. The boundary trial does not show a consistent CPU advantage, so it remains experimental. Its source and machine-code evidence are preserved.

The follow-up gives eight selected control configurations 42 fresh-process samples per implementation and conversion policy. It also checks air-quality data with the default ten-token null set using six samples per implementation and policy. These observations characterize the default/large-set uncertainty. They do not replace any original result or change a review threshold.

Pilot results choose the candidate. They do not replace the committed-source measurements below.

## Matched reference reads

Each result is the median of eight fresh processes in rotated and reversed order. Each before/after pair uses the same explicit conversion policy. CPU time is process user-plus-system time. Elapsed time measures latency separately. Peak RSS is a process high-water mark, not an allocation count or a measurement of retained DataFrame bytes.

Eager workers validate complete native types, values, null positions, and row and column order against independent input contracts. Streaming validates complete output in a separate untimed repeat. Input bytes, schema or inference, selected columns, and null tokens match. Streaming requests 10,000-row chunks. The internal 16,384-row bound stays unchanged.

REFERENCE_TABLE

The household and air-quality contracts explicitly configure two null tokens. Gains there do not establish that default ten-token lookup becomes faster. The default and larger sets retain Set lookup and have their own controls.

## Coverage beyond the reference files

The final width/null matrix includes twelve width/row combinations and five numeric null configurations. Widths are 1, 2, 4, 8, 18, and 64 at 257 and 32,769 rows. Null configurations cover inferred and explicit numeric columns at several densities.

The final text matrix contains 32 distinct byte/schema/null configurations. Null sets contain zero, one, two, four, ten, sixteen, seventeen, or 2,048 tokens. The ten-token case uses `CSVReadOptions.default.nullValues`. Requested null densities include 0%, 50%, and 90%. Exact per-column null counts, rather than requested density labels, determine validation.

Each text configuration uses either mixed Int64 and String columns or all-String columns. Input includes composed and decomposed Unicode equivalents, Kelvin-sign equivalence, empty fields, escaped quotes, and embedded newlines. Each has eight samples for the parent and candidate under both conversion policies. The [complete control tables](controls.md) retain increases as well as improvements. The [fallback follow-up](fallback-followup.md) includes the additional native-process samples.

REVIEW_STATUS

## Memory and semantics

Small sets retain a short Array of String values during conversion. Those values use Swift ownership and do not borrow CSV bytes. The Array adds bounded per-decoder metadata. Large and empty sets retain Set storage. This patch does not claim an allocation-free implementation or a universal memory reduction.

The new tests compare decoder membership with native Set behavior, including Unicode equivalence and malformed UTF-8 decoding. Public eager and streaming tests cover empty, small, default, and large sets in both conversion modes. Numeric parsing, inferred candidate order, late-failure replay, null-token priority, and output types keep their existing implementation.

## Validation

- Final Release DataFrame tests: 387 passed, zero failures or skips.
- Debug DataFrame tests: 387 passed, zero failures or skips.
- Release with Address Sanitizer: 387 passed, zero failures or skips.
- Public grammar differential: 30,720 cases match the parent digest, `e144dd63a50a7717083714de1d9e1817990a23fe5f247bbe1d5c3d49e31c6a33`.
- Final reference matrix: 512 validated workers.
- Final width/null matrix: 544 validated workers.
- Final text matrix: 1,024 validated workers.
- Fallback follow-up: 2,052 additional validated workers, with the experimental boundary-dispatch comparison kept separate.
- Standardized `tabular-smoke`, `production-default`: 190 SwiftSci and pandas responses and a matching artifact audit.
- Independent standards review: one fixture annotation corrected and confirmed, with no remaining findings.
- Independent specification review: no findings. See [review records](reviews.md).

The initial Release result preceded that test-only annotation correction. Final validation uses `small-null-release-final`, `small-null-debug`, and `small-null-asan`, whose source hashes match the committed files. These checks cover DataFrame behavior and the named tabular profile. They do not certify the full numerical, MLX, GPU, or NPU suites.

## Conditions and limits

Build receipts pin source hashes, dependency objects, compiler flags, and binary hashes. Benchmark workers are uninstrumented Release builds. The candidate module compiles for the existing `arm64-apple-macos14.0` target. That is compilation evidence, not execution on macOS 14.

Tests, sanitizer runs, builds, and diagnostic sampling finish before accepted timings start. The controllers require AC power, use warmed input bytes, run one fresh worker at a time, and record the environment. Native scheduling remains enabled within the selected conversion policy. No outliers are removed.

Review triggers are CPU median increases above 10%, or peak-RSS increases above 5% plus 8 MiB. These are investigation limits, not proof that smaller increases are zero. Unrelated host activity remains possible. The measurements do not quantify energy, FLOPs, cache hits, or instructions executed.

## Evidence

- [Reference plan](acceptance/plan.json), [medians](acceptance/summary.json), and [review triggers](acceptance/review-flags.json).
- [Width/null plan](mode-controls/plan.json), [medians](mode-controls/summary.json), and [review triggers](mode-controls/review-flags.json).
- [Text plan](text-controls/plan.json), [medians](text-controls/summary.json), and [review triggers](text-controls/review-flags.json).
- [Independent reviews](reviews.md), [grammar result](grammar-result.json), [build receipts](build-receipts), and [frozen source patch](source-change.patch.gz).
- [Fallback follow-up](fallback-followup.md), [pilot summaries](pilot-summaries.json), [standardized artifacts](standardized-artifacts.tar.gz), and [experiment sources and text inputs](experiments.tar.gz).
- [Artifact hashes](artifact-sha256.json).

Raw observations, profiling samples, disassembly, test logs, executed scripts, input contracts, and source patches accompany this report. The absolute paths describe the local run. The archive is evidence for this study, not a relocatable benchmark package.
