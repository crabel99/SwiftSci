# CSV structural mask reduction on Apple Silicon

## Decision

Keep the existing CSV data layout and replace scalar mask packing with two exact platform vector reductions. The implementation is local commit `46a9b9bf951918cd2eb281dadf554efb30c7b0a0` on `codex/csv-vector-mask-reduction`. Its parent is `9c067c6c5116d78c0849073acea7fb150404efab`.

The matched final reads support this small production change. Household eager reads use 4.7–7.6% less process CPU time across the tested schema and scheduling choices. Quoted air-quality eager reads use 1.6–2.4% less. Streaming benefits are smaller and mixed, including a 0.15% CPU increase for serial household date parsing. The largest reference CPU increase is 0.43% on late-Bool inference.

The largest control increase is 3.3%, about 10 microseconds, on a 257-row, four-column parallel read. Serial explicit-schema conversion with 90% nulls increases 2.2%, about 67 microseconds. These observations remain in the accepted results. They are not hidden by a single aggregate score.

The largest observed median peak-RSS increase is 1.42 MiB on the full household eager parallel read. The control matrix's largest increase is 0.33 MiB. The patch does not change retained metadata or column allocation policy, but this study does not count individual final-build allocations. It does not claim a memory reduction.

The patch changes `SystemsCSVParser.swift` and adds one 38-line regression test. It introduces no new public API, worker policy, batch size, coordinate representation, or retained cache. All investigation material belongs to `codex/engineering-notes`. Nothing in this report belongs in the implementation diff.

## Why inspect mask packing

The preceding coordinate-storage experiments did not demonstrate a reliable resource benefit. This investigation returned to the generated production code before changing the CSV architecture again.

The diagnostic driver uses the frozen parent module and validates native output before sampling. It then repeats serial-conversion reads through a separate async function so that each DataFrame leaves scope. The wide reference completes 1,000 reads and 35,064,000 rows. The household reference completes 30 reads and 62,257,770 rows. Both drivers exit. These are diagnostic runs, not accepted benchmark timings.

Samples frequently land in the structural scanner. Disassembly shows vector byte comparisons followed by sixteen scalar lane extractions and scalar packing operations for the 16-bit event mask. The source used `lowHalf.wrappedSum()` and `highHalf.wrappedSum()`. That syntax did not keep the reduction vectorized on this toolchain.

The sample PCs require the load slide before comparison with the preferred Mach-O addresses. The wide binary has slide `0x168000`, and the household binary has slide `0x8d8000`. The mapped hot PCs include the refill and next-event paths. Samples also show Double parsing. Sample counts do not quantify the percentage of CPU work that this patch can remove.

The patch applies the existing platform `simd_reduce_add` to two full-width byte vectors with disjoint weights. Each nonzero half contains a subset of `1, 2, 4, 8, 16, 32, 64, 128`. Its sum is at most 255. Conversion to `UInt16` precedes the upper-byte shift. The resulting mask is exact, preserves lane order, and has no floating-point precision tradeoff.

The SDK implements the 16-byte reduction with `vaddvq_u8` on Apple Silicon. The final production-linked binary contains `addv.16b` reductions in the compact scanner. This is machine-code evidence for this compiler and target, not an instruction-count, cache-hit, power, or energy measurement. The module compiles for `arm64-apple-macos14.0`. That does not prove execution on macOS 14.

## Alternatives and selection

The standalone proof checks all 65,536 masks across five expressions: the original half reductions, half-width platform reductions, a widened Swift reduction, full-width byte platform reductions, and a widened platform reduction. Every expression returns the exact mask. Several expressions still scalarize.

The public-read pilot compares the parent with the two remaining vectorized forms. It records 576 validated reads across 16 cases, two conversion policies, six balanced orders, and three implementations. The full-width byte form is more consistent on the wide and household references. The widened form has fewer reduction instructions but does not deliver a more consistent full-read CPU benefit. Source size and assembly instruction counts therefore do not decide the implementation.

The final matrices use the committed source and a frozen parent. Pilot observations do not replace final acceptance results.

## Final reference reads

Each number is a median of ten fresh processes. Lower CPU time means less process user-plus-system time per correct result. Elapsed time measures latency separately. Peak RSS is the process high-water mark observed by the driver, not a count of allocations or retained DataFrame bytes.

The comparisons use identical CSV bytes, schemas or inference rules, selected columns, null rules, native types, values, and row order. Every eager worker checks the complete native result against its input contract. Streaming workers validate the complete output in a separate untimed repeat. Streaming requests 10,000 rows per chunk. The internal 16,384-row bound stays unchanged.

| Read, input, schema | Conversion policy | CPU ms, parent → final | CPU change | Elapsed ms, parent → final | Peak RSS MiB, parent → final |
|---|---|---:|---:|---:|---:|
| eager bike-day known | parallel | 0.710 → 0.680 | -4.2% | 0.425 → 0.433 | 7.71 → 7.69 |
| eager bike-day known | serial | 0.405 → 0.394 | -2.6% | 0.452 → 0.437 | 7.53 → 7.50 |
| eager bike-hour known | parallel | 5.330 → 5.274 | -1.0% | 2.068 → 2.026 | 15.76 → 15.74 |
| eager bike-hour known | serial | 3.587 → 3.565 | -0.6% | 3.620 → 3.594 | 15.52 → 15.48 |
| eager unique-shuffled known | parallel | 6.012 → 5.793 | -3.6% | 5.386 → 5.149 | 12.33 → 12.30 |
| eager unique-shuffled known | serial | 5.841 → 5.658 | -3.1% | 5.902 → 5.695 | 12.30 → 12.27 |
| eager Aotizhongxin known | parallel | 12.438 → 12.235 | -1.6% | 4.994 → 4.792 | 23.07 → 23.05 |
| eager Aotizhongxin known | serial | 9.082 → 8.861 | -2.4% | 9.113 → 8.910 | 22.78 → 22.77 |
| eager Wanliu known | parallel | 12.563 → 12.264 | -2.4% | 4.992 → 4.794 | 22.91 → 22.86 |
| eager Wanliu known | serial | 9.013 → 8.816 | -2.2% | 9.053 → 8.867 | 22.61 → 22.59 |
| eager energy known | parallel | 352.239 → 325.462 | -7.6% | 172.969 → 155.166 | 420.84 → 422.27 |
| eager energy known | serial | 314.868 → 298.877 | -5.1% | 314.985 → 298.976 | 421.94 → 421.89 |
| eager energy infer | parallel | 351.505 → 334.834 | -4.7% | 173.099 → 156.874 | 420.89 → 421.55 |
| eager energy infer | serial | 310.993 → 295.382 | -5.0% | 311.048 → 295.441 | 421.27 → 420.48 |
| eager energy-date-full known | parallel | 365.307 → 343.308 | -6.0% | 169.274 → 150.530 | 422.25 → 421.53 |
| eager energy-date-full known | serial | 330.153 → 314.522 | -4.7% | 330.244 → 314.580 | 421.97 → 421.26 |
| eager late-bool infer | parallel | 6.814 → 6.844 | +0.4% | 6.868 → 6.894 | 9.67 → 9.64 |
| eager late-bool infer | serial | 6.789 → 6.801 | +0.2% | 6.819 → 6.840 | 9.67 → 9.64 |
| eager late-text infer | parallel | 8.712 → 8.354 | -4.1% | 8.763 → 8.414 | 16.88 → 16.83 |
| eager late-text infer | serial | 8.836 → 8.444 | -4.4% | 8.871 → 8.480 | 16.88 → 16.83 |
| stream date-100000-1 known | parallel | 4.432 → 4.370 | -1.4% | 4.482 → 4.416 | 8.58 → 8.58 |
| stream date-100000-1 known | serial | 4.394 → 4.359 | -0.8% | 4.429 → 4.418 | 8.58 → 8.55 |
| stream bike-hour known | parallel | 5.237 → 5.244 | +0.1% | 2.138 → 2.014 | 12.88 → 12.89 |
| stream bike-hour known | serial | 3.495 → 3.453 | -1.2% | 3.541 → 3.487 | 12.59 → 12.56 |
| stream unique-shuffled known | parallel | 5.500 → 5.520 | +0.4% | 4.885 → 4.895 | 9.44 → 9.45 |
| stream unique-shuffled known | serial | 5.455 → 5.416 | -0.7% | 5.491 → 5.461 | 9.41 → 9.41 |
| stream Aotizhongxin known | parallel | 12.006 → 11.999 | -0.1% | 4.601 → 4.506 | 15.61 → 16.28 |
| stream Aotizhongxin known | serial | 8.696 → 8.444 | -2.9% | 8.716 → 8.464 | 17.85 → 17.81 |
| stream energy known | parallel | 331.257 → 320.460 | -3.3% | 150.887 → 148.347 | 138.82 → 138.35 |
| stream energy known | serial | 272.181 → 270.663 | -0.6% | 272.213 → 271.353 | 136.44 → 136.41 |
| stream energy-date-full known | parallel | 338.502 → 326.731 | -3.5% | 143.432 → 140.950 | 138.09 → 138.42 |
| stream energy-date-full known | serial | 287.876 → 288.309 | +0.2% | 287.939 → 288.342 | 136.50 → 136.45 |

The original retained-index implementation at `dba26e1562503e1594194250d914327830d8f58d` is also present in the raw reference matrix as historical context. Its default scheduling differs from the explicit serial policy, so it is not the matched parent for serial comparisons. Aotizhongxin contains quotes and takes the original compact fallback. It is not evidence about the original unquoted parallel index path.

## Width and null controls

The control matrix checks widths 1, 2, 4, 8, 18, and 64 at 257 and 32,769 rows. It also checks inference at 0%, 50%, and 90% nulls, and explicit schemas at 50% and 90% nulls. Each case has eight balanced fresh-process samples for both conversion policies and both commits. All column null counts must match the independent contract.

| Input | Conversion policy | CPU ms, parent → final | CPU change | Elapsed ms, parent → final | Peak RSS MiB, parent → final |
|---|---|---:|---:|---:|---:|
| width-1-rows-257 | parallel | 0.222 → 0.219 | -1.4% | 0.247 → 0.244 | 7.05 → 7.03 |
| width-1-rows-257 | serial | 0.214 → 0.212 | -0.9% | 0.238 → 0.239 | 7.03 → 7.02 |
| width-2-rows-257 | parallel | 0.240 → 0.236 | -1.9% | 0.260 → 0.258 | 7.09 → 7.05 |
| width-2-rows-257 | serial | 0.235 → 0.225 | -4.3% | 0.260 → 0.253 | 7.06 → 7.02 |
| width-4-rows-257 | parallel | 0.302 → 0.312 | +3.3% | 0.312 → 0.301 | 7.16 → 7.12 |
| width-4-rows-257 | serial | 0.255 → 0.248 | -2.5% | 0.279 → 0.273 | 7.09 → 7.06 |
| width-8-rows-257 | parallel | 0.425 → 0.430 | +1.3% | 0.328 → 0.327 | 7.25 → 7.23 |
| width-8-rows-257 | serial | 0.279 → 0.284 | +2.0% | 0.309 → 0.309 | 7.12 → 7.12 |
| width-18-rows-257 | parallel | 0.711 → 0.703 | -1.1% | 0.432 → 0.427 | 7.50 → 7.48 |
| width-18-rows-257 | serial | 0.394 → 0.388 | -1.5% | 0.418 → 0.421 | 7.31 → 7.29 |
| width-64-rows-257 | parallel | 1.316 → 1.286 | -2.3% | 0.678 → 0.665 | 8.19 → 8.17 |
| width-64-rows-257 | serial | 0.703 → 0.711 | +1.1% | 0.727 → 0.737 | 7.95 → 7.94 |
| width-1-rows-32769 | parallel | 0.667 → 0.651 | -2.3% | 0.691 → 0.678 | 8.45 → 8.42 |
| width-1-rows-32769 | serial | 0.665 → 0.649 | -2.4% | 0.697 → 0.681 | 8.44 → 8.41 |
| width-2-rows-32769 | parallel | 1.184 → 1.126 | -4.9% | 0.952 → 0.927 | 9.11 → 9.09 |
| width-2-rows-32769 | serial | 1.091 → 1.060 | -2.9% | 1.116 → 1.086 | 9.08 → 9.05 |
| width-4-rows-32769 | parallel | 3.326 → 3.140 | -5.6% | 2.373 → 2.283 | 11.02 → 11.34 |
| width-4-rows-32769 | serial | 2.980 → 2.979 | -0.0% | 2.979 → 2.980 | 10.89 → 10.87 |
| width-8-rows-32769 | parallel | 6.466 → 6.282 | -2.9% | 3.340 → 3.121 | 14.96 → 14.92 |
| width-8-rows-32769 | serial | 5.644 → 5.402 | -4.3% | 5.671 → 5.439 | 14.77 → 14.75 |
| width-18-rows-32769 | parallel | 19.494 → 18.960 | -2.7% | 6.519 → 6.205 | 25.51 → 25.47 |
| width-18-rows-32769 | serial | 15.275 → 14.870 | -2.7% | 15.278 → 14.890 | 25.15 → 25.11 |
| width-64-rows-32769 | parallel | 83.326 → 79.957 | -4.0% | 21.618 → 20.076 | 76.12 → 73.10 |
| width-64-rows-32769 | serial | 62.698 → 61.721 | -1.6% | 62.745 → 61.746 | 72.83 → 72.80 |
| nullable-0-infer | parallel | 2.720 → 2.727 | +0.2% | 2.223 → 2.207 | 11.73 → 11.75 |
| nullable-0-infer | serial | 2.553 → 2.481 | -2.8% | 2.547 → 2.506 | 11.69 → 11.64 |
| nullable-50-infer | parallel | 3.123 → 3.055 | -2.1% | 2.421 → 2.339 | 11.59 → 11.55 |
| nullable-50-infer | serial | 2.889 → 2.837 | -1.8% | 2.904 → 2.846 | 11.50 → 11.48 |
| nullable-90-infer | parallel | 3.122 → 3.087 | -1.1% | 2.325 → 2.296 | 11.55 → 11.55 |
| nullable-90-infer | serial | 3.068 → 2.982 | -2.8% | 3.097 → 3.046 | 11.52 → 11.50 |
| nullable-50-known | parallel | 2.887 → 2.866 | -0.7% | 2.235 → 2.215 | 11.50 → 11.50 |
| nullable-50-known | serial | 2.791 → 2.699 | -3.3% | 2.831 → 2.728 | 11.47 → 11.44 |
| nullable-90-known | parallel | 3.170 → 3.204 | +1.1% | 2.349 → 2.386 | 11.84 → 11.57 |
| nullable-90-known | serial | 3.027 → 3.094 | +2.2% | 3.045 → 3.098 | 11.48 → 11.45 |

No final reference or control case exceeds the 10% CPU review threshold. No peak-RSS increase exceeds 5% plus 8 MiB. Smaller increases remain visible in the tables and raw samples.

Review limits are investigation triggers. Results below those limits are not proof that smaller regressions are zero. Tiny reads are especially sensitive to process and scheduling noise. This patch makes no universal CSV speed claim.

## Validation

- Debug DataFrame tests: 385 passed, zero failed or skipped.
- Release DataFrame tests: 385 passed, zero failed or skipped.
- Release with Address Sanitizer: 385 passed, zero failed or skipped.
- Public-parser regression: all 65,536 16-byte delimiter masks preserve ordered field coordinates.
- Public grammar differential: 30,720 cases produce the same digest as the parent, `e144dd63a50a7717083714de1d9e1817990a23fe5f247bbe1d5c3d49e31c6a33`.
- Final reference matrix: 800 validated workers.
- Final width and null matrix: 544 validated workers.
- Standardized `tabular-smoke`, `production-default`: 190 SwiftSci and pandas responses, followed by the artifact audit.
- Independent standards and specification reviews: no actionable findings. See [review scope](reviews.md).

These checks cover DataFrame behavior and the named tabular profile. They do not certify the full numerical, MLX, GPU, or NPU suites.

## Measurement conditions

The final controllers verify source and binary hashes before timing. The benchmark binaries are uninstrumented Release builds. Address Sanitizer and test builds finish before accepted timings start. The standard worker identifies the exact committed tree.

The reference run uses AC power, fresh processes, warmed input bytes, CPU execution, and native scheduling within the selected conversion policy. Orders rotate and reverse to distribute ordering effects. No outliers are removed. Unrelated computer activity remains possible. The controller records the environment and power state instead of attributing unexplained variance to a specific cache or thermal mechanism.

Parallel is the existing default. Serial disables only column-conversion workers. The patch leaves that user choice unchanged. Every resource comparison pairs the same policy before and after the change.

## Evidence

- [Final reference plan](acceptance/plan.json), [medians](acceptance/summary.json), and [review triggers](acceptance/review-flags.json).
- [Width and null plan](mode-controls/plan.json), [medians](mode-controls/summary.json), and [review triggers](mode-controls/review-flags.json).
- [Pilot medians](pilot-summary.json), [grammar result](grammar-result.json), and [five-expression proof](mask-proof-build.json).
- [Final generated-code excerpts](production-packing-disassembly.json) and [local SDK source excerpts](sdk-reduction-source.json).
- [Independent reviews](reviews.md), [build receipts](build-receipts), and [frozen source patch](source-change.patch.gz).
- [Standardized artifacts](standardized-artifacts.tar.gz), [experiment sources and input contracts](experiments.tar.gz), and [artifact hashes](artifact-sha256.json).

Raw worker rows, profiling samples, disassembly, and test logs accompany this report as compressed files. The executed controllers and build scripts are preserved beside the report. Their absolute local paths describe this run; they are not a relocatable benchmark package.
