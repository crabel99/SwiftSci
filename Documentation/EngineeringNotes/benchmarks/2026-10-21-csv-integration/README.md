# Compact CSV production integration

The validated compact CSV parser is integrated on local branch `codex/csv-compact-record-index`. The production head is `2be6fc01a80d520d637f85f9f4bbde0a855e309b`, based on `546510bb7df19fc87a664bded5947c738011ee1d`. This record belongs to `codex/engineering-notes`; it is not part of the production diff.

The implementation preserves the existing public API, conversion rules, and large unquoted parallel scan. It changes temporary field metadata and how column builders read that metadata. Finished DataFrames retain their existing storage.

## Commits and scope

- `1eb2ae139b90e30862650426477a29b9714519cf`: bounded compact field blocks, full-width fallback, synchronous scoped field access, and regression tests.
- `2be6fc01a80d520d637f85f9f4bbde0a855e309b`: shared block geometry and a public large unquoted file/stream ownership test.

Compact metadata uses eight bytes per field where the absolute scan range fits the selected bound. Wider coordinates use full-width metadata. The original unquoted parallel path retains its flat storage. One generic scanner handles the two fallback field widths. Column construction selects a flat view, compact view, or owning fallback once per column.

The borrowed views remain internal and synchronous. Their buffers must not escape the closure or enter asynchronous work. Current call sites return owned column results. The closure signature alone does not statically prevent a future caller from returning a borrowed view, so the lifetime contract and call-site review remain necessary.

## Validation on the committed implementation

| Check | Result |
|---|---|
| SwiftDataFrame Debug target | 339 tests passed, zero failures or skips |
| SwiftDataFrame Release target | 339 tests passed, zero failures or skips |
| SwiftDataFrame Address Sanitizer target | 339 tests passed, zero failures or skips; no reported memory-access errors |
| Added executable production lines | 129 of 129 covered locally |
| Standard `tabular-smoke`, SwiftSci and pandas | 19 cases × 2 engines × 5 process rounds; 190 validated samples |
| Standard certificate audit | Passed |
| Original-file valid cases | 14 of 14 match every expected value and null position |
| Original-file inference diagnostics | Twelve station failures and one date-prefix failure match the earlier implementation exactly |
| Source identity | Test receipts, standard worker receipt, and final reference build match the committed sources |

The small, explicitly typed tests cover compact encoding boundaries, block truncation/reuse, ragged rows, escaped quotes, unfinished EOF, full-width fallback, offsets above two and four GiB, and public full/streaming reads. The sparse-offset test reserves virtual address space and touches only payload pages. It does not validate throughput on a multi-GiB physical input file.

Coverage uses the instrumented test binary and LLVM profile. The Xcode aggregate listed no SwiftDataFrame source files, so that aggregate was not used. Added-line accounting sums across generic specializations and records source, binary, profile, and coverage-text hashes. This proves local line execution, not exhaustive path coverage or hosted Codecov acceptance.

The standard smoke run checks downstream grouping, sorting, filtering, joins, matrix construction, scaling, Parquet, and basic statistics. It is a conformance check; its tiny fixtures are not the production timing evidence. Initial setup attempts failed because the fresh worktree lacked generated fixtures and the system Python lacked PyArrow. Both controller and reference worker were then run in the existing benchmark virtual environment. The complete replacement run and audit passed; no production code changed to accommodate those setup errors.

## Standards review

The independent standards review found no documented-standard violations. It identified one low-priority duplication in block-size arithmetic. The follow-up commit consolidated that arithmetic in `CSVFieldBlockLayout`; the reviewer confirmed resolution. No standards findings remain.

## Spec review

The independent behavior review found no missing requirements, scope expansion, or actionable correctness findings. It checked the measured candidate against the integrated implementation, including offset bounds, block truncation, borrowed-view lifetime, inference preservation, and the unchanged parallel unquoted path. No spec findings remain.

## Bounded performance confirmation

This confirmation compares the pinned production reference, the previously measured scoped prototype, and the integrated implementation on three original files with identical supplied schemas. It supplements the [full original-file comparison](../2026-10-21-csv-reference/README.md); it does not replace its twelve-station coverage.

All three executables use identical probe bytes, dependency objects, compiler settings, public read/release boundaries, and output oracle. Six timing rounds cover all variant orders. Each timing worker has two warmups and three measured calls. Three separate memory rounds rotate order and perform one call per fresh process. There are 81 workers, 162 timing samples, and 27 memory samples. Every accepted call passes full-column value and null validation. Builds and tests finished before these timings. AC power is checked at both ends, CPU parallelism is native, and normal desktop activity is retained.

CPU time is user plus system time, not FLOPs or energy. Process peak RSS and held output heap are distinct measures. Validation is outside the timed read/release intervals and after the held-memory snapshot. Files are page-cache warm. Percent changes are medians of within-round ratios; displayed durations are medians of per-worker medians.

| Original file | CPU ms, production → integrated | Paired CPU change | Elapsed ms, production → integrated | Peak RSS MiB, production → integrated | Held heap MiB, production → integrated | CPU change from prior scoped prototype |
|---|---:|---:|---:|---:|---:|---:|
| energy | 401.17 → 395.02 | -1.7% | 94.30 → 93.82 | 720.16 → 720.19 | 285.06 → 285.06 | +0.1% |
| Aotizhongxin | 14.96 → 11.60 | -21.8% | 5.84 → 5.53 | 39.53 → 25.64 | 9.86 → 9.86 | +0.5% |
| Wanliu | 15.12 → 11.45 | -23.9% | 5.94 → 5.48 | 39.38 → 25.48 | 9.86 → 9.86 | +0.0% |

The two quoted station files retain a 21.8 to 23.9% paired CPU reduction and about 35% lower process peak RSS against production. CPU medians are within 0.5% of the earlier scoped prototype, with pair ranges spanning both directions. The unquoted energy case remains effectively neutral. Held output heap is unchanged on all three files. The individual ratios, ranges, all samples, and build identities are preserved in the evidence. These results do not establish energy savings, cache residency, or a benefit for every CSV shape.

## Remaining boundaries

The original-data numeric-inference defect still converts later fractional particulate values to null after an integer-only initial sample. Across the twelve station files it adds 398 incorrect nulls. The date diagnostic expects the UCI day-first convention, while SwiftSci documents month-first precedence for ambiguous values. The earlier classification of that mismatch as a parser defect was incorrect. Numeric inference needs a repair; date interpretation needs an explicit source-format choice. Failed inference modes are excluded from performance claims.

Local validation used Apple silicon, Swift 6.4, Xcode 27.0, and macOS 27.0.1, with the reference probe targeting macOS 14. This is the full DataFrame test target plus selected standard integration workloads, not the full SwiftSci all-module suite. Hosted CI and older supported compiler validation have not run for this local branch. No push or PR was made as part of this integration.

## Numeric inference follow-up

The separate [sampled-inference repair](../2026-10-21-csv-inference/README.md), commit `548a783f02678c95c027a733e3cbd51df363dc47`, restores the 398 measurements lost by numeric inference. Its own tests, conformance checks, and resource measurements are recorded there. The date-format capability remains separate. This integration report retains the results for its original head.

## Evidence

- [Evidence archive](evidence.tar.gz), containing test commands and summaries, logs, local coverage, standard run requests/responses/certificate, final reference oracle checks, bounded resource comparison, source patch, and build receipts.
- [Archive manifest](evidence-sha256.json), with hashes for every member and the archive.
- [Full original-data comparison](../2026-10-21-csv-reference/README.md), with source attribution, dataset provenance, all twelve station results, and the failure inventory.
- [Controlled candidate experiment](../2026-10-21-csv-borrow/README.md), with synthetic controls and compiler inspection.

Replay scripts retain the exact local cache and toolchain paths used. Dataset bytes, compiled binaries, Xcode result bundles, and caches are not committed. This is a recorded local experiment, not a new portable benchmark command.

## Date-contract correction

The follow-up [explicit date-format record](../2026-10-21-csv-date-format/README.md) distinguishes the UCI source convention from SwiftSci's documented default. Historical diagnostics, hashes, timings, and archived evidence remain unchanged. A failed comparison against the source convention is still excluded from performance claims.
