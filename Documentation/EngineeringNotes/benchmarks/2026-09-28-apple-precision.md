# Efficient precision on Apple silicon

Date: 2026-09-28. Owner: crabel99. Status: adopted engineering objective, candidate implementations and a limited compiler probe.

## Objective and constraints

crabel99 clarified that the library's core work is data structures, mutations and algorithms shared across scientific and AI workflows. Engineering solutions follow from their constraints. For our work, those constraints include Swift, Apple silicon, a specified numerical accuracy requirement, memory capacity, memory traffic, execution time and safe ownership.

Optimize the cost of meeting the required accuracy through the complete workflow. More precision, more SIMD lanes or more GPU work is not by itself success. Evaluate the representation and its consuming algorithms together.

This refines the [scientific computing charter](../CHARTER.md). It does not authorize a change to upstream public APIs or relax certification limits. The maintainer retains ownership of those decisions.

## What the existing ecosystem already does

NumPy implements SIMD kernels and chooses among supported CPU features at runtime, including ARM support. A claim that established libraries do not optimize for hardware would be inaccurate. Our opportunity is to measure and improve the combined path through ingestion, compact storage, filtering, mutation, numerical kernels and result access. A fast kernel does not establish a fast complete workflow. [NumPy CPU/SIMD architecture](https://numpy.org/doc/stable/reference/simd/index.html)

The [precision survey](2026-09-28-precision-practices.md) explains input-preserving representations and stable algorithms. Its early-offset NIST experiment supports a candidate ingestion design but does not establish Swift performance.

## Verified hardware access through Swift

A standalone probe ran on the local Apple M4 Max with 128 GiB unified memory, Swift 6.4 and the `arm64-apple-macosx27.0.0` target. It used `swiftc -O`, without unsafe floating-point optimization options. These observations apply to this toolchain and probe.

| Swift expression | Observed generated instructions |
|---|---|
| `Double.addingProduct` | Scalar `fmadd` |
| `SIMD2<Double>.addingProduct` | Two-lane `fmla.2d` |
| Separate multiplication and addition | `fmul`, then `fadd` |

Swift specifies that `addingProduct` computes the multiply-add without intermediate rounding. The generated assembly establishes that this probe uses native instructions rather than an emulated arithmetic routine. It establishes neither general compiler behavior nor a throughput ratio. [Swift Double.addingProduct](https://developer.apple.com/documentation/swift/double/addingproduct(_:_:))

The probe evaluates `(1 + 2^-27) * (1 - 2^-27) - 1`. The exact result is `-2^-54`. Separate multiplication and addition produced zero. Both scalar and SIMD fused forms produced `-5.551115123125783e-17`, exactly the expected result.

This proves one precision benefit from fusion. A long sum of fused products can still accumulate error. Compensation and a suitable reduction order need separate analysis. Error-free transformation formulas also have assumptions about finite values, overflow and underflow; they cannot be applied indiscriminately.

The probe also measured eight-byte `Double` and `CLongDouble` values and a sixteen-byte `SIMD2<Double>`. Wider native C scalars are not a precision escape on this target. Apple documents the ARM64 type convention. [Apple ARM64 ABI](https://developer.apple.com/documentation/xcode/writing-arm64-code-for-apple-platforms)

See the archived [kernels](../archive/2026-09-28/apple-precision/kernels.swift), [assertions](../archive/2026-09-28/apple-precision/main.swift), [assembly](../archive/2026-09-28/apple-precision/kernels.s) and [output](../archive/2026-09-28/apple-precision/results.txt). The [metadata](../archive/2026-09-28/apple-precision/metadata.json) records the toolchain, flags and artifact hashes. To reproduce, compile `kernels.swift` and `main.swift` together with `swiftc -O`, then run the executable. Generate assembly separately with `swiftc -O -emit-assembly -module-name PrecisionHardwareProbe kernels.swift`. This probe has no SwiftSci dependency. It does not modify production code.

## Candidate implementation order

### Preserve information with little extra storage

Test an explicit shared origin and contiguous residual array where the data contract permits it. This adds column metadata rather than a second full array of values. Preserve the origin through operations that need absolute values. Ingestion must subtract the origin before lossy conversion. Selecting an origin, accommodating outliers and reconciling different origins all need policy and tests.

Compare scaled integers where units and resolution are discrete and known. Range and overflow checks remain part of that contract. Do not silently quantize ordinary floating input.

### Spend extra precision in the calculation that needs it

A small compensated accumulator can improve a reduction without doubling every stored element. Compare scalar compensated summation, blocked pairwise reduction and compensated SIMD lanes with a checked final merge. Independent lanes may reduce dependency-chain cost, but changing reduction order also changes rounding. Measure both effects.

Use fused multiply-add where its semantics fit dot products, polynomial evaluation or residual calculations. Inspect generated instructions and test error behavior. Do not assume ordinary `a * b + c` fuses or that fusion alone makes a dot product accurate.

Two-part arithmetic is a candidate for selected accumulators or residuals before considering two-part storage throughout a dataframe. Arbitrary precision remains useful for independent reference answers and workloads that require it.

### Keep the data path compatible with native kernels

Maintain contiguous numeric buffers and avoid materializing absolute values solely to hand them to another routine. Compare an Accelerate call with a custom kernel only under the same numerical contract. The installed Apple SDK's `vDSP.h`, under "Exactness, IEEE 754 conformance", permits reordered calculations and does not generally promise IEEE-754 behavior, correct rounding or identical NaN/infinity handling. The header is in the macOS SDK under `Accelerate.framework/Versions/A/Frameworks/vecLib.framework/Versions/A/Headers/vDSP.h`. This observation concerns vDSP and must not be generalized to every Accelerate routine. Include packing, selection and output allocation in workflow measurements.

For mutations, account for copy-on-write ownership, changed ranges, metadata reconciliation and any required rebase. An origin does not make arbitrary mutation free. A representation that saves arithmetic but repeatedly copies a column may lose at workflow scale.

### Choose CPU and GPU under the accuracy requirement

Keep CPU binary64 as the initial candidate for the sensitive statistical cases. Metal Shading Language 4.1 section 2.1 excludes `double` and `long double`; its native floating types include `float`, `half` and `bfloat`. Emulated precision would require its own implementation and cost assessment. [Metal language specification](https://developer.apple.com/metal/Metal-Shading-Language-Specification.pdf) A GPU path must state its supported scalar format and validate any conversion against the required error. Unified memory can simplify sharing but does not remove synchronization, layout conversion or allocation costs. Neither CPU nor GPU wins by designation; measure complete operations with their accuracy requirements held constant.

Do not apply broad reassociation or unsafe floating-point settings to precision-sensitive kernels. If evaluating such settings, treat them as a separate numerical contract with explicit tests.

## Benchmark gate before a production change

The first bounded comparison should cover sum, dot product and variance, followed by the affected ANOVA workflow. Use the current production implementation as the baseline and compare native fused arithmetic, blocked reductions and compensated candidates. For the original-decimal cases, separately compare the input-preserving representation through ingestion and computation.

Inputs must cover cancellation, mixed magnitudes, large offsets with small spread, reordered data, null handling, subnormals, near-overflow values and ordinary observations. Include sizes that fit in cache and sizes that require sustained memory traffic. Inspect assembly and profile where the measured cost warrants it.

For each candidate, record the reference answer, absolute and relative error where meaningful, time distribution, allocation and resident memory cost. Record compiler, optimization flags and machine. Measure energy only if supported by actual instrumentation. Maintain existing failure classifications and acceptance limits.

Accept a candidate only after it meets the numerical requirement and shows a useful cost improvement on representative work. Keep narrow kernel results separate from complete-workflow claims. Validate on additional Apple silicon generations before treating a threshold measured on the M4 Max as general.
