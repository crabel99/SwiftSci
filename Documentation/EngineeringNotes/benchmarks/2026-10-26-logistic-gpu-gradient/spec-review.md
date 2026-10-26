# Spec review

Fixed point: `8926829bf2952a8f981a8be199be9ee9c3f7c458`. Reviewed the working-tree diff for the three requested tracked files, the new `BinaryCrossEntropyTests.swift`, the unchanged logistic solver call sites, and the supplied diagnosis/red/green receipts. Read-only review; no builds run.

**Missing or partial requirements: none found in the scoped implementation.** The requirement to “independently verify gradients and updates” is supported by analytic zero-logit and averaged mixed/extreme-logit derivative expectations, an analytic first GPU bias update for hard and soft targets, and prepared CPU/GPU weights, bias, and probabilities against the existing independent 0/1/32-epoch references. The routed 1,000-row fixture also checks row/prepared agreement for CPU/GPU/auto/ANE. These are specific numerical checks, not a general convergence or precision guarantee.

**Scope creep: none found.** The only production logic change replaces the BCE expression. Documentation explains the intentional training-result correction; regression tests stop preserving the demonstrated erroneous GPU trajectory. No new algorithm, dependency, CI policy, routing rule, public interface, or threshold is introduced.

**Incorrect implementation: none found.** For finite logits, `mean(logAddExp(0, logits) - logits * targets)` implements the required stable BCE with the correct derivative at zero. The recorded primitive probes establish why the previous `maximum`/`abs` expression lost the sigmoid contribution there. The red receipt rejects that previous behavior, and the green receipt passes the regression suites.

The requirement to “preserve existing calling interfaces, CPU math, Float GPU precision and routing, stored-parameter prediction behavior” is met structurally: those implementations are outside the production diff. The changed helper is used by GPU fitting; stored-model prediction does not call it. The documentation correctly calls out changed retraining trajectories, including automatic GPU routing.

**Result: 0 spec findings.** Full local CI qualification remains the parent task’s release gate; these targeted receipts alone do not establish it.
