# Batch-oriented prepared PCA candidate

## Usage, written first

```swift
let train = try frame.prepareNumericBatch(["height", "weight", "age"])
    .selectingRows(trainingRows)
let query = try frame.prepareNumericBatch(["height", "weight", "age"])
    .selectingRows(queryRows)

var scaler = StandardScaler()
let scaledTrain = try scaler.fitTransform(train)
let scaledQuery = try scaler.transform(query)

let pca = try PCA(nComponents: 2, svdSolver: .full, device: .cpu)
let trainScores = try await pca.fitTransform(scaledTrain)
let queryScores = try await pca.transform(scaledQuery)

trainScores.columnNames                 // ["PC1", "PC2"]
queryScores.originalRowIndices          // queryRows, including order and repeats
let rowMajor = try queryScores.matrix(order: .rowMajor)
let columnMajor = try queryScores.matrix(order: .columnMajor)
```

The existing calls remain source-compatible and keep their current behavior:

```swift
try await pca.fit([[1, 2], [3, 4]])
let rows: [[Double]] = try await pca.transform([[5, 6]])
let legacy = try await frame.fitPCA(columns: ["x", "y"], nComponents: 1)
```

## Problem

PCA must join the prepared workflow without turning compact columns into nested rows. It must also retain the public nested APIs, CPU solver selection, hardware routing, GPU Float arithmetic, and CPU Double projection. Prepared inputs add feature identity and row provenance. Failed refits must not leave a device from one fit beside numerical state from another.

## Public shape

```swift
public actor PCA {
    // Existing initializers, nested overloads, and public fitted properties stay.

    public func fit(_ input: PreparedNumericBatch) async throws
    public func transform(_ input: PreparedNumericBatch) throws
        -> PreparedNumericBatch
    public func fitTransform(_ input: PreparedNumericBatch) async throws
        -> PreparedNumericBatch
}
```

These three overloads are the entire new public API. There is no consuming overload because dimensionality reduction must allocate new columns. There is no matrix overload. A batch is the useful labeled result, and its existing `matrix(order:)` exports either layout without a second PCA result type.

## State and private signatures

```swift
private struct FittedPCA: Sendable {
    let resolvedDevice: ExecutionDevice
    let featureNames: [String]?       // exact prepared fit schema; nil after legacy fit
    let mean: [Double]
    let components: [[Double]]        // component-major, preserves public representation
    let explainedVariance: [Double]
    let totalVariance: Double
}

private var fitted: FittedPCA?

private static func centeredColumnMajor(
    _ input: PreparedNumericBatch, solver: SVDSolver
) throws -> (values: [Double], mean: [Double])

private static func centeredColumnMajor(
    _ input: [[Double]], solver: SVDSolver
) throws -> (values: [Double], mean: [Double])

private static func fitCPU(
    centeredColumnMajor: consuming [Double], mean: [Double],
    rows: Int, columns: Int, nComponents: Int, solver: SVDSolver
) throws -> (components: [[Double]], variance: [Double], total: Double)

private static func project(
    _ input: PreparedNumericBatch, using state: FittedPCA
) throws -> [[Double]]               // one array per output column

package static func RandomizedSVD.computeRight(
    columnMajor: consuming [Double], rows: Int, columns: Int,
    nComponents: Int, nOversamples: Int = 10,
    nPowerIter: Int = 2, seed: UInt64 = 42
) throws -> (S: [Double], Vt: [[Double]])
```

`FittedPCA` is the single stored fitted value, not a cache. A fit computes it in locals and assigns it once after the backend succeeds and all results pass validation. Public `resolvedDevice`, `mean`, `components`, `explainedVariance`, and the ratio read this value. A rejected or cancelled refit leaves the previous fitted value intact.

The two boundary adapters validate their native representation and pack one centered column-major Double buffer for CPU work. Prepared input reads `CompactNumericColumn.values` directly. The nested adapter preserves row-array compatibility but stops being the numerical implementation. Full and randomized CPU solvers consume the same flat representation.

`RandomizedSVD.computeRight` owns the flat randomized kernel. PCA does not compute or back-project `U`. Existing public `compute(X:)` packs once into column-major storage, calls the same kernel with `U` requested, and returns the unchanged public `Result`. Defaults, power passes, sketch sequence, sign normalization, and LAPACK calls stay the same.

The GPU prepared path uses `ScopedGPURead.withMatrix(batch:)`, evaluates and exports every lazy MLX value inside its closure, and keeps `svd(..., stream: .cpu)` inside the GPU default-device scope. The nested path uses its current row-major Float conversion. Both still report the routed device as GPU and store widened Float results as Double. Every transform remains CPU Double accumulation with the feature loop ascending.

Routing keeps the current sample and feature thresholds. On CPU, `.auto` still selects randomized SVD only when `k < 0.8 * min(rows, columns)`, and explicit solvers remain exact overrides. Full SVD keeps thin `dgesdd`, all singular values for total variance, and its present mean arithmetic. Randomized SVD keeps reciprocal mean scaling and row-first Frobenius reduction for total variance. GPU keeps its existing Float mean, singular values, components, and total variance calculation.

## Validation and policies

PCA owns validation at its public fit and transform boundaries. It does not reuse `PreparedNumericBatch.requireFinite()` because that helper has regression-specific wording.

- Fit requires at least one row and feature, a rectangular nested input, and `nComponents <= min(rows, features)`.
- Before routing or allocation, dimensions must fit backend integer limits and every checked element or workspace product must fit `Int`.
- Missing prepared values are rejected. Valid NaN, positive infinity, and negative infinity are also rejected. Duplicate feature names remain valid because preparation already preserves duplicate selections.
- GPU routing additionally rejects finite Double values that overflow Float conversion. This states the existing GPU precision boundary plainly; it does not imply FP64 GPU SVD.
- Prepared transform compares `columnNames` exactly, including order and duplicates, when the model was fit from a prepared batch. A model fit through the nested API checks width only. Nested transforms always check width only.
- Prepared transform permits zero rows when its nonempty feature schema matches and returns an empty score batch. Nested `transform([])` keeps throwing `emptyInput`, so old overload resolution and behavior remain unchanged.
- Solver artifacts and projected scores must be finite before commit or return. Numerical overflow throws and never publishes partial fitted state.
- Score names are exactly `PC1` through `PCk`. Scores have no missing bitmap. `replacingNumericColumns(_:columnNames:)` preserves row count and the original row mapping while replacing the feature schema.
- `fitTransform` performs the same successful fit followed by ordinary transform. It does not use `U * S`, so training and held-out projection share one arithmetic path.

The existing dataframe `fitPCA` keeps using `extractFeatures`. Its nil-to-zero rule therefore stays unchanged. The new prepared workflow is explicit and rejects missing values instead of silently changing that legacy rule.

## Module map and subtraction order

1. `PCA.swift`: first delete the uncalled private `dgesvd_wrapper` and `fitCPUCov`. Then add the prepared overloads, atomic fitted state, boundary validation, flat CPU packing, and column-producing projection.
2. `RandomizedSVD.swift`: first delete the uncalled private `dgemm_rsvd`. Then extract the current algorithm into the flat column-major kernel and adapt the existing public nested entry point.
3. `PreparedNumericBatch.swift`: no change. Its replacement, copy-on-write, matrix export, and provenance mechanisms already cover the result contract.
4. `DataFrame+Cluster.swift`: no change. `extractFeatures` remains live for other clustering APIs and preserves legacy PCA missing handling.
5. `PCA+PreparedTests.swift`: focused contract and end-to-end tests only.

This keeps the call chain at three places: PCA boundary, PCA backend, and the existing SVD kernel. There is no new public wrapper, model cache, allocator, pipeline protocol, or dataframe engine.

## Focused acceptance tests

1. Run `prepareNumericBatch`, `StandardScaler.fitTransform`, prepared PCA fit-transform, scaler transform, and held-out PCA transform. Assert `PC1...PCk`, repeated selected row provenance, and independent hand-computed scores.
2. Use a centered diagonal fixture with a known leading component, variance, 0.8 ratio, training scores, and held-out scores. This catches a self-consistent but wrong fit and transform pair.
3. For explicit CPU full and randomized solvers, compare prepared and nested means, component projectors, variance, and train/query score Gram matrices. Assert `.auto` keeps the current 80 percent rule. Keep the randomized seed, oversampling, and power count pinned.
4. On supported Apple silicon, compare prepared and nested explicit GPU results within existing Float tolerances and assert `resolvedDevice == .gpu` while transform uses Double results.
5. Fit with duplicate ordered names, reject reordered or renamed prepared input, accept a same-width nested transform, and verify a later legacy fit clears the prepared schema.
6. Reject missing, valid NaN, and both infinities before routing. Reject ragged nested rows, rank overflow, product overflow, and GPU Float overflow without changing the prior fitted state or resolved device.
7. Verify empty prepared transform returns empty `PC` columns with provenance, while empty prepared fit and legacy empty calls retain their documented errors.
8. Keep input copies and row-major and column-major matrix snapshots, fit and transform, then mutate another batch copy. Assert every snapshot and score output is unchanged. Export scores in both layouts and compare indexed values and provenance.
9. Refit successfully with a new schema and fixture, then assert every public fitted property and transform comes from the new fit. Force a failed refit and assert the complete prior state remains.
10. Test the flat randomized entry against the public nested result, including signs and LAPACK error checks. Any resource comparison must run the same solver, device, projection, and exported checks on both paths; otherwise make no allocation or speed claim.

## Rationale

The batch is the deepest existing interface for this workflow. Three overloads hide validation, routing, packing, fitting, schema checks, score naming, and provenance. Callers coordinate no lower-level stages. Fixed output names avoid an options type whose only job would be naming.

Column-oriented input and output match prepared preprocessing and `replacingNumericColumns`. A single centered column-major allocation then matches LAPACK and randomized BLAS. The design accepts a pack before CPU SVD in exchange for one representation shared by both CPU solvers. It accepts matrix export after projection in exchange for avoiding six more fit, transform, and fit-transform overloads plus a second provenance contract.

## Synthesis decision

This candidate chooses the batch boundary and rejects a matrix-first public API. Matrix input would save one pack only for callers that already own a matrix, while exposing layout and output ownership choices to every PCA caller. The required workflow already owns compact columns and needs labeled, provenance-preserving scores.

## Alternatives considered

- Public matrix fit and transform overloads expose layout and require a new provenance-preserving matrix output constructor. They hide less policy and do not compose directly with prepared preprocessing.
- A new `PCAScores` wrapper could carry names, values, and provenance, but `PreparedNumericBatch` already owns that contract.
- Storing both nested and flat components would speed one traversal at the cost of synchronized fitted caches. One component representation is simpler and keeps existing public behavior.

## Open questions and risks

- Are `PC1...PCk` the desired stable names, or does the project already have an undocumented naming convention that should replace them before implementation?
- Should nonfinite solver output map to a new PCA-specific error case, or is `SwiftMLError.invalidParameter` the intended public error vocabulary?

## Next implementation step

Delete the three proven-dead private functions, then add tests for the prepared signatures, schema, provenance, and transactional refit behavior before extracting the flat randomized kernel.
