# Dataset strategy: numerical and exact-model foundations

The full strategy remains in progress. This change implements the first numerical dataset families and reusable provenance checks. It does not establish general numerical stability or model quality.

## Commits and build identity

Both implementation commits are local on `codex/standardized-benchmarks`; this task did not push that branch or create a PR.

- `3151fd2cf2`: NIST regression and ANOVA conformance.
- `74a49e0253`: exact PCA and Naive Bayes contracts.

Every source hash in each build record matches its corresponding commit: 317 files for the first stage, 325 for the second. Builds took place before the commits, so the build records also retain the then-current parent commit and the complete actual source fingerprint. Tests and fixture manifests are separately retained in the committed tree and run plans.

## Scope

Stage 1 adds eight NIST linear least-squares datasets and all eleven balanced one-way ANOVA datasets. It preserves original files and notices, pins source/input/reference hashes, and reconstructs independent references at 80 decimal digits. Two profiles retain the same 19 cases. One compares against original-decimal NIST coefficients, residual sums and F statistics, with separately derived predictions. The other compares arithmetic against an exact-binary64-input reference.

The runtime contract explicitly requests CPU OLS. SwiftSci attempts its analytical solver and can fall back to gradient descent. The public API reports the device but not the solver. SciPy uses pivoted QR through gelsy. These are mathematical-output comparisons, not identical-algorithm benchmarks.

Stage 2 adds exact synthetic full and truncated PCA fixtures and multinomial Naive Bayes. Expected outputs use standard-library Fraction arithmetic. PCA checks component projectors and training/query/cross-Grams so consistent eigenvector signs are allowed while transform inconsistency remains detectable. Naive Bayes separates sorted class labels from returned prediction indices.

## What stage 1 found

At the predeclared absolute tolerance 1e-10 and relative tolerance 1e-9:

| Reference basis | SwiftSci | Python SciPy adapter |
| --- | ---: | ---: |
| Original decimal | 11 of 19 pass | 14 of 19 pass |
| Exact binary64 input | 11 of 19 pass | 17 of 19 pass |

SwiftSci fails six ANOVA cases under both bases: AtmWtAg, SmLs04, SmLs06, SmLs07, SmLs08 and SmLs09. Both implementations fail coefficient checks for Wampler4 and Wampler5. The original-decimal Python profile also fails SmLs07–09 because binary64 input conversion loses information.

SmLs09 illustrates the distinction. The NIST decimal F is 2001. The exact binary64-input reference is about 2001.13492622095. SwiftSci produces about 1983.94286108864, so storage quantization alone does not explain its deviation. SciPy produces about 2001.134926220951 and passes the binary-input check.

These thresholds are engineering acceptance criteria, not promises to reproduce all published digits. A strict coefficient failure on an ill-conditioned regression does not establish that every fitted prediction is poor. The recorded response identifies the first mismatch; future diagnostics should characterize coefficient, prediction and residual errors separately without weakening the acceptance gate.

## Verification and review

The stage 1 Release worker built without coverage instrumentation. All 61 controller tests passed. The original smoke profile passed 28 of 28 engine cases and passed its audit. All 76 new NIST processes completed, and both profiles correctly received failed records. Their audits reject them.

Real-worker adversarial checks passed two valid controls and rejected eight deliberately invalid attempts. Both workers reject a changed final prediction, ragged data, Boolean features and leaked answer fields. Review found a checksum-valid sibling substitution that could share the same answer. References now bind their derived input digest and size, with a regression test proving rejection.

The independent reference implementation is separate from both runtime implementations. Its NIST decimal results are checked against published rounded values. Binary-input and prediction references currently have one high-precision implementation, not two independently written reference solvers.

The existing filename certificate.json also appears for failed runs. Its status is failed, all acceptance gates enforce that status, and no passing certificate is claimed. A future protocol revision may use a less ambiguous filename, while retaining failed evidence.

## Exact-model results

All three Python cases pass. SwiftSci full PCA and Naive Bayes pass; truncated PCA reports ratio 1.0 instead of 0.8. The model profile correctly receives a failed record and its audit rejects it. No reference or tolerance was changed to accommodate that result.

The final Release build passed, and the final controller test run passed all 67 tests. The expanded worker passed the original 28-case smoke profile and audit. Real-worker model checks passed four controls and rejected eight intentional failures, including a modified PCA cross-Gram with otherwise unchanged component and self-Gram outputs, a wrong Naive Bayes prediction index, a ragged PCA query and a negative multinomial input. The regeneration test also verifies inventory.json bytes.

## Remaining strategy

1. Finish the testing and certification suite before production repairs. The user corrected the order on September 27. After suite completion, use a separate repair branch with one commit per error. Establish the formal performance baseline after those repairs pass. Study conditioning and backward error before setting any alternate OLS acceptance contract.
2. The selected controlled inference, one-cluster KMeans, Kalman, cosine and two-feature KernelSHAP cases are now implemented in local commit 279c01433d. See [the controlled-suite report](2026-09-27-controlled-suite.md). Shared multi-cluster initialization and broader forecast/explanation contracts remain open. A shared seed does not guarantee shared starting states.
3. Add versioned raw supervised datasets, frozen split IDs, training-only preprocessing and held-out quality metrics. The existing target-filtered wine pipeline is descriptive preprocessing, not predictive evaluation.
4. Expand dataframe semantic, missing-value, mutation, layout and interoperability cases, then size/memory sweeps. Use pandas test patterns while retaining independent mathematical and semantic answers.
5. Add pinned neural weights and logits/cache/vision contracts, explicit precision/device reporting, synchronized MLX evaluation and separate checkpoint-quality datasets.
6. Integrate passing families into CI with tiered schedules. Keep known failures visible as diagnostics until corrected. Large research and performance runs must not turn into implicit correctness claims.

Kiraa remains an unofficial development reference with known bugs. It is neither an accuracy oracle nor a production baseline. No production algorithms changed in these dataset commits.

Engineering plans, evidence and this report belong only to codex/engineering-notes. The contribution branch contains fixture provenance, contracts, tests and usage documentation.
