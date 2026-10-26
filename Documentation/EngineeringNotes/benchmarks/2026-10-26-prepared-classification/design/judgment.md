# Cross-judgment

## Scores

| Rubric criterion | Candidate A | Candidate B | Evidence |
| --- | ---: | ---: | --- |
| 1. Prepared caller path and legacy conformance | 3 | 3 | Both add prepared fit, label and probability protocol requirements, compatibility defaults, pipeline dispatch and supervised/budget conveniences. Row-only conformers still compile and retain unsupported-probability behavior. |
| 2. Remove expansion/allocation without broad machinery | 3 | 1 | A's two private read-only views avoid nested-row expansion and reuse epoch scratch without copying feature storage. B also reuses scratch, but its defining shape adds a mandatory N by P Double copy to every CPU fit and prediction, including existing row callers and one-row prediction. |
| 3. Preserve arithmetic and behavioral contracts | 2 | 3 | Both preserve CPU loop/update order, Float GPU work, routing, zero epochs and strict `p > threshold`. A wrongly proposes binary-only targets and rejects zero-width legacy rows. B explicitly preserves row soft targets and intercept-only zero-width CPU calls and gives a stronger epochs 0/1/32 test plan. |
| 4. Validation, ownership and failure-safe state | 2 | 3 | Both atomically publish parameters, schema and resolved device and use pipeline failed-refit invalidation. A's validation is over-broad and leaves transformer provenance preservation mostly contractual. B more clearly separates prevalidation from post-mutation failure and names the compatibility cases. |
| 5. Small surface and short call chain | 3 | 2 | A keeps the numerical path over existing owners with only tiny private adapters. B keeps the public surface small but adds a packed CPU representation and route-specific conversion policy whose main cost is imposed on legacy calls. |
| 6. Xcode 27 / Swift 6.3.3 validation and evidence | 2 | 2 | Both identify focused integration, routing and frozen-workload evidence but omit the requested explicit Xcode 27 / Swift 6.3.3 command matrix and production-versus-engineering evidence section. B's test inventory is more detailed; neither fully satisfies the criterion. |
| **Total** | **15/18** | **14/18** | |

## Selection

Use **Candidate A** as the base. Its structural choice removes repeated epoch allocation while preserving existing feature owners and avoiding a new full copy on row CPU fit and prediction. Its two serious compatibility mistakes are narrow policy choices that can be corrected without changing that architecture. By contrast, removing Candidate B's mandatory Double pack would replace its defining design with A's view-based kernel.

## Grafts into A

1. Take B's legacy compatibility policy, strengthened to preserve the same mathematical target domain on both routes: accept finite, aligned soft targets for row and prepared logistic fits. Documentation and fixtures may use binary labels, but the new prepared route must not narrow existing logistic behavior.
2. Preserve nonempty zero-width legacy CPU rows as intercept-only fits and predictions. Prepared supervised input may still require at least one named feature. Keep a narrow explicit zero-extent GPU path if current GPU behavior supports it because `ScopedGPURead` rejects zero extents.
3. Use B's direct `ScopedGPURead.withMatrix(batch:)` call for prepared GPU fit and prediction. Use the row/value closure only for row storage. This reuses the strongest existing ownership boundary and avoids optional per-cell batch access while packing Float data.
4. Take B's concrete verification inventory: epochs 0, 1 and 32; strict threshold ties; row soft targets; zero-width CPU rows; route preservation; failed-refit state; existential native dispatch; legacy unsupported probability; and exact CPU row/prepared parameters and predictions.
5. Add A's consistent probability-row-width check and enforce transformer row count plus `originalRowIndices` preservation after each prepared transform. Do not assume binary probability width at the generic classifier boundary.

## Compatibility pitfalls

- Legacy row prediction currently returns `[]` before checking fitted state; preserve that ordering. Add shape checks for nonempty rows without adding blanket finite-value rejection to the legacy prediction route. Prepared prediction should continue to call `requireFinite()`.
- Validate and construct the complete fitted candidate before the actor's single assignment. Check Double parameters and their Float mirrors so failed conversion cannot pair old parameters with a new resolved device or schema.
- Scratch reuse must preserve the exact sequence: predictions by row/feature, gradients by row/feature, scale, gradient check, weight updates, then bias update. Do not fuse passes or use reductions.
- Pipeline prevalidation failures leave the prior fit usable. Once a transformer mutates, any later failure keeps `needsSuccessfulFit` set until a complete fit succeeds.
- Cancellation at epoch boundaries is a new observable failure point. Verify it preserves the prior aggregate state; successful numerical results must remain unchanged.
- Keep dataframe row conveniences, persistence, Core ML getters, One-vs-Rest behavior, router policy and supplied-parameter routing unchanged. Do not depend on unmerged PCA APIs or add classifier/agent infrastructure.
- Add an explicit Xcode 27 validation section before implementation handoff: compile production and focused tests in the supported Swift mode, run the independent CPU fixtures for epochs 0/1/32, and record any Swift 6.3.3 ownership/existential-dispatch evidence separately from production code. No Xcode rollback is planned.

## Diversity note

The arena produced useful structural diversity (borrowed views versus route-specific packing), but no model-family diversity: all enabled models, including the configured 5.6-sol option, are GPT-family models. Treat agreement as correlated evidence rather than an independent cross-family vote.
