# SwiftSci consumer and storage boundaries

Reviewed 2026-09-26 at commit `4c5bb953547ba5d84c7fd86bf868b1680c5f1811` in `/Users/crabel/Documents/src/SwiftSci`.

This is source inspection, not a new benchmark or a complete correctness audit. No production files changed. A bounded CPU-only diagnostic package built and ran after source inspection; no full suites or benchmarks ran. Citations below refer to that commit. I searched every module for dataframe and matrix conversions, then read the concrete implementations cited here. Coverage includes dataframe storage and conversion, preprocessing, statistics, ML, clustering, forecasting, sparse NLP, LLM caches, vision inputs, model selection, explanations, database ingestion, visualization, and agent statistics. It does not include a line-by-line audit of every estimator, serialization format, neural layer, or database driver.

## Finding

The recent filter and sort work optimizes table execution within the existing optional-array representation. The data-to-computation boundaries remain unfinished. Many consumers first reconstruct nested Double matrices, then copy them into the layout the actual kernel wants. Compact columns will help only if these consumers can operate on their buffers or perform one explicit packing step into the final layout.

No single physical representation fits all the current consumers. The common contract should describe type, shape, strides, validity, ownership, selected rows, and conversion policy. Nullable columns, dense matrices, sparse matrices, image tensors, and autoregressive caches should remain distinct structures with intentional adapters.

## Verified conversion paths

| Public operation | Current implementation and cost visible in source | Required boundary |
|---|---|---|
| `TypedColumn<T>` | Public stored `[T?]`; nonoptional initializer maps every value into an optional. Cached null count. [TypedColumn.swift:21](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftDataFrame/Columns/TypedColumn.swift:21), [TypedColumn.swift:50](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftDataFrame/Columns/TypedColumn.swift:50) | Typed value buffer plus optional validity; individual element access may remain optional without reconstructing an optional array. |
| `select` and `withColumn` | Select builds a new column descriptor list. `withColumn` copies map/order values and replaces only one column. These operations do not explicitly copy all column payloads. [DataFrame.swift:242](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftDataFrame/Core/DataFrame.swift:242), [DataFrame.swift:433](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftDataFrame/Core/DataFrame.swift:433) | Preserve cheap immutable sharing; distinguish metadata edits from payload mutation. |
| Filtering, sorting, `gathered(at:)` | Materializes each output column. Gather preserves supplied order and may duplicate rows. Parallel work uses estimated optional output bytes. [DataFrame.swift:647](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftDataFrame/Core/DataFrame.swift:647) | Carry selection/permutation until a consumer requires a contiguous result; remeasure dispatch thresholds after changing storage size. |
| `toFeatureMatrix` | Accepts only concrete Double, Int64, Bool columns; allocates `[[Double]]` and writes by columns into rows; nil becomes NaN. Float, Int32 and native Int columns are not accepted by these branches. [DataFrame+Matrix.swift:10](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftDataFrame/Core/DataFrame+Matrix.swift:10) | All supported numeric types; explicit output dtype and missing policy; flat matrix with order/strides. |
| `toTargetVector` | Allocates an N-by-1 nested matrix, then maps its rows to a vector. [DataFrame+Matrix.swift:49](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftDataFrame/Core/DataFrame+Matrix.swift:49) | Direct single-column borrow or one conversion, retaining row identity. |
| `toFlatFeatureMatrix` | Allocates one row-major Double array, but still accepts only Double/Int64/Bool and fills with strided writes by column. [DataFrame+Matrix.swift:59](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftDataFrame/Core/DataFrame+Matrix.swift:59) | Good starting seam; add requested layout, dtype and missing policy rather than another unrelated adapter. |
| `stats(for:)`, `describe` | `toDoubles()` drops nil and allocates Double values, then calls Stats. [TypedColumn.swift:196](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftDataFrame/Columns/TypedColumn.swift:196), [DataFrame+Stats.swift:7](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftStats/Extensions/DataFrame+Stats.swift:7) | Univariate skip-null reduction directly over values/validity, with explicit NaN policy and accumulation dtype. |
| `StandardScaler` on a dataframe | Converts optional columns to nested rows; fit extracts each column back into a contiguous Double buffer; allocates a shifted buffer per column. Transform allocates nested output and shifted row buffers, then dataframe wrapper reconstructs columns. Fit-and-transform wrapper extracts input twice. [DataFrame+Preprocessing.swift:10](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftPreprocessing/Core/DataFrame+Preprocessing.swift:10), [StandardScaler.swift:49](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftPreprocessing/Core/StandardScaler.swift:49), [StandardScaler.swift:100](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftPreprocessing/Core/StandardScaler.swift:100) | Column reductions and column transforms operating directly on contiguous storage; reusable scratch and optional unique-storage mutation. |
| Classifier/regressor dataframe overloads | Both call `toFeatureMatrix` and `toTargetVector`. Estimator protocols take `[[Double]]` and `[Double]`. [DataFrame+ML.swift:11](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftML/Core/DataFrame+ML.swift:11), [EstimatorProtocols.swift:84](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftML/Core/EstimatorProtocols.swift:84) | A prepared feature batch contract, with legacy array adapters at the edge. |
| CPU linear regression | Copies nested rows into column-major Double matrix plus bias; copies targets into LAPACK output workspace; `dgels_` mutates both work buffers. [LinearRegression.swift:106](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftML/Core/LinearRegression.swift:106) | Column-major writable workspace or consuming matrix ownership; do not mutate aliased dataframe storage through LAPACK. |
| GPU linear regression | `features.flatMap { row.map(Float.init) }`, constructs MLXArray, reshapes; predictions call `asArray(Float.self).map(Double.init)`. CPU fit also builds Float MLX weights for its public interface. [LinearRegression.swift:75](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftML/Core/LinearRegression.swift:75), [LinearRegression.swift:225](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftML/Core/LinearRegression.swift:225), [LinearRegression.swift:290](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftML/Core/LinearRegression.swift:290) | Explicit Float conversion once; let GPU consumers retain tensor results rather than forcing CPU materialization. |
| Dataframe KMeans/PCA/DBSCAN | A separate extractor accepts only Double and turns nil into zero, then creates nested rows. [DataFrame+Cluster.swift:5](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftCluster/Core/DataFrame+Cluster.swift:5) | Unify conversion semantics before storage replacement. Missingness currently differs from ML/preprocessing. |
| PCA | CPU randomized route copies/centers nested rows; other route allocates a flat centered matrix; GPU packs Float then reads output back. [PCA.swift:142](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftCluster/Core/PCA.swift:142), [PCA.swift:214](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftCluster/Core/PCA.swift:214), [PCA.swift:372](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftCluster/Core/PCA.swift:372) | Dense matrix view with consuming centered workspace; separate precision policies for CPU and GPU. |
| Histogram boosting | Extracts and sorts each column from nested rows; builds nested UInt8 bins; allocates gradients/hessians per iteration. [HistGradientBoosting.swift:142](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftML/Core/HistGradientBoosting.swift:142) | A feature-column scan and compact binned representation are more useful than forcing every learner onto a generic dense Double matrix. |
| Decision trees | Builds stable featurewise presorted row indices and reads `X[row][feature]`. [DecisionTree.swift:112](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftML/Core/DecisionTree.swift:112) | Column access plus index selections; avoid physically copying each node's subset. |
| ARIMA | `[Double]` series and optional nested exogenous regressors; rejects NaN/infinity in series; builds row-major design matrix then transposes it to column-major for LAPACK. [ARIMA.swift:45](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftForecast/Core/ARIMA.swift:45), [ARIMA.swift:387](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftForecast/Core/ARIMA.swift:387) | Ordered series, aligned exogenous rows, explicit gap policy, and one final solver layout. |
| Kalman filtering | Public nested matrices, internal flat Double arrays; BLAS GEMM/GEMV operate on row-major arrays; nested results materialize from flat slices. [KalmanFilter.swift:302](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftForecast/Core/KalmanFilter.swift:302) | Reuse a shared dense matrix representation; keep small recurrent state mutable and separate from the input table. |
| Arrow import/export | Import reads every Arrow element into new optional arrays; export appends every scalar through Arrow builders. [ArrowTableBridge.swift:8](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftDataFrame/Internal/ArrowTableBridge.swift:8), [ArrowTableBridge.swift:124](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftDataFrame/Internal/ArrowTableBridge.swift:124) | Real ownership-aware Arrow borrowing, including validity and chunk offsets. |
| NPY import | `NPYArray.toDoubles` copies binary buffers and widens several dtypes. `toDataFrame` builds new Double columns from that array. [NPYReader.swift:25](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftDataFrame/IO/NPYReader.swift:25), [NPYReader.swift:122](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftDataFrame/IO/NPYReader.swift:122) | Preserve dtype and memory order, borrow mapped input where safe, make casts explicit. |

The copy counts here identify allocations and data movement in source. They are not measured byte totals; Swift array assignments can share storage until mutation. A new dataframe value does not itself imply a copy of every element.

## AI phases need different storage

### Data preparation and scientific calculation

Column scans, predicates, stable permutations, grouped reductions and feature scaling favor typed contiguous columns. Missing values must retain their row positions until an operation chooses a documented policy. The next kernel may want one vector, many separate feature columns, or a dense matrix. Packing all three through nested Double arrays discards useful structure.

A representative current chain is CSV to optional columns, filter to gathered optional columns, sort to another gather, matrix extraction to nested Double rows, scaler to temporary Double columns and back to rows, model to column-major Double or row-major Float, then result back to Swift arrays and optional columns. The opportunities are eliminating redundant materializations and selecting a final compute layout once.

### Training and model selection

Many estimators consume dense row matrices; trees scan columns and selected rows; histogram models already derive UInt8 data. Cross-validation shares read-only input across candidate tasks, so mutations must never alter other models' observations. Grid search creates one task per parameter pair at [GridSearchCV.swift:59](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftOptimize/Search/GridSearchCV.swift:59). Buffer reuse needs explicit exclusivity, not a global mutable matrix cache.

KernelSHAP creates many feature perturbation vectors and concurrent model calls. Its background mean extracts each column with `map`, then reduces. See [KernelSHAP.swift:23](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftExplain/Core/KernelSHAP.swift:23). Batch prediction and reusable bounded scratch are useful here; arbitrary one-row tensor conversions would add overhead.

### Sparse language and categorical features

`SparseMatrix` is already a separate immutable CSR/CSC structure with Double values, Int inner indices and outer offsets. See [SparseMatrix.swift:23](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftPreprocessing/Core/SparseMatrix.swift:23). It should consume sparse builders directly rather than first allocating a dense matrix. One-hot encoding currently emits dense Double rows at [OneHotEncoder.swift:75](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftPreprocessing/Core/OneHotEncoder.swift:75). TFIDF has its own `SparseVector` representation and sparse output at [TFIDFVectorizer.swift:237](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftNLP/Core/TFIDFVectorizer.swift:237). There is an integration opportunity between these existing forms, not a reason to turn sparse values into nullable dataframe cells.

### Embeddings and retrieval

`LocalEmbeddingEngine.embed` returns dense Double vectors produced by character n-gram hashing and Accelerate normalization. It is not a learned transformer embedding in this implementation. [LocalEmbeddingEngine.swift:52](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftNLP/Core/LocalEmbeddingEngine.swift:52).

`VectorStore` holds one Double array per entry, plus ID and metadata, behind a lock. Replacement swaps an entry; removal shifts entries and rebuilds the ID map. [VectorStore.swift:19](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftCluster/Core/VectorStore.swift:19), [VectorStore.swift:123](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftCluster/Core/VectorStore.swift:123), [VectorStore.swift:158](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftCluster/Core/VectorStore.swift:158). A dense embedding matrix with stable row IDs could support contiguous search and batch updates; metadata belongs in a table. Index maintenance and model identity remain separate concerns.

### Vision and neural inference

`ImageDataset` stores flat Double pixels; U-Net prediction explicitly converts channel-major input to Float NHWC and MLXArray. [ImageDataset.swift:196](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftVision/ImageDataset.swift:196), [ImageDataset.swift:288](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftVision/ImageDataset.swift:288). Image shape and channel order need a tensor contract, not inference from column names.

LLM KVCache stores MLX arrays and concatenates on update. [KVCache.swift:26](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftLLM/Core/KVCache.swift:26). PagedKVCache keeps arrays of tensor slots and stacks them when retrieving, so its documentation does not establish contiguous paged attention or allocation-free decoding. [PagedKVCache.swift:19](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftLLM/Core/PagedKVCache.swift:19), [PagedKVCache.swift:91](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftLLM/Core/PagedKVCache.swift:91). Compact dataframe storage can reduce competition for memory, but it is not a direct replacement for weights, activations or KV cache buffers.

### Streaming and serving

`ChunkedDataFrame` streams DataFrames but each transform uses AsyncThrowingStream without a bounded buffering policy. `collect` retains every chunk then concatenates. [ChunkedDataFrame.swift:90](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftDataFrame/Core/ChunkedDataFrame.swift:90), [ChunkedDataFrame.swift:174](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftDataFrame/Core/ChunkedDataFrame.swift:174). A future batch interface needs backpressure and cancellation, not only smaller individual columns.

The current lazy engine still executes each filter through eager `df.filter` during collect. [LazyDataFrame.swift:61](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftDataFrame/Lazy/LazyDataFrame.swift:61). Carrying a selection into the final matrix export could avoid intermediate full-table gathers, but this is a proposed optimization, not existing behavior.

## Correctness boundaries to settle first

1. **Row alignment.** `DataFrame.correlationMatrix` independently drops nulls in each column, then correlates the resulting arrays. Equal surviving counts with different missing positions silently pair different original observations. [DataFrame+Stats.swift:50](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftStats/Extensions/DataFrame+Stats.swift:50). For example `[1,nil,3,4]` and `[2,4,nil,8]` become `[1,3,4]` and `[2,4,8]`, instead of jointly selecting rows 0 and 3. The external CPU diagnostic reproduced a correlation of 0.92857142857142827 instead of the jointly valid rows' correlation of 1.0. Visualization heatmaps repeat the pattern and substitute zero for some failures at [SwiftVisualization.swift:14](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftVisualization/SwiftVisualization.swift:14). The agent correlation tool also independently extracts columns at [SwiftSciToolbox.swift:49](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftAgent/SwiftSciToolbox.swift:49).
2. **Missing versus NaN versus zero.** Matrix conversion uses NaN; cluster conversion uses zero; `toDoubles` drops missing rows. New storage must not silently select one policy for all these APIs. Reductions, paired statistics, model fitting, text processing and temporal gaps need their own explicit contracts.
3. **Type fidelity.** `SupportedType` includes Float, Int32 and native Int, but matrix extraction does not. Int64-to-Double can round integers above 2^53; GPU Float narrowing has a different precision envelope. Default routing should not silently turn a scientific precision requirement into a lower-precision operation.
4. **Order and shape.** `NPYArray` records `fortranOrder`, but `toDataFrame` indexes only as row-major at lines 131-146. The external diagnostic reproduced the order error on a 2-by-3 Fortran array. No fix was applied. Its docs' zero-copy statement does not match the implementation. Signedness, endianness, truncated payloads, multi-dimensional shapes and byte strides need validated input contracts.
5. **Ownership and async lifetime.** `ArrowDataBuffer` accepts an optional arbitrary owner and raw pointer. No current production caller constructs it outside its own slicing method. Its test accesses an Array pointer only within `withUnsafeBytes`, passing an unrelated MockOwner. That test does not establish post-closure pointer validity or actual Arrow owner retention. [ArrowDataBuffer.swift:13](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftDataFrame/Internal/ArrowDataBuffer.swift:13), [DataFrameArrowTests.swift:259](/Users/crabel/Documents/src/SwiftSci/Tests/SwiftDataFrameTests/DataFrameArrowTests.swift:259).
6. **Empty output schema.** Current gather returns schema-less `DataFrame.empty` for zero selected rows. A prepared model batch still needs dtype, feature order and shape when row count is zero. Decide this explicitly instead of relying on the old behavior.

The existing tests inspect common matrix types and nil-to-NaN behavior, but they do not establish these broader contracts. See [DataFrameRelease35CoverageTests.swift:106](/Users/crabel/Documents/src/SwiftSci/Tests/SwiftDataFrameTests/DataFrameRelease35CoverageTests.swift:106). The inspected dataframe correlation test is null-free. [StatsTests.swift:290](/Users/crabel/Documents/src/SwiftSci/Tests/SwiftStatsTests/StatsTests.swift:290).

## Mutations need not all be expensive

Fixed-width packed values plus a validity bitmap permit a unique owner to overwrite an element and its validity bit in constant time. Append with reserved capacity is amortized constant time. The expensive cases are shared storage, resizing, insertion/deletion in the middle, changing variable-length content, and mutation while a foreign or GPU consumer still reads the buffer.

For the proposed compact design:

- Use an exclusive builder for CSV/database ingestion and repeated appends; reserve both payload and validity capacity, maintain null count during writes, then freeze.
- Offer scoped mutable access only when storage is uniquely owned, correctly typed, writable, and not in use asynchronously. Otherwise copy the affected column or chunk once, then perform the whole update batch.
- Provide batched scatter updates, including deterministic repeated-index behavior and validity updates. Avoid invoking copy-on-write separately for each cell.
- Treat structural insertion/deletion separately. Chunk append, selection/deletion maps and periodic compaction may fit interactive edits, but extra indirection can hurt repeated scientific scans. Benchmark the full edit-then-compute sequence.
- Keep LAPACK scratch writable and owned. Its destructive solver calls must never mutate a borrowed dataframe or an Arrow reader's shared memory.
- Strings need offsets plus byte storage or an established Arrow representation; fixed-width mutation claims do not extend automatically to length-changing text edits.
- An immutable table can expose inexpensive snapshots while a unique builder handles edits. This preserves Swift value expectations without forcing every update through a full-table reconstruction.

These are design proposals. Their performance is not established by this inspection.

## Apple silicon implications from current code

`HardwareRouter` uses sample counts and feature counts to choose CPU/GPU. It does not include packing cost, buffer residence, numeric precision, available memory or the next operation. It maps ANE requests to GPU for training. [HardwareRouter.swift:19](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftPreprocessing/Core/HardwareRouter.swift:19). A prepared batch should expose dtype and residence so a routing decision can include those constraints.

`WiredMemoryManager` is a concurrent-task limiter. Its limit is based on active processor count; it does not reserve a byte budget. [WiredMemoryManager.swift:4](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftPreprocessing/Core/WiredMemoryManager.swift:4). Smaller columns help memory pressure, but unmanaged simultaneous matrix copies can still exhaust available memory. Peak live bytes and bounded workspaces belong in end-to-end measurements.

Unified memory does not remove the explicit copies seen above, convert Float64 to Float32 for free, or make a strided column selection one contiguous matrix. A no-copy adapter must prove layout, dtype, lifetime and synchronization compatibility. Otherwise one well-placed conversion is the honest API.

## Proposed acceptance criteria for the next branch

Priority 0, semantics and access:

- One shared conversion policy for null handling, row alignment, precision, feature order and matrix layout.
- Typed borrowed buffer access with owner lifetime, read-only/mutable status, count, offset and validity offset.
- Explicit conversion results distinguishing a borrowed view from a newly allocated packed buffer.
- Tests for Int32/Int/Float, large Int64, nil/NaN/infinity, alternate missing positions, empty selections, reordered and duplicate indices, and escaped owner lifetime.

Priority 1, real operation chains:

- Filter and stable sort to a selected set of feature columns, directly to a CPU Double solver matrix.
- The same chain directly to a Float MLX batch, with conversion precision checked and result materialization timed.
- Column-wise scaler fit and transform without reconstructing nested rows.
- Direct target-vector extraction and row-aligned correlation.
- Append and sparse patch workloads, both unique and shared ownership, followed by repeated filters and matrix operations.
- Arrow import to filter to compute to Arrow export, accounting for actual bytes copied.

Priority 2, specialized consumers:

- Sparse vector/CSR/CSC adapters without dense intermediate matrices.
- Time-series windows and lag features with explicit gap policy.
- Chunked model batches with backpressure and memory budgets.
- Dataframe metadata linked to external tensor/embedding buffers rather than expanding every tensor element into a table column.

Measure complete workflows as well as individual kernels. Report conversion time, allocations, peak live memory, steady-state compute, mutation cost, numeric accuracy, and copy counts. Retain separate row-major, column-major, sparse and tensor types where their algorithms need them. The shared work is ownership and conversion contracts, not forcing every algorithm into a single container.

## Executed boundary diagnostic

[BoundaryProbe source](/Users/crabel/local-ai/spl/swiftsci/data-architecture-research/probes/Sources/BoundaryProbe/main.swift) imports only SwiftDataFrame and SwiftStats. Release build completed in 29.69 seconds. The source constructs inputs and independently computes or supplies expected results. No production source changed. [Exact output](/Users/crabel/local-ai/spl/swiftsci/data-architecture-research/probes/result.jsonl), [build and source provenance](/Users/crabel/local-ai/spl/swiftsci/data-architecture-research/probes/metadata.json).

| Boundary | Input and expected result | Observed result |
|---|---|---|
| Paired missing values | x = `[1,nil,3,4]`, y = `[2,4,nil,8]`; jointly valid original rows 0 and 3 yield Pearson 1.0 | 0.92857142857142827 from independently compacted vectors |
| NumPy Fortran order | `<f8`, shape `[2,3]`, Fortran true, physical payload `[1,4,2,5,3,6]`; expected logical rows `[[1,2,3],[4,5,6]]` | `[[1,4,2],[5,3,6]]` |
| NumPy Int64 precision | `<i8`, shape `[3]`, values 9007199254740992, 9007199254740993, 9007199254740994 | `toInt64s` preserves all values; dataframe dtype becomes Double and the middle value becomes 9007199254740992 |
| Numeric matrix inputs | Float, Int32 and native Int columns, each containing `[1,2]` | All three throw `Cannot cast column 'v' to Double.` |

These are demonstrated behaviors, not a claim that every conversion API fails. Null-free Double/Int64/Bool matrix paths remain covered by existing tests. The Int64 result shows an implicit lossy conversion; a future API could permit that conversion explicitly, but must distinguish it from dtype-preserving interchange.
