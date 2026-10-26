# Next verified units after ML Program qualification

Reviewed October 26, 2026. This is a source/record assessment, with no builds, tests, training, inference or production edits. The five-hour run ends at 01:27 UTC. Finish source-bound qualification and publication for the current ML Program study before starting another expensive measurement.

The current records do not support inventing a broad new numerical feature list. PCA, prepared logistic classification/training, the GPU zero-logit gradient correction, and representative legacy Core ML qualification are completed contributions. Three bounded units remain useful and evidenced below.

## 1. Converge the complete qualified PCA stack into the continuation

This is the first source task after the current study. The later continuation does not yet include prepared PCA at all.

Evidence:

- `/private/tmp/SwiftSci-local-ai-handoff-20261025.md` records prepared PCA as a completed PR89 contribution, with the review correction published at `4f33c76f3938e070105c2a5928c712aa5e067a00`.
- `/private/tmp/SwiftSci-pr89-review-handoff-20261026.md` explicitly keeps that review branch separate from the Core ML continuation. Its final independent reviews have zero findings and all 1,667 native tests passed in both configurations.
- Current continuation HEAD is `a1e234d25677d91ce5914062603c41233fe13c09`. Its direct history includes classification `8926829bf2`, GPU correction `53063789b1`, and foundation base `e19db7dda4`. It does not include PR89.
- The continuation has `Sources/SwiftCluster/Core/PCA.swift` containing its original LAPACK implementation. `Decomposition/PCAComputation.swift` and `PCAFullSVDLayout.swift` are absent. Therefore the review guard correction cannot be cherry-picked alone.
- PR89's full stack above the shared foundation base is `2278521eb7`, `fcab7ea5b9`, `09607a7e9c`, `6061a70217`, then `4f33c76f39`. The last commit removes the initial overly restrictive sufficient-workspace bound. Keep that correction with its predecessor.

Scope and consumer benefit:

Create a separate continuation integration branch and bring in the complete qualified PR89 stack. Resolve only actual overlap with later classifier/GPU/CoreML changes. This gives later scientific consumers one revision containing both prepared PCA and prepared classification while preserving the maintainer-requested checks. Keep the existing PR89 branch focused and unchanged. No upstream merge or new PR is implied.

Verification unit:

Check that final PCA production/tests equal PR89 except reviewed integration resolutions, and that later classifier/GPU/CoreML production changes remain present. Run prepared PCA, layout and mean-overflow regressions together with prepared classification/GPU and multiclass export regressions on the integrated revision. Before publishing source, run the applicable full local workflow and compatibility checks on that revision. Its results are new integration evidence, not a restatement of either sibling branch's old receipts.

Do not redo the PCA design, relax workspace limits, or move later commits into PR89. Do not requalify the whole frozen-model study merely because the unrelated PCA stack is now present. Preserve the original study's exact tested source and artifact fingerprints.

## 2. Make documentation coverage reporting truthful

This is a small independent maintenance contribution, not an excuse to revise numerical gates.

Evidence:

- `Documentation/EngineeringNotes/benchmarks/2026-10-25-foundation-closeout/README.md`, in the current PR89 notes checkout, states that actual coverage was 2431/2464 declarations and that the existing checker prints an inaccurate 100% success line.
- Current continuation `scripts/verify_doc_coverage.py` still counts `total_public`, `documented_public` and `missing_docs`, prints the measured ratio at lines46-47, then unconditionally prints `100.00% DocC Public API Coverage Verified` at line70 whenever no placeholders exist. Missing documentation never affects that verdict.
- Current `.github/workflows/ci.yml` labels the invocation `Verify Public API Documentation Coverage (100%)` at line204. The advertised gate and actual gate differ.

Scope and consumer benefit:

Remove the false unconditional 100% assertion. Report the actual counted ratio and the separate placeholder result. Name the workflow step according to what it verifies. Preserve existing placeholder failure behavior. Do not silently introduce a new 100% coverage policy or a lower threshold. If enforcing complete documentation is desired, make that a separately scoped policy decision and missing-documentation contribution.

Verification unit:

Use tiny temporary Swift fixtures to prove documented, undocumented, empty-source and placeholder cases produce truthful output and the intended exit status. The uncovered fixture must never print a 100% success claim. A placeholder fixture must still fail. Run the script against the final source and record the actual ratio. No Swift numerical behavior changes, so this unit needs controller/script checks and the actual CLI output rather than another hardware benchmark study.

Do not expand the checker into a Swift parser, fill unrelated API comments mechanically, or adjust the numerical/reference inventory. Its current declaration-count heuristic should be described honestly rather than presented as authoritative DocC symbol-graph coverage.

## 3. Reconcile the current record index and next-action tracker

The latest handoff has advanced beyond the retained roadmap snapshot and the engineering-notes entry index. This unit prevents completed work becoming the next chat's backlog again.

Evidence:

- `Documentation/EngineeringNotes/benchmarks/2026-10-25-foundation-closeout/roadmap-after.json` records the explicit open maintenance task to update each milestone's completed work, next action and deferred items. It is a dated issue snapshot, not a live status check.
- That snapshot still has an unchecked representative-model/placement item. The October26 legacy study completed one portion, and the current ML Program study is handling another. Preserve those distinctions rather than marking all inference/device research complete.
- The current notes checkout `/private/tmp/swiftsci-pr89-review-20261026/notes` contains October26 directories for prepared PCA, classification, GPU correction, representative CoreML and PR89 review. Its top-level `README.md` contains no `2026-10-26` entries, so those records are difficult to find through its entry index.
- The original handoff still begins with old PR87/88 delivery status, but current continuation history contains their merge commits. Its appended completed milestones correct later work. A short current-state entry should explicitly distinguish these historical paragraphs from live continuation state.

Scope and consumer benefit:

Add concise links to the completed October26 records and this study after publication. Record the integrated source from unit1 if completed. Keep historical measurements at their tested fingerprints. Prepare a precise current tracker update, and read the actual live issue before applying any update so newer state is preserved. The source code roadmap at `ROADMAP/ROADMAP.md` marks every listed release through3.8 completed; it is not an actionable list of new implementation requests.

Verification unit:

Check every index link exists in the published tree, manifests match the published evidence, current source heads are named separately, and unfinished/unsupported claims survive. Re-read the resulting index and handoff as a fresh reader. This unit finishes when the next action is explicit and old completed entries cannot be mistaken for pending work.

Do not rewrite old experiment results, reopen completed foundation scope, close the entire long-term tracker, or claim hosted checks passed without observing them.

## Work that remains broader or conditional

The E-core timing baseline remains explicitly unqualified. The foundation closeout preserves ten failed CPU/elapsed twin controls and an observation-gap overrun. This is an operating-state research problem, not a request to rerun panels until a favorable sample passes. Broader cache counters, false sharing, Metal staging and automatic hardware routing remain deferred research. They are outside the supported foundation contract and lack a new concrete consumer defect here.

The company integration handoff also identifies real SwiftLLM/SwiftAgent gaps. Current `LLMModel` exposes only `AsyncStream<String>`, while `TransformerDecoder.generateDetails` separately emits rich completion/error data. `ReActAgent.run(query:model:options:)` still concatenates the legacy stream, so generic model use loses stop reasons and token counts. That is a useful future bounded consumer-contract audit. It is not yet a selected adapter design, an instruction to choose a new runtime, or permission to start a server/launcher replacement. Likewise, no combined official MLX Swift LM dependency graph has been qualified by these records. Keep those gaps visible without converting them into speculative implementation during the remaining flight window.

Recommended order is source convergence, truthful documentation reporting, then current record/index closeout. Reserve enough time to finish verification and publish reviewable evidence. A smaller number of completed units is preferable to an unqualified new model/runtime feature.
