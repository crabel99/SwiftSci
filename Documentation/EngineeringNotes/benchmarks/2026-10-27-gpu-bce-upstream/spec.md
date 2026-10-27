# Independent GPU BCE correction

Current upstream initializes logistic weights and bias to zero. For binary cross entropy with logits, the derivative at zero must be0.5 minus the target. The pinned MLX maximum/absolute-value composition instead supplies minus the target, so even one GPU training step is wrong. Existing broader investigation and its independent controls are recorded in the October26 logistic-gradient engineering note; this delivery verifies the isolated correction against current upstream rather than replaying unrelated prepared APIs.

Required behavior:

1. Mean BCE loss remains finite for the tested extreme logits and has analytical sigmoid-minus-target gradients, including zero. The stable log-add-exp expression replaces the nonsmooth composition.
2. One public legacy GPU training epoch on one zero feature updates bias by minus learning-rate times0.5-minus-target, for the three existing regression parameter cases.
3. Preserve public signatures, CPU arithmetic, precision, device routing, zero-epoch behavior, dependencies and existing reference policy. Existing GPU training trajectories intentionally change at the incorrect derivative.
4. Delivery diff contains only the shared loss helper and the existing analytical regression suite. Keep prepared classification, PCA, CoreML serialization, documentation-check policy and agent work out of this PR.
5. Reproduce the old failure, freeze source, and complete fresh applicable local checks and older-compiler compilation before publishing the PR. Report existing comparator/security findings and hosted status accurately.

Fixed review base: e19db7dda4567c425b7eb002da82e234e6c7980f. No throughput, convergence or general predictive-quality claim.
