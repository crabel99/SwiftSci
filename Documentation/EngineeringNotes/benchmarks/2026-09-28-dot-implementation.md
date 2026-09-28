# Dot-product accuracy policy implementation

Date: 2026-09-28. Owner: crabel99. Implementation: `ede79c1ad3fda868d3661979360aaeed31dcbf9c` on `codex/apple-silicon-precision`.

## Public contract

The existing `Stats.dotProduct(a, b)` function remains available, including as a two-argument function reference. It selects `.performance`. A new overload accepts `accuracy: DotProductAccuracy`, with `.performance` and `.compensated` cases. Both modes accept and return Double. There is no global state or implicit conversion to Float.

Performance mode uses vDSP below 4,096 elements and BLAS at or above that size when the count fits the CBLAS Int32 interface. Larger counts retain vDSP. This conservative crossover is supported by measurements on the M4 Max; it is not claimed optimal for every Apple processor. Final rounding bits can change when the backend changes.

Compensated mode retains a leading value and two correction components using SIMD and fused product residuals. It restarts from the original operands when products are at risk of losing an unrepresentable residual, an intermediate component is nonfinite, or the result indicates severe cancellation. It never returns a weaker finite BLAS result as its fallback.

The cancellation trigger compares `abs(result) / largestProduct` with `count * Double.ulpOfOne`. This is a conservative dispatch heuristic, not a certified error estimate. Ordinary compensated arithmetic still has finite depth; the policy does not promise universally correct rounding or cross-platform bitwise reproducibility.

## Range recovery

The fallback decodes finite binary64 inputs into integer significands and exponents, forms each product with full-width integer multiplication, and accumulates positive and negative magnitudes separately. The base unit is `2^-2148`. Each magnitude uses 67 UInt64 limbs. That covers all finite Double products plus the maximum possible Swift array length on a 64-bit platform. The numeric limb storage is 1,072 bytes in total, excluding array headers and allocator overhead. No isolated allocation measurement was made.

After cancellation between the magnitudes, it rounds once to the nearest Double with ties to even. Guard and sticky bits cover normal values, subnormals and overflow boundaries. Negative tiny exact totals can round to negative zero; exact cancellation returns positive zero. NaN and infinite operands are classified separately from overflowing finite products.

Two independent design sketches compared this approach with rejecting unsupported ranges. The cross-review favored exact recovery because rejection would leave solvable finite cases unsupported. We retained the smaller public interface and explicit range contract from the bounded design. We rejected a common floating-point rescale because it can discard small terms across wide exponent ranges.

Broader full-exponent testing exposed 49 cases where the first three-component prototype exhausted its corrections without producing a nonfinite value. The severe-cancellation trigger routes those cases through exact recovery. This finding is why range checks alone are insufficient. The retained evidence includes both the design sketches and the corrected qualification.

## Regression and independent verification

The first Xcode test attempt found a fixture type-inference error. After correcting the fixture to `[Double]`, the tests ran against the original vDSP arithmetic and produced 32 failed expectations across cancellation, product-residual and range cases. That is the failing-before result. The compile failure is not counted as numerical regression evidence.

The final Release run reports 141 passed, zero failed and zero skipped. The Swift Testing portions report 83 statistics tests and 56 forecast tests; Xcode also counts the two test wrappers. Added tests cover the original entry point, explicit performance mode, SIMD and tail boundaries, ordinary product residuals that do not invoke exact fallback, severe cancellation, underflow, overflowing products and sums, ties, sticky bits, long carry/borrow chains, signed zero, validation and exceptional values on both sides of the BLAS crossover.

The actual public compensated API matched the rounded exact rational reference in all 678 qualification cases and all 2,414 full-exponent cases. The seeded full-exponent set includes reordered cancellation, rounding carry into the normal range, overflow midpoints and long magnitude carry chains. These 3,092 observations supplement the maintained tests; they do not prove universally correct rounding.

Maintained profiles on the integrated worker:

| Profile | Result |
|---|---|
| NIST univariate | 81 executions passed; certificate audit passed |
| Numerical binary64 | 19 executions passed; certificate audit passed |
| Original-decimal numerical conformance | 16 passed; SmLs07, SmLs08 and SmLs09 remain failed |

The decimal failures remain input-conversion failures. This increment does not change their fixtures or tolerances. It also does not change sum, matrix operations, vector search or other direct vDSP callers.

The worker source fingerprint is `f8de2c80e59d7211b24e3aaec21bf4e229085130d4f3f8e0e060ccc7ba7715d5`. All 369 source-identity files were checked against the clean build snapshot. The successful test command built the worker without coverage instrumentation. The build record was captured before the commit, with the exact source bytes later committed. This was targeted statistics/forecast validation, not a new full-library or GPU qualification.

## Integrated public-API performance

Hardware and toolchain remain Apple M4 Max, macOS 27.0 and Apple Swift 6.4. These measurements compile actual SwiftStats sources with `swiftc -O`. The previous API implementation is reproduced with its validation and vDSP call in the same driver. Both new modes call the actual public functions.

The first run overlapped test compilation and is retained as preliminary evidence. The reported medians combine two later processes after the build and certification work completed. Each process rotates the candidates through 17 rounds, discards four warmups and retains 13 samples. The combined medians therefore have 26 samples per case. Inputs are reused between calls; these are repeated-buffer timings. Input generation and reference calculations are outside the timed interval.

| Mixed-sign elements | Previous API | New performance API | Compensated API |
|---|---:|---:|---:|
| 32 | 0.00579 us | 0.00741 us | 0.189 us |
| 1,536 | 0.133 us | 0.134 us | 2.255 us |
| 4,096 | 0.356 us | 0.188 us | 5.929 us |
| 65,536 | 8.802 us | 1.865 us | 93.583 us |
| 1,048,576 | 148.208 us | 40.771 us | 1,615.854 us |
| 8,388,608 | 1,153.438 us | 823.355 us | 11,824.979 us |

The large-vector performance gains are about 1.9x at 4,096 values, 4.7x at 65,536, 3.6x at 1,048,576 and 1.4x at 8,388,608 on this machine. At 32 values, dispatch adds about 1.6 ns in this experiment. Do not claim every size improves.

Compensated mode has a substantial cost. At 1,048,576 mixed-sign values it is about 40 times slower than the new performance path. The deliberately severe product-cancellation input invokes exact recovery and takes about 7.347 ms at that size. The corrected range-safe implementation therefore costs more than the earlier unguarded SIMD prototype.

Every timed compensated result matched the analytical reference for the mixed-sign, positive and product-cancellation families. The performance implementations lose the deliberately constructed product-cancellation residual. Their timing advantage is not an equivalent-accuracy comparison.

## Evidence and contribution boundary

The [evidence archive](../archive/2026-09-28/dot-implementation/evidence.tar.gz) contains the design comparison, regression logs and Xcode summary, exact-reference generators and fixtures, public-API drivers and outputs, timing samples, maintained-profile records, source snapshots and hashes. Its manifest verifies every retained member. Compiled binaries and Xcode result bundles are excluded; their text summaries and logs are retained.

Only source, regression tests and the public usage guide are in the implementation commit. This engineering report and experimental evidence remain on `codex/engineering-notes`. No PR was opened for this increment.
