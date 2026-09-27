# Controlled model, forecast, search and explanation conformance

## Required work order

The user's September 27 correction supersedes the earlier suggestion to repair ANOVA and PCA before expanding the suite. Finish the testing and certification branch first. Use a separate branch for production repairs, with one commit per distinct error. Establish the formal performance baseline only after those repairs pass the completed suite.

This increment completes the ten selected, controllable stage-3 fixtures. It does not complete the full dataset strategy. Production algorithms remain unchanged, and all timings from these conformance runs are diagnostic.

## Contribution and provenance

Commit `279c01433dfd76e6768c72c7af7d2950fa5d3944` is local on `codex/standardized-benchmarks`. It adds fixture generation, pinned manifests, worker adapters, contract tests and public usage documentation. It does not push that branch or create a PR.

All 332 source hashes in the uninstrumented Release build record match that commit. The source fingerprint is `dd49877297a7997dee9541f5b100e1ea6f6d4b5b84e1fa2e21cbbfa61085f388`. The build and run records retain the parent commit because verification preceded the commit; their complete source hashes identify the tested bytes. No production `Sources/` or `Tests/` files changed. Private engineering notes remain on their separate branch.

## Added coverage

- Supplied-weight linear and logistic inference, including returned parameters, all predictions, both class probabilities and the zero-logit decision boundary.
- One-cluster KMeans, checking the exact centroid, all training/query labels and inertia. This certifies the one-cluster solution, not common multi-cluster initialization.
- Scalar and constant-velocity Kalman filtering, checking every filtered mean and covariance and one subsequent prediction. Every repeat constructs fresh state.
- Exact cosine result identity, scores and closest-first ranking, including complete tie groups and identical small nonzero vectors. Workers check native descending order before normalizing tie order outside timing.
- Two-feature affine and interaction KernelSHAP, with exact exhaustive coalition references and every contribution checked. The declared missing-feature rule uses background column means.

Fixtures are original synthetic examples under the repository license. References use Fraction arithmetic or 80-digit Decimal probabilities. The Kalman reference uses an algebraically equivalent covariance recurrence independently of the runtime Joseph-form update. Runtime workers do not import the reference generators.

## Results

| Check | Result |
| --- | --- |
| Controller tests and fixture regeneration | 75 passed |
| Release worker build | Passed, coverage instrumentation disabled |
| Existing smoke suite | 28 of 28 engine cases passed; certificate audit passed |
| New controlled suite, SwiftSci | 7 of 10 passed |
| New controlled suite, Python adapters | 10 of 10 passed |
| Real-worker valid controls | 8 passed |
| Deliberately wrong outputs | 8 rejected |
| Malformed inputs | 8 rejected |
| Inputs containing leaked expected answers | 8 rejected |

The controlled run has 34 validated measured samples, from 17 passing processes with two samples each. Its overall record is failed, and the audit rejects it. Warmups are also checked. The run does not yield a passing certificate for the profile.

## Errors retained for the later repair branch

1. Supplied-weight CPU linear regression refuses prediction with `Model must be fitted before calling predict or transform.`
2. Supplied-weight CPU logistic regression refuses prediction with the same error.
3. Cosine search returns 0 rather than 1 for identical nonzero vectors of magnitude 1e-7.

Source review suggests the supplied-weight constructors leave the resolved device unset, causing prediction to select the unfitted MLX path. The cosine implementation applies an absolute norm-product threshold. These are diagnosis leads, not production changes in this commit. Treat each error separately when planning the repair commits.

Earlier ANOVA, PCA and ill-conditioned least-squares failures remain recorded in the preceding report. This increment did not rerun those profiles because their production implementations and adapters did not change. Existing fixture/controller coverage passed. Numerical conditioning must still be characterized before interpreting the strict Wampler coefficient failures as implementation defects.

## Scope boundaries and remaining suite work

Stage 4 remains next: versioned raw supervised data, frozen train/validation/test row IDs, training-only transformations, held-out predictions and independent quality metrics. A pass on small exact examples is not evidence of predictive quality.

Stage 5 expands dataframe semantics, missingness, mutation, memory layout and interoperability, followed by shape and memory sweeps. Stage 6 adds fixed neural weights, logits/cache checks and vision preprocessing with explicit precision and synchronized device execution. Stage 7 integrates profiles and CI schedules, including visible known failures and capability gaps. Complete these suite stages before production repairs and the formal performance baseline.

Shared multi-cluster initialization remains blocked by the absence of a public initial-centroids control. Broader sampled explanations, TreeSHAP background conventions, ARIMA/Holt-Winters initialization and trained checkpoint quality need separate contracts. They are not silently covered by this profile. Zero-vector cosine policy and mismatched dimensions are also outside the contract.

Kiraa remains an unofficial research reference with known bugs. It is not an oracle or a production baseline. The Python adapters here use direct arithmetic, NumPy or SciPy as declared by each workload; different algorithms are disclosed rather than presented as matched performance measurements.

## Review and evidence

Reviewer configuration was `gpt-5.6-sol`. The review found no blocking issue. Two missing evidence pointers in the decision trail were supplied in an appended row. No full transcript was available beyond the inherited summaries and saved artifacts.

Evidence lives under `Documentation/EngineeringNotes/archive/2026-09-27/suite-controlled/` on `codex/engineering-notes`. It includes immutable run plans, requests, responses, failed and passing records, build identity, all adversarial requests and results, test logs, source reviews and the decision trail. A content manifest binds every archived file. Run requests retain their original local paths for provenance; the committed profiles and generators are the portable rerun interface.
## Subsequent supervised checkpoint

The first stage-4 increment is now implemented in local commit `72a20129d4`. See [the supervised-suite report](2026-09-27-supervised-suite.md) for fixed splits, train-only preprocessing and passing held-out OLS checks. Classifier training is still pending. The suite-first order is unchanged.

