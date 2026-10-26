# Prepared PCA contribution

User authorized starting the proposed first complete numerical workflow. Worktree source is current upstream e19db7dda4567c425b7eb002da82e234e6c7980f, after PR87/88 merged. Production changes stay on codex/prepared-pca-workflow; engineering decisions, experimental harnesses and raw results stay outside production.

Scope: provide a real data -> prepared preprocessing -> PCA fit -> held-out projection -> usable labeled/provenance-preserving result path. Preserve existing public nested-array calls and explicit full/randomized/auto solver and CPU/GPU behavior. Reuse Accelerate/LAPACK and existing MLX path; no new model runtime, allocator or general dataframe engine.

Design rubric, score0-3 each:
1. Existing callers remain valid, including empty-call overload resolution and dataframe glue's missing-to-zero behavior.
2. Prepared fitting and projection avoid nested-row materialization, respect both matrix layouts, preserve input snapshots and source-row provenance, and have a clear output schema.
3. Full/randomized and device/precision choices remain explicit. No hidden solver substitution or claim of FP64 GPU SVD.
4. Validation and fitted feature identity have one owner; malformed inputs and rejected refits leave coherent state. Prepared missing/NaN/Inf behavior is documented.
5. Small public interface and local implementation; remove genuinely dead code first and reuse existing storage/provenance helpers.
6. Tests cover the real end-to-end path, independent known answers, held-out transform, repeated fits, snapshots, layouts and schema; resource comparisons count complete work with equivalent algorithms.

Compare structurally distinct choices: batch-oriented fit/transform using existing replacement columns versus matrix-oriented fit/transform using contiguous storage and a minimal provenance-preserving matrix output helper. Both can propose adapters but avoid adding all possible overloads without demonstrated use. Need lower-level flat column-major RandomizedSVD path to remove centered-rows-plus-repack. Existing default randomized seed/power/sketch behavior should remain.

Do not add code yet. Each candidate writes usage first, signatures, module map, rationale, accepted tradeoffs and test plan. Limit candidate to ~200 lines. Read architect/references/runner-prompt.md and rationale-template.md and screen design-red-flags.md. Candidates are proposals; parent chooses final design.
