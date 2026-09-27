# Classification suite review

Reviewer configuration: `gpt-5.6-sol`

Base commit: `72a20129d43771dc22a02e3cfc2529af22eb8c3e`

## Verdict

I found no release blocker in the 27 staged files. The diff extends the benchmark suite only. It contains no staged change under `Sources/`, so it does not hide a production fix inside the conformance work.

The three WDBC cases consistently define zero, one, and 32 full-batch updates from zero weights and bias. The learning rate is 0.125, which survives the public Swift API's `Float` conversion exactly. The high-precision reference, NumPy and SciPy comparator, and Swift worker use the same mean unregularized binary cross-entropy update. Their implementations are separate.

The output contract covers training-only means and scales, every fitted parameter, both probabilities and the label for every row, training prevalence, and 44 validation and test scores. Confusion counts use TN, FP, FN, TP order. Probability 0.5 maps to class zero. Precision returns zero when the model predicts no positives. ROC AUC gives ties half credit. The zero-update case exercises all three rules directly.

Input validation rejects unknown training fields, Boolean or out-of-range epoch counts, nonpositive or inexact learning rates, nonbinary targets, and partitions missing either class. Both runtimes fit scaling and model parameters from training rows only. Held-out label changes leave every model output unchanged and alter only the 44 held-out score values.

The reference records bind the raw source, generated input, and expected output by SHA-256 and byte count. Regeneration checks every derived byte. The 80-digit reference produces the same binary64 values at 120 digits. The README limits the claim to finite-step numerical conformance. It does not claim convergence, tuning, clinical utility, or a performance baseline.

## Evidence checked

- `controller-tests-final.log`: 89 tests passed in 12.061 seconds. These include the closed-form first update, metric ties, zero denominators, strict controls, regeneration, leakage checks, complete-output mutations, and 120-digit stability.
- `results.json`: all 12 supervised engine cases passed with 24 validated samples. All 28 smoke engine cases also passed.
- Release Swift classification samples had a maximum absolute error of `1.4210854715202004e-14`. Python comparator samples had a maximum absolute error of `2.2737367544323206e-13`.
- `negative-workers/summary.json`: six control runs and six held-out-label variants passed. All 36 requests with a wrong probability, label, score, invalid training control, single-class partition, or leaked answer failed. SwiftSci and pandas each passed six and rejected 18.
- `git diff --cached --check` passed. The staged base remained `72a20129d43771dc22a02e3cfc2529af22eb8c3e` during review.

The formal performance baseline and any production error fixes remain separate work, as the plan requires.

## Attention

reviewed by gpt-5.6-sol

No flags.
