# Standards review

Fixed point: `8926829bf2952a8f981a8be199be9ee9c3f7c458`. Reviewed the working-tree diff for `Losses.swift`, `PreparedClassification.md`, and `PreparedLogisticRegressionTests.swift`, plus the untracked `BinaryCrossEntropyTests.swift`. There are no intervening commits. No applicable on-disk `AGENTS.md` was found in the source ancestors or reviewed target subtrees; the user's supplied subtraction instruction was applied.

**Documented-standard findings: 0.** The change remains within SwiftML's existing loss owner, uses the pinned MLX operation, adds no public API or mutable state, and supplies direct gradient and training regression tests under the correct test target. Numeric fixtures remain explicitly typed and small. This follows `CONTRIBUTING.md` Development Guidelines: Architecture, Performance, Documentation, Tests, and Swift type checking in tests. It also follows the required `principle-subtract-before-you-add/SKILL.md`: three compositional loss operations and their temporary bindings are replaced by the existing primitive rather than adding an abstraction or validator. The guide records the intentional change to GPU training trajectories.

**Heuristic smell findings: 0.** Checked the supplied Fowler baseline as judgment calls. The two direct derivative tests repeat a short differentiation setup, but one covers a scalar zero-logit derivative and the other covers mean reduction over mixed/extreme logits; extracting their distinct assertions would add indirection without useful shared behavior. Removing route-specific incorrect GPU reference arrays reduces duplication.

This was a read-only source review, with no builds or tests. `CONTRIBUTING.md:34,44–46,72–73` still requires standardized numerical checks, compilation of test targets with the CI compiler, and passing tests before submission; this review does not certify those execution requirements.

Summary: 0 documented-standard breaches; 0 actionable heuristic smells.
