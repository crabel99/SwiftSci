# Controlled classifier conformance

- [x] Read the workflow principles and current suite contracts.
- [x] Confirm explicit CPU training controls and public scoring functions.
- [x] Add WDBC checkpoints at zero, one and 32 full-batch updates from zero weights with exactly representable learning rate 0.125.
- [x] Compute independent high-precision coefficients, both probabilities, labels, confusion counts and held-out metrics; test ties and undefined precision rules.
- [x] Verify input boundaries, repeat isolation, held-out leakage, real workers and reference precision stability.
- [x] Review, commit suite-only changes and archive evidence on engineering-notes.

Done means all declared outputs are independently checked and malformed requests fail. Retain production failures if exposed. No quality threshold is selected from test scores. Existing production defects remain for the separate repair branch. Fixed training controls describe a finite update procedure, not convergence or a tuned classifier.

Verified local suite commit: `31b3cff290`. The initial supervised pack now has regression and controlled binary classification. The full strategy remains in progress; dataframe semantics/layout coverage is next. No production fix or formal performance baseline was included.
