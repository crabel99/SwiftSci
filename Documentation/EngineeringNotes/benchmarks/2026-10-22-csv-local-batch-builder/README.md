# CSV worker-local batch builder

This experiment follows the [CSV streaming layout investigation](../2026-10-22-csv-stream-layout/README.md). It moves the existing mutable column builder into a local value for each batch, then returns it to the column object.

## Decision

Retain the worker-local builder as a local candidate that removes the measured household streaming regression. Final parallel streaming uses 6.8% less CPU than the Array baseline; serial streaming uses 2.2% less. Household eager reads use 1.5% to 4.2% less CPU across the checked schemas and policies. Benefits depend on the workload. Small default-token cases retain CPU increases. The initial final matrix flags one small all-String default-token case at +11.8%. A 640-worker follow-up does not reproduce that parallel penalty and has no review-limit failures, but records other default-token costs up to 9.2%. Preserve the original flag, both datasets, and the default-token optimization work item. The source is committed locally. No branch was pushed and no PR was opened.

The local source branch is `codex/csv-local-batch-builder` at `c906c3fbbb0baf1357438a7079921a6448e0c9e5`. Its parent is direct-key head `1c15702331ed68ea1bd214daf844d1c9d571dacd`. The unqualified compiler-marker branch remains separate and is not included. Nothing was pushed in this experiment. Raw measurements and engineering records stay on `codex/engineering-notes`.

## Implementation

Before the field loop, `CSVColumnAttempt.append` swaps its builder with an empty local builder. The loop mutates the local value. A second swap restores the completed builder before rejection handling. The validating Double method uses the same ownership sequence.

The transfer includes the existing array and null counter. It preserves array capacity across batches. The empty placeholder has zero reserved capacity. No data-buffer copy, parser change, worker change, cache, or new public option is requested by the implementation. The final resource results qualify observed costs rather than treating source-level ownership as an allocation measurement.

The row loop no longer mutates the builder through a class property. The same column object still owns the completed state between calls. Rejection discards the restored partial output, and draining a column resets the builder as before.

## Why the compiler-only trial was rejected

The prior screen appeared to fix the streaming regression with an inlining marker. Full source-path qualification contradicted that result. The screened and production selected executables had byte-identical instructions and constants. Explicit versus default parallel selection did not explain the difference. Changing only the program-name argument shifted CPU medians for one unchanged executable.

That setup sensitivity made the compiler marker insufficient evidence. The current branch omits it. The separate report preserves failed qualifications, the excluded build-overlapped quick reproduction, and all diagnostic controls.

The worker-local builder trial tests a structural alternative. It changes the location of repeated mutable bookkeeping while preserving parsing, output buffers, and scheduling. Shared cache-line traffic is a possible explanation for the improvement. No hardware cache-coherency counter was measured, so that physical mechanism remains unproven.

## Source-path and launcher check

The current source was compiled at the actual implementation checkout before the new lifecycle tests. Each worker checks every native output value and type against the household reference contract. Parent and candidate receive identical program-name arguments for each launcher form. Three forms vary the caller's setup. Twelve balanced orders produce 72 validated observations.

| Launcher form | Parent CPU ms | Candidate CPU ms | CPU change |
|---|---:|---:|---:|
| short | 273.363 | 258.925 | -5.3% |
| production-name | 272.791 | 259.288 | -5.0% |
| screen-name | 275.246 | 259.126 | -5.9% |

See [all source-path observations](screens.md). This diagnostic does not replace the full comparison below.

## Matched final comparison

The combined change compares with frozen Array-lookup head `680ac74b96ab6c6968d83a9511ebdce69d30093b`. Both use identical compiler flags, dependency objects, input bytes, schemas or inference, null tokens, and native scheduling. Parallel compares with parallel. Serial disables only column-conversion workers.

Every fresh-process worker validates native values, types, null positions, and row and column order. Streaming validates through a separate untimed complete read. Input is warmed, power is AC, and orders rotate and reverse. No outlier is removed. No task build, test, or profiler runs during accepted timing.

CPU is process user-plus-system time per complete read. Elapsed time is separate. Peak RSS includes the whole worker and is not an allocation count. No energy, FLOP, cache-occupancy, or hardware-counter conclusion follows from these observations.

| Input and schema | Policy | CPU ms, parent to final | CPU change | Elapsed ms, parent to final | Peak RSS MiB, parent to final |
|---|---|---:|---:|---:|---:|
| eager bike-day known | parallel | 0.796 to 0.787 | -1.1% | 0.437 to 0.451 | 7.80 to 7.77 |
| eager bike-day known | serial | 0.436 to 0.439 | +0.6% | 0.448 to 0.457 | 7.60 to 7.59 |
| eager bike-hour known | parallel | 5.204 to 5.475 | +5.2% | 2.080 to 2.107 | 15.84 to 15.81 |
| eager bike-hour known | serial | 3.732 to 3.821 | +2.4% | 3.779 to 3.849 | 15.59 to 15.55 |
| eager unique-shuffled known | parallel | 6.069 to 6.173 | +1.7% | 5.388 to 5.493 | 12.38 to 12.33 |
| eager unique-shuffled known | serial | 5.968 to 6.194 | +3.8% | 6.023 to 6.223 | 12.37 to 12.31 |
| eager Aotizhongxin known | parallel | 11.402 to 11.278 | -1.1% | 4.559 to 4.551 | 23.14 to 23.21 |
| eager Aotizhongxin known | serial | 8.899 to 8.606 | -3.3% | 8.913 to 8.651 | 22.87 to 22.86 |
| eager Wanliu known | parallel | 11.499 to 11.238 | -2.3% | 4.640 to 4.464 | 25.52 to 22.95 |
| eager Wanliu known | serial | 8.736 to 8.496 | -2.7% | 8.791 to 8.540 | 22.66 to 22.67 |
| eager energy known | parallel | 283.440 to 273.999 | -3.3% | 127.366 to 123.474 | 422.36 to 422.34 |
| eager energy known | serial | 254.825 to 250.906 | -1.5% | 254.979 to 251.346 | 422.01 to 421.95 |
| eager energy infer | parallel | 287.312 to 275.337 | -4.2% | 128.242 to 125.595 | 421.66 to 422.38 |
| eager energy infer | serial | 262.245 to 256.801 | -2.1% | 262.313 to 256.843 | 422.02 to 421.55 |
| eager energy-date-full known | parallel | 322.114 to 318.428 | -1.1% | 154.452 to 153.206 | 422.23 to 420.85 |
| eager energy-date-full known | serial | 284.626 to 278.825 | -2.0% | 284.958 to 278.890 | 421.27 to 420.56 |
| eager late-bool infer | parallel | 6.862 to 7.025 | +2.4% | 7.002 to 7.031 | 9.75 to 9.73 |
| eager late-bool infer | serial | 6.872 to 6.822 | -0.7% | 6.911 to 6.865 | 9.73 to 9.73 |
| eager late-text infer | parallel | 8.202 to 8.102 | -1.2% | 8.200 to 8.117 | 16.92 to 16.89 |
| eager late-text infer | serial | 8.287 to 8.025 | -3.2% | 8.294 to 8.057 | 16.88 to 16.89 |
| stream date-100000-1 known | parallel | 4.519 to 4.806 | +6.4% | 4.552 to 4.920 | 8.58 to 8.61 |
| stream date-100000-1 known | serial | 4.439 to 4.663 | +5.0% | 4.535 to 4.702 | 8.54 to 8.62 |
| stream bike-hour known | parallel | 5.316 to 5.410 | +1.8% | 2.037 to 2.195 | 12.89 to 13.15 |
| stream bike-hour known | serial | 3.620 to 3.550 | -1.9% | 3.723 to 3.608 | 12.55 to 12.61 |
| stream unique-shuffled known | parallel | 5.673 to 5.832 | +2.8% | 4.997 to 5.214 | 9.45 to 9.47 |
| stream unique-shuffled known | serial | 5.505 to 5.803 | +5.4% | 5.541 to 5.874 | 9.44 to 9.42 |
| stream Aotizhongxin known | parallel | 11.305 to 10.944 | -3.2% | 4.233 to 4.271 | 16.52 to 16.25 |
| stream Aotizhongxin known | serial | 8.341 to 8.062 | -3.3% | 8.349 to 8.071 | 17.80 to 15.27 |
| stream energy known | parallel | 281.429 to 262.331 | -6.8% | 122.411 to 117.473 | 139.25 to 139.25 |
| stream energy known | serial | 253.166 to 247.612 | -2.2% | 253.258 to 247.660 | 138.80 to 138.77 |
| stream energy-date-full known | parallel | 310.284 to 304.534 | -1.9% | 150.326 to 147.979 | 139.16 to 138.91 |
| stream energy-date-full known | serial | 286.536 to 283.958 | -0.9% | 286.838 to 284.108 | 138.78 to 138.84 |

The [complete controls](controls.md) include widths from 1 to 64, small and large row counts, numeric null density, all-String inputs, empty through 2,048 null tokens, long String keys and values, and Unicode-equivalent null matching.

Reference, width, numeric-null, and long-key groups have no review flags. The original text group has one CPU flag: all-String default tokens with no scheduled null injection, +11.8% or 0.459 ms. The larger default-token follow-up has zero review flags. It records -3.6% CPU for that parallel case and +7.3% for its serial counterpart. A mixed default-token case records +9.2% parallel CPU. Absolute small-read timings shift across studies, so compare within each paired study. Do not erase the original flag, aggregate those medians into one speedup, or claim a uniform default-path benefit. The largest final median peak-RSS increase is 0.71 MiB.

See the [640-observation default-token follow-up](default-followup.md). The next optimization target is the default hashed String decoder. Investigate whether the optional-value path can avoid classified-result conversion, then qualify it separately across defaults, Unicode, large null sets, and both column policies. Do not change null semantics or add a dataset-specific shortcut.

## Verification

All 391 DataFrame tests pass separately in Release, Debug, and Release with Address Sanitizer, with zero failures or skips. The 30,720-case grammar digest matches the parent. All 2,336 final resource workers validate complete native output contracts. The standard tabular-smoke production-default run produces 190 SwiftSci and pandas responses, and its artifact audit passes.

The new 62-line test file uses explicit types. Integer and validated-Double tests check accumulation across calls, null counts, draining, preservation of prior output, and rejection followed by another append. Existing parser, eager, streaming, and Unicode tests remain unchanged.

No timing assertion enters unit tests. The resource controller retains the targeted 3% parallel-household-streaming CPU detector, alongside the broader review triggers. It does not relax the benchmark policy or numerical tolerances. Passing this compiler does not establish compatibility with every CI compiler. The standard regression run is not full numerical certification.

## Evidence

- [Artifact hashes](artifact-sha256.json)
- [Complete resource controls](controls.md)
- [Source-path launcher results](screens.md)
- [Default-token follow-up](default-followup.md)
- [Final build receipt](build-receipts/production/build.json)
- [Final identity check](final-attestation.json)
- [Grammar comparison](grammar-result.json)
- [Standard benchmark artifacts](standardized-artifacts.tar.gz)
- [Combined source change](source-change.patch.gz)
- [Incremental builder change](incremental-change.patch.gz)
- [Frozen parent sources and inputs](experiments.tar.gz)

Controllers retain original absolute paths and hashes. Generated text inputs and input contracts are archived. Resolve reference-data paths on another checkout while retaining byte hashes, schemas, null policies, and native output contracts.
