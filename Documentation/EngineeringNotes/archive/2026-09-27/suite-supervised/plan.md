# Supervised dataset contracts

- [x] Read the figure-it-out workflow and poteto principles.
- [x] Frame the work. Suite only; production fixes remain deferred.
- [x] Verify and vendor small raw supervised sources with license and exact provenance.
- [x] Freeze train/validation/test identities and training-only preprocessing.
- [x] Add independent full-output references and public worker adapters for supported deterministic models.
- [x] Test regeneration, leakage, malformed inputs, altered expected outputs and real Release workers.
- [x] Review with a separate model, commit the verified suite increment, archive private evidence separately.

The first target is raw Diabetes regression and Wisconsin diagnostic breast cancer preprocessing. Fit/predict contracts will only be included when deterministic, mathematically defined and independently checkable. Do not invent a model-quality threshold after inspecting test results. Numerical conformance and comparison with a training-only constant predictor are separate from general quality claims. Unsupported classifier training controls must be recorded for follow-up.

Done means raw sources and derived artifacts are hash-pinned, split IDs are disjoint and exhaustive, preprocessing uses only training features, all declared outputs have independent references, and invalid worker requests fail. The formal performance baseline remains deferred until the suite and subsequent repairs are complete.

The first supervised increment is verified in local commit `72a20129d4`. Licensed WDBC preprocessing and red-wine OLS replace Diabetes for now because its original-data redistribution license remains unestablished. Classifier training and an independently controlled probability/metric contract remain the next supervised increment. The full strategy is not complete. No production errors were repaired and no formal performance baseline was established.
