# Prepared regression production extraction

Draft [PR #62](https://github.com/Nodibell/SwiftSci/pull/62) publishes `codex/prepared-memory-integration` at `2cd1cbe52a12537d472fd2176eae2676e30dcc80`. It is a partial implementation of [issue #40](https://github.com/Nodibell/SwiftSci/issues/40). Merge [PR #60](https://github.com/Nodibell/SwiftSci/pull/60) first; Arrow PR #61 is independent.

## Extraction boundary

The branch starts at `409e6ee545b88c22b83520845660c27ec584125d`. A three-way patch carries the selected production changes from the memory experiment's merge base, preserving newer upstream changes. The original `codex/arrow-chunk-import` checkout remains unchanged. Experimental targets, retained Arrow views, asynchronous workspace trials, and this engineering record are absent from the production diff.

The contribution keeps prepared columns through scaling and regression, adds whole-estimate FIFO admission, preserves synchronous GPU input ownership until completion, and drains autoreleased matrix owners. Legacy task-count tickets remain available with deprecation guidance. Persistent model/result accounting remains the caller's responsibility.

## Review and compatibility

The independent standards review found no documented violations. One optional duplication remains at the independently callable pipeline and model validation boundaries.

The behavior review identified changed errors for nonfinite row-array training. Exact-error regression tests failed before correction. The fix lets the existing numerical checks preserve `trainingFailed` and zero-epoch initialization. Prepared validation remains strict. Final review found no remaining actionable findings.

Five direct tests cover the dataframe additions in the CPU-only target used by hosted CI. The MLX-dependent integration suites are covered by the local full run.

## Final validation

At `2cd1cbe52a12537d472fd2176eae2676e30dcc80`:

- Full Release: 1,174 test definitions passed, no failures, two optional tokenizer-fixture skips. Parameterized execution accounts for additional test runs.
- CPU regression policy: 196/196 Swift cases and 192/196 Python-reference cases passed. All 15 profiles completed. Four existing Wampler failures remain failed conformance. No baseline or tolerance changes.
- Public API documentation checker exited successfully and reported 98.60% global coverage.
- The final snapshot and remote PR head were verified against the committed branch.

Prepared and compatibility qualification each passed 32 NIST checks and their public workflow checks. The fresh-process matrix probe passed aliased/copied imports, errors after submission, and cancellation while a scope remained open. Completed cycles did not accumulate Metal allocations. These are bounded lifetime checks, not proof against every possible leak.

## Measurement

| Rows × features | Input case | Rows, ms | Prepared, ms | Rows, peak MiB | Prepared, peak MiB |
|---|---|---:|---:|---:|---:|
| 1,000 × 4 | ordinary, retain | 10.31 | 10.51 | 20.55 | 20.56 |
| 1,000 × 4 | ordinary, materialize | 10.68 | 10.47 | 20.62 | 20.61 |
| 100,000 × 8 | ordinary, retain | 80.31 | 74.86 | 57.16 | 49.62 |
| 100,000 × 8 | ordinary, materialize | 83.41 | 75.73 | 64.06 | 56.52 |
| 100,000 × 8 | noisy, retain | 80.60 | 73.79 | 57.95 | 49.55 |
| 100,000 × 8 | noisy, materialize | 81.76 | 76.42 | 64.03 | 56.58 |

Three interleaved fresh processes per case and API path, Apple M4 Max, 128 GiB, macOS 27, Swift 6.4. Release with testability enabled, coverage disabled at the Xcode test action, and executable instrumentation verified absent. Native threading is unchanged. Selection, preparation, fit and prediction are timed. Source construction and prepared-path admission are outside timing. Peak RSS is sampled before the independent reference calculation.

Measured production source commit: `4cd39548be1c5ae91a38f91968eac364b89d33f6`. The successor `2cd1cbe52a12537d472fd2176eae2676e30dcc80` changes only tests; production Sources and dependency files were compared and are unchanged. The temporary qualification manifest adds preserved launcher targets; those targets are not part of the PR.

Executable SHA-256: `dd4969cbeb9cd6cd7baf4e737d408030cdcba2352da45db007beeafc4d1f8c98`.

The first comparison contained coverage instrumentation despite compiler-level flags. Its timings and memory comparisons are marked invalid and superseded. The corrected run used `build-for-testing -enableCodeCoverage NO` and the repository's binary instrumentation check. Raw earlier results remain retained with the invalidation record.

## Retained evidence

Evidence set `prepared-memory-integration-20261006` contains the extraction patch, exact commands, failing compatibility regression, result bundles, review state, and PR text. Final correctness evidence is in `release-cpu/`; uninstrumented comparison, NIST and lifetime evidence is in `final/`. Raw evidence stays local, including machine identifiers in Xcode outputs. This published-form summary excludes those identifiers and local personal paths.

## Remaining work

Hosted checks for #62 must finish before readiness. Persistent-output admission, asynchronous GPU ownership, retained Arrow views and experimental scheduling remain separate work. The declared minimum deployment is unchanged, but these runtime checks used macOS 27 with a macOS 14 deployment target.
