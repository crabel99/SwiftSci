# Precision branch performance comparison

Comparison date: September 28, 2026. Current implementation: `3a31534e3604bb0eb516546b2f8ab898f1f87ccd`, branch `codex/apple-silicon-precision`. Before reference: `36053baca6bf38a9233ca9798c151816f4bdf259`, the parent of the precision changes. This compares the precision branch with its starting point; it does not claim to compare every pending branch against upstream main.

## Findings

The default dot product and large-group ANOVA are faster than before and close to NumPy/SciPy at about one million inputs. The improved variance calculation costs a few percent versus the prior Swift implementation and gives better accuracy on large-offset inputs. Compensated dot products have a substantial explicit cost.

The maintained dataframe benchmark passes for both languages. Target extraction and the dataframe scaler workflows remain much slower than their Python counterparts in this branch. The previously implemented direct target extraction is on `codex/compact-column-storage`, commit `826cdd0d9b`, and is not an ancestor of the measured branch. These results must not be presented as a regression in that unmerged optimization.

## Matched numerical operations

Times are milliseconds. Each entry is the median of three process medians, each based on nine measured batches after four warmups. Both Swift binaries compile the actual committed SwiftStats source with the same `swiftc -O` command and identical existing dataframe dependencies. Those dataframe sources did not change between the two commits. Python uses NumPy 2.5.3 and SciPy 1.18.1.

| Operation and size | Before Swift | Current Swift | NumPy/SciPy | Before/current speedup |
|---|---:|---:|---:|---:|
| Dot, 65,536 elements | 0.0090 | 0.0017 | 0.0021 | 5.19x |
| Dot, 1,048,576 elements | 0.1569 | 0.0512 | 0.0536 | 3.07x |
| Dot, 8,388,608 elements | 1.2492 | 0.9349 | 0.7897 | 1.34x |
| Variance, 1,048,576 large-offset values | 0.5440 | 0.5631 | 0.5250 | 0.97x |
| Standard deviation, 1,048,576 large-offset values | 0.5596 | 0.5866 | 0.5242 | 0.95x |
| Variance, 8,388,608 large-offset values | 4.5059 | 4.6369 | 4.2845 | 0.97x |
| ANOVA, three groups of 1,048,576 | 8.4417 | 5.0201 | 4.9871 | 1.68x |

A speedup below 1 means the current implementation is slower. The large-offset variance and standard-deviation rows are not equivalent-accuracy results: the prior Swift and NumPy values miss the declared supplemental `abs(reference) * 1e-12 + 8 * smallestSubnormal` threshold; the current values pass. This is an analytical stress criterion, not a change to the maintained NIST tolerances.

The default dot result matches the analytical answer for every mixed-sign timed size. At 8,388,608 values, Python has the lower median, but the process ranges overlap: current Swift 0.918 to 0.989 ms, Python 0.763 to 0.954 ms. Do not infer a stable platform-wide advantage from that row. At one million values, current Swift and NumPy are close; both use Apple Accelerate for BLAS.

## Explicit accuracy cost

| Dot product, 1,048,576 elements | Performance mode | Compensated mode | Result |
|---|---:|---:|---|
| Mixed signs | 0.0512 ms | 1.5562 ms | Both match the reference |
| Constructed product cancellation | 0.0528 ms | 7.5025 ms | Only compensated mode matches the reference |

For ordinary mixed-sign data, compensated mode is about 30 times slower in this run. The cancellation case invokes exact recovery and costs about 142 times the fast path. Old Swift, current performance mode and NumPy all return zero for that constructed case; the exact answer is `-2.9103830456733704e-11`. The compensated API recovers it.

The two-value rounded-mean regression returns variance `67.578125` with the old implementation and NumPy, versus the exact binary64-input result `67.5703125` with the current implementation. Faster arithmetic is not automatically more accurate arithmetic.

## Decimal ingestion and ANOVA

These calls start with identical original decimal strings. Both include parsing, exact decimal centering, conversion and ANOVA inside the timed call. Swift uses its public decimal API; Python uses checked Decimal arithmetic at precision 80 followed by SciPy. JSON decoding is outside timing. All returned F statistics pass the unchanged NIST tolerances. The old API has no equivalent original-decimal input path, so it is not given an equivalent-correctness speed column.

| Dataset | Observations | Swift | Python Decimal + SciPy | Python/Swift speedup |
|---|---:|---:|---:|---:|
| SmLs07 | 189 | 0.0831 ms | 0.2826 ms | 3.40x |
| SmLs08 | 1,809 | 0.7482 ms | 0.6566 ms | 0.88x |
| SmLs09 | 18,009 | 7.7085 ms | 4.1794 ms | 0.54x |

The largest decimal case remains about 1.84 times slower in Swift. This is a clear ingestion optimization opportunity. It does not impose a cost on the existing binary64 API.

## Maintained standard profile against Python

This is the current recorded Release worker, source fingerprint `80897d608cb0ed3619edc474317549cce82a60451e63674355833f54b1c15b11`. All 84 process executions pass and the certificate audit passes. The profile uses three processes per case per engine, two warmups and five measured samples. Each engine is summarized as a median of process medians. The table uses 100,000-row dataframes, all final outputs checked against the same references. Times are milliseconds.

| Operation | SwiftSci | Python | Python/Swift speedup |
|---|---:|---:|---:|
| csv-read | 7.3015 | 11.0157 | 1.51x |
| filter | 0.2448 | 0.7530 | 3.08x |
| sort | 2.9909 | 3.0034 | 1.00x |
| group-sum | 0.3885 | 0.5507 | 1.42x |
| flat-matrix | 0.1279 | 0.7265 | 5.68x |
| target | 3.9074 | 0.1104 | 0.03x |
| standard-scale | 28.3930 | 0.9808 | 0.03x |
| minmax-scale | 33.2366 | 0.8013 | 0.02x |
| mean | 0.0076 | 0.0158 | 2.07x |
| variance | 0.0533 | 0.0578 | 1.08x |
| stddev | 0.0532 | 0.0573 | 1.08x |

Python explicitly copies target and flat-matrix output arrays. The target gap is not a borrowed-view versus copied-array comparison. Swift `toTargetVector` currently constructs `[[Double]]` using `toFeatureMatrix`, then maps its first column. The direct extraction repair on the compact-storage branch removes that structure.

The scaler rows measure fit, transform and export through the dataframe API, not an isolated arithmetic kernel. Swift extracts nested feature matrices for fitting and transformation, creates transformed columns and exports a flat matrix. The Python adapter uses NumPy arrays to produce the declared final row-major values. Source inspection identifies conversion and reconstruction as candidates for profiling; it does not quantify their individual cost. These dataframe and preprocessing implementations are unchanged from the precision branch starting point.

No new before/after standard-dataframe run was made. The before/after numerical table uses independently built exact source snapshots. Earlier exploratory memory measurements found the variance change eliminated an approximately 64 MiB temporary at 8,388,608 elements; memory was not remeasured in isolation here.

## Reproducibility and limits

Hardware is Apple M4 Max on macOS 27.0, Apple Swift 6.4. NumPy was built with Accelerate. `VECLIB_MAXIMUM_THREADS`, `OPENBLAS_NUM_THREADS` and `OMP_NUM_THREADS` were set to 1 for all new runs; this records requested thread limits, not a proof of undocumented backend thread dispatch. Inputs are reused across timed calls. This measures repeated-buffer behavior.

Before, current and Python process order rotates across three rounds. Input hashes match across implementations for all 37 numerical input cases. Independent rational formulas supply variance, dot and ANOVA references. Construction, hashes and reference calculation are outside timing. Decimal fixture hashes also match. No tests or compilation ran concurrently with timing processes. This was a normal desktop session with background services, not an isolated performance lab. Raw process spreads are retained.

The standard profile was run sequentially after the numerical experiments. A source-hashed maintained worker and the unchanged versioned contracts identify that run. The numerical and decimal experiments are supplemental public-API comparisons, not new formal suite definitions. No production code changed for this report.

All drivers, exact source snapshots, build commands, backend information, raw timings, analytical references, standard run outputs and certificate are retained in [the performance comparison archive](../archive/2026-09-28/performance-comparison/evidence.tar.gz). `MANIFEST.json` checksums every archived member. Engineering evidence remains exclusively on `codex/engineering-notes`.

## Next priorities

Integrate and validate the already-existing direct target extraction on the appropriate branch. Profile the dataframe scaler conversion and reconstruction work, where the measured workflow gaps are about 29 times and 41 times. Improve decimal parsing and centering while preserving the exactness checks. Further ordinary dot-product tuning is a lower priority at the million-element size, where the current implementation is already close to NumPy on the same backend.
