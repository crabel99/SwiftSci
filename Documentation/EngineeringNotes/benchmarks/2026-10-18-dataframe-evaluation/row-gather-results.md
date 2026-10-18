# Row-partitioned gather results

2026-10-18. Trial branch `codex/dataframe-row-partition-gather-trial`, head `5ee2d5b2617fd225176d9e9aa293f8669fe29188`. The main CSV/sort branch remains at `d23bf7cac9`. Nothing from this trial is promoted or pushed.

The experiment found two separate costs: generic copying that Swift did not specialize through the new protocol witness, and scheduling more work across row ranges. Concrete dispatch fixes the first cost. Row parallelism helps some large copies and mixed-column sorts, but it is not a universal improvement.

## What changed

The rejected first candidate added an internal protocol for partitioned copying. It compiled a generic loop with metadata-dependent strides and indirect calls, and substantially slowed the primary numeric cases. Its incomplete screening evidence is preserved in `v1-rejected.json`. Unrun cases are not passing evidence.

The second candidate replaces that protocol with a concrete-type switch at the column boundary. Its object file contains explicit specializations for the supported types. The source copy algorithm remains generic; each concrete call lets the compiler specialize it before entering the loop. Custom `AnyColumn` conformers retain their existing gather implementation.

Large eligible selections divide each final column into disjoint row ranges. Sources and indices remain borrowed until synchronous completion. Each column has one final allocation, with no chunk payloads or concatenation. Private counters preserve exact null counts. Small selections and already-wide tables retain the earlier copy routines, although their dispatch wrapper changed. The latter still needs attention because some protected cases regress.

A serial control uses the same specialized source, partition ranges, initialization and counters, replacing row `concurrentPerform` with a serial task loop. Existing column-level parallelism remains. This separates the scheduling decision from much of the specialization change, while retaining compiler differences caused by the dispatch boundary.

## Original implementation versus specialized row parallelism

Five paired fresh-process rounds per case used the same frozen public-API harness, two warmups and five timed samples per process. Runs used AC power and native CPU scheduling. Every sample checked the complete output after timing. The screen contains 54 cases, 540 processes and 2,700 measured samples.

Values below are milliseconds, using the median of process medians. The ratio is the median paired baseline/candidate ratio; its bracketed range is the minimum and maximum paired ratio. Ratios above one favor the candidate. The range is observed spread, not a confidence interval.

| Operation | Rows | Columns | Input | Original ms | Candidate ms | Paired ratio [range] |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| sort | 1,000,000 | 1 | random, numeric | 20.764 | 19.105 | 1.076 [1.049, 1.214] |
| sort | 1,000,000 | 2 | random, numeric | 20.434 | 19.073 | 1.095 [1.042, 1.149] |
| sort | 1,000,000 | 4 | random, numeric | 22.512 | 22.219 | 1.055 [1.006, 1.150] |
| sort | 1,000,000 | 16 | random, numeric | 35.446 | 37.036 | 0.977 [0.951, 1.073] |
| sort | 100,000 | 2 | nulls, mixed | 7.033 | 3.395 | 2.071 [1.688, 2.180] |
| sort | 100,000 | 4 | nulls, mixed | 7.314 | 3.496 | 2.092 [2.028, 2.793] |

Mixed 100,000-row complete sorting improved by about 2.1 times against the original implementation. Million-row narrow numeric gathering improved by about 1.75 to 2.24 times, but complete numeric sorting improved much less. The four-column case illustrates why an isolated gather ratio cannot be substituted for the complete-sort result.

## Specialized serial control versus row parallelism

This separate paired campaign contains ten cases, 100 processes and 500 samples. Compare implementations within this campaign. Its absolute timings differ from the previous campaign; do not combine or multiply ratios across them. Both source specialization and native scheduling can affect a complete operation.

| Operation | Rows | Columns | Input | Specialized serial ms | Row-parallel ms | Paired ratio [range] |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| gather | 100,000 | 1 | random, numeric | 0.128 | 0.084 | 1.484 [1.328, 1.654] |
| sort | 100,000 | 1 | random, numeric | 1.623 | 1.652 | 0.977 [0.865, 1.034] |
| gather | 100,000 | 4 | random, numeric | 0.184 | 0.213 | 0.819 [0.786, 1.259] |
| sort | 100,000 | 4 | random, numeric | 1.742 | 1.754 | 1.003 [0.935, 1.050] |
| gather | 1,000,000 | 1 | random, numeric | 1.402 | 0.707 | 2.023 [1.793, 2.151] |
| sort | 1,000,000 | 1 | random, numeric | 19.287 | 18.173 | 1.068 [1.014, 1.158] |
| gather | 1,000,000 | 4 | random, numeric | 3.846 | 2.775 | 1.382 [1.332, 1.641] |
| sort | 1,000,000 | 4 | random, numeric | 21.670 | 20.194 | 1.080 [1.045, 1.096] |
| gather | 100,000 | 4 | nulls, mixed | 1.445 | 0.730 | 1.804 [1.438, 2.008] |
| sort | 100,000 | 4 | nulls, mixed | 2.909 | 2.431 | 1.195 [1.125, 1.751] |

The 100,000-row four-column numeric gather favors specialized serial copying. Larger copies and the tested mixed case favor row parallelism. This is evidence for a crossover, not a validated universal threshold.

## Whole-process memory

Median peak RSS for representative complete-sort cases is shown in MiB. It includes the harness and validation, so these values do not establish an operation-only memory improvement.

| Rows | Columns | Input | Original MiB | Candidate MiB |
| ---: | ---: | --- | ---: | ---: |
| 1,000,000 | 1 | numeric | 94.39 | 94.70 |
| 1,000,000 | 4 | numeric | 186.36 | 186.75 |
| 1,000,000 | 16 | numeric | 553.45 | 553.41 |
| 100,000 | 4 | mixed | 37.64 | 38.50 |

The largest observed process peak in this screen was 553.47 MiB. The planned source-plus-destination payload budget was below 1 GiB. RSS is a different measurement from that logical payload bound.

## Correctness, memory and measurement limits

- The final implementation passed 333 dataframe tests in Debug, Release and Address Sanitizer runs, plus four targeted Thread Sanitizer tests. All final test source maps match the committed files.
- Tests cover all supported column types, duplicate indices, partial tasks, null counts, non-null/all-null inputs, source snapshots, NaN payloads, signed zeros, infinities, exact large integers and custom-column fallback.
- Fifteen additional retained scientific, persisted-model, streaming CSV and wine controls passed complete-output conformance. These are integration checks, not additional performance rankings.
- The paired artifact audit verifies all 640 processes and 3,200 samples, frozen harness identity, binary checksums, matching reference permutations and unchanged AC settings. The executables contain their library code and link only system libraries, so rebuilding the checkout does not replace their implementation.
- Source storage and the logical size of final payloads are unchanged. Added algorithm-visible storage is pointer metadata and one Int counter per row task. This excludes GCD internals. Generic numeric output initialization can add a zero-fill pass relative to the earlier mapped gather, so equal allocation size does not mean equal memory traffic.
- Whole-process peak RSS includes source creation, reference sorting, output validation and allocator retention. It does not isolate gather scratch. No allocation trace, DRAM traffic, cache hit rate, active-core placement, CPU work or energy measurement was collected.
- The local coverage export contains test-source coverage but no qualified library-source line map. It is not evidence of production patch coverage. Resolve this collection gap before a production PR.
- Conservative timing qualification suppresses ratios when any sample is below one microsecond. Raw summaries retain their arithmetic ratios, but those sub-microsecond gather ratios are not performance conclusions.
- These are screening cases. Held-out confirmation, application-scale CSV-to-matrix/model timing, concurrent interference and a validated dispatcher remain open. Small and wide paths also need regression protection.

## Decision and next step

Keep the evidence and the specialized candidate on the trial branch. Reject the first protocol-witness implementation. Do not promote the current row-parallel dispatcher.

First isolate specialization in the existing serial gather path, without partition metadata or changing small/wide dataframe dispatch. Then test a separate row-parallel route only where measured complete-operation gains pay for scheduling. Use held-out row counts, widths, selection densities and mixed layouts for confirmation. Define useful absolute gains, protected-case bounds and memory limits before collecting that confirmation. Parallel radix and stable merge remain separate competing experiments from the unchanged parent baseline.

## Full screen

The table retains every registered screening case. Sub-microsecond cases are marked unresolved.

| Operation | Rows | Columns | Input | Original ms | Candidate ms | Paired ratio [range] |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| gather | 129 | 1 | random, numeric | 0.000791 | 0.000625 | unresolved |
| sort | 129 | 1 | random, numeric | 0.006 | 0.005 | 1.120 [0.937, 1.165] |
| gather | 129 | 2 | random, numeric | 0.001 | 0.002 | 0.774 [0.534, 0.875] |
| sort | 129 | 2 | random, numeric | 0.006 | 0.007 | 0.867 [0.801, 0.993] |
| gather | 129 | 4 | random, numeric | 0.002 | 0.003 | 0.772 [0.747, 0.863] |
| sort | 129 | 4 | random, numeric | 0.008 | 0.008 | 0.973 [0.865, 0.980] |
| gather | 129 | 16 | random, numeric | 0.010 | 0.011 | 0.980 [0.972, 1.061] |
| sort | 129 | 16 | random, numeric | 0.015 | 0.015 | 0.983 [0.958, 1.087] |
| gather | 4,096 | 1 | random, numeric | 0.004 | 0.004 | 1.083 [1.039, 1.356] |
| sort | 4,096 | 1 | random, numeric | 0.051 | 0.051 | 0.994 [0.931, 1.022] |
| gather | 4,096 | 2 | random, numeric | 0.012 | 0.013 | 0.907 [0.900, 0.993] |
| sort | 4,096 | 2 | random, numeric | 0.059 | 0.060 | 0.974 [0.959, 1.008] |
| gather | 4,096 | 4 | random, numeric | 0.028 | 0.029 | 0.979 [0.959, 1.000] |
| sort | 4,096 | 4 | random, numeric | 0.075 | 0.075 | 0.983 [0.955, 1.010] |
| gather | 4,096 | 16 | random, numeric | 0.105 | 0.107 | 1.072 [0.858, 1.085] |
| sort | 4,096 | 16 | random, numeric | 0.161 | 0.177 | 0.941 [0.708, 1.064] |
| gather | 32,768 | 1 | random, numeric | 0.037 | 0.035 | 1.029 [0.997, 1.072] |
| sort | 32,768 | 1 | random, numeric | 0.488 | 0.474 | 1.020 [0.816, 1.135] |
| gather | 32,768 | 2 | random, numeric | 0.080 | 0.083 | 0.967 [0.921, 1.174] |
| sort | 32,768 | 2 | random, numeric | 0.550 | 0.551 | 0.998 [0.955, 1.063] |
| gather | 32,768 | 4 | random, numeric | 0.085 | 0.090 | 0.978 [0.924, 1.161] |
| sort | 32,768 | 4 | random, numeric | 0.580 | 0.604 | 0.927 [0.841, 0.989] |
| gather | 32,768 | 16 | random, numeric | 0.273 | 0.275 | 0.954 [0.567, 1.200] |
| sort | 32,768 | 16 | random, numeric | 0.755 | 0.757 | 1.006 [0.969, 1.047] |
| gather | 100,000 | 1 | random, numeric | 0.114 | 0.080 | 1.393 [0.995, 1.483] |
| sort | 100,000 | 1 | random, numeric | 1.633 | 1.629 | 0.993 [0.983, 1.012] |
| gather | 100,000 | 2 | random, numeric | 0.218 | 0.121 | 1.804 [1.431, 1.926] |
| sort | 100,000 | 2 | random, numeric | 1.725 | 1.675 | 1.047 [1.003, 1.154] |
| gather | 100,000 | 4 | random, numeric | 0.232 | 0.199 | 1.182 [0.950, 1.840] |
| sort | 100,000 | 4 | random, numeric | 1.775 | 1.753 | 1.022 [0.972, 1.065] |
| gather | 100,000 | 16 | random, numeric | 0.863 | 0.862 | 0.961 [0.691, 1.456] |
| sort | 100,000 | 16 | random, numeric | 2.291 | 2.406 | 0.955 [0.881, 1.117] |
| gather | 1,000,000 | 1 | random, numeric | 1.557 | 0.720 | 2.164 [1.861, 2.502] |
| sort | 1,000,000 | 1 | random, numeric | 20.764 | 19.105 | 1.076 [1.049, 1.214] |
| gather | 1,000,000 | 2 | random, numeric | 2.830 | 1.264 | 2.226 [2.198, 2.307] |
| sort | 1,000,000 | 2 | random, numeric | 20.434 | 19.073 | 1.095 [1.042, 1.149] |
| gather | 1,000,000 | 4 | random, numeric | 4.659 | 2.657 | 1.754 [1.616, 1.883] |
| sort | 1,000,000 | 4 | random, numeric | 22.512 | 22.219 | 1.055 [1.006, 1.150] |
| gather | 1,000,000 | 16 | random, numeric | 15.206 | 14.673 | 0.952 [0.881, 1.132] |
| sort | 1,000,000 | 16 | random, numeric | 35.446 | 37.036 | 0.977 [0.951, 1.073] |
| gather | 100,000 | 4 | ties, numeric | 0.317 | 0.286 | 1.076 [0.748, 1.939] |
| sort | 100,000 | 4 | ties, numeric | 1.171 | 1.078 | 1.122 [0.891, 1.299] |
| gather | 100,000 | 4 | identity, numeric | 0.280 | 0.184 | 1.566 [1.222, 1.994] |
| sort | 100,000 | 4 | identity, numeric | 0.726 | 0.594 | 1.223 [1.167, 1.273] |
| gather | 100,000 | 4 | reverse, numeric | 0.270 | 0.225 | 1.270 [1.190, 1.348] |
| sort | 100,000 | 4 | reverse, numeric | 0.691 | 0.610 | 1.151 [1.000, 1.623] |
| gather | 100,000 | 4 | nulls, numeric | 0.413 | 0.288 | 1.433 [0.979, 2.330] |
| sort | 100,000 | 4 | nulls, numeric | 2.006 | 1.970 | 1.046 [0.923, 1.134] |
| gather | 100,000 | 4 | sparse, numeric | 0.280 | 0.178 | 1.491 [1.342, 1.950] |
| sort | 100,000 | 4 | sparse, numeric | 0.591 | 0.531 | 1.087 [0.958, 1.258] |
| gather | 100,000 | 2 | nulls, mixed | 4.888 | 1.460 | 2.869 [2.551, 3.966] |
| sort | 100,000 | 2 | nulls, mixed | 7.033 | 3.395 | 2.071 [1.688, 2.180] |
| gather | 100,000 | 4 | nulls, mixed | 5.756 | 1.724 | 3.108 [2.657, 3.951] |
| sort | 100,000 | 4 | nulls, mixed | 7.314 | 3.496 | 2.092 [2.028, 2.793] |

## Evidence

- [Preregistered screening plan and specialization control](row-gather-screening.md)
- [Machine-readable qualification and limits](row-gather-verification.json)
- [Experiment register](experiments.tsv)
- Evidence directory: `/Users/crabel/local-ai/spl/swiftsci/csv-sort-throughput-20261017/row-gather-trial-20261018`.
- `build.py`, `build-serial-control.py`, `compare.py`, `compare-typed.py`, `compare-serial.py`, `check-integration.py` and `audit.py` retain the build and measurement procedure. Use new destinations when repeating a run.
- Original/candidate pairs and serial/parallel pairs are separate raw JSONL files. Original build receipts and fingerprints remain unchanged; `committed-source.json` maps the exact final candidate source to its commit.
- `v1-gather-assembly.txt` and `v2-gather-symbols.txt` record the compiler evidence for the specialization decision.
- Source fingerprint: `562a2adf67260db849a9f1a45e5d1f93b34f7400f6923cbc1a900c6ca45f2b06`.
