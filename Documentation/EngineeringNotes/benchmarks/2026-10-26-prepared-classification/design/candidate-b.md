# Candidate B: route-specific packing with atomic fitted state

## Usage (caller's view)

The prepared workflow starts with one snapshot that contains features and target. Row selection happens before the split, so repeated rows, row order, and source identities stay aligned.

```swift
let snapshot = try frame.prepareNumericBatch([
    "radius", "texture", "perimeter", "diagnosis"
])
let observations = try PreparedSupervisedBatch(
    snapshot,
    targetColumn: "diagnosis"
)

let training = try observations.selectingRows(trainingRows)
let heldOut = try observations.selectingRows(validationRows)

let model = LogisticRegression(device: .cpu)
let pipeline: any ClassifierEstimator = ClassificationPipeline(
    transformers: [StandardScaler()],
    estimator: model
)

try await pipeline.fit(training)

let probabilities = try await pipeline.predictProbability(
    features: heldOut.features
)
let labels = try await pipeline.predict(features: heldOut.features)
```

Callers that need the configurable logistic controls use the native estimator directly. Zero epochs is a supported fit, not a validation error.

```swift
let model = LogisticRegression(device: .cpu)
try await model.fit(
    features: training.features,
    targets: training.targets,
    learningRate: 0.1,
    epochs: 0
)

let p = try await model.predictProbability(features: heldOut.features)
let labels = try await model.predict(features: heldOut.features, threshold: 0.5)
// Every zero-epoch p is [0.5, 0.5]. Strict p1 > threshold makes every label 0.
```

Existing conformers and callers keep working. A classifier that implements only row-array methods receives one compatibility conversion. Its existing unsupported-probability error also remains intact.

```swift
let legacy: any ClassifierEstimator = ExistingClassifier()
try await legacy.fit(training) // default converts training.features once to rows
let labels = try await legacy.predict(features: heldOut.features)
```

The existing admission types wrap the whole prepared operation when the application has measured a suitable peak estimate.

```swift
try await pipeline.fit(
    training,
    budget: sharedBudget,
    estimate: trainingPeak
)
let probabilities = try await pipeline.predictProbability(
    features: heldOut.features,
    budget: sharedBudget,
    estimate: predictionPeak
)
```

The existing `fit(_:features:target:)`, row-array fit, label prediction, and probability prediction calls remain available. A row-fitted or persisted logistic model has no named schema and therefore continues to interpret prepared columns by position.

## Problem

Classification currently loses prepared column storage, names, validity, and source-row alignment at the estimator boundary. The pipeline also lacks the prepared regression pipeline's schema checks and failed-refit rule. Logistic regression complicates the change because CPU training is ordered Double arithmetic while GPU training is Float MLX autodiff, `.auto` routing depends on row count, and the actor currently publishes `resolvedDevice` before training can fail. The design must add prepared dispatch without changing classifier output choices, epoch order, the strict `probability > threshold` rule, the deliberate zero-epoch result, or legacy classifier conformance.

## Shape

### Public classifier contract

Prepared methods become protocol requirements so existential calls reach native implementations. Defaults adapt to the existing row requirements. They do not introduce a second classifier hierarchy.

```swift
public protocol ClassifierEstimator: Sendable {
    func fit(features: PreparedNumericBatch, targets: [Double]) async throws
    func predict(features: PreparedNumericBatch) async throws -> [Int]
    func predictProbability(features: PreparedNumericBatch) async throws -> [[Double]]

    func fit(features: [[Double]], targets: [Double]) async throws
    func predict(features: [[Double]]) async throws -> [Int]
    func predictProbability(features: [[Double]]) async throws -> [[Double]]
}

extension ClassifierEstimator {
    public func fit(
        features: PreparedNumericBatch,
        targets: [Double]
    ) async throws {
        // Validate finite prepared features and finite, row-aligned targets.
        // Convert with rowValues() exactly once, then dynamically dispatch to the row requirement.
        fatalError("not implemented")
    }

    public func predict(
        features: PreparedNumericBatch
    ) async throws -> [Int] {
        // Validate finite prepared features, convert once, and dispatch.
        fatalError("not implemented")
    }

    public func predictProbability(
        features: PreparedNumericBatch
    ) async throws -> [[Double]] {
        // Validate, convert once, then call the row probability requirement.
        // A legacy conformer's existing default still throws unsupportedOperation.
        fatalError("not implemented")
    }

    public func fit(_ data: PreparedSupervisedBatch) async throws {
        try await fit(features: data.features, targets: data.targets)
    }

    public func predictProba(
        features: PreparedNumericBatch
    ) async throws -> ProbabilityMatrix {
        ProbabilityMatrix(try await predictProbability(features: features))
    }
}
```

Add the same caller-estimated `MemoryBudget` wrappers as prepared regression for prepared fit, supervised fit, label prediction, and probability prediction. The wrappers reserve around the dynamically dispatched operation and release on success or error. They do not estimate memory or retain outputs. This keeps admission policy with the caller and reuses existing infrastructure.

The generic classifier boundary checks only facts shared by binary and multiclass classifiers: feature finiteness, finite targets, and row alignment. Native prepared logistic fit owns the stricter `0` or `1` label rule. Its existing row-array fit continues to accept finite soft targets, so prepared integration does not narrow a valid legacy use. Change `PreparedNumericBatch.requireFinite()` to use a domain-neutral message such as `Prepared numeric input contains missing or nonfinite values`; do not add a second classifier-only feature scan. This is the subtraction step: one shared invariant and one error source replace a regression-specific message plus a duplicate validator.

No prepared matrix overload becomes a protocol requirement. `PreparedNumericMatrix` is an internal packing result for this design, not another public route callers must choose.

### Classification pipeline

`ClassificationPipeline` receives the prepared regression pipeline's two pieces of state and implements all three prepared requirements natively.

```swift
public final class ClassificationPipeline:
    ClassifierEstimator,
    @unchecked Sendable
{
    private var fittedFeatureNames: [String]?
    private var needsSuccessfulFit = false

    public var transformers: [any PreprocessingTransformer]
    public let estimator: any ClassifierEstimator

    public func fit(features: [[Double]], targets: [Double]) async throws
    public func fit(
        features: PreparedNumericBatch,
        targets: [Double]
    ) async throws
    public func fit(
        consuming features: consuming PreparedNumericBatch,
        targets: [Double]
    ) async throws

    public func predict(features: [[Double]]) async throws -> [Int]
    public func predict(
        features: PreparedNumericBatch
    ) async throws -> [Int]
    public func predict(
        consuming features: consuming PreparedNumericBatch
    ) async throws -> [Int]

    public func predictProbability(
        features: [[Double]]
    ) async throws -> [[Double]]
    public func predictProbability(
        features: PreparedNumericBatch
    ) async throws -> [[Double]]
    public func predictProbability(
        consuming features: consuming PreparedNumericBatch
    ) async throws -> [[Double]]
}
```

Prepared fit validates a nonempty batch, nonempty feature set, unique input names, finite values, and finite row-aligned targets before it changes pipeline state. It then sets `needsSuccessfulFit = true`, remembers the original input name order in a local, fits and transforms each training step in sequence, and transfers each prepared intermediate through `transform(consuming:)`. Only a successful estimator fit commits `fittedFeatureNames` and clears the failure flag. This fits preprocessing on training rows only.

Row fit sets `needsSuccessfulFit = true` before the first transformer can mutate. On success it clears the named schema and the failure flag. If a transformer or estimator fails after mutation begins, both row and prepared prediction throw `modelNotFitted` until a later fit succeeds. An error caught by prepared prevalidation leaves the previous fitted pipeline usable because no transformer has run.

Prepared label and probability prediction use the same sequence:

1. Reject `needsSuccessfulFit`.
2. Compare the caller's ordered names with `fittedFeatureNames` when a prepared fit established a schema.
3. Reject missing and nonfinite values.
4. Record the input row count, transfer the prepared value through every transformer's consuming method, and call the matching prepared estimator requirement.
5. Require the label count or the outer probability-row count to equal the recorded input row count.

The pipeline cannot infer the number of classes for an arbitrary classifier, so it does not invent a fixed probability width. A mismatched outer count is a pipeline error. Probability row semantics remain the estimator's responsibility.

The class stays `@unchecked Sendable`. Its existing rule remains explicit: configure transformers before fitting, and serialize configuration, fit, and prediction against fit. This change does not add locks or claim that mutable transformer existentials are safe for concurrent use.

### Logistic regression state

Replace the separately published fitted fields with one actor-owned value. Computed public getters preserve the current read API.

```swift
private struct LogisticModelState {
    let resolvedDevice: ExecutionDevice
    let cpuWeights: [Double]
    let cpuBias: Double
    let mlxWeights: MLXArray
    let mlxBias: MLXArray
    let preparedFeatureNames: [String]?
}

public actor LogisticRegression: ClassifierEstimator {
    private var state: LogisticModelState?

    public let requestedDevice: ExecutionDevice
    public var resolvedDevice: ExecutionDevice? { state?.resolvedDevice }
    public var weights: MLXArray? { state?.mlxWeights }
    public var bias: MLXArray? { state?.mlxBias }

    public func getWeightsAndBias() -> (weights: [Double]?, bias: Double?)
    public func getWeights() -> [Double]?
    public func getBias() -> Double?
}
```

Supplied-parameter construction creates this value with a nil named schema and the existing device rule: `.auto` and `.cpu` resolve to CPU, while `.gpu` and `.ane` use GPU. Persistence and Core ML export keep reading the same public properties and getters.

Every fit validates input and controls first, awaits `HardwareRouter` without touching `state`, trains into local parameters, checks cancellation before publication, and assigns `state` once. A validation error, cancellation, GPU packing failure, or solver failure therefore leaves parameters, schema, and resolved device from the last successful fit together. Actor readers cannot observe a partial assignment because the final commit has no suspension point.

```swift
private struct LogisticControls {
    let learningRate: Float
    let epochs: Int

    func validate() throws {
        // learningRate must be finite and greater than zero.
        // epochs must be greater than or equal to zero.
        fatalError("not implemented")
    }
}

private struct LogisticParameters {
    let doubleWeights: [Double]
    let doubleBias: Double
    let floatWeights: [Float]
    let floatBias: Float
}

private enum ValidatedLogisticInput {
    case rows(values: [[Double]], rowCount: Int, columnCount: Int)
    case prepared(PreparedNumericBatch)

    var rowCount: Int { fatalError("not implemented") }
    var columnCount: Int { fatalError("not implemented") }
}

private func fitValidated(
    _ input: ValidatedLogisticInput,
    targets: [Double],
    controls: LogisticControls,
    featureNames: [String]?
) async throws {
    let device = await HardwareRouter.shared.resolveDevice(
        for: "LogisticRegression",
        sampleCount: input.rowCount,
        featureCount: input.columnCount,
        requestedDevice: requestedDevice
    )
    try Task.checkCancellation()
    let parameters = try train(
        input,
        targets: targets,
        controls: controls,
        device: device
    )
    try Task.checkCancellation()
    state = LogisticModelState(
        resolvedDevice: device,
        cpuWeights: parameters.doubleWeights,
        cpuBias: parameters.doubleBias,
        mlxWeights: MLXArray(parameters.floatWeights)
            .reshaped([input.columnCount, 1]),
        mlxBias: MLXArray([parameters.floatBias]),
        preparedFeatureNames: featureNames
    )
}
```

The row overload validates a rectangular input with at least one row, finite cells, aligned finite targets, a finite positive Float learning rate, and nonnegative epochs. It deliberately does not require `0` or `1`: finite soft targets remain valid on this legacy API. It also permits rows with zero columns so the CPU route keeps its existing intercept-only behavior. The prepared overload requires at least one named feature, unique names, and targets equal to `0` or `1`, then stores those names only in the successful candidate state. Generic `ClassifierEstimator` defaults do not require binary labels.

### Concrete packed CPU kernel

This candidate deliberately does not copy LinearRegression's generic row/column subscript protocol. The CPU solver accepts one concrete contiguous representation.

```swift
private struct PackedLogisticMatrix {
    let values: [Double]       // row-major, exactly rowCount * columnCount
    let rowCount: Int
    let columnCount: Int

    init(validatedRows: [[Double]]) {
        // Allocate once and append every row in order.
        fatalError("not implemented")
    }

    init(validatedBatch: PreparedNumericBatch) throws {
        // batch.matrix(order: .rowMajor, missing: .reject) performs one pack.
        // Move its COW values into this concrete matrix without another element copy.
        fatalError("not implemented")
    }

    subscript(_ row: Int, _ column: Int) -> Double {
        values[row * columnCount + column]
    }
}
```

Route selection happens before packing. CPU converts either input to `PackedLogisticMatrix` once per fit. A zero-width row matrix is represented by an empty `values` buffer plus its nonzero row count; the CPU loop still learns the bias. GPU never creates this Double matrix. For positive widths it uses `ScopedGPURead.withMatrix(batch:)` for prepared columns and `ScopedGPURead.withMatrix(rows:columns:value:)` for row arrays, producing one row-major Float buffer with the existing synchronized owner lifetime. A zero-width legacy row input keeps the current explicit empty MLX matrix construction rather than passing an extent the scoped packer rejects.

The CPU training loop allocates `predictions` with N elements and `gradW` with P elements once before the epoch loop. Each epoch clears `gradW` in place and resets `gradB`. The computation order stays exact:

```swift
private func trainCPU(
    features: PackedLogisticMatrix,
    targets: [Double],
    controls: LogisticControls
) throws -> LogisticParameters {
    var w = [Double](repeating: 0, count: features.columnCount)
    var b = 0.0
    var predictions = [Double](repeating: 0, count: features.rowCount)
    var gradW = [Double](repeating: 0, count: features.columnCount)

    for _ in 0..<controls.epochs {
        try Task.checkCancellation()

        for i in 0..<features.rowCount {
            var z = 0.0
            for j in 0..<features.columnCount {
                z += features[i, j] * w[j]
            }
            predictions[i] = sigmoid(z + b)
        }

        for j in gradW.indices { gradW[j] = 0.0 }
        var gradB = 0.0
        for i in 0..<features.rowCount {
            let difference = predictions[i] - targets[i]
            gradB += difference
            for j in 0..<features.columnCount {
                gradW[j] += difference * features[i, j]
            }
        }

        let factor = 1.0 / Double(features.rowCount)
        gradB *= factor
        for j in gradW.indices { gradW[j] *= factor }
        // Keep the existing gradient finiteness check before the update.
        for j in w.indices { w[j] -= Double(controls.learningRate) * gradW[j] }
        b -= Double(controls.learningRate) * gradB
    }

    // Reject nonfinite final parameters before building the candidate state.
    // Convert once to Float mirrors for the existing public MLX properties.
    fatalError("not implemented")
}
```

The feature loop, sample loop, gradient scaling, and update order match the current CPU implementation. `epochs == 0` skips the loop and returns zero weights and zero bias. The extra final finiteness check does not change finite arithmetic; it prevents an overflowing last update from replacing a working state.

GPU training preserves Float inputs, Float learning rate, MLX binary cross-entropy, `valueAndGrad`, and the current update sequence. It evaluates the final parameters and extracts `[Float]` plus the Float bias inside the `ScopedGPURead` closure. No lazy result that depends on the input buffer escapes. The actor then creates standalone MLX parameter arrays and Double mirrors for `LogisticModelState`. A finite Double input can still overflow during Float conversion; the existing GPU numerical limitation remains visible as a training failure.

### Prediction

Prepared prediction first checks the successful state's named schema, then finiteness and fitted width. Row prediction validates rectangular width before indexing, replacing the current short-row trap and ignored extra columns with a dimension error. Empty row-array prediction continues to return `[]`; nonempty zero-width rows on a CPU intercept-only model return the sigmoid of the learned bias.

CPU positive-class prediction uses the same `PackedLogisticMatrix` and feature-order dot product as CPU training. Both row and prepared inputs pay one operation-local Double pack. GPU prediction packs directly to one Float buffer through `ScopedGPURead`, evaluates probabilities inside the closure, and returns materialized Doubles.

One private positive-probability function feeds both public output forms:

```swift
private func positiveProbabilities(
    for input: ValidatedLogisticInput,
    using state: LogisticModelState
) throws -> [Double]

public func predictProbability(
    features: PreparedNumericBatch
) async throws -> [[Double]] {
    let p1 = try positiveProbabilitiesForPrepared(features)
    return p1.map { [1.0 - $0, $0] }
}

public func predict(
    features: PreparedNumericBatch,
    threshold: Float = 0.5
) throws -> [Int] {
    try positiveProbabilitiesForPrepared(features).map {
        $0 > Double(threshold) ? 1 : 0
    }
}
```

Row and prepared labels both compare with `>`, never `>=`. `predictProbability(X:)` and `predict(X:threshold:)` remain available for MLX callers and retain the same strict MLX comparison.

### Copies and access patterns

| Route | Feature conversion before fit | Per-epoch feature access | Scratch and outputs |
| --- | --- | --- | --- |
| Prepared, CPU | One N by P Double pack from compact columns to row-major storage | Two sequential row-major passes in the existing row then feature order | N Double predictions and P Double gradients allocated once per fit and reused |
| Row arrays, CPU | One N by P Double pack, which is one additional full copy compared with the current nested-row solver; P equal to zero allocates no feature elements | Same contiguous passes as prepared CPU, with an empty feature loop for intercept-only data | Same reusable scratch |
| Prepared, GPU | One N by P Float pack directly from compact columns into scoped shared Metal storage; no Double matrix pack | MLX owns the iteration pattern | One N-element Float target conversion plus MLX parameters and gradients |
| Row arrays, GPU | One N by P Float pack into the same scoped storage, equivalent in size to the current `flatMap` conversion | MLX owns the iteration pattern | Same as prepared GPU |

Prepared preprocessing does not materialize rows when every participating transformer has a native prepared implementation. Snapshot column buffers remain owned by `PreparedNumericBatch`; consuming transforms may reuse unique buffers under existing copy-on-write rules. `PreparedSupervisedBatch.targets` shares its target array until a mutation occurs.

CPU prediction also packs N by P Doubles once. That gives one checked, contiguous dot-product kernel and identical arithmetic for row and prepared callers, but it is a poor trade for tiny one-off row predictions. The existing `predict(instance:)` compatibility convenience therefore incurs a one-row pack. This candidate accepts that cost to remove representation branching from the numerical code. Applications that issue many single-row predictions may prefer the column-view candidate or a separately justified fitted prediction session later. This task does not add such a session.

### Module map

| File | Responsibility after the change |
| --- | --- |
| `Sources/SwiftML/Core/EstimatorProtocols.swift` | Add prepared classifier requirements, compatibility defaults, supervised convenience, prepared `ProbabilityMatrix` convenience, and existing-budget wrappers. |
| `Sources/SwiftML/Core/EstimatorPipeline.swift` | Give `ClassificationPipeline` native prepared fit, consuming transform flow, raw-input schema memory, failed-refit invalidation, and output row-count checks. |
| `Sources/SwiftML/Core/LogisticRegression.swift` | Own boundary validation, route-specific packing, the concrete packed CPU kernel, scratch reuse, GPU scoped reads, strict-threshold output, and one-value fitted-state publication. |
| `Sources/SwiftDataFrame/Core/PreparedNumericBatch.swift` | Make the shared finite-input error text domain-neutral. Do not add a classification batch type. |
| `Sources/SwiftML/Core/DataFrame+ML.swift` | No change. Existing DataFrame conveniences remain row-array compatibility routes; prepared callers build one named snapshot explicitly. |
| `Tests/SwiftMLTests/PreparedClassificationIntegrationTests.swift` | Prove existential native dispatch for fit, labels, and probabilities; aligned repeated selection and snapshot independence; legacy conversion; schema rejection; output-count checks; failed-refit behavior; and budget release. |
| Existing logistic and routing tests | Pin epochs 0, 1, and 32 on CPU, strict threshold ties, prepared binary-label and control validation, legacy row soft targets and zero-width CPU intercepts, route preservation, direct-model failed-refit state, GPU tolerance, and row/prepared agreement for binary data. |
| Frozen supervised logistic workload | Exercise the prepared CPU route with the existing independent fixtures and tolerances. Decoding stays outside the measured workflow. |

No PCA API, partial-fit state, warm start, classifier registry, new hardware policy, or agent infrastructure enters this module map. Records and exploratory prototypes stay outside production.

### Interface depth and red-flag check

The public increase is three prepared protocol requirements plus conveniences that mirror prepared regression. That interface hides validation, legacy conversion, native dispatch, preprocessing ownership transfer, route-specific packing, and state publication. Callers never choose a matrix layout or CPU kernel. The route-specific buffer and fitted-state types remain private, so representation does not leak into pipeline or protocol code.

The call chain stays short: caller to pipeline to estimator. Pipeline methods add schema and preprocessing policy rather than pass-through layers. Solver helpers group code by logistic representation and state ownership rather than by generic load and save phases. There is one source of truth for fitted parameters and one place that checks prepared input finiteness.

## Synthesis decision

Candidate B chooses route-specific packing as its defining shape. CPU work converges on one private row-major Double matrix; GPU work packs directly to the existing row-major Float buffer. This is the strongest alternative when exact CPU ordering, compact prepared preprocessing, and simple numerical loops matter more than avoiding an extra copy for legacy CPU rows. A synthesis should take this candidate whole if it accepts that copy. Grafting only the packed solver while retaining separately mutable fitted fields would lose the failure-safety benefit.

## Tradeoffs accepted

- We accept one N by P Double copy for legacy CPU fit in exchange for one concrete CPU kernel with contiguous access and no generic per-cell dispatch.
- We accept one N by P Double copy on CPU prediction, including a one-row copy for `predict(instance:)`, in exchange for shared checked width handling and identical row/prepared arithmetic.
- We accept a full finite-value validation pass before packing in exchange for boundary errors before routing or state changes.
- We accept storing both Double parameters and Float MLX mirrors in one fitted value in exchange for unchanged public getters, persistence, export, and CPU/GPU prediction behavior.
- We accept invalidating a pipeline after any refit failure that follows transformer mutation in exchange for never pairing newly fitted transformer state with an older estimator.
- We accept positional prepared prediction for row-fitted and persisted models in exchange for preserving models that have no saved feature names.
- We accept caller-supplied admission estimates in exchange for avoiding an inaccurate automatic memory estimator. Estimates must include retained batches, the CPU Double pack or GPU Float pack, reusable scratch, preprocessing intermediates, and outputs.

## Alternatives considered

### Generic row/column access shared kernel

A private protocol with a two-index subscript avoids the CPU pack for both representations. It lost here because every numerical read crosses a representation abstraction, storage remains fragmented for nested rows, and the kernel's apparent generality exists only to support two inputs. Its public interface is equally small, but it hides less memory behavior. This is Candidate B's required structural departure from the LinearRegression precedent.

### Column-oriented CPU solver

A prepared-native solver could accumulate each gradient column from its compact contiguous buffer and avoid the N by P pack. That changes the loop nesting from sample then feature to feature then sample or requires keeping the forward pass and gradient pass on different locality patterns. The former changes floating-point accumulation order and breaks exact row/prepared comparison. The latter still leaves legacy rows with strided column reads or requires transposition. It is a credible design for a new numerical contract, but it does not fit the frozen exact-order workload.

### Public `PreparedNumericMatrix` classifier requirements

This would let callers prepack once and reuse the matrix across operations. It lost because it adds three more public requirements, makes callers choose layout, bypasses named column preprocessing, and has no prepared regression protocol precedent. The current task needs a prepared batch route, not a second public representation family.

### Keep separate row and prepared solvers

This avoids the extra legacy CPU copy. It lost because validation, cancellation, update order, final checks, and bug fixes would need to stay synchronized across two implementations. The public interface stays small, but the estimator hides duplicated rules rather than one implementation.

## Open questions and risks

- Do measured legacy CPU workloads tolerate the added pack, especially repeated one-row prediction? If not, synthesis should choose the generic access candidate rather than weaken this packed design with a second kernel.
- Should the frozen workload switch its worker to prepared input in the same implementation change, or should a new prepared workload ID preserve historical benchmark comparability? The numerical fixtures can validate either route, but benchmark identity is a reporting decision.
- Do any clients compare the exact regression-specific text from `requireFinite()`? Making it domain-neutral is the clean shared fix, but exact-string consumers would observe the wording change.
- Does Swift's current MLX version guarantee that rebuilding standalone parameter arrays from evaluated Float values preserves every public shape and persistence behavior? The implementation should verify shape, values, and Core ML export getters on both routes.
- Should cancellation be checked once per epoch on both CPU and GPU, or only before final publication? Per-epoch checks improve responsiveness without changing successful arithmetic, but they are a new observable failure point for canceled tasks.

## Next implementation step

Add the three prepared `ClassifierEstimator` requirements and compatibility defaults first, then prove existential dispatch and legacy probability behavior before changing pipeline or logistic internals.
