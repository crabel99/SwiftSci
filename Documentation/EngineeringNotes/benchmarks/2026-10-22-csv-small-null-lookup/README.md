# Bounded String null lookup in CSV reads

## Decision

Use direct native String equality comparisons for nonempty null sets containing at most two tokens. Empty sets and sets with more than two tokens retain hashed lookup, including the default ten-token set.

The local implementation is commit `680ac74b96ab6c6968d83a9511ebdce69d30093b` on `codex/csv-small-null-lookup`. Its frozen parent is `46a9b9bf951918cd2eb281dadf554efb30c7b0a0`, the [vector mask reduction](../2026-10-22-csv-vector-mask-reduction/README.md).

On the two-token household contracts, eager reads use 13.4–15.6% less process CPU time and streaming reads use 12.3–16.1% less. The date-parsing variant saves 7.9–11.3% on eager reads. Air-quality eager reads range from 0.5% to 6.9% less CPU. Several numeric/date-only cases become slightly slower, up to 3.0% in the reference matrix.

The numeric/null controls include a 5.6% CPU increase on a high-null inferred read. The original text controls include a 6.3% CPU increase on an all-String default-set case and a 7.3% increase on a four-token mixed-type case. The additional default-control medians range from 4.6% less to 2.7% more CPU. Default-configured air-quality data uses 3.1% more CPU in parallel and 1.5% less in serial. These results do not establish zero overhead on the fallback paths. Both observation sets remain visible.

The largest observed median peak-RSS increase in the original final reference/control matrices is 0.31 MiB. The candidate adds a bounded Array only for small nonempty sets. It does not demonstrate a memory reduction. The CPU benefit is conditional on null-set cardinality and workload, rather than a universal improvement in CSV performance.

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

| Input and schema | Policy | CPU ms, parent → final | CPU change | Elapsed ms, parent → final | Peak RSS MiB, parent → final |
|---|---|---:|---:|---:|---:|
| eager bike-day known | parallel | 0.846 → 0.841 | -0.5% | 0.457 → 0.476 | 7.69 → 7.77 |
| eager bike-day known | serial | 0.422 → 0.416 | -1.5% | 0.473 → 0.467 | 7.51 → 7.59 |
| eager bike-hour known | parallel | 5.336 → 5.457 | +2.3% | 2.051 → 2.058 | 15.76 → 15.83 |
| eager bike-hour known | serial | 3.595 → 3.703 | +3.0% | 3.627 → 3.733 | 15.48 → 15.59 |
| eager unique-shuffled known | parallel | 5.804 → 5.857 | +0.9% | 5.146 → 5.190 | 12.30 → 12.38 |
| eager unique-shuffled known | serial | 5.683 → 5.808 | +2.2% | 5.721 → 5.836 | 12.27 → 12.36 |
| eager Aotizhongxin known | parallel | 12.439 → 11.879 | -4.5% | 4.849 → 4.541 | 23.06 → 23.12 |
| eager Aotizhongxin known | serial | 8.970 → 8.348 | -6.9% | 9.038 → 8.388 | 22.77 → 22.85 |
| eager Wanliu known | parallel | 11.969 → 11.913 | -0.5% | 4.794 → 4.639 | 23.07 → 23.31 |
| eager Wanliu known | serial | 9.555 → 8.897 | -6.9% | 9.554 → 8.921 | 22.60 → 22.69 |
| eager energy known | parallel | 332.784 → 280.947 | -15.6% | 159.655 → 127.796 | 422.36 → 422.40 |
| eager energy known | serial | 301.471 → 261.192 | -13.4% | 301.567 → 261.337 | 421.91 → 422.00 |
| eager energy infer | parallel | 331.621 → 280.260 | -15.5% | 160.426 → 125.731 | 422.36 → 422.41 |
| eager energy infer | serial | 302.191 → 260.717 | -13.7% | 302.311 → 260.855 | 421.91 → 422.03 |
| eager energy-date-full known | parallel | 348.120 → 320.776 | -7.9% | 156.036 → 157.494 | 422.34 → 422.33 |
| eager energy-date-full known | serial | 326.758 → 289.709 | -11.3% | 326.871 → 289.860 | 421.97 → 421.98 |
| eager late-bool infer | parallel | 6.928 → 7.029 | +1.5% | 6.931 → 7.060 | 9.64 → 9.78 |
| eager late-bool infer | serial | 6.995 → 7.099 | +1.5% | 7.001 → 7.107 | 9.64 → 9.73 |
| eager late-text infer | parallel | 8.518 → 8.129 | -4.6% | 8.550 → 8.140 | 16.83 → 16.89 |
| eager late-text infer | serial | 8.456 → 8.198 | -3.0% | 8.492 → 8.215 | 16.83 → 16.88 |
| stream date-100000-1 known | parallel | 4.439 → 4.452 | +0.3% | 4.469 → 4.479 | 8.56 → 8.57 |
| stream date-100000-1 known | serial | 4.446 → 4.462 | +0.4% | 4.483 → 4.485 | 8.55 → 8.55 |
| stream bike-hour known | parallel | 5.562 → 5.527 | -0.6% | 2.064 → 2.071 | 12.91 → 12.91 |
| stream bike-hour known | serial | 3.475 → 3.489 | +0.4% | 3.511 → 3.527 | 12.56 → 12.56 |
| stream unique-shuffled known | parallel | 5.530 → 5.633 | +1.9% | 4.898 → 4.989 | 9.46 → 9.45 |
| stream unique-shuffled known | serial | 5.395 → 5.474 | +1.5% | 5.440 → 5.531 | 9.39 → 9.41 |
| stream Aotizhongxin known | parallel | 12.339 → 12.341 | +0.0% | 4.552 → 4.410 | 15.81 → 15.83 |
| stream Aotizhongxin known | serial | 8.512 → 7.974 | -6.3% | 8.571 → 8.023 | 16.08 → 16.05 |
| stream energy known | parallel | 323.368 → 271.368 | -16.1% | 148.845 → 117.827 | 138.91 → 139.05 |
| stream energy known | serial | 274.558 → 240.816 | -12.3% | 275.529 → 241.044 | 138.93 → 138.74 |
| stream energy-date-full known | parallel | 329.070 → 302.268 | -8.1% | 143.031 → 141.779 | 138.77 → 139.05 |
| stream energy-date-full known | serial | 296.280 → 263.620 | -11.0% | 296.509 → 264.279 | 138.80 → 138.79 |

The household and air-quality contracts explicitly configure two null tokens. Gains there do not establish that default ten-token lookup becomes faster. The default and larger sets retain Set lookup and have their own controls.

## Coverage beyond the reference files

The final width/null matrix includes twelve width/row combinations and five numeric null configurations. Widths are 1, 2, 4, 8, 18, and 64 at 257 and 32,769 rows. Null configurations cover inferred and explicit numeric columns at several densities.

The final text matrix contains 32 distinct byte/schema/null configurations. Null sets contain zero, one, two, four, ten, sixteen, seventeen, or 2,048 tokens. The ten-token case uses `CSVReadOptions.default.nullValues`. Requested null densities include 0%, 50%, and 90%. Exact per-column null counts, rather than requested density labels, determine validation.

Each text configuration uses either mixed Int64 and String columns or all-String columns. Input includes composed and decomposed Unicode equivalents, Kelvin-sign equivalence, empty fields, escaped quotes, and embedded newlines. Each has eight samples for the parent and candidate under both conversion policies. The [complete control tables](controls.md) retain increases as well as improvements. The [fallback follow-up](fallback-followup.md) includes the additional native-process samples.

No final reference or control median exceeds the CPU or peak-RSS review trigger. Smaller increases remain visible in the tables and raw observations.

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
