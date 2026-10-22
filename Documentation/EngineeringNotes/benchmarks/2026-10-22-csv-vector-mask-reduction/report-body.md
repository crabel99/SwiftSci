# CSV structural mask reduction on Apple Silicon

## Decision

Keep the existing CSV data layout and replace scalar mask packing with two exact platform vector reductions. The implementation is local commit `46a9b9bf951918cd2eb281dadf554efb30c7b0a0` on `codex/csv-vector-mask-reduction`. Its parent is `9c067c6c5116d78c0849073acea7fb150404efab`.

FINAL_DECISION

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

REFERENCE_TABLE

The original retained-index implementation at `dba26e1562503e1594194250d914327830d8f58d` is also present in the raw reference matrix as historical context. Its default scheduling differs from the explicit serial policy, so it is not the matched parent for serial comparisons. Aotizhongxin contains quotes and takes the original compact fallback. It is not evidence about the original unquoted parallel index path.

## Width and null controls

The control matrix checks widths 1, 2, 4, 8, 18, and 64 at 257 and 32,769 rows. It also checks inference at 0%, 50%, and 90% nulls, and explicit schemas at 50% and 90% nulls. Each case has eight balanced fresh-process samples for both conversion policies and both commits. All column null counts must match the independent contract.

CONTROL_TABLE

REVIEW_STATUS

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
