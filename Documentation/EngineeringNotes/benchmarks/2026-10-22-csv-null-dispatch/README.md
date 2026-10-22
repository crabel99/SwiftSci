# CSV String null keys at column construction

This experiment tests whether selecting a concrete decoder once per column reduces CPU work beyond the bounded Array lookup in `680ac74b96ab6c6968d83a9511ebdce69d30093b`.

## Decision

Keep the direct-key decoder as an experimental local branch, not an unconditional replacement for the parent. Household eager reads use 1.2% to 4.7% less CPU in the final matrix. However, parallel household streaming uses 8.7% more CPU in that matrix and 7.8% more in a 24-observation-per-implementation follow-up. Serial streaming improves in both studies. The reproducible CPU cost conflicts with the resource-efficiency goal even though it stays below the existing 10% review trigger. The parent branch remains preserved.

The source change is local on `codex/csv-inline-null-keys` at `1c15702331ed68ea1bd214daf844d1c9d571dacd`. Its parent remains preserved on `codex/csv-small-null-lookup`. No source branch was pushed by this experiment. Engineering evidence stays on `codex/engineering-notes`.

## Implementation

`CSVColumnPlan.conversion` selects `CSVSmallStringDecoder` only for one or two distinct null tokens. The decoder holds an owned `String` and an optional second `String`. It constructs the decoded field once and compares with normal Swift String equality. Empty and larger token sets use the original concrete `CSVStringDecoder` with hashed Set lookup. The parser, default tokens, public options, row bound, numeric conversion, inference, and worker selection are unchanged.

The previous private lookup-strategy enum and its Array allocation are removed. The existing column-conversion enum gains one case. The decision happens at column construction, rather than at each String field. No unsafe references or new public API are introduced.

## Matched comparison

The final comparison uses frozen parent `680ac74b96ab6c6968d83a9511ebdce69d30093b` and the final source head. Both use the same production compiler flags, dependency objects, input bytes, explicit schemas or inference, null sets, and native scheduling policy. Parallel compares with parallel. Serial compares with serial. Serial disables only column-conversion workers.

Each fresh-process response validates all native values, types, null positions, and row and column order against an independent contract. Streaming uses a separate untimed validation read. Warm input, AC power, eight balanced implementation orders, and no outlier removal match the previous studies. No builds, tests, or profilers run during accepted timings.

CPU is process user-plus-system time per complete read. Elapsed time is separate. Peak RSS includes the whole worker and is not an allocation counter. Metadata loses one per-column Array for eligible null sets, but this study does not measure allocation counts, energy, cache occupancy, or hardware performance counters.

| Input and schema | Policy | CPU ms, parent to final | CPU change | Elapsed ms, parent to final | Peak RSS MiB, parent to final |
|---|---|---:|---:|---:|---:|
| eager bike-day known | parallel | 0.673 to 0.714 | +6.0% | 0.399 to 0.394 | 7.78 to 7.73 |
| eager bike-day known | serial | 0.402 to 0.404 | +0.4% | 0.418 to 0.420 | 7.60 to 7.57 |
| eager bike-hour known | parallel | 5.245 to 5.330 | +1.6% | 2.003 to 2.017 | 15.81 to 15.80 |
| eager bike-hour known | serial | 3.669 to 3.563 | -2.9% | 3.687 to 3.598 | 15.59 to 15.55 |
| eager unique-shuffled known | parallel | 5.899 to 5.774 | -2.1% | 5.237 to 5.109 | 12.38 to 12.36 |
| eager unique-shuffled known | serial | 5.871 to 5.671 | -3.4% | 5.929 to 5.706 | 12.36 to 12.34 |
| eager Aotizhongxin known | parallel | 11.837 to 11.627 | -1.8% | 4.536 to 4.593 | 23.12 to 23.11 |
| eager Aotizhongxin known | serial | 8.387 to 8.248 | -1.7% | 8.449 to 8.306 | 22.86 to 22.83 |
| eager Wanliu known | parallel | 12.028 to 11.666 | -3.0% | 4.556 to 4.542 | 22.92 to 22.94 |
| eager Wanliu known | serial | 8.475 to 8.325 | -1.8% | 8.530 to 8.372 | 22.66 to 22.66 |
| eager energy known | parallel | 279.566 to 274.276 | -1.9% | 126.505 to 123.876 | 422.37 to 422.28 |
| eager energy known | serial | 259.466 to 247.172 | -4.7% | 259.492 to 247.225 | 420.58 to 420.55 |
| eager energy infer | parallel | 285.827 to 276.022 | -3.4% | 126.057 to 123.265 | 422.41 to 422.35 |
| eager energy infer | serial | 254.792 to 251.630 | -1.2% | 254.906 to 251.728 | 420.59 to 420.58 |
| eager energy-date-full known | parallel | 317.759 to 310.673 | -2.2% | 154.169 to 151.750 | 422.33 to 422.33 |
| eager energy-date-full known | serial | 280.262 to 276.812 | -1.2% | 280.331 to 276.980 | 420.55 to 420.60 |
| eager late-bool infer | parallel | 6.798 to 6.924 | +1.9% | 6.822 to 6.955 | 9.77 to 9.75 |
| eager late-bool infer | serial | 6.767 to 7.224 | +6.8% | 6.808 to 7.270 | 9.73 to 9.78 |
| eager late-text infer | parallel | 8.075 to 8.042 | -0.4% | 8.106 to 8.085 | 16.89 to 16.91 |
| eager late-text infer | serial | 7.978 to 7.920 | -0.7% | 8.026 to 7.940 | 16.88 to 16.91 |
| stream date-100000-1 known | parallel | 4.563 to 4.465 | -2.2% | 4.603 to 4.499 | 8.58 to 8.67 |
| stream date-100000-1 known | serial | 4.429 to 4.407 | -0.5% | 4.472 to 4.450 | 8.55 to 8.70 |
| stream bike-hour known | parallel | 5.191 to 5.141 | -1.0% | 1.947 to 1.926 | 12.92 to 12.96 |
| stream bike-hour known | serial | 3.439 to 3.442 | +0.1% | 3.461 to 3.485 | 12.55 to 12.65 |
| stream unique-shuffled known | parallel | 5.486 to 5.500 | +0.2% | 4.837 to 4.840 | 9.45 to 9.53 |
| stream unique-shuffled known | serial | 5.380 to 5.373 | -0.1% | 5.400 to 5.393 | 9.41 to 9.50 |
| stream Aotizhongxin known | parallel | 11.630 to 11.374 | -2.2% | 4.153 to 4.069 | 15.71 to 15.86 |
| stream Aotizhongxin known | serial | 7.732 to 7.588 | -1.9% | 7.766 to 7.636 | 14.34 to 16.17 |
| stream energy known | parallel | 272.572 to 296.192 | +8.7% | 117.265 to 119.852 | 139.27 to 139.23 |
| stream energy known | serial | 234.814 to 223.795 | -4.7% | 234.873 to 223.858 | 136.45 to 137.68 |
| stream energy-date-full known | parallel | 303.048 to 294.945 | -2.7% | 139.636 to 143.025 | 138.38 to 138.84 |
| stream energy-date-full known | serial | 258.279 to 249.418 | -3.4% | 258.326 to 249.484 | 136.43 to 136.58 |

See the [complete controls](controls.md) for widths from 1 to 64, small and large row counts, numeric null densities, Unicode fields, all-String inputs, token sets from empty through 2,048 entries, and long owned String keys and values. No median crosses the existing CPU or peak-RSS review triggers. That does not qualify every change as beneficial. The largest observed final median peak-RSS increase is 1.84 MiB, on serial air-quality streaming. Parallel household streaming is a meaningful CPU regression and blocks unconditional promotion.

The follow-up reproduces the parallel household streaming cost, 274.829 to 296.195 ms of process CPU time, or +7.8%. Its serial stream improves from 233.248 to 220.405 ms, or -5.5%. Eager household CPU improves by 1.8% with parallel conversion and 3.2% with serial conversion. The dated household and air-quality stream controls improve under both policies. See the [384-observation follow-up](followup.md). Its original trigger and all earlier observations remain visible.

## Rejected alternatives and ownership diagnosis

The [initial screen](pilot/summary.json) contains 1,400 validated reads across the original hashed implementation, the committed Array lookup, separate concrete Array decoding, tiny Set iteration, and byte matching before String construction. The [ownership screen](ownership-screen/summary.json) contains 1,792 validated reads, including direct keys and independent per-column Sets.

Tiny Set iteration adds a retain and release of the Set owner in the generated field decoder. The linked decoder retains `x21`, then releases that same owner on each exit from the iteration branch. The parallel profile spends most sampled active stacks in `swift_retain` and `swift_release`. Rebuilding an independent Set per column removes that dominant hotspot and most of the parallel CPU penalty. Serial behavior stays close. This intervention supports contention on shared reference ownership. It does not identify a hardware-cache mechanism or establish a cache-miss count.

The profiles are diagnostic runs, not accepted timings. Their leaf counts are samples across threads, not percentages of a single CPU or instruction counts. Profiles run separately from the final comparisons. The unchanged parser functions are not blamed for a slowdown confined to a rejected lookup strategy.

Byte matching before String construction helps the default-token screen but scales poorly with large custom sets. It also repeats String construction when the matcher's Unicode or escaped-field fallback returns false. This unqualified strategy is rejected. A future bounded ASCII path would need a match/miss/fallback result and broad controls before production use.

## Remaining streaming question

The [streaming profiles](stream-profiles/leaf-summary.json) do not show the dominant retain/release hotspot seen in the rejected Set-iteration design. The parallel streaming penalty therefore remains unresolved. Sampling counts alone do not explain it. The next experiment should isolate the indexed-record conversion and per-chunk dispatch from scanning and asynchronous delivery, with the same native-output contracts. Do not add a reader-specific shortcut or change scheduling to hide this cost.

## Correctness and limits

All 389 DataFrame tests passed separately in Release, Debug, and Release with Address Sanitizer, with zero failures or skips. The 30,720-case grammar digest matches the parent. All 2,336 final resource workers validate complete output contracts. The standard tabular-smoke production-default run produced 190 SwiftSci and pandas responses, and its artifact audit passed.

The new 42-line test file uses explicit fixture types. It checks decoder eligibility and String membership after mutation of the original Set. Existing eager and streamed tests exercise both column policies, Unicode equivalence, invalid UTF-8 repair, quotes, whitespace, and empty tokens. Passing this machine's compiler does not establish compatibility with every CI compiler.

These results qualify this decoder arrangement on this machine and toolchain. They do not claim a general improvement in every CSV workload. Small increases remain in the complete observations. The standard regression policy is not full numerical certification.

## Evidence

- [Artifact hashes](artifact-sha256.json)
- [Complete resource controls](controls.md)
- [Streaming resource follow-up](followup.md)
- [Rejected-design screens](screens.md)
- [Ownership profile leaf summary](ownership-profiles/leaf-summary.json)
- [Shared Set decoder assembly](ownership-profiles/set-iteration-decoder-linked.txt.gz)
- [Final build receipt](build-receipts/production/build.json)
- [Grammar comparison](grammar-result.json)
- [Standard benchmark artifacts](standardized-artifacts.tar.gz)
- [Source change](source-change.patch.gz)
- [Trial patches and frozen parent sources](experiments.tar.gz)

The archived controllers retain their original absolute input paths and file hashes. The experiments archive contains input contracts and trial patches. Reference datasets remain in their existing benchmark cache and named source records. To reproduce on another checkout, resolve those paths while keeping byte hashes, policies, and native output contracts unchanged.
