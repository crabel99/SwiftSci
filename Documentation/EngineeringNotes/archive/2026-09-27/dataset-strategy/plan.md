# Dataset strategy implementation

The full program remains active until each listed family has an implemented, verified contract or an explicit capability blocker. A completed stage is not completion of the entire strategy. Work starts from d05b9f02fe on codex/standardized-benchmarks. Plans and evidence stay on engineering-notes.

- [x] Read Principles and recover the approved dataset strategy.
- [x] Frame the first stage: certified NIST regression and balanced ANOVA plus reusable numerical fixture validation.
- [x] Stage 1: original source provenance, input schemas, independent numerical answers, explicit CPU OLS and ANOVA workers; verify references and actual outputs.
- [x] Stage 2: known-spectrum PCA and exact Naive Bayes. Validate invariants and every output; keep quality metrics separate.
- [ ] Stage 3: shared-initialization clustering and fixed inference, forecasting, vector-search and explanation fixtures.
- [ ] Stage 4: pinned raw supervised datasets and split manifests; training-only preprocessing; held-out model-quality checks.
- [ ] Stage 5: dataframe semantics and interoperability coverage, pandas-derived workloads, memory/layout/size sweeps.
- [ ] Stage 6: pinned neural weights, logits/cache/vision checks, explicit device and precision contracts; trained-model quality profiles when compatible checkpoints are available.
- [ ] Stage 7: integrated profiles, cross-model review, documentation and contribution validation.

Every stage needs independent expected results, failure tests, real worker execution, immutable evidence and a separate implementation commit. Unmet tolerance remains a failure; it must not become a success by relaxing the target after observing outputs. Public docs explain usage and provenance; private reports record decisions. New API requirements and algorithm differences remain explicit.

Stage 1 coverage is implemented and exercised. It exposes eight failing SwiftSci cases per reference basis, so this is not a passing numerical certification. Algorithm repairs are separate from adding trustworthy evidence.

Stage 2 executed both workers on all three exact fixtures. Five of six checks pass. Truncated SwiftSci PCA fails the declared total-variance ratio contract. Remaining stages are still pending.
