# Serial gather specialization plan

2026-10-18. Based on `d23bf7cac9`, branch `codex/dataframe-serial-gather-specialization`. The row-partitioned trial remains preserved separately. This plan precedes measurements of this candidate.

The candidate extracts the existing scalar gather loop into a private helper and calls it through concrete String, Bool and Date types. Keep the source and destination representation, initialization, null-count calculation, output lifetime and dataframe scheduler unchanged. Other SupportedType conformers keep the generic fallback. Numeric gather routines retain their existing dispatch. Inspect optimized object symbols to verify concrete specializations; compiler behavior is part of the evidence, not an assumed source-level property.

Reuse the previous frozen public-API executable and identical harness for original/candidate pairs. Measure prepared-permutation gather and complete stable sorting, with complete output checks outside timing. Native CPU scheduling, unchanged AC settings, one process at a time, rotating pair order, two warmups and five measured samples per process remain required. Durations below one microsecond retain correctness checks but cannot support ratios.

Screen five process pairs per case. Use numeric tables at 100,000 and 1,000,000 rows with four columns; mixed tables at 100,000 rows with two and four columns; and protected numeric cases at 129, 4,096 and 32,768 rows with one and four columns. Measure both gather and complete sort. These cases check the intended mechanism and protect the earlier numeric paths.

Reserve 250,003-row mixed tables with three and eight columns and repeated sort keys for confirmation, using ten process pairs per case and both operations. Do not retune the implementation after inspecting those results. A useful result requires at least 0.25 ms median paired absolute saving in each held-out complete-sort case, with each process pair favoring the candidate. This is an explicit absolute benefit criterion for the current preprocessing workload, not a universal percentage requirement.

Protected screening complete-sort bounds are a median paired slowdown no greater than 5 microseconds for at most 4,096 rows, 0.1 ms at 32,768 and 100,000 numeric rows, and 1 ms at 1,000,000 numeric rows. Report all paired ranges. Results within these bounds do not erase noisy or slower cases. Escalate any repeatable protected-case loss before promotion.

No additional payload/index arrays, task counters or parallel row tasks are allowed. Confirm source-plus-destination logical payload remains below 1 GiB and report peak RSS separately. A median peak-RSS increase greater than 2 MiB on a matched case needs explanation. Neither RSS nor elapsed time proves allocation count, CPU work or energy efficiency.

Run all dataframe tests in Debug, Release and Address Sanitizer configurations, complete scientific/persisted/CSV integration controls, and verify source snapshots, generic fallback, null counts and supported-type behavior. Capture the instrumented library object and raw profile together before later builds can overwrite them. Production line-coverage evidence must come from the library mapping, not only test-source coverage.
