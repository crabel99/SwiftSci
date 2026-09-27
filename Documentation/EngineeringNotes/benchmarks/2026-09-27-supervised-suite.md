# Frozen supervised splits and held-out conformance

## Work order and scope

This is the next testing-suite increment on `codex/standardized-benchmarks`. The user-required sequence remains suite first, then a separate production-repair branch with one commit per error, then the formal performance baseline.

Local commit `72a20129d4` adds licensed raw supervised data, duplicate-safe frozen train/validation/test splits, train-only standardization and complete held-out OLS checks. WDBC classifier training remains pending. This does not complete stage 4 or the full dataset strategy.

No production package changed. Every built source hash matches the committed source, as recorded in `commit-verification.json`. Verification preceded the commit, so run metadata retains the parent commit together with the exact tested source fingerprint. The contribution branch remains unpushed. Engineering notes and run evidence are kept only on `codex/engineering-notes`.

## Source decisions

WDBC original data and documentation are retained with UCI creator attribution and CC BY 4.0. All 569 records match the raw source, including original IDs, thirty predictors and malignant = 1 / benign = 0 labels. Original physical units are unspecified. IDs and labels never enter the predictor matrix.

The existing UCI red-wine source supplies 1,599 regression records and eleven predictors under CC BY 4.0. All original targets are included. The old target-filtered descriptive pipeline is unchanged and is not reused for predictive evaluation.

Diabetes stays outside the contribution. Its source is useful, but the research did not establish an original-data redistribution grant. The scikit-learn package license was not assumed to license data created by others. Research findings and pinned download identities remain in the private archive.

## Split and numerical contracts

A versioned SHA-256 partition uses canonical binary64 predictor content, without IDs or targets. Duplicate predictor rows stay together even when their targets differ. Train/validation/test counts are 959/298/342 for red wine and 328/115/126 for WDBC. Full frozen indices and source IDs are committed.

The actual StandardScaler fits only training rows. Every mean, effective scale and transformed row is checked. The wine model uses the public CPU LinearRegression fit and predict APIs, and actual SwiftOptimize Metrics calls. It exports all coefficients, every train/validation/test prediction, the training-target mean and each held-out metric. Swift can choose an analytical solver or fallback internally, so no identical-solver performance claim is made.

The independent reference uses mpmath 1.4.1 at 80 decimal digits on exact binary64 raw values. A second evaluation at 120 digits produces identical binary64 answers for every exported value. That demonstrates precision stability for these calculations, not agreement between two independently authored reference algorithms. Absolute tolerance 1e-8 and relative tolerance 1e-9 were fixed before the Swift run.

## Verification

| Check | Result |
| --- | --- |
| Controller, regeneration and precision tests | 83 passed |
| Uninstrumented Release build | Passed |
| Supervised cases across SwiftSci and Python | 6 of 6 passed, 12 measured samples |
| Existing smoke cases | 28 of 28 passed |
| Both run certificate audits | Passed |
| Real-worker controls | 6 passed |
| Held-out feature/target perturbations | 6 passed against recomputed independent answers |
| Invalid outputs, overlap, duplicate leakage and leaked answers | 24 rejected |

The perturbation checks require unchanged fitted parameters and training outputs while changing validation/test features and targets. Full expected output vectors then validate the changed held-out predictions in both workers. Aggregate metrics alone cannot pass this test.

The only whitespace warnings in the staged diff came from the unchanged upstream `wdbc.names` file. Those bytes were retained exactly. The rest of the staged diff passed the whitespace check. Existing untracked cloud-sync duplicate files were left alone.

## Held-out metrics

Both runtime implementations matched these independent values within the fixed tolerances:

| Split | Model RMSE | Model MAE | Model R-squared | Training-mean RMSE |
| --- | ---: | ---: | ---: | ---: |
| Validation | 0.652574 | 0.503679 | 0.365958 | 0.820085 |
| Test | 0.652287 | 0.498559 | 0.348924 | 0.809510 |

These results describe a fixed OLS model on a fixed split. No predictive-quality acceptance threshold was chosen from the test results. The public guide warns that repeated development against this published split does not make it a fresh final evaluation set. Timings are diagnostic; the formal performance baseline is still deferred.

## Next suite work

Finish supervised classification with a controlled training/probability contract and independent held-out metrics. Then continue dataframe semantic/layout/memory cases, fixed neural inference and CI/profile integration. Preserve existing failures for the later repair branch. Do not tune acceptance thresholds around observed implementation errors.

Kiraa remains an unofficial research reference and is not used as an accuracy oracle or production baseline.

## Review and archive

The gpt-5.6-sol review found no blocking issue and independently checked raw mappings, split identities, reference reconstruction, public API use and runtime evidence. A final appended log row records the 83-test count after the higher-precision test. No full transcript was available; review used saved artifacts and staged code.

Evidence is under `Documentation/EngineeringNotes/archive/2026-09-27/suite-supervised/` on the private notes branch. It includes a content manifest, source research, API review, run plans and responses, certificate audits, all worker rejection requests, test/build identities, the commit verification and decision trail. The committed benchmark profiles and generators are the portable rerun interface. Archived requests retain original local paths for provenance.
