## Purpose

Track the remaining Apple silicon memory integration work in one place, including follow-ups raised during research and performance investigations. Finish the current CPU/GPU contribution without losing the longer-term Core ML and working-set work.

The objective is to carry scientific and model data through ingestion, selection, preprocessing, computation, and result access with correct numerical behavior, explicit ownership, and measured memory and execution costs. A faster isolated kernel is insufficient if conversion, synchronization, or retained intermediates make the complete workflow worse.

This is a development tracker on our fork. It does not establish upstream commitments or maintainer approval. Keep it open across individual implementation PRs until every milestone is completed or explicitly deferred with a linked reason.

## Current status: focused validation complete

`codex/matrix-preparation-locality` at `017608d454` is local. Wide: 1.26-1.44x; tiny: 1-6% cost. All 1,478 workers preserve results. Debug/Release: 599 each. CPU: 202/202; Python retains four failures. Apple supplement passes 76 cases/176 samples. Draft: `matrix-preparation-locality-20261012`. Refresh after #72 merges.

## Historical status, October 12, 2026: locality-aware matrix extraction qualified

The local extraction branch `codex/matrix-extraction-locality-trial` is at `baaa29d2a5c11e692cc6de8d1a9feed66e27275c`, based on the qualified scaler branch at `5ba792665acfda7f3b22dbbc3d2189bf7f759c45`. The focused extraction patch changes one production file and two test files. It remains local and unpushed.

Three trials are preserved. Borrowing the destination once was effectively tied in its initial large-case smoke test. Unconditional tiling improved sequential selections but made one large irregular workflow about 25% slower, so that policy was rejected. The retained candidate tiles only consecutive ascending row-major selections with `.nan` handling and more than 2,048 output elements. Other selections and `.reject` keep complete column passes. Public behavior, scalar conversion, snapshots, and missing-column error precedence remain intact.

The final 48-case comparison passed 576 timing workers, 96 memory workers, and two qualifiers. An independent 16-round confirmation varies source retention across eight wide cases, with 256 timing workers, 16 memory workers, and two qualifiers. Wide sequential complete workflows improve about 1.05 to 1.11 times, and preparation improves about 1.07 to 1.17 times. Irregular selections remain near baseline. Observed finite input and prediction reference differences are zero, paired checksums match, and checkpoint heap is unchanged. These measurements do not establish exact transient peaks, statistical certainty, a universal speedup, or a particular Apple cache mechanism.

All targets compile in Debug and Release. All 609 selected dataframe, preprocessing, and ML tests pass in each configuration, without failures or skips. The final rebuilt Release artifact repeats that test pass. Full mixed CPU/GPU/Core ML qualification passes 128 normal samples, eight active-cancellation checks, and eight queued-cancellation checks across four configurations. Source preservation, output references, reservation draining, and capacity reacquisition pass. Neural policy permits CPU fallback. This is relevant-suite and integration validation, not a new full-library numerical certification.

Independent standards and spec reviews find no required fixes. The experimental shape validator accepted malformed checkpoint fields and zero total time. A stricter local validator rejects three malformed records, revalidates all 674 earlier records, and validates the final comparisons. Repairing the legacy benchmark validator remains a separate maintenance task.

Decision: retain locality-aware extraction with the previously qualified scaler optimization. Prepare any production contribution from the focused source and test changes on the appropriate upstream base. Exclude profiler parents, comparison overlays, local reports, and engineering notes. Readable results, reviews, raw records, fingerprints, and the focused patch remain local under `matrix-extraction-borrow-20261012`. Final Release worker SHA-256: `d0365fd28708ea7432349616bc1aac83003d28bb56fc4c32d5c4c723ce4e3b6d`. The final rebuild differs from the earlier focused worker in linker stubs; recorded source, main code, and data sections match. Both actual artifact fingerprints remain with their own evidence. No PR was opened or readiness changed.

## Historical status, October 12, 2026: matrix row borrowing qualified

Local trial branch `codex/matrix-scaler-row-borrow-trial` is at `5ba792665acfda7f3b22dbbc3d2189bf7f759c45`, based on the completed integration profiler at `933f9606e00d12af7c2b513223e13d080218d5f2`. Two focused commits add a numerical compatibility test, then borrow row-major inputs directly during scaling. They change only `StandardScaler+Matrix.swift` and `MatrixScalerRowBorrowTests.swift`. The input-row copy is removed and the layout decision moves outside the row loop. Array-backed intermediate outputs, row-width vDSP arithmetic, fitted statistics, public API behavior, snapshot ownership, and the gathered column-major fallback remain intact.

The paired six-size CPU profile passed 432 measured workers and 12 independent qualifiers, covering 13,824 measured calls. Matrix scaling improved about 3× and complete matrix workflows improved 1.23 to 1.39×. At 8,192 rows the complete call fell from 2.7881 ms to 2.0696 ms. The unchanged column control stayed within about 3% of its previous whole-call time. Timing and memory diagnostics ran in separate fresh processes, with build order balanced. All prediction hashes matched. These observations do not prove a hardware or cache mechanism.

The existing broader workload passed 48 cases, 576 timing workers, 96 memory workers, and two qualifiers. Every medium or large row-major case improved. At 16,384 rows and 128 features, complete workflows improved 1.25 to 1.31× for one prediction and 1.09 to 1.11× for eight. All observed matrix and prediction reference differences were zero. Initial tiny-case slowdowns of about 3% did not reproduce in 32 balanced rounds. That confirmation passed 512 timing workers, 16 memory workers, and two qualifiers. Tiny row-major whole calls ranged from 0.999 to 1.070×, with one effective tie. No universal speedup or statistical certainty is claimed.

Observed extra live heap was unchanged in every broader and tiny-case memory diagnostic. The 8,192-row matrix profile remains at about 5.557 MiB. Memory snapshots and owner-release checks do not establish exact transient peaks or general leak freedom.

All 607 dataframe, preprocessing, and ML tests passed in both Debug and Release, without failures or skips. All targets compiled in both configurations. Changed files had no compiler warnings or type-checking time warnings; unchanged tests retain existing warnings in the logs. Final mixed CPU/GPU/Core ML qualification passed 128 normal samples, eight active-cancellation checks, and eight queued-cancellation checks. References, snapshots, provenance, draining, and capacity reacquisition passed. Within that run, direct matrices beat columns by 1.29 to 1.34× for small and 1.15 to 1.22× for large balanced/wide work sets. Neural policy still permits CPU fallback.

Independent standards and spec reviews found no remaining required fixes. The auxiliary local branch `codex/matrix-scaler-shape-validation` preserves the comparison overlay, with baseline `513faa40e28b4088a8a78b4b55c038830d75899d` and candidate `87a6e8958c1cdd52a35cf18692f979e855a4738b`. Its candidate production tree matches the focused trial. Neither branch was pushed. No PR was opened or readiness changed by this task.

Decision: keep the focused scaling change. A future production PR must transplant its two commits onto the appropriate production base, excluding profiler and auxiliary overlay commits. Direct extraction is the next larger preparation cost to investigate separately. Keep caller layout choice explicit. Reports, reviews, raw results, controllers, logs, and the focused patch are saved locally under `matrix-scaler-row-borrow-20261012`. Final uninstrumented Release worker SHA-256: `34263d0965821a05c5147f6adfe1f659bef9dd3e05c77eda33e3b1947533575a`.

## Historical status, October 12, 2026: CPU stage and fresh-process memory profile

Local branch `codex/integrated-matrix-workload-validation` is now at `933f9606e00d12af7c2b513223e13d080218d5f2`. Two benchmark-only commits add CPU stage timing and separate memory diagnostics. Production sources, unit tests, and dependencies remain unchanged from the preceding integration qualification. The branch remains local and unpushed. This task does not change PR readiness or merge anything.

The six-size sweep completed 216 measured workers and six independent qualifiers. It checked 6,912 measured operations and 864 warmups. Every worker passed output hashes, row provenance, source preservation, and record validation. The 1,024-row and 8,192-row hashes match the earlier integration experiment. Each path and mode runs in a fresh process; qualification is separate from measurement. GPU and Core ML initialization are excluded from this CPU profile.

Direct matrices are faster through 2,048 selected rows, nearly tied at 4,096, and about 4.2% slower at 8,192 for this 54-feature fixture. At 8,192 rows, scaling takes 1.0695 ms versus 0.6724 ms for columns. Extraction costs 0.1076 ms more, while avoiding packing saves 0.3684 ms. Prediction and imputation are close. Stage medians do not add up to the median complete call. Staged totals differ from complete-call controls by at most 3.32%.

The separate memory diagnostic observes 5.557 MiB of extra live heap at preparation boundaries for matrices and 11.918 MiB for columns at 8,192 rows. The column probe explicitly retains the gathered dataframe through compact-buffer construction to observe their overlap. Timing runs do not use that probe. These are live-byte snapshots, not exact transient peaks or cumulative allocations. RSS includes allocator and runtime state and is not lower for matrices at every size. Post-operation heap change does not establish a leak.

Final all-target Release compilation passed without compiler warnings or errors. The controller suite ran 227 tests, with 15 optional skips and no failures. All four focused profiler tests passed. An integrated CPU/GPU/Core ML smoke run passed 32 normal samples, two active-cancellation checks, and two queued-cancellation checks. The earlier identical production and unit-test tree passed 606 Release tests; this update does not claim a new full Debug or numerical-conformance run. Independent standards and spec reviews found no required fixes. Shared controller verification and fingerprint helpers remain an optional maintenance follow-up.

Decision: keep explicit caller choice. The next focused experiment is to remove row copying from row-major matrix scaling while retaining the existing `standardizeRow` arithmetic, array-backed intermediate outputs, and column-major fallback. Both current scaling paths make the same row-width vDSP calls. Buffer traversal and copying are candidates for the measured gap; cache, alignment, compiler, and hardware causes remain unproven. Require unchanged numerical results and a complete-workflow improvement across shapes and sizes before promotion. Extraction is a secondary follow-up. No automatic routing threshold or storage redesign follows from this profile.

Readable report, review, logs, and fingerprints are saved locally under `integrated-matrix-profile-20261012`. Final worker SHA-256: `a79753dc2803729c9f225d3fa1e7f29030289eeb1cd598644949abcea54d6cca`. Earlier benchmark reports retain their own fingerprints and limitations.

## Historical status, October 12, 2026: integrated matrix workload qualification

PRs [#68](https://github.com/Nodibell/SwiftSci/pull/68), [#69](https://github.com/Nodibell/SwiftSci/pull/69), [#71](https://github.com/Nodibell/SwiftSci/pull/71) and [#72](https://github.com/Nodibell/SwiftSci/pull/72) are ready for review at their previously recorded heads. They remain open. Merge #71 before refreshing #72. This update does not change PR readiness or merge anything.

Local branch `codex/integrated-matrix-workload-validation` combines all four heads cleanly. Its final head is `c28c19fe6486b40fbc21800a002a77e67a2f952a`. The branch adds benchmark code and controller checks, with no further production changes, and has not been pushed.

The complete CPU workflow selects dataframe rows, applies training-fitted imputation and scaling, then predicts with the same CPU MLP. It compares column-first preparation with direct row-major matrices alongside GPU regression and retained Core ML inference. The 54-feature held-out Covertype fixture includes reordered storage, irregular selections, repeated rows, nils and numeric NaNs. Four rotated rounds balance path and admission-mode order across small/large and CPU/neural-policy configurations.

Final qualification passed 128 measured samples, eight active-cancellation checks and eight queued-cancellation checks. Every Core ML output and completed cancellation chunk matched synchronous direct prediction after row-array preprocessing, outside timing. This bypasses retained sessions and fused packing but shares the model and framework; it validates integration rather than independently certifying model accuracy. CPU and GPU numerical references, row provenance, source snapshots, reservation draining and full-capacity reacquisition also passed. The controller enforces exact per-mode budgets and complete batch timing records.

The existing 606 Release dataframe/preprocessing/ML tests passed on an identical production and unit-test tree. Final all-target Release compilation passed without warnings. The final controller suite ran 223 tests, with 15 optional skips and no failures. This work does not claim new full Debug or full numerical-conformance validation.

Direct matrices improved small balanced/wide work sets by 1.14 to 1.30×, but large balanced/wide work sets took about 6 to 11% longer than column preparation. Large CPU service took about 9 to 12% longer. Overlap improved the matrix workflow by 1.53 to 2.46× versus its own sequential execution. Maximum sampled RSS was about 197.84 MiB. Shared-process RSS does not isolate path allocations, and drained logical reservations do not prove general leak freedom. Neural policy permits CPU fallback.

Decision: retain explicit caller choice. Do not infer a universal routing threshold or redesign storage from these measurements. Next, profile extraction, imputation, scaling and prediction separately in the large case, then measure allocations with each CPU path in its own process. Promote only a demonstrated complete-workflow improvement into a focused production change. Earlier benchmark fingerprints remain historical evidence for their own workloads; final review corrections and the complete rerun are preserved separately.

## Historical status, October 12, 2026: direct extraction PR and matrix preprocessing

PR #70 has merged. The prepared-matrix MLP and direct-dataframe extraction follow-ups were refreshed onto main `309b7f09cc` and published together as draft [PR #71](https://github.com/Nodibell/SwiftSci/pull/71), head `c48789f705420e572f919a4164c7619980171494`. The refresh preserves the benchmarked production tree. Its 586 Release tests passed again; the prior identical tree passed 586 Debug tests. Hosted benchmark policy, builds, safe-mode tests, documentation, both CodeQL analyses and patch coverage passed. Pages is intentionally skipped; the disabled performance job provides no timing evidence.

The follow-up is published as draft [PR #72](https://github.com/Nodibell/SwiftSci/pull/72), branch `codex/prepared-matrix-preprocessing`, head `b6174bc05f70253559bf5968b81c359c89873817`. Its benchmark production fingerprint remains `ea508611d7ddf0238bd7ecbbf60dcd3e7679ccc7`; the publication head adds only a nonfinite fitted-statistics regression test. Two commits add fitted Imputer/StandardScaler matrix transforms, then change imputation to contiguous traversal in the chosen storage order. Public values remain read-only; a package-only fixed-size buffer borrow supports copy-on-write mutation. Fitting and the generic Pipeline interface are unchanged. The implementation shares the existing numerical operations and uses row-sized scaling scratch. The branch is pushed. Merge #71 first, then refresh #72 onto main before final approval.

Final validation passed 596 tests in each of Debug and Release, with no failures or skips. All test targets compiled without warnings in changed files. Nine controller tests and 1,092 final comparison workers passed; measured matrix and prediction differences were zero. The initial 1,092-worker comparison is preserved separately. Memory samples, owner-release checks, and source snapshots passed; these do not establish general leak freedom or exact transient allocation peaks.

At 16,384 rows × 128 features, with fitted imputation and scaling included, row-major complete workflows improved 1.16–1.22× for one prediction and 1.05–1.06× for eight against public gather/column preparation. Observed extra heap fell from about 42 MiB to 16 MiB. Against the leaner experimental selected-column control, speedups were about 1.04× for one prediction and 1.01–1.03× for eight. Sparse irregular row-major cases were near ties. Matched column-major scaled cases took about 9–16% longer in the extended sweep.

Decision: the row-major path offers a demonstrated memory and time improvement while preserving the existing arithmetic. Keep this an explicit caller choice and retain the column path. No automatic migration, extraction-loop fusion, new pipeline framework, GPU/Neural Engine speedup, or cache-mechanism claim is included. The bounded CPU matrix workflow development and local qualification are complete. Hosted checks and review for #72 remain pending. Further cache attribution, automatic layout selection and additional memory redesign are separate experiments, not prerequisites for this contribution.

## Historical status, October 12, 2026: direct matrix extraction

The focused local branch `codex/direct-matrix-preparation` adds one commit, `a87a19ab46b25f126c32d55c99a72f1dee321e87`, above the prepared-matrix MLP branch at `afbcf6ab699f166c9354c53ca0e85ccfce8db2c7`. It preserves the completed experiment and pending PR branches. It has not been pushed.

`DataFrame.prepareNumericMatrix` directly converts selected rows into an owned matrix. Callers choose the layout and missing-value policy. Row order, duplicate selections, schema, provenance, and snapshot behavior are preserved. Raw construction stays internal to SwiftDataFrame. Existing column preprocessing remains unchanged; the experimental fused imputer/scaler code is excluded.

The clean production commit passed 586 tests in each of Debug and Release, with zero failures or skips. All test targets compiled, and changed files had no compiler warnings. Nine controller tests and 672 comparison workers passed. Maximum measured matrix and prediction differences were zero. A temporary comparison overlay invoked the public method and was removed afterward.

Extraction-only comparisons at 16,384 rows and 128 features found 1.43–1.47× complete-workflow speedups for one prediction and 1.09–1.15× for eight, against public dataframe gather/column preparation. Observed extra heap fell from about 41.7 MiB to 16.0–16.2 MiB. Against the leaner experimental selected-column control, the gains were 1.27× and 1.04–1.07× respectively. Sparse irregular column-major cases were essentially tied. These are local measurements with separate timing and memory runs, not universal routing thresholds or exact transient allocation peaks.

Decision: direct extraction is implemented and validated as an explicit caller option. Its local commit can follow the prepared-matrix prediction contribution. Fused preprocessing remains a separate integration decision because it must share the existing preprocessing implementation and arithmetic contract. No automatic migration of callers or production claim for that fusion is included.

## Historical status, October 12, 2026: matrix preparation experiment

The local experimental branch `codex/matrix-preparation-memory-trial` is at `5cf1c517e6715d27284b4a18d5801fe9aaded1c3`, based on the completed prepared-matrix branch at `afbcf6ab699f166c9354c53ca0e85ccfce8db2c7`. It is independent of pending PR acceptance. Neither the trial nor the prepared-matrix follow-up has been pushed. The existing production branches remain separate.

The trial compares public gather/column preparation, direct selected-column preparation, and direct final-matrix construction through the same public MLP predictor. Its only production-file change widens the matrix initializer to package access for the experiment. It is not a proposed public API or an automatic routing change.

After correcting repeated row-bound validation and dataframe metadata queries in the experimental traversal, 1,524 accepted worker processes passed matrix, prediction, provenance, and applicable snapshot/lifetime checks. Measured matrix and prediction differences were zero. All 580 Release dataframe, ML, and preprocessing tests and nine controller tests passed. All test targets compiled; other suites were not executed. Maximum recorded process peak RSS before reference validation was 117.77 MiB. Thermal state was recorded without a cooldown gate.

Six-round confirmation found 1.11–1.74× complete-workflow speedups in the main 4,096-row row-major cases, with 68–69% less observed extra heap at checkpoints. At 16,384 rows and 128 features, one-prediction workflows improved 1.36–1.42× and eight-prediction workflows improved 1.10–1.12×. Extra heap fell from about 42 MiB for public column-first preparation, or 34 MiB for selected-column preparation, to about 16 MiB for direct matrix construction.

Matched column-major controls took about 3–13% longer. Sparse irregular row-major controls were near ties to modest improvements. These results support a focused row-major candidate, not replacement of every preparation path. Checkpoint maxima are not exact allocation peaks, and weak-owner checks do not establish general leak freedom. No GPU, Neural Engine, cache-counter, or zero-copy benefit is claimed.

Decision: this experiment has answered its initial question. Preserve the code and negative controls. A later production proposal needs a reviewed matrix-construction contract and an explicit layout choice. Keep the completed PRs separate and retain their original benchmark fingerprints. The readable report and raw evidence are local in `matrix-preparation-20261012/REPORT.md` and its adjacent run folders. No new production PR was opened for this trial.

## Historical status, October 11, 2026

The paired working-set experiment is complete locally. The selected production change is bounded CPU MLP batching on `codex/batched-mlp-prediction` at `a4c7eba5e8629884f245a21812dba330d3fe1987`, directly above upstream main `e9deb310c51dd5f440e4e7047f70a8fdb3858a57`. Its three-file diff contains only prediction integration, the internal batching helper, and regression tests. The complete experiment is preserved locally on `codex/mlp-prediction-validation` at `7e7645cbcf`. The production branch is published as ready for review [PR #70](https://github.com/Nodibell/SwiftSci/pull/70) at the recorded head. The validation branch remains local.

On the Apple M4 Max, 92 configurations produced 368 paired before/after comparisons using the actual public predictors. Inputs included row arrays and dataframe conversion, small and large batches, different network widths, and a separate one-thread BLAS request. All measured cases at or above 32 rows improved, with median speedups of 1.62–8.46× including applicable preparation, copies, computation, and output allocation. At 4,096 rows, the main row-input cases improved 2.98–8.46×; dataframe cases improved about 2–3×. Below 32 rows the existing path remains, with measured medians ranging from 0.95× to 1.06×. These are local measurements, not portable guarantees.

Two scratch buffers are reused within each call and released afterward, capped at 256 KiB. No permanent model workspace or new public API was added. Peak process memory stayed close to the original path, with a maximum observed worker peak of 53.4 MiB. Live allocator snapshots and complete-call timings were recorded; cumulative allocation counts and isolated transient prediction peaks were not measured.

Validation passed 288 Release ML/preprocessing tests, 2,592 qualification comparisons with matching class labels and maximum absolute difference of 1.78e-15, and 19 controller tests. All test targets compiled; the new files produced no compiler-complexity warnings at 100 ms expression / 200 ms function thresholds. The isolated production branch has the same Sources, Tests, manifest, and dependency lockfile as the tested validation head. PR #70 is ready for review at the same head. Hosted benchmark policy, Debug and Release builds, safe-mode unit tests, documentation, both real CodeQL analyses, MLX conformance checks, and patch coverage pass. The Pages deployment is intentionally skipped; the disabled performance job is not timing evidence.

The matrix-layout comparison passed 1,536 numerical checks across 48 configurations. Manual weight packing and additional row tiling did not show a consistent total-cost advantage; direct BLAS remains. Direct prepared-column MLP prediction remains experimental.

Comparisons alternated process order and inputs, and balanced matrix variant positions. Thermal state was recorded, not used as a cooldown gate; final workers reported state 1. Earlier pilot runs with incomplete alternation or ordering remain historical evidence and are not used for these claims. No hardware-counter evidence establishes a specific cache mechanism.

PR [#68](https://github.com/Nodibell/SwiftSci/pull/68) and [#69](https://github.com/Nodibell/SwiftSci/pull/69) remain drafts with their current checks passing, including both real CodeQL analyses. The expected Pages skip and disabled performance check are not performance evidence.

Next action: review PR #70 and continue the separate prepared-column experiment below. Detailed raw records, build commands, fingerprints, and readable reports remain local; engineering notes are not included in the production diff.

### Prepared-column workflow experiment, October 11

Local branch `codex/prepared-mlp-workflow-trial` at `688e310672` adds benchmark-only complete workflows above the preserved validation branch. Production sources, tests, manifest, and lockfile match PR #70. Separate commits preserve the initial workflow comparison, scoped column-buffer borrowing, and selection-before-conversion alternative. The branch has not been pushed.

Across seven sweeps, 196 configurations produced 784 paired comparisons in 1,568 worker processes. Numerical and class-label checks passed, with maximum prediction difference 1.85e-15. Qualification passed 2,592 comparisons; all 19 controller tests passed. Controls cover repeated/reordered selection, nil and valid NaN values, unchanged sources, row provenance, and train-only preprocessing. The final Release build compiled all test targets. This experiment did not rerun the full repository test suite.

Direct column borrowing helped the small network at 4,096 rows reach 2.61–2.79× public speed across mixed conversion, selection, and preprocessing. Large selection remained a problem: preparing all source rows before selection could use more memory and run slower than the public path.

Selecting the dataframe before compact conversion improved the 8,192-row large model to 1.11× public speed, or 1.28× with imputation and scaling. At 32 rows, the same order regressed wide/large workflows to 0.87–0.96×. Memory savings were inconsistent. The largest measured worker peak across all experiments was 124.27 MiB. Peak RSS includes model fitting, fixtures, and runtime initialization; live snapshots are not cumulative allocation counts. Thermal states 0 and 1 were recorded without a cooldown gate.

Decision: preserve the column-borrow experiment, but do not promote a universal preparation order or a new public prediction API. Next, test direct conversion of selected source rows into compact columns. This would avoid both full-source compact conversion and the intermediate gathered dataframe. Include caller-retained prepared-batch reuse as a separate measured workload before selecting an API contract. Neither cache behavior nor a portable crossover is established by these runs.

The readable report is retained locally as `prepared-mlp-workflow-20261011/PREPARED-WORKFLOW-REPORT.md`, alongside raw records and source/executable fingerprints. It is not a published repository artifact.

### Direct selected-row conversion follow-up, October 11

The trial now includes direct conversion at local commit `b2d9ae4598` on `codex/prepared-mlp-workflow-trial`. It writes only selected source values into final compact columns, avoiding both a gathered dataframe and conversion of discarded rows. Validity, repeated selections, parent-row provenance, and source snapshots are preserved. Production code remains identical to PR #70, which is ready for review. The trial remains local.

The new comparison covered 100 configurations and 400 paired comparisons in 800 fresh worker processes. All output and class-label checks passed, with maximum difference 1.85e-15. Qualification passed 2,592 comparisons and all 19 controller tests passed. The Release build compiled all test targets. The full repository suite was not rerun for this benchmark-only change.

Direct conversion achieved 1.18–1.41× public speed on wide/large workloads at 4,096–8,192 rows and 1.55–2.06× across the main 32-row workflows. The public reference already includes PR #70 batching. Peak memory usually fell, but not uniformly. At 8,192 rows the large selected workflow used 82.3 MiB versus 88.3 MiB; with preprocessing it used 104.3 MiB versus 110.8 MiB. The small network sometimes remained faster with full compact conversion followed by selection.

Decision: keep direct conversion as an integration candidate, without choosing a universal preparation order yet. Next, measure caller-retained prepared batches, including one-time preparation, repeated prediction, source mutation/snapshot costs, and release. Broaden selection density and irregular row access before choosing the public contract. The current timing fixtures select half the source rows in reverse order. No cache mechanism or portable crossover has been established.

The readable local report is `prepared-mlp-workflow-20261011/DIRECT-SELECTION-REPORT.md`, with raw results and fingerprints alongside it. This follow-up supersedes the earlier next action to prototype direct conversion.

### Retained-input lifecycle follow-up, October 11

The local trial is now at `32142585bf` on `codex/prepared-mlp-workflow-trial`. A four-way comparison gives both the public row-array predictor and the compact-column candidate the option to rebuild or retain prepared inputs. It includes preparation, prediction, and input-release intervals, with separate snapshot-edit and memory diagnostics. Prediction scratch stays fresh in both paths. Production code remains identical to PR #70, and the trial is unpushed.

The accepted final sweeps covered 76 configurations, 304 four-way groups, and 1,216 fresh worker processes. All prediction checksums, final full outputs, labels, and input-owner release checks passed. Maximum recorded output difference was zero. The final Release build compiled all test targets, 24 controller tests passed, and the existing 2,592-case numerical qualification passed. No full-repository test rerun is claimed. Earlier exploratory runs precede the explicit snapshot-lifetime fix and capacity instrumentation; accepted evidence is in `reuse-final-*`.

Reuse helps both representations. At eight reuses per input and 4,096 rows, compact reuse reached 1.23–1.47× row-reuse speed on the small network but only 0.99–1.02× on wide/large networks. At 32 reuses it was 0.95–0.96× on those wider models. Do not infer a general retained-column prediction advantage from comparison against a row path that rebuilds every call.

Capacity measurements explain much of the memory tradeoff. Two 4,096×64 inputs contain 4 MiB of numeric values, but the row arrays reserve 4.75 MiB of numeric capacity and compact columns about 6.00 MiB. Their live retained heap increases were about 5.09 and 6.10 MiB respectively. Compact column buffers reported 6,140 Double slots for 4,096 values. This is measured storage slack, not evidence of a particular cache mechanism. The largest accepted worker peak was 71.73 MiB. All final workers recorded thermal state 0 without a cooldown gate.

Snapshot mutation preserved originals and required roughly 48–52 KiB of additional live heap in the sampled 4,096-row cases. Weak references verified input-owner destruction; that does not prove global leak freedom or require allocator pages to return to the OS.

Decision: do not promote retained compact columns as the default prediction representation. Next, benchmark the existing row-major `PreparedNumericMatrix`, including one-time packing, repeated prediction, and dropping the source columns. Broaden selection density and irregular access before settling the public contract. The readable local report is `prepared-mlp-workflow-20261011/REUSE-REPORT.md`. This supersedes the earlier next action to measure prepare-once reuse.

### Retained matrix follow-up, October 11

Completed locally on `codex/prepared-mlp-workflow-trial` at `f636dd28e9b3391c3108e200974215538a05bbfc`. This benchmark-only commit compares retained rows, retained columns, and the existing row-major `PreparedNumericMatrix`. Production Sources, Tests, and package files remain identical to PR #70.

Across 80 configurations, 320 balanced groups and 1,280 isolated workers, all checks passed with zero measured output difference. The 2,592-case qualification passed with maximum error 1.78e-15, and all 26 controller tests passed. Release build-for-testing compiled all test targets; the full repository suite was not rerun for this experiment.

At 4,096 rows, retained matrices used about 19% less heap than rows and 32–33% less than columns for the wider models. At eight predictions per input, main wide/large speedups were 1.015–1.059× versus rows and 1.022–1.089× versus columns. One-thread and shuffled-selection controls included near-ties and small regressions against rows. Packing did not beat columns on single-use large batches. The evidence supports a workload-dependent choice, not an automatic threshold.

The tradeoff is mutation and preparation peak. Editing copied matrix values allocated about 2–4 MiB versus roughly 50 KiB for rows/columns. Packing can temporarily retain both columns and the matrix. Weak-owner checks passed; they do not prove general leak freedom. No GPU, Neural Engine, or hardware-cache benefit is claimed.

Next: evaluate a focused predictor accepting the existing prepared matrix, preserving current precision, backend, validation, and output contracts. Keep columns for preprocessing and edits, then pack for repeated prediction when appropriate. No public API or production change has been made by this trial. The readable report and raw fingerprints remain in the local engineering evidence directory as `MATRIX-REUSE-REPORT.md` and `matrix-validated-head.json`.

### Prepared matrix prediction integration, October 11

Implemented locally on `codex/prepared-matrix-mlp-integration`. Production commit `3420a0786dc38658c68ae9adca79b4af1318d09c` adds prepared-matrix overloads for MLP regression, classification, and class probabilities. Benchmark commit `607543b5cb2ed3661f808314b3bcec8c3cea0155` routes the matrix measurements through those public methods. Both matrix layouts are supported. Existing CPU Double-precision arithmetic, bounded scratch, and small/wide fallback behavior are preserved. Columns remain positional. No automatic conversion policy was added.

Validation passed 294 Release ML/preprocessing tests, 2,592 qualification cases, 26 controller tests, and 1,280 integrated benchmark workers across 80 configurations. Measured benchmark output difference was zero; qualification maximum error was 1.78e-15. All test targets compiled, with no warnings in changed files. Other test suites, Debug, and hosted CI were not run for this integration.

At 4,096 rows and eight predictions per input, wide/large matrix speedups were 1.007–1.058× versus retained rows and 1.046–1.076× versus retained columns. Retained heap fell about 19% versus rows and 32–33% versus columns. Small models can still favor columns. Copy-on-write matrix editing and transient packing peak remain tradeoffs. Maximum observed whole-process RSS was 74.64 MiB; thermal states were nominal/fair without cooldown gates.

Next: review and extract the focused production commit onto the appropriate upstream base, check the existing row API with a paired before/after run, and run Debug and required CI before publication. No push or PR has been made for this integration. The readable local evidence is `MATRIX-INTEGRATION-REPORT.md`, with source/worker mapping in `matrix-integration-validated-head.json`.

### Prepared matrix review readiness, October 11

The clean local branch is `codex/prepared-matrix-mlp` at `ebe51e71a4878fe757ecae30899cd2c28573e65f`, stacked on PR #70 at `a4c7eba5e8629884f245a21812dba330d3fe1987`. Its six-file diff contains only production integration and regression tests. The complete experiment remains on `codex/prepared-matrix-mlp-integration` at `6f657cde8493f5686b248cc6896df6a71e5b3ed1`. No push or PR has been made for the matrix change.

The before/after row comparison caught a roughly 10–14% scalar regression from value iteration in the extracted helper. A concrete-activation trial did not resolve it; restoring indexed layer access did. The full final comparison measured 0.966–1.032× baseline across 36 configurations and 0.980–0.998× in four one-thread controls. The exact compiler/ownership mechanism remains uninstrumented.

Debug and Release ML/preprocessing suites passed all 294 tests each. All test targets compiled; other suites were not executed. Qualification passed 2,592 cases with maximum error 1.78e-15. The final 1,280-worker matrix sweep passed all output and ownership checks with zero measured output difference. The larger repeated workloads retained about 19% less heap than rows and 32–33% less than columns, with 1.021–1.060× speedups against rows in the main 4,096-row/eight-use cases.

The review draft is prepared locally as `review-readiness/PR-DRAFT.md`, with readable evidence in `review-readiness/REVIEW-READINESS.md`. Next: refresh onto main when #70 merges, then publish the focused PR and run hosted CI/coverage. No benchmark experiment or engineering note is included in the clean diff.

### Earlier October 11 records


[#67](https://github.com/Nodibell/SwiftSci/pull/67) is merged at `e9deb310c51dd5f440e4e7047f70a8fdb3858a57`. The retained-session branch was refreshed onto that merge without changing its tested Git tree, pushed at `5e5a35c1595cbed932c1acf28f1f144e0723c7d9`, and published as draft [#68](https://github.com/Nodibell/SwiftSci/pull/68). Hosted checks are underway. Earlier local results below remain tied to their recorded revisions.

The next experiment is `codex/matrix-working-set-trial`, based directly on merged upstream main and independent of #68. Local commit `72e4e463b5a3e9b33904f7c9f4fb458dd6d7cb09` adds a standalone FP64 comparison of direct Accelerate BLAS, explicitly transposed weight storage, and row tiles of 32 or 128. It varies matrix shapes, source strides, operand reuse, and requested threading. Packing and output allocation count toward total time. No production behavior changes.

The committed trial passed all 960 measured numerical comparisons, its oracle rejection controls, and five controller tests. Peak worker RSS was 20.8 MiB; maximum absolute error against compensated FP64 reference sums was `4.62e-14`. The host reported elevated thermal state throughout the sweep. These results qualify correctness for the declared cases only. No performance ranking is accepted from this run.

Next action: run the timing comparison under nominal thermal conditions, repeat any promising alternatives, and assess whether packing or row tiling justifies its total cost. Keep the blocked-matrix roadmap item open until that decision has evidence. The trial branch remains local. Historical sections below describe their original publication states.

### MLP batch integration trial, October 11, 2026

Local commit `52eeae4f6a3ba6c935683269b5da992fb1ddcd64` on `codex/matrix-working-set-trial` adds a benchmark-only predictor with two reusable FP64 scratch buffers. It uses the fitted parameters from actual SwiftSci models and compares against the public regression and classification predictors. Production code is unchanged.

All 864 public-API comparisons passed across model types, activations, layer widths and depths, row counts, and chunk sizes. Maximum absolute difference was `1.33e-15`. Exact class labels matched. The largest tested scratch capacity was 256 KiB, excluding weights, inputs, returned outputs, allocator overhead, and framework workspace. Source arrays and parameters remained unchanged, prior outputs survived later calls, and scratch backing addresses remained stable. Analytic and rejection controls passed. Nine controller tests passed, and the final Release build-for-testing succeeded. This was not a full unit-test execution.

For 257 input rows through three layers, 32-row chunks reduce the modeled BLAS call count from 771 to 27. This is a structural count, not a measured speedup. No performance ranking is accepted while the host remains warm. A useful next correctness task is direct prepared-column input into the scratch buffers, with row ordering and missing-value behavior checked against the existing row-array path. Timing qualification and production adoption remain separate decisions.

### Direct prepared-column MLP input, October 11, 2026

Local commit `f39fc654e26e6ac8f232918b2d55125803bf10fc` on `codex/matrix-working-set-trial` connects prepared numeric columns directly to the bounded predictor's scratch buffers. It avoids the compatibility row-array matrix between prepared input and prediction. Each value is still copied into row-major scratch. Preparation, selection, and caller-owned imputation may allocate separately. Production code is unchanged.

All 2,592 public-API comparisons passed across row arrays, mixed-type prepared columns, and prepared columns with training-only fitted imputation. Maximum absolute difference was `2.22e-15`; class labels matched exactly. Maximum tested scratch capacity remained 256 KiB. Checks covered reversed physical column order, repeated and chained row selections, source provenance, missing entries versus valid NaNs, signed zero, rejected schemas, untouched padding, and retained snapshots. The final Release build-for-testing and ten controller tests passed. No speed or RSS improvement is claimed.

The first run exposed an existing API difference: `DataFrame.gathered(at: [])` removes the schema, but `PreparedNumericBatch.selectingRows([])` preserves it. Empty prediction now uses the original zero-row dataframe with columns as its reference. That qualifies empty prediction, not equivalence of the two empty-selection APIs. Track the schema behavior as a separate compatibility decision and repair candidate; it was not changed in this benchmark branch.

The direct prepared-input correctness task is complete. Remaining work includes timing under suitable conditions and review of the empty-selection contract. Performance evidence is still required before production adoption.

### Empty-selection compatibility PR opened, October 11, 2026

The separate branch `codex/preserve-empty-selection-schema`, based on upstream main, contains commit `0d8b01e155e44cd5dbfc9060eb522e403e591ff1`, now pushed to the fork and submitted as [draft PR #69](https://github.com/Nodibell/SwiftSci/pull/69). Empty gathers, filters, and zero-row slices now preserve typed columns. Column-free frames and explicit removal of all columns remain column-free. The matrix experiment remains preserved at `f39fc654e2` and has not absorbed this change.

This is an intentional behavior change. The earlier gather test explicitly expected column removal, so that assertion now checks schema preservation instead. Public documentation explains that callers should use `rowCount == 0` to detect no matches. The draft PR requests review of this compatibility change. Maintainer approval is pending.

Failing-before evidence showed missing columns and feature-preparation errors. After the change, all 287 dataframe tests passed in each of Debug and Release. All 127 preprocessing Release tests and all 173 preprocessing and agent Debug tests also passed, with no failures or skips. The documentation gate passed. The new regression file is 79 lines. Independent standards and behavior reviews found no actionable issues. The full repository suite remains unverified locally. The first hosted run found two benchmark references that still discarded empty-selection schema. Follow-up commit `1130c218ca580709109761105e89f8d57b947ae7` corrects the scalar reference and pandas adapter, regenerates the two answers, and preserves all tolerances and numerical failure entries. Local CPU validation passed the regression policy across 404 engine cases with four unchanged known comparator failures and zero blocking cases. The controller suite ran 212 tests with four skips and no failures. The correction is pushed to draft PR #69, and hosted CI is running on the new head.

The follow-up is now a concrete compatibility change for review rather than an unexplained benchmark workaround. Benchmark timing and production adoption of the MLP candidate remain separate pending work.

## Status update, October 10, 2026

The CPU/GPU closeout, Core ML interface, and fitted preprocessing are merged upstream:

- [#62](https://github.com/Nodibell/SwiftSci/pull/62): prepared regression and memory admission.
- [#63](https://github.com/Nodibell/SwiftSci/pull/63): prepared-column reuse and reduced GPU prediction setup.
- [#65](https://github.com/Nodibell/SwiftSci/pull/65): scoped Core ML inference and reusable prepared inputs.
- [#66](https://github.com/Nodibell/SwiftSci/pull/66): training-fitted preprocessing directly into owned Core ML inputs.

[#67](https://github.com/Nodibell/SwiftSci/pull/67) is open and ready for review. It bounds loading, preprocessing, inference, and ordered result consumption under one estimated admission quota. Hosted builds, safe-mode tests, benchmark conformance, both CodeQL analyses, documentation, and Codecov passed. The Pages deployment is intentionally skipped. The disabled hosted performance job supplies no performance evidence.

Local #67 validation at `582d062a9bcb12ae5fe90f45a866c18748c51c7c`: 1,276 Release tests passed with two existing fixture skips; 156 Debug ML tests passed with coverage; 206 controller tests passed with four skips. All 32 sustained configurations and 16 shutdown scenarios passed. Additional 4,096-batch runs passed within each compute policy. The PR records the workload, measured gains, memory observations, and historical source fingerprint. These are workload-specific results, not proof of leak freedom, exclusive Neural Engine placement, or full numerical conformance.

Core ML milestone 2 has reached its first complete verified workflow. Milestone 3's fused preprocessing and bounded handoff work have shipped or are in #67. Cache-counter attribution, broader compact-storage consumers, blocked matrix comparisons, false-sharing experiments, and Metal threadgroup staging remain open hypotheses. No cache or physical-memory placement claim follows from the throughput results.

### Mixed-workload qualification completed locally

`codex/mixed-workload-qualification` at `37df791cb1d51069b08c8c050a0194e151cc25f6` is based on #67 and remains local, with no upstream PR yet. It adds benchmark code and documentation only. The full matrix covers CPU preprocessing, MLX GPU regression, and Core ML inference with 1,024 or 8,192 rows, CPU-only or CPU-and-Neural-Engine policy, and eight-batch or whole-run inference admissions.

The quiet confirmation passed 96 normal samples and 16 queued/active cancellation trials. Every output matched its declared reference, all lanes completed, and reservations drained and were reacquired. The controller suite passed 209 tests with four skips. A clean Release build-for-testing compiled the targets and the worker passed the uninstrumented-binary check.

Overlap completed the measured work sets 1.37–2.64 times faster than sequential execution. Peak sampled process residency was 174.22 MiB. In the 8,192-row neural-policy case, whole-run admission under a tight budget produced a maximum numeric-peer wait of 429.29 ms. Eight-batch groups reduced that to 51.65 ms but paid more model-loading cost. With room for one overlapping peer, maximum waits fell below 3 ms. These finite-workload results do not prove starvation freedom, exclusive device placement, or physical-memory limits.

Decision: retain the current FIFO implementation. First choose admission headroom and inference-run duration for the application's throughput and response-time requirements. The experiment identifies an optional next comparison: persistent model ownership with smaller independently scheduled work units, while preserving memory accounting and preventing nested-acquisition deadlocks. No production change is justified solely by this matrix.

### Persistent model admission prototype completed locally

`codex/persistent-model-admission-trial` at `77e9fc1e795932f768cdde58e913dc09f43299ed` preserves the mixed-workload branch as its parent. It remains local. A package-only adapter reuses the rolling batch scheduler; public API behavior is unchanged.

The prototype retains one model in a private 49 MiB partition while each inference chunk competes with CPU/GPU requests in a separate work partition. The total allowance matches the reference strategies. This fixed partition prevents retained owners from exhausting their own required workspace in the single-model trial. Idle model capacity cannot be lent to other work.

All 144 measured samples, eight active cancellation checks, and four queued cancellation checks passed. All partitions drained and reacquired their capacity. The controller suite passed 212 tests with four existing skips. Release build-for-testing passed; this was not another full Swift unit-test execution. Peak sampled RSS was 179.67 MiB and recorded thermal states were nominal.

In the 8,192-row neural-policy workload under the 113 MiB allowance, retaining the model with eight-batch admissions reduced maximum CPU/GPU waiting from 464.04 to 18.14 ms against whole-run reservation. Median elapsed time increased from 1,202.57 to 1,229.60 ms, about 2.2%. Repeated pool creation took 1,596.94 ms. With wider allowances, whole-run reservation was generally as fast or faster. Persistent startup precedes peer launch; elapsed and first-completion times include startup, but admission waits exclude it.

These results support a caller-selected responsiveness option. They do not establish a universal chunk size, exclusive Neural Engine placement, leak freedom, indefinite fairness, or multi-model safety. The original build fingerprint is preserved, and the committed source and controller hashes match the measured code.

### Retained-session integration completed locally, October 11, 2026

`codex/retained-coreml-batch-session` at `fc9880413f80e0eeec84153cf6186912ec693e34` follows the preserved prototype. It adds scoped `CoreMLBatchPipeline.withSession` and sequential `CoreMLBatchSession.run`, with distinct lifetime/work budgets, rejection of overlapping calls, recovery after failed runs, and draining shutdown. The existing whole-run API remains available. The prototype adapter has been removed in favor of the shared scheduler.

Release build-for-testing and all 129 Release ML tests passed. The controller suite passed 212 tests with four existing skips. All 144 measured workload samples and 12 cancellation checks passed. Peak sampled RSS was 175.19 MiB with nominal recorded thermal states. Hosted CI and Codecov have not run on this local branch.

The 8,192-row neural-policy case under 113 MiB reduced maximum numeric-peer waiting from 445.59 to 20.35 ms with eight-batch session runs. Median elapsed time increased from 1,181.02 to 1,266.82 ms, about 7.3%. Repeated pool creation took 1,566.58 ms. This is a responsiveness option, not a universally faster default. The previous prototype's 2.2% cost remains historical evidence; separate short runs do not isolate the reason for the difference.

### Retained-session contribution reviewed, October 11, 2026

Local branch `codex/retained-coreml-batch-session` is now at `80a62fa48b0f06ea8fec6809a42355e9cb729130`. Standards and behavior reviews found no remaining substantive issues after fixes to cancellation-evidence validation, shutdown-test synchronization, a stale reservation description, and duplicated accounting formulas. Direct scope cancellation and mismatched-column tests were added.

Final validation passed 1,282 Release tests with two existing skips, 162 Debug ML test cases, and 212 controller tests with four existing skips. Both new public session files have 100% local executable-line coverage. The full comparison passed 144 measured samples and 12 cancellation checks. Peak sampled RSS was 179.61 MiB with nominal recorded thermal states.

The confirmation run reduced maximum numeric-peer waiting by about 95% with 4.6% longer elapsed time for eight-batch sessions in the large neural-policy workload. Earlier 2.2% prototype and 7.3% initial-integration overheads remain preserved. These separate short runs support the responsiveness option but do not establish a fixed cost or automatic chunk threshold.

### Current next action

The PR description is prepared locally. Publish the retained-session contribution with its dependency on #67 explicit; merge #67 first and refresh this contribution onto main before final approval. Neither the integration branch nor its local evidence has been published during this review. Hosted checks have not run on the new branch, and hosted Codecov currently excludes SwiftML and benchmarks, so local lifecycle coverage is reported separately.

Automatic chunk selection, multi-model retention, and broader cache/working-set experiments remain separate work. Historical records below retain their original revisions and limitations. Development notes and machine-specific evidence remain separate from contribution code.

## Historical branches and records

- Current trial: `codex/retained-memory-accounting-trial`, local head `5fa86f9f7597681561a82b42787525061c1d35f5` as of October 7, 2026. This branch is not yet published; no remote branch link is implied.
- [Engineering notes](https://github.com/crabel99/SwiftSci/tree/codex/engineering-notes) hold research, decisions, alternatives, and historical evidence. The local notes head is `c23f850ca80275964c11d04bb203639a2318c3a0`; the published branch currently trails it. Add permanent evidence links after publication review and push.
- Engineering notes remain separate from implementation branches and must not enter upstream PR diffs.
- Related upstream design discussion: [Nodibell/SwiftSci #40](https://github.com/Nodibell/SwiftSci/issues/40).
- Earlier prepared-memory contribution: [Nodibell/SwiftSci #62](https://github.com/Nodibell/SwiftSci/pull/62). This link records the related contribution, not an assertion about its current review or merge state.

## Historical position at the CPU/GPU closeout

Implemented on the local trial: prepared column reuse through standard scaling, min-max scaling and imputation; ownership transfer through compatible preprocessing steps; admission and retained-storage accounting; scoped and retained GPU input ownership; and a complete training-only preprocessing / held-out GPU regression workflow.

The latest shared-device qualification recorded 874 selected Release tests passing, two optional skips, 32 controller tests passing, and 299,520 comparison requests with matching predictions and fitted parameters. These results apply to their recorded configurations. They do not establish full-repository validation, general leak freedom, or improved SRAM/SLC utilization. Device-handle reuse removed repeated software setup work; its memory measurements did not uniformly improve.

## 1. Close the current CPU/GPU contribution

- [x] Inventory production changes, experimental owners and benchmark-only paths against the intended contribution base. Identify what ships and what remains research.
- [x] Resolve the supported ownership boundary for `RetainedLinearRegressionTrial`, `RetainedGPUInputTrial`, and `RetainedPreparedGPUInputTrial`. Promotion requires caller and lifetime review, not just renaming.
- [x] Reconcile dependency and upstream changes; preserve existing public behavior, numerical policies, source snapshots and compatibility entry points.
- [x] Document supported dtypes, layouts, missing-value semantics, cancellation/completion behavior, and the limits of estimated admission budgets.
- [x] Run the applicable Debug/Release, numerical-policy, documentation and lifecycle checks on the final contribution revision. Keep skipped or unverified cases explicit.
- [x] Preserve benchmark fingerprints, rerun comparisons affected by consolidation, and record the reviewed local contribution and evidence.

Exit condition: a bounded, reviewable CPU/GPU contribution with an explicit supported contract and validation at its final head. Later accelerator experiments do not block this milestone.

Local closeout completed October 7, 2026 on `codex/cpu-gpu-optimization-closeout` at `22c6b8908b18c967295f08a5effa69265c7fa4ef`; implementation commit `e29002e7d0`. It is based on PR #62 and includes the merged #60 dependency update with no change to the tested tree. The trial head remains preserved. Retained-owner APIs and comparison controls stay experimental; in particular, the retained prediction adapter needs an explicit GPU/precision contract before promotion.

Validation: 1,208 Debug and 1,208 Release tests passed, with two optional skips in each configuration; 160 controller tests and 100 workflow validation controls passed. All 196 Swift numerical cases passed; the Python reference retains four reviewed Wampler failures out of 196 cases. Regression policy passed without changing tolerances. Across 48 comparison workers and 299,520 requests, predictions and fitted parameters matched; lifecycle checks passed. Median throughput changes against the preserved trial ranged from -1.44% to +1.03%, a bounded qualification rather than a statistical equivalence claim. Eight additional integrity workers checked retained-source preservation and consumed-buffer reuse.

Evidence is recorded locally on `codex/engineering-notes` at `5ce0758617b4a172b1aaed882f19d82c0e4048ff`, in `Documentation/EngineeringNotes/benchmarks/2026-10-07-cpu-gpu-closeout.md`. Neither new branch head has been pushed. Runtime qualification is on the current Apple silicon host, not every supported macOS version.

- [x] Publish the reviewed CPU/GPU contribution with its dependency on #62 clear, link its PR and published evidence, and complete hosted CI. Publication is separate from the completed local development/qualification above.

## 2. Add a Core ML execution interface on a separate branch

- [x] Audit and reuse existing `CoreMLExportable` / `CoreMLExporter` support and relevant Apple APIs before introducing new abstractions.
- [x] Connect prepared data to Core ML inputs and outputs with explicit dtype, shape, stride, conversion, and ownership contracts. Evaluate compatible shared backing and reusable output buffers; verify copies rather than assuming their absence.
- [x] Keep application admission and buffer lifetimes in our memory layer. Leave model partitioning, Neural Engine scheduling and internal memory placement with Core ML.
- [x] Expose allowed compute units and fallback behavior honestly. An allowed Neural Engine does not prove execution there.
- [x] Qualify asynchronous prediction, cancellation, errors, concurrent requests, model unload and repeated reuse. Account separately for application estimates and observed framework/process memory.
- [ ] Use a representative supported inference model with independently checked outputs. Compare CPU, GPU and Neural Engine configurations where available; record actual placement, conversion costs, cold/warm behavior, latency, throughput, memory and accuracy.

Status: the first verified workflow is delivered by #65 and #66, with end-to-end bounding in #67. Broader device-placement and compute-policy comparisons remain ongoing; allowed compute units do not establish actual placement.

Exit condition: one complete, verified workflow through the adapter, with documented fallback and ownership behavior. General dataframe operations and FP64 scientific computation do not become implicit NPU workloads.

## 3. Measure and optimize working sets

Each item starts as a hypothesis with a reference implementation. Retain an optimization only when representative measurements support its tradeoff.

- [ ] Characterize actively reused bytes, dtype, access order, strides and concurrency across realistic sizes. Separate software overhead, allocation, conversion, computation and synchronization. Use hardware counters where available and distinguish observations from inferred cache effects.
- [ ] Evaluate compact columns and validity storage through ingestion and numerical consumers. Include selection, missing values, retained snapshots, mutations and conversion costs.
- [x] Evaluate blocked matrix operations and packing with varied shapes and reuse counts. Compare established Accelerate/BLAS paths before adding custom kernels; avoid a universal hard-coded crossover from one fixture or chip.
- [x] Evaluate fusion of compatible preprocessing steps over chunks to reduce intermediate arrays and memory passes. Preserve training-only fitting, arithmetic/precision requirements, missing-value treatment and source ownership.
- [ ] Evaluate worker partitioning, task size and concurrent writes for false sharing and bandwidth contention. Measure whether padding or partition changes justify their extra memory cost.
- [ ] Compare Metal threadgroup staging with direct access for a suitable workload. Include occupancy, synchronization and staging costs; do not assume explicit scratch memory is faster.
- [ ] Test CPU/GPU/Core ML handoffs and overlapping work for shared-bandwidth contention, completion ordering and memory pressure. Unified addressing does not make accesses equally cheap or remove synchronization.

Exit condition per experiment: an adopted change with evidence, or a documented rejection/deferment explaining when to reconsider it. This milestone does not promise that every proposed optimization will ship.

## 4. Keep the roadmap and evidence usable

- [ ] Record each experiment's hypothesis, branch, baseline/candidate commits, workloads, numerical contract, result and decision in the engineering notes; link it here once published.
- [ ] Use child issues for substantial work, each with an acceptance condition and a bounded branch/PR. Reference this tracker in those issues and PRs without automatically closing it.
- [ ] Maintain a representative comparison across small/large/mixed inputs, retained/consumed ownership, cold/warm execution and bounded concurrency. Include end-to-end costs and relevant Python/framework references with equivalent contracts.
- [ ] Record supported-hardware and OS coverage, unavailable counters, untested failure paths, and performance regressions. Preserve historical results at their tested fingerprints.
- [ ] At each milestone, update this issue's completed work, next action, and deferred items so follow-up conversations do not become an undocumented backlog.

## Reference material

- [Apple CPU performance and false-sharing guidance](https://developer.apple.com/videos/play/tech-talks/110147/)
- [Apple Metal shader guidance](https://developer.apple.com/videos/play/tech-talks/111373/)
- [Metal shared storage](https://developer.apple.com/documentation/metal/mtlstoragemode/shared)
- [Apple Neural Engine transformer layout and memory guidance](https://machinelearning.apple.com/research/neural-engine-transformers), a documented implementation study rather than a universal layout rule for every chip generation.
- [Core ML input/output and performance integration](https://developer.apple.com/videos/play/wwdc2022/10027/)

The current decision and remaining production boundary are recorded in the October 12 status update above.
