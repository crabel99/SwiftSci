# Classifier adapter integration

Copy `SwiftClassifierWorkloads.swift` into `Benchmarks/Worker`.

Add `SupervisedFixtureInput.Training: Decodable` with `epochs: Int` and `learning_rate: Double`, and add `training: Training?` to `SupervisedFixtureInput`. Require the training object for classifier operations and reject it for the existing scaling and OLS operations. Require exactly those two training keys. Reject Boolean values masquerading as numbers, negative epochs, and nonfinite or nonpositive learning rates. The suite's fixed cases use epochs 0, 1, and 32 and learning rate 0.125.

After the existing train-only scaler fit and output checks, dispatch classifier operations with:

```swift
return try await executeSupervisedClassifier(
  input: input, means: means, scales: scales, scaled: scaled, targets: targets)
```

The parent chooses and validates the classifier operation identifier. Extend the numerical-input dispatch operation list accordingly. Require binary labels and both classes in each split. Keep the existing nonempty, disjoint, exhaustive split checks, finite rectangular feature checks, unique row IDs, and duplicate feature-row leakage check.

The output contains, in order:

1. Feature means and scales, each of length p.
2. Bias, then p weights.
3. Every row's probability pair `[p0, p1]`, in train, validation, test order.
4. Every predicted label, in the same split order.
5. Training positive-label prevalence.
6. Validation model metrics, validation prevalence-baseline metrics, test model metrics, test prevalence-baseline metrics.

Each metric block is `[TN, FP, FN, TP, accuracy, precision, recall, F1, logLoss, rocAUC, brierScore]`. Precision, recall, and F1 use label 1. Log loss uses epsilon 1e-15. Both model and baseline labels use strict `p > 0.5`. The total length is `3*p + 3*n + 46`.

The adapter fits only `scaled[0]` with `targets[0]`. Validation and test targets enter scoring only. The prevalence baseline uses only training targets. The parent preprocessing code fits the scaler on training features only.

# Source findings and verification

All source paths below are relative to `/Users/crabel/Documents/src/SwiftSci`.

- `Sources/SwiftML/Core/LogisticRegression.swift:61` exposes the Float learning-rate fit API. Line 84 converts it to Double for CPU training. Using 0.125 makes the conversion exact.
- `LogisticRegression.swift:96` implements CPU fitting. Lines 100-101 initialize zero weights and bias. Lines 116-127 average full-batch gradients. Lines 134-137 apply the update with no regularization. Epoch zero retains the initialized parameters.
- `LogisticRegression.swift:41` exposes the original Double CPU weights and bias. The adapter uses this accessor rather than the Float MLX copies at lines 143-144.
- `LogisticRegression.swift:211` uses the CPU Double parameters for prediction. Line 236 exposes `[1-p, p]` probability pairs. Line 287 applies strict `p > threshold`, so a probability of 0.5 predicts class 0.
- `Sources/SwiftOptimize/Metrics/Metrics.swift:45`, `:57`, `:70`, and `:83` define accuracy, precision, recall, and F1. Precision, recall, and F1 return zero for their zero denominators.
- `Metrics.swift:180` computes mean binary log loss with explicit clipping. Line 196 computes mean squared probability error for Brier score.
- `Metrics.swift:207` builds ROC points, grouping equal scores at lines 221-222. Line 233 integrates trapezoids. All tied scores produce ROC AUC 0.5 when both classes occur. A single-class input returns zero, so the fixture decoder and adapter require both classes.
- No public confusion-count function appears in `Metrics`. The adapter counts the four cells directly, using `2*truth + prediction` to preserve `[TN, FP, FN, TP]` order. It calls the public Metrics API for every other metric.

`swiftc -frontend -parse` passed for the adapter. A Swift interpreter probe ran the actual Metrics source and passed checks for all-tied AUC 0.5, mixed-tie AUC 0.875, precision/recall/F1 zero-denominator behavior, log loss at p=0.5, finite endpoint-clipped loss, and Brier score 0.25. The integrated worker still needs its normal build and WDBC comparison runs. No production model or metric edits were made.

No metric mismatch was found in these probes. Source inspection found that CPU fit and prediction do not validate all array dimensions themselves. Strict fixture decoding and the adapter's shape checks prevent malformed fixtures from reaching those loops.
