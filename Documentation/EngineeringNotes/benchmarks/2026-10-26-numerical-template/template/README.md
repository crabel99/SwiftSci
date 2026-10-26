# A complete SwiftSci numerical workflow

This example carries named numeric columns through training-only imputation and scaling, prepared PCA, and prepared logistic classification. It uses existing public APIs. The small deterministic fixture includes a missing feature, a valid NaN, a constant feature, and reordered held-out rows with a duplicate.

The code fits every learned stage on rows 0 through 7. Held-out rows 10, 8, 10, 9 and 11 only transform and predict. Features and labels are selected together with PreparedSupervisedBatch. PCA retains source-row identity. Prediction arrays do not carry it, so the example associates each output with the score batch's originalRowIndices.

The core workflow is in `Sources/ScientificWorkflow/ScientificWorkflow.swift`. Replace its named input columns and row selections with your own data. Keep the target outside feature preprocessing. Fit Imputer and StandardScaler once on training features, then reuse those fitted values for query features. StandardPreprocessingPlan currently exposes model-specific integration rather than a public general transform operation; this example uses its public staged composition.

The package pins the exact qualified SwiftSci revision. Build and run on Apple silicon macOS with Xcode:

```sh
xcodebuild -scheme ScientificWorkflow -configuration Release \
  -destination 'platform=macOS,arch=arm64' -derivedDataPath .build-native \
  MTL_FAST_MATH=NO MTL_MATH_MODE=SAFE MTL_MATH_FP32_FUNCTIONS=PRECISE build
.build-native/Build/Products/Release/ScientificWorkflow
```

Output is JSON containing fitted parameters, stage values, probabilities, predicted classes and associated source rows. The example deliberately requests CPU execution for both algorithms. Diagnostic row export happens after the prepared pipeline; the PCA-to-classifier handoff stays prepared.

Existing MLX initialization still requires an accessible Metal device. A sandboxed or headless launch can fail before this CPU workflow starts.

This toy fixture demonstrates integration, not generalization accuracy, speed or a memory bound. Its output is checked against a separate legacy-API path and independent scalar preprocessing, a closed-form two-feature PCA solution and 64 full-batch logistic updates. The declared numerical check is `abs(error) <= 1e-12 + 1e-12 * abs(reference)`. Missing feature values are imputed; infinite features and invalid labels still need correction at the caller boundary. Do not impute labels or fit learned stages on query data.

[Qualification records](https://github.com/crabel99/SwiftSci/blob/codex/engineering-notes/Documentation/EngineeringNotes/benchmarks/2026-10-26-numerical-template/README.md) include the independent checks, exact source and dependency pins, successful remote package build/run, and retained limitations.
