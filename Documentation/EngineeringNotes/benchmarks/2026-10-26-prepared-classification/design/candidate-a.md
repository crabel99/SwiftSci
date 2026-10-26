# Candidate A: one logistic kernel over existing row and batch views

## Usage

The ordinary workflow selects features and labels together, splits once, fits preprocessing only on training rows, and predicts held-out rows through the classifier protocol.

```swift
import SwiftML
import SwiftDataFrame

let snapshot = try PreparedSupervisedBatch(
    frame.prepareNumericBatch(["radius", "texture", "malignant"]),
    targetColumn: "malignant"
)
let train = try snapshot.selectingRows(trainIndices)
let test = try snapshot.selectingRows(testIndices)
let pipeline: any ClassifierEstimator = ClassificationPipeline(
    transformers: [StandardScaler()],
    estimator: LogisticRegression(device: .cpu)
)
try await pipeline.fit(train)
let probabilities = try await pipeline.predictProbability(features: test.features)
let labels = try await pipeline.predict(features: test.features)
// probabilities[i] and labels[i] correspond to test.features.originalRowIndices[i].
```

Callers who need a frozen finite-step experiment keep the existing logistic controls. They fit the scaler on training data and reuse it for held-out data.

```swift
var scaler = StandardScaler()
let scaledTrain = try scaler.fitTransform(train.features)
let scaledTest = try scaler.transform(test.features)
let model = LogisticRegression(device: .cpu)
try await model.fit(features: scaledTrain, targets: train.targets,
                    learningRate: 0.125, epochs: 32)
let probabilities = try await model.predictProbability(features: scaledTest)
let labels = try await model.predict(features: scaledTest, threshold: 0.5)
```

Legacy classifiers require no source changes. Only their compatibility path materializes nested rows. Existing dataframe convenience methods retain their row-array behavior; prepared selection is explicit.

```swift
let classifier: any ClassifierEstimator = ExistingLegacyClassifier()
try await classifier.fit(train)
let labels = try await classifier.predict(features: test.features)
// Unsupported probability estimation still throws its existing error.
```

## Problem

Classifier protocols currently accept only nested rows, while prepared regression already supports native batches, transformer dispatch, joint target selection and admission budgets. Logistic regression must use those existing mechanisms without changing its CPU Double arithmetic, GPU Float arithmetic, router policy, strict threshold comparison, or valid zero-epoch behavior. New prepared overloads must dispatch through existential classifier references. Failed fitting must leave a usable old logistic model; pipelines that have already mutated transformers must refuse predictions until a later fit succeeds.

## Shape

Subtract the duplicated CPU representation handling and independently mutable fitted fields before adding prepared entry points. A private generic read-only view supplies dimensions and scalar access to one fit kernel and one CPU probability kernel. The existing row and batch storage remain their owners. No new public storage type, classifier, matrix requirement, training session, or generic estimator framework is needed.

```swift
public protocol ClassifierEstimator: Sendable {
    // Existing row requirements remain unchanged.
    func fit(features: [[Double]], targets: [Double]) async throws
    func predict(features: [[Double]]) async throws -> [Int]
    func predictProbability(features: [[Double]]) async throws -> [[Double]]

    // Requirements, rather than extension-only overloads, preserve native dispatch.
    func fit(features: PreparedNumericBatch, targets: [Double]) async throws
    func predict(features: PreparedNumericBatch) async throws -> [Int]
    func predictProbability(features: PreparedNumericBatch) async throws -> [[Double]]
}

extension ClassifierEstimator {
    // Prepared defaults validate generic finite/aligned inputs, then convert once.
    // They impose no binary-class restriction and cannot remember training names.
    public func fit(_ data: PreparedSupervisedBatch) async throws
    public func predictProba(features: PreparedNumericBatch) async throws -> ProbabilityMatrix
    public func fit(features: PreparedNumericBatch, targets: [Double],
                    budget: MemoryBudget, estimate: MemoryEstimate) async throws
    public func fit(_ data: PreparedSupervisedBatch,
                    budget: MemoryBudget, estimate: MemoryEstimate) async throws
    public func predict(features: PreparedNumericBatch,
                        budget: MemoryBudget, estimate: MemoryEstimate) async throws -> [Int]
    public func predictProbability(features: PreparedNumericBatch,
                                   budget: MemoryBudget, estimate: MemoryEstimate) async throws -> [[Double]]
}

private protocol LogisticFeatures {
    var rowCount: Int { get }
    var columnCount: Int { get }
    subscript(row: Int, column: Int) -> Double { get }
}
private struct LogisticRows: LogisticFeatures { let rows: [[Double]] /* accessors */ }
private struct LogisticColumns: LogisticFeatures { let batch: PreparedNumericBatch /* accessors */ }

private struct FittedLogisticState {
    let doubleWeights: [Double]
    let doubleBias: Double
    let mlxWeights: MLXArray
    let mlxBias: MLXArray
    let resolvedDevice: ExecutionDevice
    let featureNames: [String]?
}

public actor LogisticRegression: ClassifierEstimator {
    private var fitted: FittedLogisticState?
    public let requestedDevice: ExecutionDevice
    // Existing public getters read one state. Their names/types remain unchanged.
    public var weights: MLXArray? { fitted?.mlxWeights }
    public var bias: MLXArray? { fitted?.mlxBias }
    public var resolvedDevice: ExecutionDevice? { fitted?.resolvedDevice }

    public func fit(features: PreparedNumericBatch, targets: [Double]) async throws
    public func fit(features: PreparedNumericBatch, targets: [Double],
                    learningRate: Float = 0.1, epochs: Int = 1000) async throws
    public func predict(features: PreparedNumericBatch) async throws -> [Int]
    public func predict(features: PreparedNumericBatch,
                        threshold: Float = 0.5) throws -> [Int]
    public func predictProbability(features: PreparedNumericBatch) async throws -> [[Double]]

    private func fitValidated<F: LogisticFeatures>(
        features: F, targets: [Double], names: [String]?,
        learningRate: Float, epochs: Int
    ) async throws
    private static func fitCPU<F: LogisticFeatures>(
        features: F, targets: [Double], learningRate: Double, epochs: Int
    ) throws -> (weights: [Double], bias: Double)
    private static func fitGPU(X: MLXArray, y: MLXArray,
                               learningRate: Float, epochs: Int) throws
        -> (weights: MLXArray, bias: MLXArray)
    private func positiveProbabilities<F: LogisticFeatures>(features: F) throws -> [Double]
}

public final class ClassificationPipeline: ClassifierEstimator, @unchecked Sendable {
    private var fittedFeatureNames: [String]?
    private var needsSuccessfulFit = false
    // Existing configuration and row methods remain.
    public func fit(features: PreparedNumericBatch, targets: [Double]) async throws
    public func fit(consuming features: consuming PreparedNumericBatch,
                    targets: [Double]) async throws
    public func predict(features: PreparedNumericBatch) async throws -> [Int]
    public func predict(consuming features: consuming PreparedNumericBatch) async throws -> [Int]
    public func predictProbability(features: PreparedNumericBatch) async throws -> [[Double]]
    public func predictProbability(consuming features: consuming PreparedNumericBatch) async throws -> [[Double]]
}
```

These are design signatures, not compiling skeletons. Existing initializers, row methods, MLX prediction methods and parameter getter methods remain. No separate validation result or kernel file is necessary. Private view types belong beside the solver whose indexing they serve, per minimize-reader-load.

### Numerical and state rules

Boundary validation checks rectangular finite rows, positive feature width, nonempty training rows, aligned finite labels, finite positive Float learning rate, and nonnegative epochs. Logistic alone requires labels exactly 0 or 1. Prepared boundaries also reject missing values and duplicate names. Rename the existing `requireFinite` error text to say numeric input, so its reused validator is not regression-specific. Prediction checks every row's width and finiteness before indexing. A native prepared fit remembers ordered names; later prepared predictions require exact equality. Unnamed row calls and supplied-parameter construction remain positional. A later successful row fit clears names. Generic compatibility defaults cannot enforce remembered schemas; the pipeline can.

`fitValidated` resolves the requested device into a local value across the router suspension, computes all results locally, checks final parameter finiteness and cancellation, then assigns one `FittedLogisticState`. Validation, routing failure, numerical failure and cancellation never alter prior state. Do not update `resolvedDevice` early. Actor readers during router suspension see the previous complete model. Concurrent fit completion order remains actor completion order; do not add a new fit scheduler. There are no awaits between starting a solver and publishing its result. Cancellation is checked after routing, at epoch boundaries, and before publication, including epochs equal to zero. This is a single state assignment per type-system-discipline.

CPU fit allocates predictions and weight-gradient arrays once per fit. Each epoch zeroes gradient elements in ascending index order, computes all predictions in ascending row/feature order, accumulates all gradients in the original row/feature order, scales, checks gradients, then updates weights and bias in the original order. Do not fuse those passes or replace them with reductions. Zero epochs returns zero parameters, probabilities of 0.5 and labels 0. Final finiteness checks close the existing last-update gap without changing successful arithmetic. The private probability kernel preserves the same dot-product order for both representations. Labels continue using strict `p > Double(threshold)`.

GPU fitting preserves the existing Float BCE/autodiff loop. Use `ScopedGPURead.withMatrix(rows:columns:value:)` over the same feature view, so one shared orchestration function works without converting a batch into rows. Evaluate fitted parameters and materialize Double mirrors inside the scope. Prediction also evaluates and returns concrete arrays before scope exit. No lazy tensor derived from temporary input storage may escape. Preserve existing Float representability limits rather than claim Double/GPU equivalence. Routing policy and supplied-parameter routing remain unchanged.

Pipeline prepared validation runs before transformer mutation. Set `needsSuccessfulFit` immediately before the first possible mutation, fit/transform training batches through existing consuming transformer requirements, then fit the classifier through the prepared protocol requirement. Commit original input names and clear the failure flag only after classifier success. A later error leaves the flag set because transformers may now disagree with the old classifier. The same failure guard covers labels and probabilities, row and prepared entry points. Validate row counts after each transform, retain provenance through existing prepared transforms, and validate prediction row counts. Probability results must have one row per input and a consistent class width for nonempty results. Do not require binary width at a generic classifier boundary. An initially empty pipeline with a supplied fitted estimator should retain its existing delegation behavior; the flag represents failed refit, not a new fitted-state gate.

Feature/target selection stays in `PreparedSupervisedBatch`. Transforming features must not select or reorder rows. Returned arrays stay in input row order, while callers retain provenance on the input batch. Copy-on-write snapshots retain source values even when a consuming path can reuse uniquely owned buffers. Admission wrappers reserve the caller's whole-operation estimate and release on success or failure. They are not a claim that retained model state or returned arrays disappear when the reservation ends.

### Module map

| File | Responsibility |
| --- | --- |
| `Sources/SwiftML/Core/EstimatorProtocols.swift` | Prepared classifier requirements, legacy defaults, supervised convenience and reservation wrappers |
| `Sources/SwiftML/Core/LogisticRegression.swift` | Private views, shared kernels, validation, atomic model state, native prepared entry points |
| `Sources/SwiftML/Core/EstimatorPipeline.swift` | Native prepared transformer flow, input schema, failed-refit guard, output row contracts |
| `Sources/SwiftDataFrame/Core/PreparedNumericBatch.swift` | Generalize the existing finite-input error wording only |
| `Tests/SwiftMLTests/PreparedClassificationIntegrationTests.swift` | Existential dispatch, legacy defaults, split alignment, pipeline schema/state/lifetime behavior |
| Existing logistic/routing tests and frozen conformance runner | Arithmetic, zero/one/32 epochs, routing and probabilities/labels |
| SwiftML documentation | One train-only preprocessing and held-out prediction workflow, serialized pipeline fitting/configuration rule |

The public interface hides representation adaptation, validation, dispatch, fitted schema and GPU owner lifetime behind familiar fit/predict calls, per boundary-discipline. Custom epoch controls stay specific to LogisticRegression. Pipelines continue using the estimator's existing protocol defaults; adding a new public training-configuration object would make this change larger without a demonstrated caller.

## Synthesis decision

Candidate submitted for parent synthesis. Its defining choice is a shared native CPU implementation over tiny private views, with one fitted-state record. It does not depend on APIs from the unmerged prepared PCA work.

## Tradeoffs accepted

- We accept indexed access into column-major batch storage in exchange for no fit-time nested rows or mandatory dense packing, and exact preservation of the existing loop order.
- We accept one copy-on-write view owner per fit in exchange for snapshot safety without unsafe pointers or custom lifetimes.
- We accept legacy conformers materializing rows and lacking remembered model schemas in exchange for source compatibility. Native pipeline validation still protects the pipeline's input names.
- We accept invalidation after a pipeline transformer has mutated in exchange for avoiding a broad transformer snapshot/rollback protocol.
- We accept existing Float limits on GPU routes and CPU/GPU numerical differences in exchange for preserving the established device contract.

## Alternatives considered

1. Convert every prepared fit into nested rows. The public interface is small, but it conceals a permanent allocation penalty and forfeits the foundation this workflow is meant to exercise. It also leaves per-epoch scratch duplication untouched.
2. Convert rows and batches into one owning column-major matrix before fitting. This hides indexing differences well but forces a full extra copy for ordinary row callers and existing batch owners. No current solver requires contiguous LAPACK storage, so that cost buys little.
3. Duplicate a batch-specific CPU loop beside the row implementation. It reduces adapter code but duplicates the numerical contract, gradient allocation policy and bug fixes. Callers see a similar interface while maintainers own two algorithms that must remain numerically identical.

## Open questions and risks

- Can specialization of the private feature views retain adequate CPU performance on the installed Swift compiler while preserving the frozen arithmetic? Measure full workflows before making any speed claim.
- Should direct legacy row calls with positive row count and zero feature width keep their accidental intercept-only behavior? This candidate rejects them consistently with prepared supervised input; explicit preservation would require a narrow solver path and GPU packing exception.
- Will final CPU parameter checks reveal previously accepted divergent last updates? They should fail while preserving the old model; frozen finite fixtures must remain unchanged.
- Does a third-party native transformer preserve row identity when it returns a batch with the same count? The protocol contract must require preservation; output count checks alone cannot prove it.

## Next implementation step

Add prepared classifier protocol requirements and legacy defaults with dispatch tests, then make LogisticRegression return and publish one complete fitted state before wiring native batch views and the classification pipeline.
