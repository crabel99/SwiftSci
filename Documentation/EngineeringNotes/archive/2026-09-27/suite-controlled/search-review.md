# Search and explanation fixture review

This review inspected Swift source and calculated independent references. It did not build Swift, execute production code, or modify the repository.

## Cosine search

`VectorStore(metric: .cosineSimilarity)`, `add(id:vector:metadata:)`, and `search(query:topK:)` provide the required contract. Results expose both ID and score. See [VectorStore.swift](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftCluster/Core/VectorStore.swift:113), [insertion](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftCluster/Core/VectorStore.swift:123), [search](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftCluster/Core/VectorStore.swift:200), and [result fields](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftCluster/Core/VectorStore.swift:43).

For query `[3,4]`, vectors `[3,4]`, `[4,3]`, `[0,5]`, `[5,0]`, `[-3,-4]` have exact cosine scores `1`, `24/25`, `4/5`, `3/5`, `-1`. Their norms are exact integers, so a Fraction calculation independently establishes the answer. Top K of four checks truncation and order without ties.

The second proposed case includes all five entries, with vectors `[3,4]`, `[6,8]`, `[5,0]`, `[10,0]`, `[-3,-4]`. Scores are `1`, `1`, `3/5`, `3/5`, `-1`. Canonicalize equivalent ties by input row index outside timing. The public API promises closest-first results but does not promise a tie order. Do not truncate through a tie boundary. Source sorting compares only scores, and replacement requires strictly better scores at [lines 257 onward](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftCluster/Core/VectorStore.swift:257).

Zero vectors need an explicit public contract before becoming golden cosine fixtures. The implementation assigns score zero whenever the product of norms is at most 1e-12 at [line 242](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftCluster/Core/VectorStore.swift:242). Thus both a zero query and a zero entry yield zero, although mathematical cosine is undefined there. This policy appears only in implementation. The same threshold also returns zero for two identical nonzero vectors `[1e-7,0]`, whose mathematical cosine is one. The approved `cosine-small-norm` fixture checks this mathematical score of one. Preserve a runtime failure; do not redefine the reference or scale inputs to hide the threshold.

Mismatched dimensions are another contract blocker. The dot product and entry norm use the shared prefix, while the query norm uses the full query. `[3,4]` queried against `[3]` gives 3/5 by source analysis; reversing the roles gives one. Restrict fixtures to equal dimensions. This restriction does not certify the mismatched case.

## KernelSHAP

The [public method](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftExplain/Core/KernelSHAP.swift:23) accepts an asynchronous model, instance, background, and coalition count. It returns feature contributions only. For at most two features, the [analytical path](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftExplain/Core/KernelSHAP.swift:43) avoids random subset sampling. More than two features use unseeded randomness at [line 97](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftExplain/Core/KernelSHAP.swift:97), so this pack does not claim deterministic coverage there.

Use model `5 + 2*x0 - 3*x1`, instance `[4,2]`, and background `[[0,0],[2,4]]`. The background mean is `[1,2]`. Baseline is one, feature contributions are `[6,0]`, and prediction is seven. Proposed complete output is `[1,6,0,7]`.

Use model `x0*x1`, instance `[3,5]`, and single background row `[[1,2]]`. Coalition values are two for empty, six for feature zero, five for feature one, and fifteen for both. Averaging marginal contributions over both feature orders gives `[7,6]`. Proposed complete output is `[2,7,6,15]`.

The helper evaluates the model to report baseline and prediction; these are not fields returned by KernelSHAP. They allow an independent additivity check. The nonlinear fixture uses one background row because the implementation replaces missing values with column means at [line 32](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftExplain/Core/KernelSHAP.swift:32). Mean imputation and expectation over a background distribution differ for nonlinear models. For the interaction example with background `[[0,0],[2,4]]`, mean imputation gives baseline two and contributions `[7,6]`; averaging over both background rows gives baseline four and contributions `[6,5]`. Keep those interpretations explicit.

## Other explanation APIs

LIME has a fixed random sequence at [LIME.swift line 72](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftExplain/Core/LIME.swift:72). With zero regularization and affine model `5 + 2*x0 - 3*x1`, its exact theoretical weights are `[2,-3]`. At instance `[4,2]`, its centered intercept and prediction are both seven, and local R-squared is one. The [design matrix centers features](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftExplain/Core/LIME.swift:122), so the expected intercept is not five. This is a suitable later fixture, subject to runtime numerical validation.

Permutation importance uses unseeded shuffling, but its [identity-permutation rule](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftExplain/Core/TreeSHAP.swift:267) makes exactly two rows deterministic. For features `[[0,0],[2,3]]`, the affine model above, and targets `[5,0]`, swapping feature zero increases MSE by sixteen; swapping feature one increases it by eighty-one. The dictionary result is `feature_0:16, feature_1:81`.

PDP on `[[0,0],[2,4]]` with the same model, feature zero, and three grid points gives grid `[0,1,2]` and values `[-1,1,3]`. See [calculatePDP](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftExplain/Core/TreeSHAP.swift:298).

Direct TreeSHAP lacks a sufficiently defined baseline contract for this pack. [FlatTreeNode](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftML/Core/DecisionTree.swift:36) has no cover counts, while [TreeSHAP traversal](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftExplain/Core/TreeSHAP.swift:85) ignores internal node values. For a stump with leaves ten and fifty, source analysis gives contributions minus forty or forty. A separately specified background with equal left/right probability would give minus twenty or twenty relative to baseline thirty. The current public method takes no background distribution, so do not assume that convention or silently accept the source output as mathematical truth. Existing [additivity-named tests](/Users/crabel/Documents/src/SwiftSci/Tests/SwiftExplainTests/KernelSHAPTests.swift:137) only check finiteness. Defer a golden TreeSHAP fixture until its intended baseline and coverage semantics are explicit. Keep the discrepancy visible in planning.

## Deliverables

`search-pack` contains five controlled source specifications, independent Fraction-based reconstruction, separate input and reference JSON, proposed typed Swift helpers, and pure Python comparators. No expected values enter timed payloads. The helpers have not been compiled. The Python comparators compute results from payloads and do not import reference generation code or read reference files.
