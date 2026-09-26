# NIST univariate coverage increment

## Scope and API mapping

Expand the initial NumAcc4 coverage to all nine NIST StRD univariate datasets: PiDigits, Lottery, Lew, Mavro, Michelso and NumAcc1 through NumAcc4. Each dataset checks mean, sample variance and sample standard deviation through existing SwiftStats and NumPy APIs. This is 27 cases per engine, compared with three previously.

The raw files remain unchanged and checksum-pinned. The original headers provide the observation counts, decimal reference answers and data boundaries. Fixture tests independently recompute the answers with 60-digit decimal arithmetic. Variance is derived from the published standard deviation and is labelled accordingly. Autocorrelation and the ANOVA/regression collections need separate API mappings; they are outside this increment.

## Numerical acceptance

Use a fixed input-scale policy, set before running either engine. The absolute budget is twice the maximum binary64 ULP among the dataset's values. Mean and standard deviation use that budget. Variance propagates it as `2 * reference_stddev * budget + budget²`. Relative allowances are 1e-14, 1e-12 and 2e-12 respectively. Unit tests enforce those choices. The policy allows representation and reduction rounding; it does not establish a formal error bound or promise all printed NIST digits.

All initial accuracy checks passed without changes to production statistics code or adjustments to the tolerances. NumAcc4's small dispersion at a large offset and Mavro's narrow spread now receive explicit coverage. The report exposes the worst measured absolute error, so a passing status does not conceal the observed accuracy.

## Measurement correction

The first repeated run exposed an avoidable measurement cost. The Swift worker awaited a shared asynchronous dispatcher even for synchronous statistics. Tiny mean calls took several microseconds before accounting for useful numerical work. The dispatcher existed to accommodate asynchronous CSV reads.

The correction keeps CSV asynchronous and calls synchronous operations directly. Measurement contract v2 prevents comparison with the old timing boundary. This changes the benchmark, not the library algorithm. Preserve the v1 run as diagnostic evidence; do not present the timing difference as a SwiftSci optimization. The v2 run then exposed three cases with zero-duration clock readings. These were correct outputs, but the earlier protocol failed them before retaining the sample. Contract v3 separates output accuracy from timing resolution. Each worker retains the raw duration and marks samples below one microsecond as unresolved. Zero is accepted only with that explicit flag; negative durations and inconsistent flags fail. A case receives no speedup ratio if any measured sample is unresolved. No samples are retried, discarded or replaced with invented positive durations. This supports accuracy certification of tiny reductions without pretending their timings are reliable. Calibrated batching remains future work.

Historical positive-duration records remain readable. The schema permits the new timing flag as an additive field, while zero-duration records require it. Experiment contract v3 prevents comparisons across the changed measurement rules.

## Verification and contribution boundary

The coverage commit is `cb38cbedd9`; the timing correction is `e6444c46a1`. Full native Debug and Release suites each passed 901 tests with no skips for the coverage implementation. All 477 native source, test and package files matched that tested snapshot. The later timing correction changed the worker and its contract identifier; numerical validation is repeated with that worker. The final protocol correction is `83f9639e4d`. The Python suite now has 24 passing tests. Final native and repeated-run results are recorded alongside this decision.

Public fixtures, schemas, tests and usage instructions stay on `codex/standardized-benchmarks`. This rationale and all local run evidence stay on `codex/engineering-notes`. No contribution PR has been submitted. The GitHub workflow now checks every NIST case but has not been executed on GitHub.

## Final results

The final source is `83f9639e4d2b4664470e31dd92d27a525c76425f`. All 477 native files in the tested snapshot match that revision. Debug and Release each passed 902 tests, with zero failures and zero skips. The Python protocol suite passed 24 tests.

The repeated NIST profile passed 162 fresh processes and all 810 measured output checks across SwiftSci and NumPy. Each engine contributes 405 samples. SwiftSci had 363 samples below the one-microsecond threshold, including three zero-duration readings. Those affect 25 of its 27 case summaries, which therefore have no speedup ratio. NumPy had no unresolved samples. These small datasets validate numerical behavior; most SwiftSci reductions need a separately designed batched experiment before useful timing comparisons can be made.

The separate certification run passed all 54 engine/case combinations. The dataframe smoke run passed all 28 combinations. All three certificates passed checksum and complete-coverage audit. Self-comparison also verified that unresolved cases never produce speedup ratios.

The [evidence archive](../archive/2026-09-26/nist-univariate/) contains the final run records, certificates, test counts, worker build identity and SHA-256 manifest. It also retains the v1 run with asynchronous dispatch overhead and the v2 failed timing diagnostic. These earlier records explain the measurement correction; they are not library performance comparisons. The full local logs remain under the ignored `Benchmarks/Runs` directories and the paths recorded in the build evidence.

The contribution branch is committed locally. It has not been pushed, and no PR has been created for this increment. Its history passes the local guard against engineering-note paths. The GitHub conformance workflow still needs an actual hosted run.
