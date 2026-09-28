# Native precision reduction increment

Date: 2026-09-28. Owner: crabel99. Status: implemented, targeted tests and numerical profiles checked; performance measurements are local experiments.

## Implementation and dependency

Branch `codex/apple-silicon-precision` starts at repair commit `36053baca6bf38a9233ca9798c151816f4bdf259`. It retains the earlier fault repairs and adds two separate commits:

- `5f6b67f68e`: fix variance accuracy and remove the input-sized centered buffer for inputs handled by the new finite reduction.
- `1cc66fc663`: reuse that reduction for ANOVA within-group sums of squares.

Public method signatures and the existing certification tolerances are unchanged. The production dot-product implementation is unchanged. This branch depends on the repair branch; its two new commits are the scope of this increment, not all changes relative to upstream main.

## Variance defect and fix

The actual `Stats.variance` API returned `67.578125` for `[1e15 + 5.75, 1e15 - 5.875]`. The exact variance of those represented binary64 inputs is `67.5703125`. Their absolute mean falls between representable doubles. Centering around that rounded absolute mean adds error.

The new internal `CenteredMoments` calculation keeps the mean relative to the first observation. It uses four independent SIMD accumulators with compensation for the first pass. The second pass uses fused square accumulation in 256-value blocks, then compensates the scalar block merges. A final correction accounts for error in the relative mean. Neither pass allocates an input-sized array.

Inputs that overflow this centered calculation or contain nonfinite values fall back to the existing Accelerate path. This preserves that path's established handling rather than claiming a new arbitrary-range guarantee. The new regression tests cover the concrete failure, block boundaries, translation, group order, constants, tiny finite variance, overflowing range and existing validation errors.

## Algorithm comparison

The first prototype used one four-lane compensated accumulation chain. It met the explored accuracy requirement but was slower than scalar compensation. Four independent chains reduced dependency latency. On the large inputs in the second exploratory run, compensated SIMD summation was about 2.2 times faster than scalar compensated summation. Both were slower than unqualified vDSP summation. Compensation has a cost, and the methods do not have identical error behavior.

The exploratory checks use exact rational references for the actual binary64 input values. Their criterion is absolute error no greater than `abs(reference) * 1e-12 + 8 * smallestSubnormal`. This is a supplemental experiment, not a replacement for the maintained certification contracts.

| Operation | Cases | Initial implementation misses | Accurate candidate misses |
|---|---:|---:|---:|
| Sum | 78 | 5 for vDSP | 0 for scalar and SIMD compensation |
| Dot product | 69 | 8 for vDSP, 18 for scalar FMA, 7 for SIMD FMA | 0 for compensated SIMD with product residuals |
| Variance | 131 | 25 for the production algorithm | 0 for the blocked candidate and integrated public API |
| ANOVA | 11 | 0 for the repaired production algorithm | 0 for the candidate and integrated public API |

These finite cases do not establish arbitrary-range dot-product or sum guarantees. Those candidates remain research material. The initial variance prototype had an FMA argument-order error; independent references detected it before integration. The corrected implementation passed the checks above.

## Public-API performance and memory

Machine: Apple M4 Max, 128 GiB memory. The comparison executables compile real SwiftStats sources with `swiftc -O`, linked to existing Apple and dataframe dependencies. The variance baseline is a copy of the previous production routine; its accuracy results were also checked against the actual pre-change API. These measurements are not the library's formal performance baseline.

Every timed input has an independent exact analytical reference. Variance runs alternate the baseline and integrated path within one process, discard two initial rounds and retain nine timing samples. Small inputs use repeated calls per sample. The table uses inputs around `1e12` with small binary-exact variations.

| Values | Previous variance | Integrated variance | Change |
|---|---:|---:|---:|
| 32 | 0.0592 microseconds | 0.0862 microseconds | 46% slower, 27 nanoseconds added |
| 1,024 | 0.451 microseconds | 0.618 microseconds | 37% slower, 167 nanoseconds added |
| 65,536 | 0.0327 ms | 0.0344 ms | 5% slower |
| 1,048,576 | 0.515 ms | 0.550 ms | 7% slower |
| 8,388,608 | 4.242 ms | 4.421 ms | 4% slower |

A separate process per implementation measured maximum resident memory with `/usr/bin/time -l` for 8,388,608 values. The old path reached 140,722,176 bytes; the new path reached 73,580,544 bytes. The difference is 67,141,632 bytes, approximately 64 MiB. These are process peaks, not isolated allocation counters. The eliminated 8-byte-per-value temporary independently accounts for 64 MiB.

ANOVA uses actual before/after public API binaries with the same driver. Three alternating process pairs retain 27 measured samples per size per implementation. All computed F statistics meet the exact-reference criterion.

| Values per group, three groups | Before | After | Speedup |
|---|---:|---:|---:|
| 32 | 0.375 microseconds | 0.459 microseconds | 0.82x |
| 1,024 | 0.00725 ms | 0.00454 ms | 1.60x |
| 65,536 | 0.467 ms | 0.298 ms | 1.57x |
| 1,048,576 | 7.865 ms | 4.731 ms | 1.66x |

The variance change trades a modest large-input time increase for improved accuracy and lower memory. ANOVA replaces an already compensated scalar calculation and gains speed on the measured medium and large groups. The smallest ANOVA case is slower by about 84 nanoseconds. Neither result justifies a universal speed claim.

## Verification

| Check | Result |
|---|---|
| Final Release statistics and forecast test run | 128 passed, 0 failed, 0 skipped in Xcode's summary |
| Swift Testing portion of that run | 70 statistics tests and 56 forecast tests passed |
| Independent public variance cases | 131 passed |
| Independent ANOVA cases | 11 passed |
| Maintained NIST univariate profile | 81 executions passed; certificate audit passed |
| Maintained numerical-binary64 profile | 19 executions passed; certificate audit passed |
| Maintained numerical-conformance profile | 16 passed; the existing three original-decimal failures remain |

The retained failures are `nist-smls07-decimal`, `nist-smls08-decimal` and `nist-smls09-decimal`. The original-decimal profile remains failed. Input-preserving ingestion has not been implemented by this increment.

The worker was built during the successful Xcode test run from a tracked-source snapshot. Before producing its build record, all 365 recorded source files were checked against that snapshot, and the binary was inspected for coverage instrumentation. The fingerprint is `6aff660e386ed53a5d6d0ae808f4e67eb5745d42cb2565662d032a1eadebd891`. The recorded command and binary hash accompany the evidence. This used the completed test build rather than rerunning the equivalent build-only command.

The tests target statistics and forecasts. This is not a new full-library or GPU validation claim. Existing dataframe dependencies were used by the isolated public-API probes; the Xcode test run built from the tracked source snapshot and the package's resolved dependencies.

## Evidence and next decision

The [evidence archive](../archive/2026-09-28/precision-kernels/evidence.tar.gz) contains the prototype source, exact-reference driver, public-API driver, raw accuracy and timing records, memory measurements, test summary, build record and maintained-profile run records. Paths in the drivers describe the local experiment environment. The archive manifest hashes each member.

Next, evaluate whether sum and dot-product accuracy warrants a separate API contract or a default implementation change. Their finite experimental results are encouraging, but exceptional values, overflow, very long reductions and compatibility need qualification. Do not replace the current dot product solely because the compensated prototype passed these cases. The explicit input-preserving representation remains a separate design and implementation step.
