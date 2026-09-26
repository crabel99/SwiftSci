# Data storage boundaries for SwiftSci on Apple silicon

Research date: 2026-09-26. Status: design recommendation, no production implementation or dependency changes.

## Decision

The current dataframe optimization work has a tested endpoint, but the broader data-to-computation architecture is unfinished. Keep the compact-storage work. Its next milestone should be a complete workflow that preserves compact columns through selection and preprocessing, then prepares the exact matrix or tensor the consumer needs.

Use shared ownership and access rules across several representations: nullable columns, dense arrays, sparse matrices, and table batches. Preserve their distinct layouts. A numerical routine should receive its required layout with a documented lifetime and mutation policy. Repeated conversion through nested optional or Double arrays should become an edge compatibility path.

Compact numeric mutation can be cheap. Our experimental representation stores ordinary fixed-width values with a validity bitmap. It does not compress values. An exclusive owner can overwrite a value directly. Shared snapshots, structural edits, capacity growth and asynchronous readers introduce separate costs.

For the user's main workflow, the proposed path is:

```text
CSV / Arrow / database
        |
compact typed columns + validity
        |
filter selection + stable sort permutation
        |
column reductions / scaling
        |
prepare one compute batch, preserving row identity
        |
        +-- Double matrix, requested order --> Accelerate / LAPACK
        +-- Float tensor, requested shape --> MLX / Metal
        +-- CSR / CSC matrix -------------> sparse algorithms
        |
results joined to original rows by the retained mapping
```

This is a proposed execution path. Current SwiftSci often materializes a new table after each filter or sort and reconstructs arrays again at the numerical boundary.

## Evidence and review scope

The host reports Apple M4 Max with 128 GiB of unified memory. No hardware-specific bandwidth claim was measured during this investigation.

| Codebase | Reviewed revision or version | Coverage |
|---|---|---|
| SwiftSci | `4c5bb953547ba5d84c7fd86bf868b1680c5f1811`, branch `codex/dataframe-pipeline-optimization` | Storage, selection, conversion, representative consumers in every module family, compact prototypes |
| Kiraa Swift Pandas | `fc5d957401f70e9d3b6b07270f7f300d488fd39f` | Numeric ownership, nullable mutation, borrowed buffers, vector storage, lazy optimizer, Metal search |
| MLX Swift used by SwiftSci | Pinned 0.31.6, `0bb916c67f4b9e5c682cbe02a42c701c93ab5021` | Array construction/export, C/C++ allocation path, managed-pointer lifetime |
| Separate MLX Swift checkout | `901941965d82e4a216d4d117231d847d194c563d` | Comparison of managed-pointer finalizer behavior |
| MLX Swift LM | `ee673d6a71d76e67b532dc7eaf91d92edc3bb8bb` | Capacity-based and rotating KV cache implementations |
| NumPy / pandas / SciPy | Tagged 2.4.0 / 3.0.0 / 1.17.0 | Ownership and assignment, nullable and Arrow mutation, LAPACK dispatch, compressed sparse updates |
| Arrow / DLPack | Arrow 21.0.0 bridge source, published format interfaces; DLPack 1.2 | Layout, lifetime and interchange contracts |

Three research agents inspected separate consumer, interoperability, and mutation lanes. The root review checked MLX and AI integration and cross-checked key findings. This was a broad source review, not a line-by-line audit of every estimator or backend. Code-level allocations are identified below; they are not measured allocation profiles.

Supporting reviews and exact line citations are retained locally:

- [SwiftSci consumers](/Users/crabel/local-ai/spl/swiftsci/data-architecture-research/agent-notes/swiftsci-consumers.md)
- [Array interoperability](/Users/crabel/local-ai/spl/swiftsci/data-architecture-research/agent-notes/array-interop.md)
- [Mutation and hardware](/Users/crabel/local-ai/spl/swiftsci/data-architecture-research/agent-notes/mutation-hardware.md)

Earlier Debug and Release suites each passed 891 tests. Earlier compact-storage experiments showed a substantial resident-memory benefit but slower optional-to-compact-to-optional conversion. Those results support integrating consumers before replacing storage. They do not establish that the proposed architecture is faster. See the [storage experiment](/Users/crabel/local-ai/spl/swiftsci/filter-optimization/storage-experiment/REPORT.md) and [production comparison](/Users/crabel/local-ai/spl/swiftsci/production-comparison/results/20260926T104626Z/REPORT.md).

## Problems demonstrated in the current implementation

A separate CPU-only package imported the actual SwiftDataFrame and SwiftStats products. It built and ran six diagnostic cases without modifying production code. These are reproductions, not fixes or a new complete test suite.

| Boundary | Executed result | Required contract |
|---|---|---|
| Correlation with different null positions | `[1,nil,3,4]` and `[2,4,nil,8]` produce `0.92857142857142827`. Jointly valid original rows 0 and 3 produce `1.0`. | Apply a shared row selection to paired quantities; define pairwise versus complete-case deletion. |
| Fortran-order NPY conversion | Shape `[2,3]`, payload `[1,4,2,5,3,6]` becomes `[[1,4,2],[5,3,6]]` instead of `[[1,2,3],[4,5,6]]`. | Preserve order and strides when importing a matrix. |
| Int64 NPY conversion | `9007199254740993` becomes Double `9007199254740992`; the direct Int64 reader preserves it. | Preserve dtype by default; require an explicit lossy conversion policy. |
| Feature-matrix extraction | Float, Int32 and native Int columns each throw a cast error. | Define numeric type coverage consistently across storage and consumers. |

[Diagnostic source](/Users/crabel/local-ai/spl/swiftsci/data-architecture-research/probes/Sources/BoundaryProbe/main.swift), [results](/Users/crabel/local-ai/spl/swiftsci/data-architecture-research/probes/result.jsonl), [provenance](/Users/crabel/local-ai/spl/swiftsci/data-architecture-research/probes/metadata.json).

These cases were missing from the earlier passing suite. Storage changes must preserve intended semantics rather than preserve these defects. Separate regression fixes should precede performance comparisons that depend on these paths.

## Where existing SwiftSci operations meet storage

| Consumer | Current implementation | Integration opportunity |
|---|---|---|
| `TypedColumn` | Public immutable `[T?]`; constructing from `[T]` introduces optionals. | Packed fixed-width values, optional validity, element-level optional access without rebuilding an array. |
| Filter, sort, gather | Materializes output columns. Gather can reorder and duplicate rows. | Carry a selection or permutation until a consumer benefits from gathering. |
| `toFeatureMatrix` / `toTargetVector` | Nested Double rows; target extraction constructs an N-by-1 matrix first. | One flat prepared batch; direct target extraction. |
| `toFlatFeatureMatrix` | Already has flat row-major output, limited numeric types and implicit nil-to-NaN policy. | Extend this existing boundary with explicit dtype, order and null policy. |
| StandardScaler | Columns to nested rows, back to temporary columns, then rows and columns again. | Fit and transform columns directly; pack only for the next consumer. |
| CPU linear regression | Builds a column-major Double matrix with bias, then LAPACK overwrites workspace. | Prepare the final solver layout once; give destructive kernels exclusive scratch. |
| GPU regression / PCA | Flattens nested rows and converts to Float; constructs MLX arrays; reads results back. | Retain prepared tensors across operations, delaying host result conversion. |
| Trees / histogram boosting | Feature scans, presorted row indices, compact UInt8 bins. | Column access with selections and specialized derived bins. Dense Double is not a universal model input. |
| MLP / Adam | Flat mutable weights, gradients and moment arrays. Best-weight snapshots rely on Swift value semantics. | Owned tensor workspaces with safe snapshots and controlled in-place updates. |
| ARIMA / Kalman | Ordered Double series, dense design matrices, small recurrent state; some row-to-column-major copies. | Explicit temporal alignment and solver layout; reuse recurrent buffers. |
| One-hot / TFIDF / sparse matrices | Dense one-hot output, separate sparse vectors, existing CSR/CSC structure. | Direct sparse construction and adapters without a dense intermediate. |
| VectorStore | Separate Double vector per entry plus ID and metadata. | Dense vector batches with stable IDs; keep metadata in columns. |
| Vision | Flat pixels converted to Float NHWC tensors for models. | Explicit image shape, channel order, normalization and dtype. |
| Arrow / NPY | Arrow builders copy scalars; NPY dataframe conversion copies through Double. | Retained typed import/export where compatible; explicit materialization elsewhere. |
| Chunked / lazy execution | Lazy filters still execute eager table filters. Streaming transforms lack bounded buffering; collect retains chunks. | Selection fusion, backpressure, cancellation and bounded batch memory. |

Source entry points include [TypedColumn](../../Sources/SwiftDataFrame/Columns/TypedColumn.swift), [DataFrame](../../Sources/SwiftDataFrame/Core/DataFrame.swift), [matrix conversion](../../Sources/SwiftDataFrame/Core/DataFrame+Matrix.swift), [StandardScaler](../../Sources/SwiftPreprocessing/Core/StandardScaler.swift), [LinearRegression](../../Sources/SwiftML/Core/LinearRegression.swift), [MLP](../../Sources/SwiftML/Core/MLP.swift), [SparseMatrix](../../Sources/SwiftPreprocessing/Core/SparseMatrix.swift), [Arrow bridge](../../Sources/SwiftDataFrame/Internal/ArrowTableBridge.swift), [NPY reader](../../Sources/SwiftDataFrame/IO/NPYReader.swift), and [chunked execution](../../Sources/SwiftDataFrame/Core/ChunkedDataFrame.swift). The consumer review gives exact lines for the remaining modules.

The main opportunity is reducing repeated preparation work. A new table descriptor does not necessarily copy payloads because Swift arrays can share until mutation. Count actual materializations, not object assignments.

## What AI needs at each phase

The bottlenecks in this table are hypotheses to profile for the relevant workload. They are not new timing results.

| Phase | Structures and operations | Likely limiting costs | Storage requirement |
|---|---|---|---|
| Ingestion and cleaning | Typed columns, strings, validity; parsing, filtering, grouping, sorting | Parsing, allocations, memory traffic, hash/comparison work | Builders with capacity, consistent null semantics, cheap typed scans |
| Feature preparation | Column reductions, scaling, row selection, target alignment | Repeated copies, dtype conversion, gathering | Prepare requested columns directly into one final layout; retain row mapping |
| Sparse text/categorical preparation | Token IDs, ragged sequences, CSR/CSC | Index construction, irregular access, accidental dense expansion | Offset/value buffers; canonical sparse indices; separate masks and sequence lengths |
| Classical model fitting | Dense matrices, selected columns, binned features | BLAS/LAPACK compute, tree scans, workspace allocation | Algorithm-specific dense, column or binned input; explicit precision |
| Neural training | Batches, weights, activations, gradients, optimizer moments | Compute, activation storage, live graph memory | Dense device-compatible tensors; reusable workspaces; preserve values needed by backward computation |
| Validation and search | Shared input plus concurrent model state | Duplicate preparation, competing workspaces | Immutable input snapshots and byte-budgeted concurrency |
| LLM prompt processing | Token batches, masks, weights, growing KV cache | Attention/matrix work and intermediate storage | Ragged or padded batches with documented masks; tensor-native state |
| LLM token generation | Weights and retained KV tensors; append/update and attention | Often bandwidth and cache capacity at low batch size; model-dependent | Capacity or page management consumed directly by attention; bounded lifetime and reuse |
| Embedding retrieval | Dense Float vectors, IDs, metadata, search indexes | Scans, irregular index access, candidate gathering | Vector plane plus stable IDs; index and norm invalidation after edits |
| Reporting and persistence | Scalar results, scores, labels, row IDs | Materialization and serialization | Restore table columns at the output boundary without losing alignment |

A compact dataframe can leave more unified memory available for models and context. It does not increase a model's configured context limit, replace its KV cache, or remove the compute cost of longer context. Quantify usable workload size under memory pressure separately from single-operation speed.

SwiftSci's current local embedding engine uses normalized character n-gram hashing, not a transformer encoder. Its storage needs should not be inferred from its class name alone. See [LocalEmbeddingEngine](../../Sources/SwiftNLP/Core/LocalEmbeddingEngine.swift).

## Memory costs that the design must expose

For N fixed-width elements of width w, the proposed numeric payload uses N × w bytes plus 8 × ceil(N / 64) bytes when a UInt64 validity bitmap exists. This excludes capacity slack, owners and allocator overhead. With no nulls the bitmap can be absent. Compare this with the measured Swift optional stride for each concrete type rather than assuming every optional doubles storage.

Selections have costs too. An Int row-index array on this arm64 host takes 8 bytes per selected row before overhead. For one narrow column it can cost more than copying the selected values; for many columns, sharing one selection can save substantial payload copying. A retained selection also keeps its base buffers alive. Selection density, table width and the next consumer must guide materialization.

A dense N-by-P compute batch costs N × P × element width, plus any solver workspace. Training adds live activations, gradients and optimizer states. For a conventional cache with equal key/value head dimensions, KV payload scales approximately as 2 × layers × batch × retained tokens × KV heads × head dimension × bytes per element. Quantization metadata, padding, sliding windows and model-specific cache types change that estimate.

The relevant memory budget includes base columns, retained snapshots, selections, packed batches, device intermediates, model state and concurrent jobs at the same time. Reducing one stored column is useful, but preparing several full copies can consume those savings. Record peak live allocations and usable workload capacity alongside throughput.

## Apple silicon and MLX constraints

Contiguous typed CPU buffers help compiler specialization, cache locality and Accelerate access. Null checks can be removed for all-valid columns. Irregular selections may need gathering; a unit-stride vector and an arbitrary row-index list are different inputs. Apple's [vDSP stride guidance](https://developer.apple.com/documentation/accelerate/controlling-vdsp-operations-with-stride) supports testing contiguous paths first.

Unified memory gives CPU and GPU access to compatible shared resources. It does not eliminate packing, scalar conversion, synchronization or ownership. A Metal-compatible allocation must stay alive through command completion, and host writes cannot race device reads. See [shared storage](https://developer.apple.com/documentation/metal/mtlstoragemode/shared) and [resource synchronization](https://developer.apple.com/documentation/metal/resource-synchronization).

In the pinned MLX Swift implementation:

- Generic Swift array construction calls `mlx_array_new_data`; the C++ constructor allocates storage and copies elements. The `converting: [Double]` overload first builds Float values.
- `asArray` evaluates and copies. `asData` evaluates; its no-copy variants require the caller to retain the MLXArray. The returned Data uses no deallocator to own the original allocation.
- `asMTLBuffer(noCopy: true)` still evaluates, requires contiguous storage for its no-copy branch, and requires the original array to outlive the buffer without mutation. Otherwise it takes a copying path.
- Managed raw-pointer import requires a compatible allocation and contiguous shape/dtype. It is not a general permission to escape an Array's scoped pointer.

These are pinned source observations in [initializers](https://github.com/ml-explore/mlx-swift/blob/0bb916c67f4b9e5c682cbe02a42c701c93ab5021/Source/MLX/MLXArray%2BInit.swift), [byte export](https://github.com/ml-explore/mlx-swift/blob/0bb916c67f4b9e5c682cbe02a42c701c93ab5021/Source/MLX/MLXArray%2BBytes.swift), and [Metal export](https://github.com/ml-explore/mlx-swift/blob/0bb916c67f4b9e5c682cbe02a42c701c93ab5021/Source/MLX/MLXArray%2BMetal.swift).

There is also a version-specific ownership concern. The pinned raw-pointer finalizer uses `passRetained` with `takeUnretainedValue`; its local release helper is unused. The C callback invokes the finalizer without releasing that Swift capture box. The separate newer checkout uses `takeRetainedValue` and explains the retained-resource leak. This is source evidence, not a runtime leak measurement in this investigation. A managed-buffer adapter must verify release-once behavior and choose a dependency version containing the fix before relying on that path. [Newer finalizer implementation](https://github.com/ml-explore/mlx-swift/blob/901941965d82e4a216d4d117231d847d194c563d/Source/MLX/MLXArray%2BInit.swift).

MLX operations are lazy. Assignment to a Swift property does not prove device execution or copying. Explicit evaluation and host reads establish important timing boundaries. Float64 is CPU-only in the reviewed MLX documentation; GPU routing must respect required precision. See [lazy evaluation](https://github.com/ml-explore/mlx/blob/main/docs/src/usage/lazy_evaluation.rst) and [data types](https://ml-explore.github.io/mlx/build/html/python/data_types.html).

[HardwareRouter](../../Sources/SwiftPreprocessing/Core/HardwareRouter.swift) currently uses sample/feature thresholds. It omits packing cost, precision, memory residence and subsequent operations. [WiredMemoryManager](../../Sources/SwiftPreprocessing/Core/WiredMemoryManager.swift) limits concurrent tasks rather than reserving bytes. A future dispatcher should first reject incompatible dtype/layout/device combinations, then compare total preparation, execution and result-access costs. The Neural Engine requires its own supported model/runtime path; shared buffers do not make arbitrary dataframe kernels run there.

### KV caches illustrate a separate integration problem

SwiftSci's [KVCache](../../Sources/SwiftLLM/Core/KVCache.swift) concatenates existing and new tensors on update. [PagedKVCache](../../Sources/SwiftLLM/Core/PagedKVCache.swift) stores tensor objects per slot and stacks live slots when read. These paths need evaluated profiling before assigning a copying cost.

PagedKVCache also has source-level correctness concerns. A shared block table can record a page after allocating it only in the current layer; a subsequent layer can index a page it has not allocated. Reset removes sequence metadata while retaining physical page arrays. Neither issue was executed in the CPU-only probes. They deserve isolated tests before cache performance work.

MLX Swift LM's [KVCacheSimple](https://github.com/ml-explore/mlx-swift-lm/blob/ee673d6a71d76e67b532dc7eaf91d92edc3bb8bb/Libraries/MLXLMCommon/KVCache.swift#L408) grows capacity in steps and writes new slices. Its rotating cache bounds storage and updates slots. These are useful implementation comparisons, not proof that the same parameters fit SwiftSci.

The PagedAttention research combines page management with attention that consumes that representation. Merely naming a container "paged" does not provide that integration. Its GPU-server performance results cannot predict Apple silicon results. [Kwon et al., PagedAttention](https://arxiv.org/abs/2309.06180).

## Interoperability and the proposed adapter boundary

| Representation | Required metadata | Appropriate interchange |
|---|---|---|
| Nullable numeric column | Dtype, count, values offset/stride, validity bit offset, null count, owner | Native Swift kernels; Arrow when layout is compatible |
| Dense tensor | Dtype, shape, strides with explicit units, byte offset, device, owner, access mode | Accelerate, MLX, optional NumPy/buffer or DLPack adapter |
| Sparse matrix | Shape, format, index width, offsets/indices, values, canonicalization rules | Existing SwiftSci CSR/CSC consumers and explicit SciPy adapters |
| Table batch | Schema, equal row counts, column owners, selection and row identity | Arrow batches, streaming ingestion, preprocessing |

NumPy uses a homogeneous array with shape and affine strides. Separately allocated dataframe columns generally need one packing step to form a 2D matrix. A compatible individual column can be a shared vector. A table backed by one homogeneous matrix could offer column views, but would inherit that matrix's layout and mutation tradeoffs. See the [NumPy array interface](https://numpy.org/doc/stable/reference/arrays.interface.html) and [C API ownership](https://numpy.org/doc/stable/reference/c-api/array.html).

SciPy's LAPACK wrappers may allocate for dtype or memory-order compatibility even when overwrite is allowed. CSR/CSC distinguish updating an existing value from structural insertion. Build sparse structure once where possible, then reuse it for value updates and solves. See [LAPACK wrappers](https://docs.scipy.org/doc/scipy/reference/linalg.lapack.html) and [compressed sparse implementation](https://github.com/scipy/scipy/blob/v1.17.0/scipy/sparse/_compressed.py#L851).

Arrow is appropriate for nullable tables. Its C data interface carries schema, buffers, offsets and release callbacks. DLPack describes dense tensors and managed lifetimes, without a general null bitmap. Neither protocol supplies numerical algorithms. [Arrow format](https://arrow.apache.org/docs/format/Columnar.html), [Arrow C interface](https://arrow.apache.org/docs/format/CDataInterface.html), [DLPack 1.2](https://github.com/dmlc/dlpack/blob/v1.2/include/dlpack/dlpack.h).

SwiftSci already depends on Arrow. Start by connecting actual buffer ownership to its existing bridge. A general plugin registry can wait until multiple adapters demonstrate a need. Native Swift ports of NumPy/SciPy operations should accept the native descriptors; calling Python requires a separate Python runtime/object adapter. Array API compatibility and buffer sharing are different deliverables.

Every conversion request should specify output dtype, layout and missing-value policy. Copy policy should distinguish forbid, allow and require-independent-storage. Every result should identify whether it borrowed, retained, transferred ownership or allocated. Reject impossible no-copy requests. Never silently discard rows, narrow integer identifiers, or change precision merely to choose the GPU.

## Streamlining mutation without losing snapshots

Kiraa provides a useful starting example. Its `NativeArray` checks uniqueness before bulk mutable access. `NullableArray` updates a value and validity bit, and its scoped column access exposes packed buffers to kernels. Pandas masked arrays likewise update separate values and masks directly. These implementations refute a blanket claim that compact columns are expensive to mutate. [Kiraa ownership](https://github.com/hypermedia-tech/kiraa-swift-pandas/blob/fc5d957401f70e9d3b6b07270f7f300d488fd39f/Sources/SwiftPandas/Core/Array/NativeArray.swift#L95), [nullable assignment](https://github.com/hypermedia-tech/kiraa-swift-pandas/blob/fc5d957401f70e9d3b6b07270f7f300d488fd39f/Sources/SwiftPandas/Core/Array/NullableArray.swift#L228), [pandas masked assignment](https://github.com/pandas-dev/pandas/blob/v3.0.0/pandas/core/arrays/masked.py#L365).

Proposed rules:

1. A builder owns capacity and initialized count. Reserve values and validity together; publish only a valid table with equal column lengths.
2. A mutation session establishes uniqueness once for the affected column, then performs a batch of updates. A public value copy retains snapshot semantics.
3. A synchronous borrow cannot escape its scope. A retained foreign/GPU read lease holds the allocation version alive. Ordinary writes detach while that version is in use.
4. A writable foreign lease requires exclusive ownership until completion. Foreign writes must not bypass Swift snapshot guarantees or leave cached null counts, norms, group maps and indexes stale.
5. Point overwrite and structural mutation are separate operations. Append uses spare capacity; insertion may shift values; strings may resize byte storage; sparse insertion changes indices.
6. Validity transitions update null count. The first null may allocate a bitmap for the whole column. Retaining spare bitmap capacity can avoid repeated allocation.
7. Parallel nullable writes need bitmap-word ownership. Disjoint rows can share one word and race. Batch scatter must define duplicate-index behavior and floating-point accumulation order.
8. Destructive LAPACK operations receive owned scratch or consumed storage. Training snapshots and values needed by backward computation remain immutable until released.

Swift `Span` and `MutableSpan` can express scoped access on supporting toolchains. They do not replace retained asynchronous leases. The installed compiler is newer than SwiftSci's declared Swift tools 6.0; adopting these APIs needs an explicit compatibility decision. [Span proposal](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0456-stdlib-span-properties.md), [MutableSpan proposal](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0467-MutableSpan.md).

Start with contiguous numeric storage and column-level copy-on-write. Add chunked snapshots or edit buffers only if measured sparse-update workloads justify the scan and packing overhead. A retained permutation can avoid immediate sorting copies, but repeated dense operations may benefit from gathering once. Preserve order and duplicate rows; a bitmap cannot encode either by itself.

## How to evaluate the design

The Roofline model relates attainable compute to memory traffic and arithmetic intensity. Use that reasoning to distinguish low-work scans from matrix kernels, then measure actual bandwidth and complete-workflow time. Do not treat theoretical bandwidth as an achievable result. [Williams, Waterman and Patterson](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2008/Archive/EECS-2008-134.pdf).

X100 provides precedent for processing bounded vectors through pipelines to reduce per-row overhead and intermediate materialization. Positional-update research provides options for read-heavy column stores with edits. Both inform experiments; neither requires importing a database engine's full architecture into an in-memory Swift library. [X100](https://ir.cwi.nl/pub/16497/16497B.pdf), [positional updates](https://ir.cwi.nl/pub/16172/16172D.pdf).

Acceptance workloads must include:

- Read, filter, stable sort, scale, prepare a Double solver matrix, solve, and attach results to original row IDs.
- The same preparation into a Float MLX batch, with conversion error checked and evaluation/result access included in timing.
- Repeated fits or epochs reusing a prepared matrix, plus a single-use path that charges all packing costs.
- Unique and shared mutations, short and long-lived snapshots, random and contiguous edits, duplicate scatter, first-null allocation, append growth and empty outputs.
- MLP early stopping that proves saved weights remain unchanged after subsequent optimizer updates.
- Sparse assembly, canonicalization, value-only updates and occasional structural changes.
- Arrow/NumPy import and export with sliced offsets, dtype/order differences, non-byte-aligned validity, read-only views and release-once checks.
- Asynchronous GPU access, cancellation and owner destruction; attempted mutation or resize while views are active.
- Small cache-resident tables, large tables, varied widths/null patterns/selectivity, strings/categories, and realistic memory pressure with a local model resident.

Report end-to-end latency, steady-state kernel time, preparation/evaluation/synchronization time, copied bytes, allocation count, peak live memory and resident memory. Include accuracy and output identity. Run performance comparisons with fixed model residency and thermal conditions; retain unseen workloads to detect overfitting. Establish any chunk sizes or CPU/GPU thresholds from those results.

## Recommended implementation order

| Step | Deliverable | Gate before moving on |
|---|---|---|
| 1 | Separate regression fixes for paired row alignment, NPY order/type fidelity, and numeric matrix coverage | Exact diagnostic cases become tests; policies documented |
| 2 | Compact numeric owner, validity and scoped read/batch-write access | Snapshot, null-count, lifetime and concurrent-access tests |
| 3 | Direct scaler and target-vector consumers; prepared dense batch with row mapping | Full filter/sort/scale/CPU solve parity and measured memory/copy reduction |
| 4 | Existing ML estimators consume prepared batches; reuse matrix workspaces | Repeated-fit, cross-validation and early-stopping parity |
| 5 | Ownership-aware Arrow and MLX adapters | Version-gated lifetime tests, explicit copy reporting and evaluated GPU timings |
| 6 | Sparse and embedding adapters; bounded streaming | No accidental dense expansion, stable IDs and bounded peak memory |
| 7 | Optional Python-facing adapter or broader plugin packaging | Actual consumer demand and tested lifetime/dtype contracts |

Keep this work on the compact-storage development path. The current optimization branch can remain a reviewable improvement to the existing representation. Do not combine every cache, scientific API and storage issue into one performance patch.

## Local AI contribution and limits

The already loaded local Qwen3-Coder-Next 4-bit model reviewed only the two SwiftSci KV cache files through the local LM Studio endpoint. It received no tools or write access. Its response helped flag concatenation, slot objects and stacking for inspection, but incorrectly inferred eager MLX execution from Swift assignment and suggested allocation behavior the supplied files could not establish. Those claims were rejected. MLXArray is a class, and MLX graph evaluation is lazy.

The cache conclusions in this report come from source verification and primary documentation, not the model's assertions. This task illustrates a useful delegation boundary: local AI can inventory code and propose questions; ownership, laziness and numerical correctness require source checks or executable evidence. [Prompt, response and provenance](/Users/crabel/local-ai/spl/swiftsci/data-architecture-research/local-ai/metadata.json).

No production code, dependency pin, branch, commit or PR changed during this research. The six small CPU diagnostics demonstrate current conversion behavior. GPU lifetime concerns, cache behavior, proposed mutation contracts and the new end-to-end architecture remain to be tested and implemented.
