# Public multiclass MLP export assessment

Read-only source assessment at `53063789b1893b28250ea239d5fdca4fed84c4c9`. No model execution, build, or source change.

## Conclusion

The multiclass exporter has a concrete serialization defect on the real public `MLPClassifier.exportCoreML` path. It requests softmax but serializes an empty generic activation message. This blocks claiming a working trained multiclass export-to-predictor workflow. Core ML compile rejection is the expected runtime outcome, but has not been observed in this read-only task. If a compiler accepts the malformed layer, its output still lacks serialized softmax semantics, so numerical probability qualification is mandatory.

It does not block a binary MLP example-mode workflow. The binary branch selects sigmoid, and the builder has a sigmoid case. Existing tests cover that branch but do not establish trained binary probability parity.

## Exact path

1. `MLPClassifier.fit` sorts observed labels. More than two classes create `numClasses` output units. `Sources/SwiftML/Core/MLP.swift:175-195`.
2. Public `MLPClassifier.exportCoreML` obtains trained layers and labels, then calls `CoreMLExporter.exportBinaryMLPClassifier`. `Sources/SwiftML/Serialization/CoreMLExportable.swift:303-322`.
3. The exporter converts the internal input-major flat weights into output-major nested arrays, forwards hidden activation, and selects sigmoid for one output or softmax otherwise. The `classLabels` parameter is accepted but unused in the body. `CoreMLExporter.swift:521-550`.
4. `buildNeuralNetworkModel` emits rank-one Double array input and rank-one Double output. Layer weights and biases are serialized as Float32. `CoreMLProtobuf.swift:619-625`, `:637-674`.
5. The last multiclass layer has `actType == "softmax"`, so `hasActivation` is true. A final layer named `act_<index>` is created. Its generic `ActivationParams` writer receives no fields because the switch only handles relu, sigmoid, tanh and otherwise breaks. The builder nevertheless writes that empty message to `NeuralNetworkLayer.activation`, field 130. `CoreMLProtobuf.swift:652-655`, `:681-700`.
6. A `NeuralNetworkLayer.softmax`, field 175, constant already exists but this builder never writes it. `CoreMLProtobuf.swift:56-63`.

## Smallest deterministic public exporter reproduction

The following uses public API only and isolates serialization from training. The model should map input `[1]` to softmax `[-1,0,1]`, approximately `[0.0900305732,0.2447284711,0.6652409558]`.

```swift
import CoreML
import Foundation
import SwiftML

let layer = LayerWeights(W: [-1, 0, 1], b: [0, 0, 0], inDim: 1, outDim: 3)
let bytes = CoreMLExporter.exportBinaryMLPClassifier(
    inputNames: ["x"], outputName: "probabilities", layers: [layer])
let url = FileManager.default.temporaryDirectory
    .appendingPathComponent("MLPSoftmax-\(UUID().uuidString).mlmodel")
try bytes.write(to: url)
let compiled = try MLModel.compileModel(at: url) // Expected first runtime failure.
```

This reproduction must remove raw and compiled temporary artifacts in its actual test harness. A passing compile alone is insufficient. Run a prediction and compare all three probabilities to the independent reference, including finite values and unit sum.

## Smallest trained public consumer reproduction

```swift
import CoreML
import Foundation
import SwiftDataFrame
import SwiftML
import SwiftPreprocessing

let rows: [[Double]] = [[-1], [0], [1]]
let classifier = MLPClassifier(hiddenLayerSizes: [], maxIter: 1,
    seed: 42, requestedDevice: .cpu)
try await classifier.fit(features: rows, targets: [-3, 7, 12])
let expected = try await classifier.predictProbability(features: rows)
let classes = await classifier.trainedClasses
let url = FileManager.default.temporaryDirectory
    .appendingPathComponent("TrainedMLP-\(UUID().uuidString).mlmodel")
try await classifier.writeCoreML(to: url, featureNames: ["x"], outputName: "probabilities")
let compiled = try MLModel.compileModel(at: url) // Expected first runtime failure.
let predictor = try CoreMLPredictor(compiledModelURL: compiled,
    inputColumns: ["x"], outputName: "probabilities", computeUnits: .cpuOnly)
let input = try PreparedNumericBatch(columnNames: ["x"], columns: [[-1, 0, 1]])
let budget = try MemoryBudget(limit: 1_048_576)
let result = try await predictor.predict(input, budget: budget, workspaceBytes: 65_536)
```

This snippet is a proposed reproduction, not a reported successful execution. It omits file cleanup and assertions for brevity. The same workflow with a hidden layer tests hidden activation, weight transposition, final softmax, and adapter conversion together.

## Intended consumer contract

- The compiled model has vector input `[1]` and output `[3]`, both declared Double. Public `CoreMLPredictor` uses default `.examples`, so no production matrix abstraction is required. `CoreMLPredictionSession.swift:48-75`.
- Output columns are `probabilities[0]`, `[1]`, `[2]`, in sorted `trainedClasses` order `[-3,7,12]`. The Core ML artifact is a numeric `neuralNetwork`, not `neuralNetworkClassifier`; class labels are not serialized. The application keeps class mapping separately. `CoreMLExportable.swift:314-322`, `CoreMLExporter.swift:527-550`, `CoreMLProtobuf.swift:707-708`, `CoreMLPredictionSession.swift:63-66`.
- Each output row should match softmax of the frozen exported weights' logits. Compare separately with Double trained-model outputs, because export quantizes weights and biases to Float32. Existing in-process `predictProbability` already applies stable softmax for multiclass. `MLP.swift:957-966`.
- For three one-feature rows and three outputs, logical copy counts should be 24 input bytes and 72 output bytes. Row provenance must survive, budget reservations should return to zero, and predictions should repeat without changing model state.
- Multiclass label prediction is argmax followed by sorted class mapping. `MLP.swift:378-387`. The adapter returns probabilities, not labels.

## Existing coverage

- `CoreMLExporterBinaryTests.swift:352-389` exports a handwritten two-layer classifier with one output, compiles it, runs a prediction, and checks only that its probability exists. It does not check a numerical probability or use a trained `MLPClassifier`.
- `CoreMLExporterBinaryTests.swift:392-427` covers a scalar linear MLP regressor numerically.
- `CoreMLPredictorTests.swift:51-75` checks vector regression, feature ordering, copy counts, and compute-unit permissions. It does not export or predict a multiclass classifier.
- `MLPBatchedPredictionTests.swift:28-60` checks two-class and three-class in-process probabilities against independent scalar forward/softmax. `MLPPreparedMatrixClassificationTests.swift:7-25` checks row/prepared-matrix parity. Neither crosses Core ML serialization.
- A search of existing SwiftML tests found no multiclass Core ML classifier export test and no softmax serialization assertion.

## Scope judgment

The smallest justified production correction, after running the cheap deterministic reproduction, is to serialize softmax as its actual neural-network layer field instead of as an empty activation. No public API change or new inference owner is implied. Keep trained-workflow qualification distinct from a change to training mathematics. The training loop's multiclass final outputs are raw logits while prediction applies softmax; that separate algorithm question is visible in `MLP.swift:223-245` and is not required to reproduce the exporter defect with frozen layers.
