# Dot-product qualification and remaining input-precision faults

Date: 2026-09-28. Owner: crabel99. Status: measured research; no production replacement.

## Scope and conclusion

The implementation under test is `codex/apple-silicon-precision` at `1cc66fc663ead7250f39996034306bfe462e83ba`, based on the certification repairs at `36053baca6bf38a9233ca9798c151816f4bdf259`. This investigation changes no production source or certification threshold.

The remaining SmLs failures originate in conversion of the original decimal observations to binary64. The current public dot product has separate product-rounding and accumulation-cancellation weaknesses. Native SIMD compensation improves those cases, but costs throughput and does not handle every exponent range. A stronger three-component accumulator matched the correctly rounded exact answer in all 667 tested cases outside the dedicated overflow and underflow groups. That is an observed result for this sweep, not a proof of correct rounding for every input.

BLAS provides a useful speed opportunity for larger vectors. Its cancellation behavior does not meet the stronger accuracy goal. Do not replace the public dot product with either candidate before choosing the accuracy and range contract.

## The three retained SmLs failures

The experiment calls the actual `Stats.oneWayANOVA` implementation three ways: direct conversion, subtraction of a common origin after conversion, and subtraction in decimal arithmetic before conversion. All observations and group memberships come from the maintained original NIST fixtures.

| Dataset | Certified F | Direct conversion | Center after conversion | Center before conversion |
|---|---:|---:|---:|---:|
| SmLs07 | 21 | 21.000811887818774 | 21.000811887818774 | 20.999999999999996 |
| SmLs08 | 201 | 201.01300409594845 | 201.01300409594845 | 201.00000000000006 |
| SmLs09 | 2001 | 2001.134926220951 | 2001.134926220951 | 2001.0000000000005 |

Centering before conversion meets the existing decimal-profile tolerances. Centering afterwards cannot recover the discarded information. These are translation-invariant ANOVA calculations, so a shared origin is mathematically valid for this experiment. A general column representation must retain its origin, units and conversion rules; the experiment does not establish that arbitrary APIs can silently receive shifted values.

The maintained original-decimal profile remains failed. This experiment does not modify its fixtures, outputs or acceptance rules. An input-preserving representation remains a separate implementation task.

## Input identity caught a test defect

The first exploratory dot driver used `JSONSerialization` followed by an `as! [Double]` bridge. On this toolchain, 5,007 of 429,482 numeric input occurrences differed in bit pattern from Python's binary64 values. Comparing against the original Python inputs falsely attributed some conversion errors to the reduction algorithm.

The corrected driver transports unsigned 64-bit patterns as decimal strings and constructs each value with `Double(bitPattern:)`. The exact oracle uses Python `Fraction` for every product and the entire sum. No fixed decimal precision is assumed.

A separate typed `JSONDecoder` check preserved all 429,482 values. The maintained numerical worker decodes ANOVA and OLS values through typed `JSONDecoder`; its `JSONSerialization` call checks field names. The observed exploratory bridge problem therefore does not establish a defect in that worker.

The previous public variance and ANOVA evidence was rechecked using exact-bit input transport. All 131 variance cases and 11 ANOVA cases still pass their original criterion. The old 69-case dot sweep still has eight public-API misses. Earlier results were not silently replaced with a looser tolerance.

## Minimal dot-product faults

For `e = 2^-27`, the exact dot of `[1 + e, -1]` and `[1 - e, 1]` is `-2^-54`. The actual public API returns zero. A rounded multiplication has already lost the residual before reduction.

The exact dot of `[1e16, 1, -1e16]` and `[1, 1, 1]` is one. The public API returns zero. Here the loss occurs in accumulation.

A scalar FMA loop does not solve arbitrary cancellation. It avoids an intermediate product rounding within each operation but still rounds each accumulated result. The compensation candidates retain both the product residual and addition residuals. The generated optimized assembly contains ARM64 fused scalar instructions and two-double SIMD fused instructions. This verifies hardware use; it does not establish that more unrolling is faster. The one-chain SIMD4 candidate was generally faster than the SIMD16 and SIMD32 variants in this experiment.

## Accuracy sweep

The 678 cases include ordinary and positive random values, wide exponent ranges, 240 constructed cancellation cases with reordered versions, sum cancellation, product rounding, subnormal inputs, product underflow, intermediate overflow, final-result overflow, zero and cancellation beyond two working precisions.

The exploratory criterion is `abs(error) <= abs(exact) * 1e-12 + 0.5 * minimumSubnormal`. Results also record distance from the correctly rounded exact answer. This criterion is not a new public API contract. Counts depend on the deliberately adversarial case mix and are not an estimate of real-world failure frequency.

| Case family | Cases | vDSP passes | SIMD4 two-component passes | SIMD16 three-component passes |
|---|---:|---:|---:|---:|
| Ordinary, positive and wide-range | 378 | 378 | 378 | 378 |
| Constructed cancellation | 240 | 0 | 240 | 240 |
| Sum-rounding cancellation | 15 | 10 | 15 | 15 |
| Product-rounding cancellation | 25 | 3 | 25 | 25 |
| Beyond two working precisions | 3 | 0 | 0 | 3 |
| Subnormal inputs and zero | 6 | 6 | 6 | 6 |
| Product underflow | 8 | 4 | 4 | 4 |
| Intermediate overflow | 2 | 0 | 0 | 0 |
| Final-result overflow | 1 | 1 | 0 | 0 |

All 678 actual public API results have the same bits as the standalone vDSP baseline. The two-component SIMD4 candidate matched the rounded exact answer in 624 of the 667 cases outside the dedicated range groups. The three-component candidate matched all 667. Passing the relative criterion and returning the correctly rounded result are different claims.

The stronger accumulator still returns zero when individual products of `2^-537` and `2^-538` underflow, although their exact sum can be representable. It returns NaN when overflowing intermediates contaminate its residuals. The two finite exact results in those overflow tests are one and `Double.greatestFiniteMagnitude`. It also returns NaN in a case whose correctly rounded result is positive infinity. That last result is a regression from the production baseline and alone rules out an unconditional replacement.

Existing public validation was recorded separately. Empty and unequal-size arrays throw. NaN propagates; positive infinity remains infinity when appropriate; opposite infinities and zero times infinity produce NaN. The one-element negative-zero probe returns positive zero. Any replacement needs explicit compatibility tests for this behavior. These observations do not promise identical NaN payloads on other implementations.

## Throughput and memory

Machine: Apple M4 Max, macOS 27.0 build 26A428, Apple Swift 6.4, optimized `swiftc -O` without fast-math flags. The benchmark times reduction kernels, not end-to-end model training or public API validation overhead.

Each size has mixed-sign, positive and product-cancellation inputs. The first two use deterministic dyadic values with exact integer sums. The cancellation family has an exact analytical answer. Every timed result is checked. Input construction and reference calculation are outside the timed interval. Candidates rotate through 17 rounds; four warmup rounds are discarded and 13 samples retained. Small sizes use repeated calls per sample. These are repeated-buffer measurements, not a cold-cache workload.

The table shows medians for mixed-sign inputs in the default Accelerate environment.

| Elements | vDSP | BLAS ddot | SIMD4 two-component | SIMD16 three-component |
|---|---:|---:|---:|---:|
| 32 | 0.00348 us | 0.00674 us | 0.0167 us | 0.0778 us |
| 384 | 0.0338 us | 0.0392 us | 0.132 us | 0.388 us |
| 1,536 | 0.134 us | 0.122 us | 0.487 us | 1.508 us |
| 65,536 | 8.781 us | 1.886 us | 22.333 us | 62.344 us |
| 1,048,576 | 147.125 us | 56.917 us | 361.584 us | 954.834 us |
| 8,388,608 | 1,111.791 us | 837.125 us | 2,909.333 us | 7,656.792 us |

A second process set `VECLIB_MAXIMUM_THREADS=1`. BLAS still took 1.885 us at 65,536 values, 67.625 us at 1,048,576 values and 846.417 us at 8,388,608 values. The corresponding vDSP times were 8.750, 153.625 and 1,170.000 us. This checks the environment setting, not the actual thread count or undocumented Accelerate dispatch internals.

At common embedding dimensions, the two-component candidate costs roughly three to four times vDSP in this experiment. At the larger sizes it costs about 2.5 to 2.6 times vDSP. It is faster than scalar compensation but is not a throughput improvement over the existing unqualified reduction. The stronger candidate costs about 6.5 to 11.5 times vDSP over the listed medium and large sizes.

All compensated timed results matched the analytical references. vDSP and BLAS lost the constructed product-cancellation residual at every timed size. Their faster times must not be presented as equivalent-accuracy results.

The candidates use fixed-size accumulator state and read both arrays directly. They allocate no input-sized product or centered arrays. This is established by implementation inspection; this study did not measure isolated peak memory or allocation counts.

## Where integration would matter

`Stats.dotProduct` currently calls vDSP directly. Pearson correlation and covariance have their own centered dot calls. VectorStore, HNSW search, word embeddings and both Naive Bayes classifiers also call vDSP directly. Changing only `Stats.dotProduct` would not update those callers.

MLP, randomized SVD and forecasting wrappers use matrix BLAS calls such as GEMM and GEMV. Replacing those with a loop of individually compensated dots would change batching and performance substantially. This study does not justify that change.

The next implementation should separate the ordinary fast reduction from an accuracy-qualified reduction. Use a declared error requirement and a supported range, or return a defensible error estimate. Do not infer the caller's scientific intent from vector size. An error-estimate-driven fallback is a proposal for further work, not an implemented guarantee.

A fast-path comparison should investigate the BLAS crossover over more sizes and actual callers. An accurate path needs exceptional-value handling and a range-safe fallback, potentially exponent bins or an exact accumulator. A global rescale is not sufficient for arbitrary mixed exponents. The triple-component prototype is useful evidence but is not a substitute for a proven full-range design.

## Reproduction and evidence

The [evidence archive](../archive/2026-09-28/dot-qualification/evidence.tar.gz) contains Swift candidate and public-API drivers, seeded fixture generation, exact references, all results, generated assembly, verification assertions, build logs and environment metadata. Its manifest hashes every retained member. Compiled binaries are excluded.

`REPRODUCE.md` in the archive gives the sequence. Public probes use tracked SwiftStats source and cached dataframe dependency objects at the recorded local paths. No full-library or GPU test run was needed for this source-unchanged qualification. The previous targeted Xcode test result remains historical evidence for its recorded commit.

Algorithm background: [Ogita, Rump and Oishi, Accurate Sum and Dot Product](https://www.tuhh.de/ti3/paper/rump/OgRuOi05.pdf) provides the error-free transformation and compensated dot-product basis. Its guarantees have assumptions about precision and range. Our SIMD layout and three-component candidate are experiments, not claimed reproductions of every theorem in that paper. [Swift addingProduct](https://developer.apple.com/documentation/swift/double/addingproduct(_:_:)) supplies the fused operation used to recover a product residual.
