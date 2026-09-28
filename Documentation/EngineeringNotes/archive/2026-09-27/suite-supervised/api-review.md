# Stage 4 supervised API review

Reviewed SwiftSci at `/Users/LOCAL_USER/Documents/src/SwiftSci`, HEAD `279c01433dfd76e6768c72c7af7d2950fa5d3944`. This was a source review. No repository files were edited and no new Swift code was compiled or executed. This report belongs in temporary working material, outside the contribution branch.

The first useful increment is raw Diabetes input, persisted train/validation/test row IDs, an actual `StandardScaler` fitted only on training rows, and actual CPU `LinearRegression.fit` and held-out `predict` calls. Compare every held-out prediction against an independent high-precision least-squares reference. Return fitted scaler parameters as well, since OLS predictions can stay unchanged under invertible changes of feature scale and cannot prove that preprocessing is correct by themselves.

## Source locations and exact semantics

All paths below are relative to the reviewed SwiftSci root.

### StandardScaler

`Sources/SwiftPreprocessing/Core/StandardScaler.swift`:

- Lines 32-41 define a public value-type `StandardScaler` with `public private(set) var mean: [Double]?` and `std: [Double]?`.
- Line 49 defines `public mutating func fit(_ data: [[Double]]) throws`.
- Lines 50-59 reject empty input, zero columns, and ragged rows.
- Lines 68-84 compute column means using vDSP, then sum squared deviations and divide by the row count. This is population variance, `ddof = 0`. The stored scale is `sd < 1e-12 ? 1.0 : sd`. The comparison is strictly less than; exactly `1e-12` is retained.
- Lines 87-90 overwrite the fitted mean and scale. `fit` does not mutate the caller's input matrix.
- Line 100 defines `public func transform(_ data: [[Double]]) throws -> [[Double]]`. It reads fitted parameters, creates a fresh matrix, and returns `(x - mean) / std`. The input and fitted parameters remain unchanged.
- Lines 106-117 throw if unfitted, return `[]` for empty input after the fitted check, and reject wrong feature widths.
- Line 133 defines `public mutating func fitTransform(_ data: [[Double]]) throws -> [[Double]]`.

There is no finite-value check. NaN or infinity may propagate through fitted statistics and output. A benchmark decoder must reject them before timing. Use a fresh `var scaler` for each sample. Do not use `fitTransform` on validation or test rows, because it would overwrite the training statistics.

A constant training column gets scale 1 and becomes zero in the training transform. A different held-out value becomes its difference from the training mean. Do not replace every held-out value in a constant training column with zero.

### LinearRegression

`Sources/SwiftML/Core/LinearRegression.swift`:

```swift
public actor LinearRegression: RegressorEstimator
public init(device: ExecutionDevice = .auto)                 // line 25
public func fit(features: [[Double]], targets: [Double]) async throws // line 51
public func fit(
    features: [[Double]], targets: [Double],
    learningRate lr: Float = 0.01, epochs: Int = 1000
) async throws                                             // lines 62-67
public func predict(features: [[Double]]) throws -> [Double] // line 290
public func getWeightsAndBias() -> (weights: [Double]?, bias: Double?) // line 42
public func getWeights() -> [Double]?                       // line 341
public func getBias() -> Double?                            // line 348
```

These actor methods require `await` from the worker, including methods without `async` in their declaration. `requestedDevice` is public immutable state; `resolvedDevice` is public read-only state at lines 15-17.

The CPU fit first attempts analytical least squares at lines 97-102. The solver appends a column of ones, requires `n >= p + 1`, and invokes Accelerate `dgels_` in double precision at lines 106-159. The last solution element is the intercept. There is no regularization, target scaling, or random initialization in this path. Learning rate and epochs affect only the fallback. `dgels_` is a full-rank least-squares solver; a rank-deficient fixture needs separate handling and is outside this first increment.

Every analytical error triggers full-batch gradient descent. There is no public solver-name or fallback flag. Gradient descent starts from all-zero weights and bias, makes exactly `epochs` updates, and minimizes mean squared error using factor `2/n` at lines 176-220. No shuffle, RNG, early stopping, or seed is involved.

After a successful fit, double-precision CPU weights and bias are available through the getters. Public MLX weights and bias are also created, but they are narrowed to Float at lines 164-166. Use the getters and `predict(features:)` for double-precision output. The CPU prediction branch at lines 295-303 requires `resolvedDevice == .cpu`.

The top-level fit checks only that the two outer arrays are nonempty. It does not enforce equal row and target counts, equal row widths, or finite data. Invalid input can crash instead of throwing. Validate the complete fixture before calling it. CPU prediction likewise indexes each row using the fitted width without shape validation.

`fitCPUGradientDescent` is public, but calling it directly does not assign `resolvedDevice`. Use the ordinary `fit` entry point for this suite.

### Explicit CPU routing and dependency caveat

`Sources/SwiftPreprocessing/Core/HardwareRouter.swift:19-29` returns an explicit `.cpu` request unchanged. Automatic routing for both regressions switches at 1,000 rows at lines 39-40. Always pass `.cpu` and verify `await model.resolvedDevice == .cpu` after fitting.

The regression implementations are under `#if os(macOS)` and import MLX. Even a CPU fit creates MLXArray compatibility state. This is a CPU numerical workload with existing MLX dependencies, not proof of a dependency-free or GPU-resource-free process. No production changes are needed to use it.

### LogisticRegression for a later increment

`Sources/SwiftML/Core/LogisticRegression.swift`:

```swift
public init(device: ExecutionDevice = .auto)                // line 24
public func fit(features: [[Double]], targets: [Double]) async throws // line 50
public func fit(
    features: [[Double]], targets: [Double],
    learningRate lr: Float = 0.1, epochs: Int = 1000
) async throws                                             // lines 61-66
public func predictProbability(features: [[Double]]) async throws -> [[Double]] // line 236
public func predict(features: [[Double]]) async throws -> [Int] // line 271
public func predict(features: [[Double]], threshold: Float = 0.5) throws -> [Int] // line 281
public func getWeightsAndBias() -> (weights: [Double]?, bias: Double?) // line 41
```

CPU training at lines 96-145 is deterministic, zero-initialized, unregularized full-batch gradient descent. It runs exactly the requested epoch count. The gradient uses `1/n`. The public learning rate is Float and is widened to Double, so the reference must use the same binary32-rounded rate. An explicit `Float(0.125)` is exactly representable and avoids decimal-rate ambiguity; it is a proposal, not a tuned or validated WDBC configuration. Freeze the rate and epoch count using training and validation data before evaluating the test split.

`Sources/SwiftML/Core/Numerics.swift:8-10` implements sigmoid by clamping logits to `[-50, 50]`, then evaluating `1 / (1 + exp(-z))`. The CPU classifier calls this at training and prediction. It does not use an unclamped expit on extreme negative logits.

The probability output is `[probabilityClass0, probabilityClass1]` for each row, in that order. Labels use strict `p1 > Double(threshold)`, so equality at 0.5 yields class 0. Getters retain CPU Double parameters; MLX public fields narrow to Float.

For WDBC, exclude the patient ID and diagnosis from the 30 feature columns, retain IDs only as metadata, define the diagnosis encoding in the fixture, and preserve it across all workers. A reasonable explicit convention is malignant = 1 and benign = 0. Stratify the frozen splits and check both classes occur in each split. Do not presume the encoding of a third-party dataset loader matches this convention.

A default scikit-learn LogisticRegression fit is not an equivalent oracle. It uses different optimization and regularization choices. A same-library CPU/GPU comparison also cannot establish correctness. A later reference should independently compute the fixed number of full-batch updates at high precision with the specified clamp, zero initialization, and effective learning rate. A separate converged optimizer can assess quality, but its coefficients are not the expected coefficients for finite-epoch gradient descent.

### Existing supplied-weight problem remains visible

Both constructors accepting weights and bias set only `cpuWeights`, `cpuBias`, and `requestedDevice`. They leave `resolvedDevice`, MLX weights, and MLX bias unset. See LinearRegression lines 34-38 and LogisticRegression lines 33-37. Their array prediction methods fall through to the MLX route when `resolvedDevice` is nil, then report an unfitted model.

The existing fixed-inference adapters are at `Benchmarks/Worker/ControlledAPIWorkloads.swift:98-118`. Leave their behavior and failures intact. A training adapter creates a new model and calls fit on training data. Do not patch supplied-weight initialization, fit dummy data into that adapter, replace model predictions with a hand-coded dot product, or relabel a workaround as fixed inference.

## Metrics that can be exercised

`Sources/SwiftOptimize/Metrics/Metrics.swift` exposes static functions with `yTrue` and `yPred` arguments:

| Metric | Line | Behavior relevant to this suite |
| --- | --- | --- |
| `meanSquaredError` | 278 | Sum of squared errors divided by row count |
| `rootMeanSquaredError` | 288 | Square root of the above MSE |
| `meanAbsoluteError` | 297 | Sum of absolute errors divided by row count |
| `r2Score` | 339 | `1 - SSE/SST`, with held-out target mean; constant targets return 0 |
| `accuracy` | 45 | Fraction of equal labels |
| `precision`, `recall`, `f1Score` | 57, 70, 83 | Explicit `label`; zero denominators yield 0 |
| `logLoss` | 180 | Binary class-1 probabilities, clipped to `[eps, 1-eps]`; default eps is `1e-15` |
| `brierScore` | 196 | Mean squared error of binary target and class-1 probability |
| `rocAUC` | 233 | Trapezoidal ROC integration with score ties grouped |

Several metric APIs return zero for malformed or empty arrays; precision and recall silently use the shorter zip. The adapter must reject malformed output before calling metrics. For a first regression case, emit RMSE, MAE, and R2 for each held-out split in addition to all predictions. Independently recompute the metrics from the actual returned predictions to separate metric correctness from model error.

## Minimal adapter design

Use one typed supervised fixture containing raw training, validation, and test matrices and targets, feature names in fixed order, and distinct row IDs. Record and verify source and split hashes. Preserve raw Diabetes units; do not start from already globally standardized features. The source conversion and split generator need their own tests. Dataset downloading and parsing stay outside the timed worker sample unless the workload explicitly includes ingestion.

Before timing, validate dimensions, finite values, unique and disjoint IDs, split coverage, nonempty splits, expected feature counts, and `nTrain >= p + 1`. Certify full rank and report a condition estimate in reference metadata. Validate the expected vector layout and length. A new sample creates fresh scaler and model instances, then times fit, all transforms, actual model fit, prediction, and the declared metric calls. Expected-file generation and reference comparison remain outside timing.

The existing worker already imports and links the needed modules through `Package.swift:438-440`. `Benchmarks/Worker/NumericalWorkloads.swift:96-111` shows the existing actual OLS adapter and getter usage. Its current predictions are in-sample only. `Benchmarks/Worker/main.swift:67-138` runs warmups and samples, times execution, then compares returned values against expected values.

A benchmark-only adapter can follow this sketch. `input` is assumed to have passed the validations above. The sketch is intentionally not a compiled patch.

```swift
import SwiftPreprocessing
import SwiftML
import SwiftOptimize

var scaler = StandardScaler()
try scaler.fit(input.trainFeatures)
let train = try scaler.transform(input.trainFeatures)
let validation = try scaler.transform(input.validationFeatures)
let test = try scaler.transform(input.testFeatures)
guard let means = scaler.mean, let scales = scaler.std else {
    throw BenchmarkFailure("Missing fitted scaler parameters")
}
let model = LinearRegression(device: .cpu)
try await model.fit(
    features: train, targets: input.trainTargets,
    learningRate: 0.01, epochs: 1000)
guard await model.resolvedDevice == .cpu else {
    throw BenchmarkFailure("Supervised regression did not resolve to CPU")
}
let validationPrediction = try await model.predict(features: validation)
let testPrediction = try await model.predict(features: test)
let parameters = await model.getWeightsAndBias()
guard let weights = parameters.weights, let bias = parameters.bias,
    weights.count == means.count,
    validationPrediction.count == input.validationTargets.count,
    testPrediction.count == input.testTargets.count else {
    throw BenchmarkFailure("Invalid supervised regression output dimensions")
}
let validationMetrics = [
    Metrics.rootMeanSquaredError(yTrue: input.validationTargets, yPred: validationPrediction),
    Metrics.meanAbsoluteError(yTrue: input.validationTargets, yPred: validationPrediction),
    Metrics.r2Score(yTrue: input.validationTargets, yPred: validationPrediction),
]
let testMetrics = [
    Metrics.rootMeanSquaredError(yTrue: input.testTargets, yPred: testPrediction),
    Metrics.meanAbsoluteError(yTrue: input.testTargets, yPred: testPrediction),
    Metrics.r2Score(yTrue: input.testTargets, yPred: testPrediction),
]
let values = means + scales + [bias] + weights
    + validationPrediction + validationMetrics + testPrediction + testMetrics
guard values.allSatisfy(\.isFinite) else {
    throw BenchmarkFailure("Nonfinite supervised regression output")
}
return .values(values)
```

Append transformed validation and test values if the first operation must independently certify the transform arithmetic itself. Returning means and scales certifies fit semantics, while a distinct scaler-only case can test the complete transform output without making the OLS vector large. A constant and near-constant training-column microfixture should test the `1e-12` rule separately from the public dataset.

The ordinary API does not expose whether its analytical solver or fallback completed. Report this as CPU fit with analytical OLS first, and verify its result against OLS. If strict exclusion of successful GD fallback is required, `epochs: 0` makes a fallback retain zero weights and intercept, which will fail a nontrivial Diabetes reference. This is a benchmark-only control through the existing API, but it must be declared and reviewed explicitly. It still is not a solver-path trace. Do not claim that `resolvedDevice == .cpu` alone proves use of `dgels_`.

## Independent reference and acceptance

Generate expected values from frozen source bytes and split IDs with a separate high-precision implementation, for example mpmath at 80 decimal digits. Convert the parsed binary64 values exactly through their integer ratios, so the reference certifies the same numeric inputs Swift receives. Compute training means and population standard deviations independently, apply the same scale floor, append the intercept column, and solve the rectangular least-squares problem using high-precision QR. Avoid ordinary-precision normal equations, which square the condition number.

Record the high-precision residual, rank evidence, condition estimate, tool versions, source hashes, split hash, feature order, output layout, and precision in reference metadata. Regenerate at higher precision, such as 120 digits, and require stability well below the declared Float64 tolerance. An independent NumPy or SciPy SVD solve is a useful second check, but it should not be the sole high-precision oracle.

Use the reference scaler and coefficients to generate every validation and test prediction. Verify raw-space coefficients `wRaw[j] = wScaled[j] / scale[j]` and `bRaw = bScaled - sum(wScaled[j] * mean[j] / scale[j])` as a second formulation. Compare the full prediction arrays, scaler parameters, coefficients, and metrics with predetermined tolerances. Coefficient tolerance may need to account for conditioning; do not loosen prediction tolerance to hide coefficient drift. Choose tolerances from numerical analysis and observed high-precision stability, then freeze them before benchmark runs.

Also compute RMSE, MAE, and R2 independently from Swift's actual predictions. This catches a metrics implementation defect even when a model differs slightly within prediction tolerance. Scalar quality scores alone cannot certify training, scaling, or row order.

Keep validation and test separate. For the fixed OLS increment there are no tuned training hyperparameters. Report both held-out sets without refitting. If a later workflow selects parameters on validation, freeze that choice before test evaluation and declare whether a new model fits train only or train plus validation. Never reuse old scaler statistics after a declared refit.

The first increment does not need WDBC training. Reserve its raw dataset and split contracts now, then add actual classifier fitting when the independently controlled finite-epoch reference and probability checks are ready.

## Implemented temporary adapter

The parent task subsequently selected existing licensed wine data for the first fit case and requested a concrete helper. `/private/tmp/swiftsci-suite-stage4/SupervisedWorkloads.swift` now contains `SupervisedFixtureInput.decode` and `Worker.executeSupervised`. It is separate from this review and has not changed SwiftSci production code.

The decoder accepts exactly `operation`, `row_ids`, `feature_names`, `features`, `targets`, and `splits`. Nested split fields are exactly `train`, `validation`, and `test`. It rejects malformed shapes, nonfinite values, empty or repeated IDs and feature names, incomplete or overlapping row partitions, and any identical feature row assigned to different partitions. Both operations require more training rows than features. OLS also requires varying validation and test targets so R2 is defined.

`supervised-scale` returns means, scales, and all scaled rows in train, validation, test order. `supervised-ols-cpu` returns means, scales, bias, weights, predictions in train, validation, test order, training-target mean, six validation scores, then six test scores. Each score block is model RMSE, MAE, R2 followed by constant-training-mean RMSE, MAE, R2. These scores use actual `SwiftOptimize.Metrics` functions. OLS uses the default public fit controls; it does not use the optional zero-epoch fallback control discussed above.

The helper passed `swiftc -frontend -parse`. Module type checking, integration, and actual numerical runs remain for the parent task. No expected values or oracle generation code are embedded in this helper.
