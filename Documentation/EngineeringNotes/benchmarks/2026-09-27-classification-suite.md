# Controlled classifier training and scoring

## Scope and work order

Local commit `31b3cff290` extends the testing branch with controlled WDBC classification. It adds no production fixes and leaves the formal performance baseline deferred. Complete suite coverage first, then repair each error in a separate commit on the repair branch.

This completes the initial supervised data pack: frozen licensed data, duplicate-safe partitions, training-only preprocessing, held-out regression and controlled binary-classifier outputs. It does not complete the wider suite. Dataframe semantics, memory-layout cases, fixed neural inference and integrated CI coverage remain.

The contribution branch is unpushed. Engineering plans and evidence remain exclusively on `codex/engineering-notes`. Build records precede the commit but their complete source hashes match the committed bytes, verified in `commit-verification.json`.

## Training and reference decisions

The public CPU LogisticRegression API supports explicit epoch count and learning rate. The suite uses zero, one and 32 full-batch updates from zero weights and bias, with learning rate 0.125. This rate is exactly representable by Swift's Float parameter and avoids an implicit decimal-to-Float conversion mismatch. The boundary rejects nonbinary labels, unsupported controls, learning rates not exactly representable as Float32, and partitions missing either class.

The objective is mean unregularized binary cross-entropy. Standardization fits only training predictors. Every gradient uses the old parameters for all rows, then weights and bias update together. There is no early stopping, random shuffle, regularization or hyperparameter search. Zero updates tests initialization, the strict greater-than-0.5 label rule and tied scores. One update also has an independent closed-form gradient check. Thirty-two updates tests accumulated behavior without a convergence claim.

The high-precision reference directly implements sigmoid and gradients using mpmath. The runtime comparator uses NumPy matrix operations and SciPy sigmoid. The Swift adapter calls public fit, probability, prediction and metric APIs. Neither runtime imports reference code. Recalculation at 120 digits produces the same binary64 answers as the pinned 80-digit reference.

Each result exports means, scales, bias, every weight, both probabilities and every label for every row, and training-positive prevalence. Validation and test each contain model and constant-prevalence score blocks. Each block has TN, FP, FN, TP, accuracy, positive-label precision, recall, F1, log loss, ROC AUC and Brier score. The reference computes AUC using pairwise concordance and half credit for ties. The Python adapter uses average ranks; Swift integrates its grouped-tie ROC curve.

## Verified outcomes

| Check | Result |
| --- | --- |
| Controller tests | 89 passed |
| Release build | Passed without coverage instrumentation |
| Expanded supervised profile | All 12 engine cases passed, 24 measured samples |
| Core smoke profile | All 28 engine cases passed |
| Both certificate audits | Passed |
| Real-worker controls | 6 passed |
| Held-out label changes | 6 passed with unchanged model outputs |
| Altered probabilities, labels, scores and invalid inputs | All 36 rejected |

The negative requests use matching file hashes, so workers reject the actual wrong content instead of merely noticing a checksum mismatch. Held-out label inversions leave fitted parameters, all probabilities, all predicted labels and training prevalence unchanged. Only the held-out metric blocks change. No existing production error was repaired or hidden.

The reviewer independently observed maximum absolute classifier output errors of approximately 1.42e-14 for Swift and 2.27e-13 for the Python adapter. Acceptance remains the predeclared absolute 1e-8 and relative 1e-9 tolerance shared with the supervised fixtures. No tolerance was changed in response to the results.

## Held-out results for the fixed 32-update case

| Split | Accuracy | Positive recall | F1 | Log loss | ROC AUC | Brier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Validation | 0.939130 | 0.934783 | 0.924731 | 0.168114 | 0.982042 | 0.044357 |
| Test | 0.976190 | 0.960000 | 0.969697 | 0.143511 | 0.993684 | 0.037249 |

The constant training-prevalence predictor has ROC AUC 0.5 on both partitions. Its test accuracy is 0.603175, log loss 0.675711 and Brier score 0.241218.

These are scores for a defined finite computation on a published split. They do not establish a tuned model, convergence, medical utility or a quality acceptance threshold. Changing a threshold after inspecting these results would need a new held-out evaluation design. Timings are diagnostic and remain separate from the later formal performance baseline.

## Next work

Continue the dataframe semantic and layout pack: missing values versus NaN, sorting ties, grouping keys, mutation/copy isolation, type preservation, matrix extraction and shape/memory cases. Keep the already exposed numerical and API errors visible until the suite is complete. Then use the requested repair branch and one commit per error.

Shared initialization for general clustering, sampled explanation contracts and trained model quality remain capability boundaries. Kiraa remains an unofficial research reference, not a numerical oracle or production baseline.

## Evidence

The gpt-5.6-sol review found no blocking issue. Review used code, saved artifacts and task context; no complete transcript was available.

The archive is `Documentation/EngineeringNotes/archive/2026-09-27/suite-classification/` on the engineering-notes branch. It contains a content manifest, build identity, controller output, real-worker requests and responses, passing certificates and audits, independent review, decision trail and commit identity. Committed profiles and generators provide portable reruns; archive requests retain the original local paths.
