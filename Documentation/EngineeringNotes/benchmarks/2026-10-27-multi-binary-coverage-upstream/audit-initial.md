# Initial evidence and decision-trail audit

reviewed by gpt-6-astra

Reviewed source commit `08486058190836df0a3b1916aa2cb633450a35fc` against `200d3935cc43396658a315bf4d5f745b6c7b496c`, spec.md, the three existing decision rows, the scoped transcript, retained failed and passing regression logs, both historical controls, and historical-green.lcov. This is an interim audit. Full final-head qualification and publication have not been approved by this review.

The three-file diff matches the requested correction. It removes the concatenated shell argument list and failure mask, invokes LLVM with an explicit object for each additional executable, preserves stderr and normal nonzero exit status, and holds output until all three required modules have positive line counts. No library code, dependency pin, threshold, exclusion, or safe-test skip changed. I found no actionable implementation defect in this scope.

The regression evidence is credible. Transcript line 152 records final fixtures run against the untouched upstream workflow and restores the candidate workflow afterward. All eight controls fail in regression-red-final-fixtures.log. The corrected workflow passes those eight controls plus the five existing documentation controls in regression-green-2.log and regression-python39.log. The first failed green attempt remains in regression-green.log. Its count collision and diagnostic path mismatch explain the fixture correction, which strengthens the negative control rather than relaxing the expected behavior.

The historical controls show why binary order matters. Transcript line 149 and baseline-reproduction-known-path/result.json preserve the sorted Agent-first control that unexpectedly contained all three required modules and failed the omission assertion. Line 157 and baseline-original-order/result.json show the original find order selected NLP first and omitted Agent. That line also checks the retained prior workflow report, which has the same omission. This supports the bug without implying every ordering omits the same module. The existing reproduce row states this distinction accurately.

I independently counted the corrected historical LCOV. Agent has 8 source records with 8 executed, DataFrame 50 with 47 executed, and NLP 45 with 44 executed. Transcript line 177 records the successful helper invocation using the old package's binaries and profile. These are historical artifact checks, not new final-head package test execution.

## Attention

reviewed by gpt-6-astra

- Final-head qualification remains open. spec.md requires complete actual package safe tests and applicable checks before the draft PR. Current regression success and historical LCOV do not meet that gate. Inspect the completed six jobs, exact source identity, actual fresh exported coverage, and retained limitations before marking complete.
- Append the historical lookup pivot to decisions.tsv. Transcript lines 140 and 147–149 show the task's stalled `swift build --show-bin-path` process, its termination, and the switch to a known historical artifact directory. This explains why that reproduction bypassed the original lookup. The decision trail currently omits it.
- Append the source commit, historical green scope, and qualification launch/checkpoint before handoff. The three current rows are accurate but do not yet connect commit `0848605819` and the running checks to their evidence. Resolve the first row's shorthand `prior coverage-followup.md` to its real retained path or publication-relative artifact so a reviewer can follow it.
- Keep the raw task transcript local until publication sanitization has been checked. Although restricted to this user turn, it includes account usage and credit-balance telemetry, inherited connector attribution, local user paths, and broad process-list output. A turn boundary alone is not a privacy filter. The later publication audit must inspect the actual staged files and redaction manifest, not only a sanitizer's success message.
