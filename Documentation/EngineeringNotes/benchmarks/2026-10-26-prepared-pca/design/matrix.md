# Problem

PCA currently accepts nested `Double` rows, which forces prepared data through row-array materialization and gives transformed data no schema or row provenance. The existing `PreparedNumericMatrix` already owns a contiguous snapshot in either layout, but its package-only constructor prevents SwiftCluster from returning a provenance-preserving score matrix. The design must retain legacy nested calls, explicit solver/device behavior, MLX Float arithmetic and CPU-stream SVD, while sharing one flat numerical implementation.

# Usage (caller's view)

Prepared callers pack once, choose the layout for their pipeline, and receive labeled scores with the original row mapping:

```swift
let train = try frame.prepareNumeric(columns: ["x", "y", "z"])
let test = try frame.prepareNumeric(columns: ["x", "y", "z"])
let trainMatrix = try train.matrix(order: .columnMajor, missing: .reject)
let testMatrix = try test.matrix(order: .columnMajor, missing: .reject)

let pca = try PCA(nComponents: 2, svdSolver: .full, device: .cpu)
let scores = try await pca.fitTransform(trainMatrix)
let heldOut = try await pca.transform(testMatrix)
// scores.columnNames == ["PC1", "PC2"]
// scores.originalRowIndices == train.originalRowIndices
```

The same fitted actor projects a row-selected matrix without losing repeated provenance:

```swift
let selected = try test.selectingRows([4, 1, 4])
let projected = try await pca.transform(try selected.matrix(order: .rowMajor,
                                                             missing: .reject))
```

Existing nested callers keep their calls and return types:

```swift
let rows = try await pca.fitTransform([[1.0, 0.0], [0.0, 1.0]])
```

# Shape

`PCA` gains three actor methods, with no batch overloads:

```swift
public func fit(_ matrix: PreparedNumericMatrix) async throws
public func transform(_ matrix: PreparedNumericMatrix) async throws -> PreparedNumericMatrix
public func fitTransform(_ matrix: PreparedNumericMatrix) async throws -> PreparedNumericMatrix
```

The prepared methods require a nonempty rectangular dense matrix, `nComponents <= min(rows, columns)`, and finite values. Callers use `missing: .reject`; missing entries and valid NaNs are both rejected at the PCA boundary because matrix storage intentionally carries no validity bitmap. A matrix fit records the exact input `columnNames`; later prepared transforms require the same ordered names. Legacy nested fits clear this optional schema and retain width-only checks, preserving their existing role and behavior.

`PreparedNumericMatrix` gains one public helper in SwiftDataFrame:

```swift
public func replacingValues(_ values: [Double], columnNames: [String]) throws
    -> PreparedNumericMatrix
```

It checks `values.count == rowCount * columnNames.count` with checked arithmetic, keeps the receiver's order and private row provenance, and returns an owned snapshot. This is the only output bridge PCA needs; it also makes dimension reduction explicit without exposing `sourceRows` or a transport type.

The internal PCA engine accepts a validated matrix view and creates one centered, column-major `Double` buffer. Column-major input is traversed directly; row-major input is reordered once. Mean accumulation remains row-order `Double`. Full SVD consumes that buffer. Randomized SVD gets a lower-level column-major entry point (`compute(columnMajor:rows:columns:...)`) and uses the existing p/q/seed defaults; its public nested API becomes a validating adapter. Components, sign normalization, selected variance, total variance, and ratios retain current formulas. GPU fitting still packs row-major `Float`, computes the MLX mean and centering as `Float`, and calls `svd(..., stream: .cpu)` before widening exported state to `Double`.

Prepared transform computes scores directly into the receiver's order, using fitted `mean` and components with the existing ascending feature loop. `fitTransform` commits the model before building scores, so its output is the same as `fit` followed by `transform`. Fit computes all new state in locals and commits only after validation, routing, solver completion, and output preparation succeed; a failed refit therefore leaves the prior model intact. Device routing and `.auto` CPU solver thresholds remain unchanged, and no new solver default, allocator, cache, or model runtime is introduced.

Module map:

- `SwiftDataFrame/Core/PreparedNumericBatch.swift`: `replacingValues` on `PreparedNumericMatrix`, preserving order/provenance and snapshot semantics.
- `SwiftCluster/Core/PCA.swift`: prepared overloads, schema validation, flat centered buffer, direct score output, and atomic state commit; nested methods adapt into the same engine.
- `SwiftCluster/Decomposition/RandomizedSVD.swift`: checked flat column-major implementation used by PCA; nested `compute` remains the public compatibility adapter.
- Before construction, remove the three grounded dead private LAPACK definitions (`dgesvd_wrapper`, `fitCPUCov`, `dgemm_rsvd`); keep public `RandomizedSVD.Result.U` and `svdFlip`.

The public surface is deliberately deep: one matrix input and one matrix output hide layout traversal, validation, centering, solver selection, backend precision, sign policy, and provenance handling. Callers retain only data preparation, solver/device choice, and feature-name identity. No temporal load/validate/transform modules or pass-through batch facade is added.

# Synthesis decision

This is the matrix-oriented candidate. It favors the existing contiguous ownership and makes the one unavoidable dimension-changing output operation explicit. Batch-oriented convenience overloads were omitted because they would expose a second prepared entry point while adding no capability beyond `batch.matrix(...)`.

# Tradeoffs accepted

- We accept one pack from row-major input into centered column-major storage in exchange for a single solver representation and no nested rows.
- We accept rejecting valid NaNs at PCA's dense boundary in exchange for a clear finite-value invariant when validity bits are unavailable.
- We accept prepared schema checks only after a prepared fit in exchange for legacy nested fits remaining width-compatible.
- We accept a public `replacingValues` helper in SwiftDataFrame in exchange for keeping provenance storage private and avoiding a PCA-specific output type.
- We accept retaining full-SVD workspace and public randomized `U` until existing API contracts change; this design removes only proven dead wrappers.

# Alternatives considered

An API accepting `PreparedNumericBatch` and returning a replacement batch would preserve names naturally, but it exposes feature-column storage and forces PCA to own a batch-to-matrix conversion policy. It also needs a second output representation for reduced width; the matrix surface hides more complexity with fewer calls.

Keeping only nested APIs and adding an internal flattening optimization would improve execution but cannot preserve prepared row provenance or output schema, so it fails the end-to-end prepared workflow.

Adding a public generic flat-buffer solver protocol would expose layout, strides, and backend policy to callers. It has a larger, shallower interface than the two existing matrix methods and leaks numerical transport details.

# Open questions and risks

- Should prepared transforms require names even when a model was fitted through a nested call, or is width-only compatibility for that mixed case the desired migration behavior?
- Should generated score names be `PC1...PCk` permanently, or should a future caller-supplied prefix be added only after a real use case?
- Does the lower-level randomized kernel need a package-visible flat result type, or can its internal result remain private while preserving the public nested `U`/`Vt` contract?

# Focused validation and tests

Add focused tests for: both matrix layouts against legacy numerical answers; fit/held-out transform with exact names; repeated and reordered source rows in `originalRowIndices`; input and exported-output snapshot preservation after source mutation; missing, valid NaN, infinity, empty, rank, overflow, ragged legacy, and schema errors; rejected refits preserving the prior model; full/randomized/auto and explicit CPU/GPU routing parity; GPU Float mean plus CPU-stream SVD tolerance; and `fitTransform == fit + transform`. Keep existing nested, dataframe missing-to-zero, sign, ratio, and solver-threshold tests. Run `PCATests`, `PCA+RoutingTests`, `RandomizedSVDTests`, and prepared matrix tests on Apple silicon; hosted CI remains insufficient for MLX coverage.

# Next implementation step

Remove the three dead private definitions, then add and test `PreparedNumericMatrix.replacingValues` before wiring PCA's validated matrix overloads to the shared flat solver.
