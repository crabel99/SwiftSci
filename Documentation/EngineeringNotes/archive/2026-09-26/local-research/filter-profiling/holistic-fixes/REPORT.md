# Integrated optimization results

Branch `codex/dataframe-optimizations`, baseline `3387fd4189`, final `27f3c1bdf1`. Six local commits implement and validate this pass. No PR was opened and these six commits have not been pushed.

## What changed

- Native Int sorting stays in the integer domain. Ordinary reductions accept Int values and retain their existing Double output contract. Custom Int values also convert correctly.
- Numeric filters dispatch outside row loops for every built-in numeric width. Mixed integer/floating thresholds compare represented values exactly in both directions, without truncating fractions, erasing low integer bits or trapping at integer limits. Float NaNs now follow the same IEEE comparison rules as Double.
- Group identity uses typed components and first-seen prefix IDs. Literal null markers, tuple delimiters, subsecond dates and unequal values with equal hashes no longer collapse groups. Signed zeros group together, NaNs have a present identity distinct from null, and first-seen output labels remain unchanged.
- Rename reuses immutable storage and the cached null count. Filtered and unique columns retain counts established during construction.
- Native Int, Float and Int32 gathers use concrete dispatch into the same typed map strategy as Int64. Existing Double gather stays unchanged.

## Measurements

Apple M4 Max, 128 GiB memory, macOS 27, Swift 6.4, arm64 Release. One million rows and 100 groups. Three before/after process pairs alternate order; each process has two warmups and five timed samples per operation. Tables report medians of 15 samples. Full output values and row order are checked after timing. The before binary has known incorrect native Int sum and sorting behavior; native Int sum is excluded from speedup claims.

| Operation | Before, ms | After, ms |
|---|---:|---:|
| Native Int filter | 209.010 | 3.133 |
| Float filter | 158.400 | 3.125 |
| Int32 filter | 193.473 | 3.151 |
| Int64 filter | 3.184 | 3.143 |
| Double filter | 2.920 | 2.840 |
| One integer grouping key | 3.529 | 3.531 |
| One string grouping key | 18.228 | 18.550 |
| Two integer grouping keys | 416.586 | 39.116 |

Rename no longer scans one million values. Its old cost was about 17.6 ms; the new probe is near timer resolution. This supports the algorithmic removal of the scan, not a reliable nanosecond speedup ratio.

Whole-process peak resident memory was about 203.2 MB before and 193.0 MB after, measured by macOS time in the same benchmark process. These include fixture construction, every operation and correctness checks. They do not isolate a kernel's allocation count or demonstrate compact column storage.

Isolated stage probes located the remaining filtering cost in generic gather, not comparison. Selection took about 1.3 ms per numeric type. Before gather specialization, native Int gather took about 8.7 ms and Float/Int32 about 5.5–5.8 ms. Alternating comparisons after specialization measured roughly 0.9 ms for these gathers. End-to-end filtering improved too.

Nullable gather probes check both ordered and deterministically permuted indices against full reference arrays and exact null counts. All passed. With about 1% source nulls and half the rows selected, these runs measured about 0.9–1.1 ms; they are not a separate controlled before/after comparison.

Small movements in already-fast paths are not evidence of a universal speedup or regression. This is one machine and a specified workload, not a claim about every cardinality, distribution or model pipeline. No GPU or Neural Engine offload is involved, and no achieved DRAM bandwidth or SIMD instruction count is claimed.

## Correctness and review

Before the fixes, native Int regressions reported 11 assertion failures; numeric filter cases reported 78, and the reverse mixed-comparison extension reported 64; structured grouping reported 14. The corresponding tests pass after implementation.

All 318 scoped checks pass in Debug and Release: 32 DataFrame XCTest cases, 2 statistics XCTest cases, 157 DataFrame Swift Testing tests, 61 statistics tests, 56 forecasting tests and 10 independent checks. This is not the full MLX-dependent package suite. The earlier full-package attempt was blocked by local generated-bundle signing metadata.

Subsequent full-package validation resolved that blocker: all 840 tests pass in both Debug and Release, including MLX/GPU suites. See the [full-suite validation report](../../full-suite-validation/REPORT.md) for the build setup, one-line test import correction, and retained results.


An additional independent Python oracle generated 200 integer/Double pairs across limits, fractions, subnormals, nonfinite values and deterministic random bit patterns. All 4,800 Swift checks passed across both public filter methods, all six comparisons and both operand directions. Fixtures store integer strings and floating bit patterns to avoid JSON rounding. The generator, Swift checker, fixtures and result are retained as mixed-oracle.* and mixed-oracle-result.txt.

The documentation checker exits successfully with no placeholders, but reports 2042/2060 documented symbols before an inaccurate 100% banner. No complete-coverage claim is made.

Subagents independently researched hardware, algorithms and comparison semantics, then reviewed the integrated implementation. The chosen design and primary citations are in DESIGN.md and the three research notes. No correctness blocker remained in that review.

## Constraints retained and explicit limits

The user targets modern Apple Silicon. The inherited minimum OS was not used to rule out a better implementation; this pass needed no newer OS-specific API, so the manifest stays unchanged. Public optional arrays and ownership semantics stay unchanged. Compact storage remains separate.

AnyColumn does not expose equality for arbitrary non-Hashable values. Such custom keys retain a documented, per-component runtime-type/description fallback; equal descriptions can still merge unequal custom values. Custom Hashable keys use actual equality. Exact integer sums still require sumChecked; existing sum/mean result dtypes were not silently replaced.

Further work would require a new measured hypothesis: bounded first-component lookup for composite keys, reusable group IDs, cardinality-adaptive hash/sort aggregation, or a different numeric sorting algorithm. They are not claimed as completed here.

## Reproduction

`main.swift` and `Package.swift` preserve the matched probe. Put the source at Sources/ReviewProbe/main.swift within the package directory and build arm64 Release. The local dependency path identifies the SwiftSci checkout. `before` and `after` are saved executables; `final-comparison.py` reruns the alternating measurement. Metadata records hashes, revisions and environment. Raw timing samples are in final-comparison.json, with output checks in final-*.txt. Logs preserve red and green test runs.
