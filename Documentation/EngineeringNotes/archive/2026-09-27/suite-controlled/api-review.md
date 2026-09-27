# Stage-three API review

Scope is suite construction only. Keep numerical failures visible, finish the testing and certification branch first, fix production errors later on a separate branch with one commit per error, and take a formal performance baseline after those fixes. No repository files or builds were changed by this review.

The immediate implementation pack selects four operations: fixed linear inference, fixed logistic inference, one-cluster KMeans, and controlled Kalman filtering. The two inference operations are expected to fail in current source. Exponential smoothing and two-feature KernelSHAP remain suitable follow-on fixtures.

## Fixed linear and logistic inference

Both public initializers accept weights, bias, and explicit `.cpu`. They store CPU coefficients but leave `resolvedDevice` unset and MLX parameters nil. Both prediction paths require `resolvedDevice == .cpu` to use CPU coefficients, then otherwise call an MLX prediction function that throws `modelNotFitted`. Relevant files are `Sources/SwiftML/Core/LinearRegression.swift`, initializer line 34 and prediction line 295, and `Sources/SwiftML/Core/LogisticRegression.swift`, initializer line 33 and prediction line 211.

```swift
let linear = LinearRegression(weights: [2, -1], bias: 3, device: .cpu)
let predictions = try await linear.predict(features: [[0,0],[1,2],[-2,4],[3,-1]])
// Intended exact predictions: [3,3,-5,10]. Keep current error visible.

let logistic = LogisticRegression(weights: [2, -1], bias: 0, device: .cpu)
let probabilities = try await logistic.predictProbability(features: [[0,0],[1,0],[0,2],[-1,1],[1,2]])
let labels = try await logistic.predict(features: [[0,0],[1,0],[0,2],[-1,1],[1,2]])
// Logits: [0,2,-2,-3,0]; labels use probability > 0.5: [0,1,0,0,0].
```

Use exact Fraction dot products for linear outputs and Decimal exponential arithmetic at 80 digits for logistic probabilities. Export parameters with `getWeightsAndBias`, complete prediction matrices, and labels. Do not call `fit` to make these cases pass, since that would replace the supplied parameter contract.

## One-cluster KMeans

`KMeans` accepts a seed, iteration limit, tolerance, and explicit device, but no initial centroids. Shared-start multi-cluster comparisons remain blocked until an API accepts initial centroids. Identical integer seeds in different libraries do not supply identical initial conditions. The CPU and GPU stopping rules also differ.

```swift
let model = try KMeans(nClusters: 1, maxIterations: 20, tolerance: 1e-6, seed: 42, device: .cpu)
try await model.fit(features: [[0,0],[0,2],[4,0],[4,2]])
let centroids = await model.getCentroids()
let labels = try await model.predict(features: [[0,0],[0,2],[4,0],[4,2]])
let queryLabels = try await model.predict(features: [[-1,3],[10,-9]])
```

Expected centroid is `[2,1]`, all labels are zero, and training inertia is 20. Export centroid, all training and query labels, and independently derived inertia. Use `getCentroids`; the CPU fit does not populate public MLX `centroids`. Assert the resolved device is CPU. A one-cluster case tests averaging and distance calculations, not initialization quality or general clustering quality.

## Controlled Kalman filtering

`KalmanFilter` exposes every required transition, observation, noise, initial-mean, and initial-covariance matrix through public setters. `filter` returns each full mean and covariance. `predict` returns one next-step mean and covariance without updating internal state. These APIs have no device selector and use CPU Accelerate operations.

```swift
let filter = try KalmanFilter(stateSize: 1, observationSize: 1)
try await filter.setTransitionMatrix([[1]])
try await filter.setObservationMatrix([[1]])
try await filter.setProcessNoise([[1]])
try await filter.setMeasurementNoise([[1]])
try await filter.setInitialState(mean: [0], covariance: [[1]])
let states = try await filter.filter(observations: [[1],[2],[3]])
let next = try await filter.predict()
```

Exact filtered mean/covariance pairs are `[2/3,2/3]`, `[3/2,5/8]`, and `[17/7,13/21]`; the next prediction is `[17/7,34/21]`. Add a two-state constant-velocity case with nonsymmetric transition `[[1,1],[0,1]]`, observation matrix `[[1,0]]`, quarter-identity process noise, unit measurement noise, initial mean `[0,1]`, unit initial covariance, and observations `[[1],[2],[4]]`. Its off-diagonal covariance checks matrix layout. Generate all answers with exact rational Kalman equations, using covariance subtraction rather than copying the source's Joseph-form computation. Reset by creating a new actor for every sample.

## Follow-on forecast and explanation operations

Simple exponential smoothing supports a fixed alpha without optimization:

```swift
let model = ExponentialSmoothing(method: .simple, alpha: 0.5)
try await model.fit(series: [2,4,8,10])
let result = try await model.forecast(horizon: 3)
```

With the initial level equal to the first observation, exact fitted values are `[2,2,3,11/2]`, residuals `[0,2,5,9/2]`, forecasts `[31/4,31/4,31/4]`, MSE `197/16`, and MAE `23/8`. Those 13 outputs form a small exact point-forecast check. Interval formulas require a separately declared approximation contract; this fixture would not certify uncertainty intervals. Auto-fitted smoothing and ARIMA need separate optimizer and initialization contracts.

KernelSHAP has an exact two-feature path with an explicit mean-imputation baseline:

```swift
let shap = KernelSHAP()
let phi = await shap.explain(
  model: { x in 2 + 3*x[0] - x[1] + x[0]*x[1] },
  instance: [3,5], background: [[0,0],[2,4]], numCoalitions: 4)
```

The background mean is `[1,2]`; coalition values are 5, 15, 5, 21, so expected attributions are `[13,3]`. This is explicitly mean-imputation SHAP. It is not the result of averaging predictions over the background distribution. For more than two features, the API has no seed or supplied coalition masks, uses random sampling and concurrent completion order, and therefore lacks controls for a shared-coalition exact comparison.

LIME can test an affine-model identity with zero regularization: `LIMEExplainer(kernelWidth: 2, regularization: 0).explain(model: { x in 2+3*x[0]-2*x[1] }, instance: [2,-1], numSamples: 32, featureScales: [1,1])` should return weights `[3,-2]`, centered intercept 10, prediction 10, and local R-squared 1 for a full-rank sampled design. Its RNG is internally fixed but has no public seed or supplied perturbations. General shared-neighborhood comparisons are blocked. Do not interpret the centered intercept as the global affine intercept 2.

TreeSHAP accepts `FlatTreeNode` arrays, but nodes contain no background population or node cover counts and `explain` has no background argument. A standard distribution-dependent TreeSHAP contract is therefore underspecified. Define that ownership and baseline first; do not silently certify the existing output as standard TreeSHAP.

## Verification status

The report is based on source inspection. No Swift fixture was run. The temporary implementation pack verifies independent numerical answers and comparator behavior separately. Current fixed-initializer failures must remain failures, and any timings collected while completing the suite are diagnostics only.
