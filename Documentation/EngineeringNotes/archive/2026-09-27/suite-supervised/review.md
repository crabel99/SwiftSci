# Stage 4 supervised suite review

Reviewed the staged SwiftSci changes against `279c01433dfd76e6768c72c7af7d2950fa5d3944`. I found no blocking correctness, provenance, leakage, output-contract, or scope defect.

The staged change stays under `Benchmarks/`. It adds benchmark adapters and fixtures without changing production packages. The worker calls the public SwiftSci `StandardScaler`, CPU `LinearRegression`, and `Metrics` APIs. Input decoding occurs before timing. Each measured repeat gathers the frozen splits, creates fresh model state, fits on training rows, transforms all partitions with training statistics, predicts, computes metrics, and materializes the complete output.

The WDBC bytes match the pinned UCI hashes and byte counts. The captured UCI record states CC BY 4.0, and the staged attribution names the creators, source, license, and modifications. The existing red-wine bytes match their prior pin and attribution. Diabetes is absent from the staged files because the research record did not establish an original-data redistribution license.

I independently checked that every WDBC and wine input row maps exactly to its raw source, including IDs, predictors, targets, and the malignant = 1 mapping. The stored split indices and row IDs agree with the inputs. The SHA-256 partition is based only on predictor content and keeps duplicate wine predictor rows together. The three independent reference arrays reproduce exactly in memory with mpmath 1.4.1 at 80 decimal digits. The committed test also recalculates them at 120 digits and requires the same binary64 answers.

The numerical contract exports every scaler mean and scale plus every transformed row for both datasets. The OLS case also exports the intercept, coefficients, every training, validation, and test prediction, the training-target mean, and model and constant-predictor metrics for both held-out partitions. This is enough to catch wrong late outputs and to distinguish a correct scaler from OLS prediction invariance.

The completed evidence is consistent. The controller suite passed 83 tests. The Release worker has no coverage instrumentation and its recorded source-tree identity matches the run. All six supervised engine cases passed with twelve measured samples. The existing smoke profile passed all 28 cases. Direct worker checks passed six controls and six held-out perturbations, while both workers rejected all 24 altered-output, overlapping-split, duplicate-feature, and leaked-answer requests.

The documentation keeps the claims narrow. It calls the timings diagnostic, leaves the formal performance baseline for later, makes no deployment claim, sets no quality threshold from test results, and warns that a published split is not a fresh final evaluation set. WDBC classifier training, larger models, and production fixes remain outside this increment.

## Attention

reviewed by gpt-5.6-sol

- No full run transcript was available to this reviewer. I matched every decision-log row to staged code or a supplied artifact, but I could not check the transcript for an omitted pivot or abandoned approach.
- The review supports this suite increment only. It does not approve a production fix or a formal performance claim.
