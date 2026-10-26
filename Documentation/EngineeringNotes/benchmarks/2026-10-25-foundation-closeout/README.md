# Foundation closeout and full E-core resource study

## Scope and delivery

The supported foundation covers CSV ingestion, selectable compact Double columns, row selection, sorting, joining, grouping, numerical preparation, fixed-size mutation, preprocessing, and supported CPU, GPU, and Core ML ownership. General foreign mutable buffers and hardware-specific experiments remain follow-on work. The public contract lives with the production documentation. Decisions and raw measurements remain on this engineering-notes branch.

The source is divided into the five pending CSV commits on `codex/csv-resource-closeout`, followed by the focused foundation fixes on `codex/foundation-contract-closeout`. Both start from upstream `962fd9ff4d155e5116baf6f177abfa3e84fd8754`. The second branch includes the CSV commits and needs review in that order. Review [CSV PR #87](https://github.com/Nodibell/SwiftSci/pull/87) first, followed by [foundation PR #88](https://github.com/Nodibell/SwiftSci/pull/88). Both are drafts while hosted checks and upstream review remain pending.

The data audit found repeated optional-column materialization inside compact floating-key grouping, avoidable grouping and join input exports, and lost schema after empty joins. The ownership audit found that pipeline admission materialized identity row indices just to inspect their capacity. The fixes use existing indexed access, the existing compact collection view, normal typed join assembly, and the existing retained-provenance capacity accessor. No new allocator, dtype system, scheduling layer, or public API is added.

An initial generalized typed-column join was narrowed after an unqualified diagnostic suggested an optional-path CPU cost. The retained change preserves direct optional-array specialization and adds compact collection specialization only where needed. Intermediate diagnostic results and superseded validation attempts remain in the archive. Final-head checks, rather than those intermediate receipts, determine delivery readiness.

## Full E-core study

The completed study measured `06adea701994f8fbbe82481684dfdafd77958a09` before the foundation fixes. It contains 144 queues, 9,216 jobs, and 48 complete-output checks over public air-quality and household-energy workflows. Application workers recorded zero P-core user time. Permitted kernel P-core work remains separate. Four persistent workers retain native library parallelism. These facts do not establish equal CPU frequencies or energy consumption.

All complete-output checks pass. Identical-condition peak-RSS controls pass. Compact SwiftSci storage uses about 28.4% less sampled peak memory than optional storage in both the primary and twin conditions. Polars still uses less sampled peak memory than compact SwiftSci. The memory result does not mean every operation is allocation-free or that the framework has no leaks.

The full timing panel remains unqualified. Ten CPU or elapsed-time twin controls fail, with deviations of roughly 16% to 31%. One observation gap is 50.526 ms against the frozen 50 ms limit. The user's tolerance for that marginal overrun does not rewrite the recorded control. Accounted execution rates correlate with CPU-time variation, but there is no concurrent direct frequency trace proving Apple's internal scheduling mechanism. The counter report does not normalize timings, select a passing repeat, or waive failed controls.

The [counter report](full-e-core-counter-report.md), [original audit](full-e-core-panel-audit.json), and [post-run verification](full-e-core-verification.json) retain the exact verdict. The source bundle preserves the measured branch. It requires an upstream prerequisite identified by `git bundle verify`.

## Evidence archive

[Full E-core study](full-e-core-study.tar.gz) preserves all 757 study files. Every archived file was rehashed against [the file manifest](full-e-core-study-files.json). Saved diagnostics equal replayed diagnostics, all 743 capture files remain unchanged, and all 589 recorded worker and controller PIDs had exited at the post-run check. The launch README inside the archive is historical; the final verification and diagnostic reports record completion.

[The roadmap snapshot](roadmap-before-closeout.md) provides the previous issue body with trailing blank lines removed. The exact 65,530-character body remains in `roadmap-before.json` inside the closeout archive. The live fork tracker keeps the current state and future work. Source PRs exclude this report, its archives, and every engineering decision record.

## Remaining boundary

Functional validation and resource interpretation are separate. A numerical regression-policy pass retains four failed Python Wampler conformance cases. It does not certify universal numerical accuracy. Local tests on this Apple silicon toolchain do not substitute for hosted CodeQL, Codecov, older-compiler coverage, or testing on every device. A certified timing baseline requires repeatable operating conditions beyond the controls achieved in this study.

## Final validation

The [final audit](final-audit.json) verifies clean source heads and the actual compiled Swift source hashes. CSV head `da03a630154843acee994c2e8b3af2924ee8b253` passes 1,647 tests in each of Debug and Release. Combined foundation head `5cc699a7efe3f1d6a2697172eb62b94a35bc3a26` passes 1,656 tests in each configuration. All 15 native test targets execute, with zero failures or skips. Strict ONNX prerequisites and the hash-checked Llama tokenizer are enabled.

Each branch separately passes 226 benchmark-controller tests with Metal opt-in enabled. Each CPU acceptance run covers 404 Swift/Python executions. Swift passes 202/202 and Python passes 198/202. The regression policy passes without changing its inventory, tolerance, or coverage bindings; all four Python Wampler numerical conformance failures remain failed. This is not full numerical certification.

Changed Swift files have no warnings under the 100 ms expression and 200 ms function type-check thresholds. Changed tests are at most 105 lines. [The documentation and size record](final-docs-and-size.json) records actual documentation coverage of 2431/2464 declarations. The existing checker prints an inaccurate 100% success line, which is not adopted here. Local checks do not prove hosted CodeQL or Codecov success.

## Focused resource diagnostics

A Release diagnostic confirms the compact grouping defect before the patch. CPU time grows from about 2.3 ms at 2,000 rows to 157 ms at 16,000 rows. The final indexed path uses about 0.3 ms at 16,000 rows and about 16.4 ms at one million rows. Exact output checks pass. This is evidence of the repeated materialization and its removal, not a qualified timing comparison.

The million-row compact self-join's median recorded process peak RSS falls from about 95.1 MiB to 64.5 MiB. Removing two optional Double input arrays accounts for roughly 32 million bytes of temporary storage. The optional-array kernel remains specialized directly, and compact/optional mixed inputs have parity regressions. Its peak RSS stays about 95.1 MiB; the uncontrolled optional CPU median changes from about 90.4 ms to 92.1 ms. That difference does not establish a regression or an improvement. [The diagnostic summary](diagnostic-summary.json) keeps intermediate and final samples separate.

These probes run in fresh processes alongside correctness validation, without P/E-core placement controls or matched operating-state qualification. Their elapsed and CPU deltas must not be presented as certified gains or an energy measurement. The large full E-core study is separate and predates these foundation fixes.

[Closeout evidence](closeout-evidence.tar.gz) retains scripts, build and test receipts, controller logs, strict acceptance records, diagnostic inputs and results, both code-review axes, the evidence review, and the decision trail. It excludes worktrees, virtual environments, compiled binaries, model weights, and xcresult bundles. Historical or interrupted attempts remain explicitly distinct from the final receipts.

Reproduction requires the recorded source, pinned dependencies, dataset cache, tokenizer, and ONNX environment. These archives are environment-specific receipts, not a standalone benchmark package.

The [independent evidence review](final-evidence-review.md), by `gpt-5.6-sol`, verifies the reviewed archive snapshot and identifies the remaining hosted, numerical, and measurement limits. The archive is regenerated after incorporating that review. No transcript audit is claimed.
