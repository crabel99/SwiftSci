# CSV CI and coverage repairs

The fixes are committed and pushed to [#85](https://github.com/Nodibell/SwiftSci/pull/85) at `48070073a6c8c0e37b09fafdb6aa3833ab731014` and [#86](https://github.com/Nodibell/SwiftSci/pull/86) at `d205cb71c07bb5a94772393571371632cdd00e9e`. Both remain drafts. Merge order remains #85, then #86 after its base refresh and validation. Engineering notes were not pushed or included in either source diff.

## Repair the actual CI compiler failure

Both failing #86 jobs stopped while compiling the same optional join-key expression in `CompactJoinTests.swift`. The unit log and benchmark artifact identify Swift 6.3.3 from Xcode 26.6. Local validation used Swift 6.4 and did not reproduce that solver timeout.

Commit `9df6c56f83` gives the map closures concrete argument and return types, calculates the offset once, and separates nil selection from Double construction. Fixture sizes, values, and assertions remain unchanged. All 431 local dataframe tests pass after this isolated fix. Hosted safe-mode unit tests then pass at that exact head, providing the older compiler check that the local build could not supply. Benchmark verification and the refreshed combined head still require their own hosted results.

## Cover the reachable boundaries

The initial #85 Codecov comment reports 12 uncovered added lines across four files. Once #86 can compile, its report identifies the same 12 lines plus one compact-specific radix-buffer swap. The Codecov patch status itself passes at both initial reporting points; the missing-line comments are still useful evidence.

Commit `48070073a6` covers wide-index inferred Double conversion with absent fields, the existing unfinished-record EOF behavior, and exhausted streaming budgets. A small bounded implementation of the existing index-field protocol exercises widening without allocating multi-gigabyte fields. The batch handler shares completion and cancellation handling after retry. Production invariant traps remain intact.

Commit `d205cb71c0` adds all-present sorting cases with one, three, and five active radix digits for both optional and compact storage. It checks both directions, stable equal-key order, and unchanged source bits. A fresh profile records 12 executions of the previously uncovered swap at TypedColumn.swift line 684. The sorting algorithm is unchanged.

The shared ingestion repair is merged into the compact review branch without rewriting published history. Relative to ingestion, the current compact diff is 23 files and 17 graph commits, including the integration merge. No benchmark specifications, failure entries, tolerances, or coverage exclusions change.

## Local verification

| Check | Ingestion | Combined compact |
|---|---:|---:|
| Debug dataframe tests | 398 passed | 436 passed |
| Release dataframe tests | 398 passed | 436 passed |
| Test failures or skips | 0 | 0 |
| Fresh source-level coverage profile | Captured | Captured |
| New radix cases observed running | Not applicable | Both cases |

All 226 benchmark controller tests pass with Metal opt-in enabled. The new Swift test files are 47, 49, and 38 lines. These are focused follow-up results. The earlier full-package test results remain evidence for their recorded heads, not a full-package rerun on these follow-ups.

Fresh local source coverage executes every added executable line in CSVColumnConversion, CSVEagerReader, and CSVReadCursor under this compiler's mapping. SystemsCSVParser retains three zero-count mappings: an invariant-trap statement at line 205 and closing braces at lines 232 and 244. These mappings remain visible. No invalid pointer state, deliberate process crash, or coverage exclusion is used to claim 100% coverage. Hosted Codecov may map lines differently.

The original Xcode archive omitted package-library source coverage. An initial direct export also found a stale cached profile and is not used as evidence. The retained `ingestion-source.lcov` is that invalid attempt. Only `ingestion-fresh.lcov` and `compact-fresh.lcov` support the source coverage claims. Each comes from a newly collected raw profile, a recorded instrumented-binary SHA-256, and an unchanged binary during the test run. Old profiles must not be used against rebuilt executables.

## Hosted state and evidence

The final snapshots show the new heads with hosted checks running or queued. No check is waived or represented as successful while pending. The earlier #86 safe-mode success belongs to the isolated fixture-fix head. The disabled performance job is not performance validation, and a neutral CodeQL aggregate does not replace the actual Swift and Python analyses.

Both PR descriptions identify the follow-up heads and focused tests, preserve the original full-package receipts, and retain the historical benchmark fingerprints. No performance study is rerun, and no speed claim is assigned to the new parser-handler refactor.

The [repair heads](repair-heads.json), [source-coverage audit](local-source-coverage-audit.json), [radix swap count](radix-swap-coverage.json), and native test receipts retain the concise evidence. The [experiment archive](experiments.tar.gz) preserves failing CI logs, the downloaded benchmark build log, public Codecov snapshots, validation drivers, raw profiles, and exported coverage. It excludes xcresult bundles and compiled executables. The [source bundle](repair-source.bundle) preserves the repair commits relative to the published starting heads. Reproduction requires a fresh build and matching fresh profiles; binary hashes are not a portable executable archive.
