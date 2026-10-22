# CSV streaming layout sensitivity

This experiment addresses the parallel-streaming CPU cost in the [direct null-key trial](../2026-10-22-csv-null-dispatch/README.md). It keeps the direct String keys and separates the typed field loop from the outer column dispatcher.

## Decision

Do not promote the compiler-boundary-only change. Its final source-path qualification reports 13.4% more CPU for parallel household streaming and fails both the broad and targeted CPU checks. Correctness passes. The screened and production selected executables have identical TEXT code and constants, so the earlier screened improvement is insufficient evidence. Subsequent launcher and local-builder controls identify setup sensitivity and a promising worker-local builder experiment, which still needs production-path qualification.

The final source is local on `codex/csv-typed-conversion-boundary` at `5db047d23e9262fa7d1e396525ab7c3f5e147baa`, based on experimental head `1c15702331ed68ea1bd214daf844d1c9d571dacd`. The earlier direct-key and Array-lookup branches remain preserved. No source branch was pushed in this experiment. Engineering reports and raw evidence stay on `codex/engineering-notes`.

## What changes

`CSVColumnAttempt.append` receives `@inline(never)`. This is the existing batch method around the typed field loop. The method handles one column batch. The method retains the existing rejected-field check and borrows its builder for the whole batch.

The marker prevents the compiler from folding those typed loops into the outer column dispatcher. No parser, value representation, null semantics, inference, batch size, allocation policy, or worker selector changes. The inner decoder and row loop remain available for specialization inside the typed method. The incremental source diff is two lines, including its intent comment.

## Diagnosis

The previous uncontaminated comparison and its 384-observation follow-up both showed higher parallel household streaming CPU with the direct-key decoder. Serial streaming and eager reads improved.

The first quick reproduction in this session overlapped a trial build. Its 32 native-output validations are retained, but its timing and resource ratios are excluded. See the [conditions exception](repro/conditions-exception.json). The subsequent 400-observation screen and final comparisons start after all builds finish.

Three independent trials test compiler boundaries. One forces the column dispatcher to inline. One keeps the typed batch method separate. One gives the small String decoder an optional-value method. All retain native output contracts, scheduling, and parsing. The [screen](screen/summary.json) records all results, including regressions and small differences. The typed-method boundary gives the best household parallel-streaming CPU result in that screen and requires no duplicate decoder implementation.

The [assembly record](assembly/summary.json) shows 868 static instruction entries in the parent's compact-record dispatcher and 1,515 in the unadjusted direct-key trial. The selected trial has no standalone specialization for that dispatcher. Instead, six typed compact-record append methods remain separate. Static entries describe emitted code, not executed instructions, FLOPs, or cache misses.

The same key-construction code remains in the selected trial. Its improved CPU result argues against key construction as the sole cause. The intervention supports a compiler inlining and specialization explanation. It does not prove the hardware-cache mechanism or rule out interaction with worker-pool timing.

## Qualification contradicts the compiler-only screen

The source-path build reproduces the streaming cost. Its selected trial and production executables have identical bytes in every TEXT section, including instructions and constants. See [section hashes](binary-sections.json). Static specialization differs from the older Array baseline, but it does not explain why the screened and production selected executables time differently.

The [additional controls](layout-controls.md) separate setup from code. Explicit versus default parallel selection produces nearly identical timings for each executable. A same-binary launcher experiment changes only the program-name argument and reports different CPU medians. That result suggests setup sensitivity. It does not isolate allocator placement, cache coherence, or scheduler behavior.

A further trial swaps the mutable builder out of the column object into a local value for each batch. It swaps the completed state back before rejection handling. This changes where the field loop mutates bookkeeping, without changing parsing, row bounds, worker policy, or data-buffer capacity. The plain local-builder trial improves household parallel streaming in the controlled screen, but its eager and serial results are mixed. It remains a research result until a source-path build and launcher variation pass.

The earlier static code-size observation therefore does not justify shipping the compiler marker. No hardware-counter claim follows from these experiments.

## Matched final comparison

Final measurements compare the combined change with frozen Array-lookup head `680ac74b96ab6c6968d83a9511ebdce69d30093b`. Each source version uses identical compiler flags, dependency objects, input bytes, schema or inference, null tokens, and native scheduling. Parallel compares with parallel. Serial disables only column-conversion workers.

Every worker validates native values, types, null positions, and row and column order against independent contracts. Streaming uses a separate untimed validation read. Processes are fresh, input is warmed, power is AC, and implementation orders rotate and reverse. No outlier is removed. No task build, test, or profiler runs during accepted measurements.

CPU is process user-plus-system time per complete read. Elapsed time is reported separately. Peak RSS includes the whole worker and is not an allocation count. These measurements do not establish energy use, cache occupancy, or hardware performance counters.

| Input and schema | Policy | CPU ms, parent to final | CPU change | Elapsed ms, parent to final | Peak RSS MiB, parent to final |
|---|---|---:|---:|---:|---:|
| eager bike-day known | parallel | 0.744 to 0.710 | -4.6% | 0.414 to 0.421 | 7.78 to 7.70 |
| eager bike-day known | serial | 0.411 to 0.415 | +1.0% | 0.442 to 0.440 | 7.59 to 7.50 |
| eager bike-hour known | parallel | 5.435 to 5.343 | -1.7% | 2.081 to 2.071 | 15.82 to 15.75 |
| eager bike-hour known | serial | 3.747 to 3.618 | -3.4% | 3.785 to 3.665 | 15.58 to 15.48 |
| eager unique-shuffled known | parallel | 6.051 to 5.911 | -2.3% | 5.365 to 5.300 | 12.43 to 12.31 |
| eager unique-shuffled known | serial | 6.051 to 5.918 | -2.2% | 6.110 to 5.967 | 12.83 to 12.33 |
| eager Aotizhongxin known | parallel | 11.918 to 11.946 | +0.2% | 4.678 to 4.753 | 23.22 to 24.87 |
| eager Aotizhongxin known | serial | 8.858 to 8.731 | -1.4% | 8.888 to 8.747 | 23.80 to 22.80 |
| eager Wanliu known | parallel | 11.664 to 11.539 | -1.1% | 4.636 to 4.519 | 22.95 to 22.84 |
| eager Wanliu known | serial | 8.686 to 8.466 | -2.5% | 8.770 to 8.516 | 22.66 to 22.60 |
| eager energy known | parallel | 278.488 to 272.397 | -2.2% | 126.431 to 122.530 | 422.43 to 422.34 |
| eager energy known | serial | 257.673 to 252.117 | -2.2% | 257.838 to 252.253 | 422.02 to 421.94 |
| eager energy infer | parallel | 278.363 to 280.137 | +0.6% | 124.854 to 122.088 | 422.42 to 422.37 |
| eager energy infer | serial | 252.278 to 251.217 | -0.4% | 252.513 to 251.884 | 422.02 to 421.94 |
| eager energy-date-full known | parallel | 320.377 to 315.854 | -1.4% | 152.785 to 151.069 | 422.07 to 422.28 |
| eager energy-date-full known | serial | 279.683 to 279.887 | +0.1% | 279.844 to 281.187 | 421.97 to 421.21 |
| eager late-bool infer | parallel | 6.700 to 6.689 | -0.2% | 6.746 to 6.749 | 9.75 to 9.69 |
| eager late-bool infer | serial | 6.790 to 6.782 | -0.1% | 6.830 to 6.831 | 9.73 to 9.69 |
| eager late-text infer | parallel | 8.056 to 8.081 | +0.3% | 8.109 to 8.123 | 16.89 to 16.83 |
| eager late-text infer | serial | 8.122 to 7.872 | -3.1% | 8.169 to 7.930 | 16.88 to 16.83 |
| stream date-100000-1 known | parallel | 4.516 to 4.440 | -1.7% | 4.568 to 4.495 | 8.57 to 8.58 |
| stream date-100000-1 known | serial | 4.471 to 4.432 | -0.9% | 4.518 to 4.497 | 8.55 to 8.59 |
| stream bike-hour known | parallel | 5.294 to 5.373 | +1.5% | 2.115 to 2.039 | 12.97 to 13.05 |
| stream bike-hour known | serial | 3.582 to 3.514 | -1.9% | 3.622 to 3.593 | 14.00 to 12.59 |
| stream unique-shuffled known | parallel | 5.503 to 5.481 | -0.4% | 4.885 to 4.865 | 9.44 to 9.46 |
| stream unique-shuffled known | serial | 5.389 to 5.410 | +0.4% | 5.446 to 5.460 | 9.41 to 9.45 |
| stream Aotizhongxin known | parallel | 12.110 to 11.704 | -3.4% | 4.351 to 4.257 | 15.63 to 15.90 |
| stream Aotizhongxin known | serial | 7.838 to 7.763 | -1.0% | 7.898 to 7.825 | 14.31 to 14.39 |
| stream energy known | parallel | 264.587 to 300.067 | +13.4% | 116.188 to 117.345 | 139.02 to 139.05 |
| stream energy known | serial | 236.894 to 227.175 | -4.1% | 237.186 to 227.309 | 138.78 to 136.48 |
| stream energy-date-full known | parallel | 305.604 to 299.406 | -2.0% | 139.426 to 140.950 | 138.85 to 138.88 |
| stream energy-date-full known | serial | 262.168 to 255.679 | -2.5% | 262.285 to 255.814 | 137.56 to 136.49 |

The [complete controls](controls.md) cover widths from 1 to 64, two row counts, numeric null density, empty through 2,048 null tokens, all-String data, long keys and values, and Unicode-equivalent null matching.

The final comparison has two review flags, both for parallel household streaming. It fails the 10% broad CPU review trigger and the stricter 3% symptom detector. Width, numeric null, text, long-key, and peak-RSS controls do not cross their review triggers. These correctness and resource results must not be summarized as a passing performance qualification.

## Verification

All 389 DataFrame tests pass separately in Release, Debug, and Release with Address Sanitizer, with zero failures or skips. The 30,720-case grammar digest matches the parent. All 2,336 final resource workers validate complete native output contracts. The standard tabular-smoke production-default run produces 190 SwiftSci and pandas responses, and its artifact audit passes.

The existing small, explicitly typed String-null tests exercise eligibility, ownership, Unicode equality, malformed UTF-8 repair, quoting, eager reads, and streaming under both column policies. No noisy wall-clock assertion is added to unit tests. The experiment controller separately detects a household parallel-streaming CPU increase above 3%, in addition to the existing broader CPU and memory review triggers. This stricter diagnostic detects the specific regression under investigation. It does not replace the library's benchmark policy or waive failures.

A passing local compiler does not establish compatibility with every CI compiler. The standard regression run is not full numerical certification.

## Evidence

- [Artifact hashes](artifact-sha256.json)
- [Complete resource controls](controls.md)
- [Trial screening table](screens.md)
- [Additional layout controls](layout-controls.md)
- [Ranked hypotheses](hypotheses.json)
- [Static assembly observations](assembly/summary.json)
- [Final build receipt](build-receipts/production/build.json)
- [Final identity check](final-attestation.json)
- [Grammar comparison](grammar-result.json)
- [Standard benchmark artifacts](standardized-artifacts.tar.gz)
- [Combined source change](source-change.patch.gz)
- [Incremental boundary change](incremental-change.patch.gz)
- [Trial patches and frozen parent sources](experiments.tar.gz)

Archived controllers retain their original absolute paths and hashes. Generated text inputs and input contracts are preserved in the experiments archive. Resolve reference-data paths on another checkout while retaining byte hashes, schemas, null policies, and output contracts.
