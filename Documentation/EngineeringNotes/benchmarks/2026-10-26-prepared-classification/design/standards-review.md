# Standards review — updated source

## Findings

No actionable Standards-axis findings.

The prior P1 is resolved. `ClassificationPipeline` now follows the documented Tier C model: one private `NSLock` protects its transformer configuration, fitted schema, lifecycle flags, active-prediction count, and configuration generation. Fit and prediction take local snapshots while locked and perform transformation and asynchronous estimator work after releasing the lock. Fits exclude other fits and active predictions; predictions reject an active or invalidated fit. Configuration changes invalidate an existing fit, increment a generation, and prevent an in-flight fit from committing stale transformer state. Every begun operation balances its lifecycle state with `defer`, including throwing and cancellation paths.

`ClassificationPipelineConcurrencyTests` meaningfully covers row and prepared overlap, competing fits, both prediction routes during fit, configuration changes during a suspended fit, stale-commit rejection and recovery, concurrent prediction snapshots, getter copy behavior, and legacy NaN imputation. The implementation holds no lock across `await`, and the tests use gates rather than timing assumptions.

The remaining reviewed changes continue to meet the stated standards: public additions have DocC comments; `LogisticRegression` remains actor-isolated and atomically publishes one fitted state; CPU reference tests pin independently generated 0/1/32-epoch parameters and probabilities; row/prepared parity, Float GPU tolerances, cancellation, schema, threshold, soft-target, zero-feature, and compatibility contracts have focused coverage. The shared row/column logistic implementation removes duplication without adding speculative public structure. No material Fowler smell was introduced.

Runtime validation remains pending the parent task's final run; this re-review made no build or runtime-pass claim.
