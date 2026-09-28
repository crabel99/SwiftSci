# Scientific precision practices and a SwiftSci proposal

Date: 2026-09-28. Status: research and measured input-conversion experiment. The API direction below is a proposal for discussion, not a maintainer-approved design.

The reviewed SwiftSci checkout is `7054d5e93ffbbf7d0fd224bb97e3d4f11740782c`. This note belongs only to the fork's `codex/engineering-notes` branch. No production code or acceptance tolerances changed.

## Finding

Established scientific packages address precision through input representation, stable arithmetic and result diagnostics. A shared offset fits some scientific data well. It cannot recover information already discarded during conversion, and it does not solve every numerical problem.

Caller intent should usually enter through a data type, units, resolution or accuracy requirement. The library should choose stable algorithms within that contract. Users should not need to select summation algorithms for ordinary statistics.

## Practices in existing libraries

### Astropy preserves absolute time, then computes in relative time

Astropy `Time` stores a date as two binary64 parts. Arithmetic preserves those parts; display precision is a separate setting. This is a per-value representation, distinct from one origin shared by a column. [Astropy time documentation](https://docs.astropy.org/en/stable/time/index.html#internal-representation)

The pinned implementation uses compensated `two_sum` and `two_product` operations. Its decimal conversion splits the input before converting parts to floats. Keeping two fields would not help if every operation first collapsed them into a single `Double`. [Astropy 7.1.0 implementation](https://github.com/astropy/astropy/blob/v7.1.0/astropy/time/utils.py)

Astropy's Lomb-Scargle constructor accepts absolute `Time` values, retains them, subtracts the first observation, and passes relative days to numerical routines. Ordinary numeric inputs retain their relative-time interpretation. This is a close precedent for an accurate input representation feeding conventional floating-point kernels. [Lomb-Scargle implementation](https://docs.astropy.org/en/stable/_modules/astropy/timeseries/periodograms/lombscargle/core.html)

### CF/netCDF makes scale and offset part of the data contract

CF packed data decodes as `packed * scale_factor + add_offset`. Missing-value handling occurs before the transformation. Scale and offset metadata state how to interpret the stored values. [CF packed-data convention](https://cfconventions.org/cf-conventions/cf-conventions.html#packed-data)

Unidata recommends rounding to the nearest integer when encoding packed integers. This generally quantizes the input. In exact arithmetic, without clipping, the quantization error is at most half the scale magnitude; floating-point encoding and decoding can add error. A packed integer column and a column of floating residuals therefore make different promises. [Unidata attribute conventions](https://docs.unidata.ucar.edu/netcdf-c/current/attribute_conventions.html)

For SwiftSci, retaining a scale or origin through suitable operations deserves investigation. Eagerly reconstructing a large absolute `Double` can discard the small variation again.

### NumPy and SciPy improve arithmetic within the selected type

NumPy uses partial pairwise summation in many cases. Its choice depends on the reduction axis and memory layout. The caller can select an accumulator dtype; variance also supports a wider accumulator than the input storage. This separates storage cost from reduction accuracy. [NumPy sum](https://numpy.org/doc/stable/reference/generated/numpy.sum.html), [NumPy variance](https://numpy.org/doc/stable/reference/generated/numpy.var.html)

SciPy 1.18.0's equal-variance `f_oneway` path subtracts the combined mean before calculating sums of squares. Its source explicitly identifies numerical stability as the reason. Centering improves arithmetic on the supplied values, but cannot restore decimal distinctions already lost on ingestion. [Pinned SciPy source](https://github.com/scipy/scipy/blob/v1.18.0/scipy/stats/_stats_py.py)

### LAPACK returns evidence about the solution

The expert linear solver `DGESVXX` supports equilibration, condition estimates, iterative refinement and error bounds. Its refinement computes residuals at least twice the working precision. It can warn when the requested accuracy cannot be guaranteed. Those guarantees have documented assumptions and limitations. [LAPACK DGESVXX](https://www.netlib.org/lapack/explore-html/df/d38/group__gesvxx_ga4b2a7e11fe7425c012ca9eba6c06877f.html)

This suggests operation-specific diagnostics for SwiftSci. A condition estimate describes sensitivity to input perturbations; a residual describes how well a computed solution satisfies the equations. Neither is interchangeable with measurement uncertainty. DGESVXX is a square-system solver, not a proposed replacement for least squares. Availability in Apple's supplied LAPACK has not been established here.

### MPFR keeps higher precision explicit

MPFR provides selectable precision and rounding. Its manual recommends string conversion when a numeric constant would otherwise round to a native double first. Increasing precision after that rounding cannot reconstruct the original decimal. Parsing a string into a finite binary format can itself round. [MPFR manual](https://mpfr.org/mpfr-current/mpfr.html)

An arbitrary-precision reference can distinguish input error from algorithm error. It need not become the default dataframe representation. Its performance and interoperability costs require separate measurement.

## Local evidence

SwiftSci's `CSVReader.parseCSVDouble` returns a `Double` directly, using the byte parser or a string fallback. That path commits to binary64 before a statistical API receives the column. The benchmark Python worker's ANOVA comparator uses SciPy; its least-squares comparator uses SciPy's `gelsy` driver. A comparator labeled with the pandas ecosystem is not independent proof of numerical correctness.

The [existing repair record](2026-09-27-pr41-repairs.md) records the distinction between original-decimal certification and the exact binary64-input reference. These research results do not supersede that validation.

### Controlled conversion experiment

The probe parses the existing SmLs07, SmLs08 and SmLs09 JSON numeric tokens as exact rational values. It evaluates ANOVA with exact rational arithmetic after each conversion path, so subsequent floating-point arithmetic cannot obscure the ingestion effect.

1. Preserve the original decimal values as the reference.
2. Convert each absolute value to binary64.
3. Subtract the exact origin `1000000000000`, then convert residuals to binary64.
4. Convert absolute values first, then subtract the origin in binary64.

| Dataset | Original decimal F | Absolute binary64 input F | Shift before conversion F |
|---|---:|---:|---:|
| SmLs07 | 21 | 21.000811887818771 | 20.999999999999999630 |
| SmLs08 | 201 | 201.013004095948455 | 200.999999999999994079 |
| SmLs09 | 2001 | 2001.134926220950509 | 2000.999999999999938568 |

Shifting after conversion gave exactly the same rational F as the absolute binary64 input in all three cases. Shifting before conversion reduced absolute F error to approximately `3.70e-16`, `5.92e-15` and `6.14e-14`, respectively.

These are conversion-isolation results, not SwiftSci execution or throughput measurements. They establish a useful candidate representation for these fixtures. They do not establish a universal origin-selection rule, streaming behavior, performance improvement or the accuracy of every downstream operation.

The archived [probe](../archive/2026-09-28/precision-practices/probe.py) and [results](../archive/2026-09-28/precision-practices/results.json) include input hashes and the source revision. Run the probe with Python 3 and a checkout containing the recorded fixtures:

```sh
python3 probe.py /path/to/SwiftSci
```

## Proposed SwiftSci boundaries

Keep the existing `Double` API's meaning. Its input is the represented binary64 value. Do not reinterpret that value as an inferred decimal or silently change its units.

Prototype an explicit input-preserving representation separately. Compare a shared origin with `Double` residuals, scaled integers, and two-part values. Text or another precise representation must reach this boundary before binary64 rounding. Caller-provided units and resolution can state the accuracy requirement without exposing every algorithm choice.

Route compatible operations through residuals. Filtering against an absolute threshold must transform that threshold consistently. Sorting values under one common origin is simpler than comparing columns with different origins. Joins, concatenation, mutation, streaming outliers and persistence must preserve or deliberately reconcile their metadata. A variance or common-shift ANOVA can exploit translation invariance; a mean must retain its origin. Nonlinear operations need their own derivation.

Make conversion to ordinary matrices explicit when it would collapse preserved detail. Relative feature matrices can use ordinary kernels when the algorithm and model metadata retain the transformation. An absolute matrix export cannot promise more precision than its scalar type.

Add diagnostics where the mathematics supports them. Keep input-conversion error, numerical error and measurement uncertainty distinct. A universal accuracy flag would conceal these differences.

## Apple silicon tradeoffs

Apple's ARM64 ABI makes C `long double` equivalent to `double`; Swift `Float80` is restricted to supported x86 targets. Wider native scalars cannot be assumed for our target platform. [Apple ARM64 ABI](https://developer.apple.com/documentation/xcode/writing-arm64-code-for-apple-platforms), [Swift Float80](https://developer.apple.com/documentation/swift/float80)

A shared origin with contiguous `Double` residuals is attractive because it can preserve the existing kernel layout. Its nominal payload is eight bytes per sample plus origin metadata. Two binary64 parts need sixteen bytes per sample before metadata. These are representation counts, not measured memory or speed ratios. Paired arithmetic, rebasing and conversions add work. Unified memory does not increase arithmetic precision, and GPU conversions need their own error tests.

## Next evidence needed

Before proposing a public API, test one complete ingestion-to-result path using preserved input and the current Double path. Include the three difficult NIST fixtures and ordinary scientific data. Keep existing certification results intact rather than quietly replacing their inputs.

Exercise different origins, mixed signs, outliers, units, missing values, threshold boundaries, concatenation, mutation and persistence. Check results against an independently computed high-precision reference. Measure ingestion, resident memory, reductions and matrix export separately on Apple silicon.

The intended decision is whether an explicit representation improves complete scientific workflows at acceptable cost. It is not whether a special path can make three fixtures pass.
