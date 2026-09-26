# Array interoperability and mutation boundaries

Research date: 2026-09-26. This note reviews implementations and proposes contracts. It makes no performance claim beyond the code paths described. No builds, benchmarks, production changes, or commits were made.

## Findings that determine the design

A compact nullable column, a dense tensor, and a sparse matrix should share an ownership layer, but they should not pretend to have the same layout. Columnar filtering needs independently typed columns and validity. Dense linear algebra needs a homogeneous multidimensional allocation with predictable strides. Sparse arithmetic needs indices and row or column offsets. The conversion points between these representations are part of the architecture, not incidental glue.

A dataframe assembled from separately allocated numeric columns cannot generally become one zero-copy NumPy matrix. An ndarray describes one data region with shape and affine byte strides. Independent column pointers do not satisfy that description. A single compact numeric column can qualify as a vector. A homogeneous matrix-backed table can expose its columns as strided views, at the cost of changing the table's allocation and mutation behavior. This is an inference from the [NumPy array interface](https://numpy.org/doc/stable/reference/arrays.interface.html), not a measured result.

Likewise, a filtered row-index view is not ordinarily a strided tensor. Arbitrary gathers must either remain an indexed representation understood by the consumer or materialize when a dense consumer requires one.

## What the reviewed code actually does

### NumPy

Reviewed tagged NumPy v2.4.0 source. The current documentation resolves to v2.5 and should not be treated as proof of every installed version's behavior.

- `PyArray_SetBaseObject` retains an owning object, forbids resetting that dependency, and shortens view ownership chains. A borrowed address alone is insufficient. [arrayobject.c, lines 154 onward](https://github.com/numpy/numpy/blob/v2.4.0/numpy/_core/src/multiarray/arrayobject.c#L154).
- `PyArray_AssignArray` checks destination writability and casting, broadcasts strides, and handles overlapping views. Some overlap patterns require a temporary copy. Correct writable views have costs beyond exposing a pointer. [array_assign_array.c, lines 299-484](https://github.com/numpy/numpy/blob/v2.4.0/numpy/_core/src/multiarray/array_assign_array.c#L299).
- The C API distinguishes alignment, contiguity, byte order, dtype, and ownership. `PyArray_SetBaseObject` ties an externally allocated buffer to a lifetime owner. [NumPy C API](https://numpy.org/doc/stable/reference/c-api/array.html).
- The array interface carries shape, byte strides, dtype and byte order, a data address, and read-only status. Its legacy capsule form is discouraged for new code. The buffer protocol and DLPack are preferable starting points. [Array interface](https://numpy.org/doc/stable/reference/arrays.interface.html).
- `numpy.from_dlpack` accepts an object with the DLPack methods. `copy=False` requires rejection if sharing is impossible. NumPy's destination device is CPU. This is not a general Metal compute bridge. [NumPy DLPack import](https://numpy.org/doc/stable/reference/generated/numpy.from_dlpack.html).

A NumPy-compatible operation API is different from buffer interoperability. The Python Array API standard describes functions, promotion and dispatch behavior. It does not automatically make a native Swift object callable by SciPy. SciPy's own per-function backend support remains uneven. The optional Python adapter therefore needs a real Python object or extension boundary, and each operation needs a supported-backend decision. [Array API purpose](https://data-apis.org/array-api/latest/purpose_and_scope.html), [SciPy backend support](https://docs.scipy.org/doc/scipy/dev/api-dev/array_api.html).

### SciPy dense linear algebra

Reviewed SciPy v1.17.0 source. In `eig`, SciPy validates the input, checks square shape, determines whether it may overwrite, selects a typed LAPACK routine, allocates or queries workspace, then calls the routine. Buffer compatibility removes only one class of cost. Validation, workspaces and factorization outputs remain. [\_decomp.py, lines 213-260](https://github.com/scipy/scipy/blob/v1.17.0/scipy/linalg/_decomp.py#L213).

`find_best_blas_type` selects real or complex precision and examines Fortran contiguity. The dispatch cache includes dtype and Fortran layout. This supports explicit dtype and order in a Swift dense descriptor. [blas.py, lines 310-334 and 396-412](https://github.com/scipy/scipy/blob/v1.17.0/scipy/linalg/blas.py#L310).

The low-level LAPACK documentation says a C-contiguous input or wrong precision can cause f2py to allocate a compatible intermediate. `overwrite_a=True` does not guarantee in-place work on the original buffer. [LAPACK wrapper documentation](https://docs.scipy.org/doc/scipy/reference/linalg.lapack.html).

Design implication: choose matrix order for the next consumer, retain it through repeated solves or factorizations, and expose an explicit consuming or exclusive-mutation operation when LAPACK overwrites. Do not convert dataframe → row-major array → column-major scratch for every iteration. A CBLAS operation that accepts row-major layout has different requirements from a Fortran LAPACK wrapper; adapters must state which they need.

### SciPy sparse data

Reviewed SciPy v1.17.0 `scipy/sparse/_compressed.py`.

`_matmul_vector` and `_matmul_multivector` pass `indptr`, `indices`, `data`, and dense input/output buffers to typed sparse kernels. `_set_many` samples existing offsets. If all requested coordinates exist, it updates the values directly. Structural insertion takes a separate path and warns that LIL or DOK is more efficient. [Compressed sparse implementation, lines 387-413 and 851-910](https://github.com/scipy/scipy/blob/v1.17.0/scipy/sparse/_compressed.py#L387).

CSR favors row slicing and matrix-vector products; CSC favors column-oriented access. COO is useful for assembly and conversion. Sparse structure and numeric values need separate ownership decisions. Changing an existing coefficient is not the same operation as inserting a new graph edge. [SciPy sparse tutorial](https://docs.scipy.org/doc/scipy/tutorial/sparse.html).

Proposed phases: assemble with COO or a mutable builder, canonicalize duplicates and index order once, then freeze structure into CSR or CSC and permit repeated value-only updates. Track index width and overflow. Null entries are not implicit zeros; missingness must be resolved before ordinary sparse linear algebra.

### Pandas nullable arrays and Arrow-backed arrays

Reviewed pandas v3.0.0.

`BaseMaskedArray.__setitem__` writes `_data` and `_mask` directly. Its null mask uses true for missing, the opposite of Arrow validity. `to_numpy` uses dtype and missing-value policy to decide whether it can share or must cast/copy and substitute values. This is direct evidence that compact nullable data can support cheap fixed-size mutation. [masked.py, lines 365-385 and 512-606](https://github.com/pandas-dev/pandas/blob/v3.0.0/pandas/core/arrays/masked.py#L365).

The Arrow-backed implementation has a different mutation cost. A scalar assignment creates slices plus a replacement array, builds a chunked array, then calls `combine_chunks`. Masked updates use Arrow compute or replacement logic before installing a new `_pa_array`. This is not the same mutation contract as a uniquely owned numeric buffer. [Arrow array implementation, lines 2192-2273](https://github.com/pandas-dev/pandas/blob/v3.0.0/pandas/core/arrays/arrow/array.py#L2192).

Thus “mutation is expensive” needs qualification. Fixed-width overwrite under exclusive ownership can be constant work. Shared snapshot detachment, string resizing, structural sparse insertion, or rebuilding immutable Arrow arrays can require much more work.

### Arrow interoperability

Arrow fixed-width arrays use value buffers and a validity bitmap with set bits for valid elements. Null count is metadata; an all-valid array may omit its bitmap. Booleans use a packed values bitmap. Variable-length strings use offsets and a byte buffer. Arrow's recommended 64-byte padding is not evidence that 64 bytes is the best Apple-specific tuning choice; the cited rationale includes AVX-512. [Columnar format](https://arrow.apache.org/docs/format/Columnar.html).

The C interface passes buffers, children, schema, length, offset, null count and a producer release callback. An exporter must hold buffer owners in private state until release. Consumers cannot retain pointers beyond release. Children and dictionaries have coordinated lifetimes. [C data interface](https://arrow.apache.org/docs/format/CDataInterface.html).

The implementation reinforces this contract. Arrow C++ `ExportedArrayPrivateData` holds array data and exported children; `ReleaseExportedArray` frees exporter state and marks release complete. [Arrow 21.0.0 bridge.cc, lines 533 onward](https://github.com/apache/arrow/blob/apache-arrow-21.0.0/cpp/src/arrow/c/bridge.cc#L533).

A format-compatible Swift numeric column is a plausible zero-copy Arrow export. `[String?]` and byte-wide Swift `Bool` values need conversion to the corresponding Arrow layouts. An Arrow-compatible validity bitmap alone does not make every dtype Arrow-compatible. CPU C-data export also does not imply GPU interoperability; Arrow defines a separate device interface with device and synchronization contracts. [Device interface](https://arrow.apache.org/docs/format/CDeviceDataInterface.html).

### DLPack

The reviewed DLPack v1.2 header describes a dense tensor using data pointer, device, dtype, shape, element strides and byte offset. Its managed wrapper carries a deleter, and its versioned form has flags including read-only. It has no general dataframe schema or null bitmap field. Nullable table interchange should use Arrow; dense tensor interchange can use DLPack after missingness is resolved. [DLPack header, lines 218-377](https://github.com/dmlc/dlpack/blob/v1.2/include/dlpack/dlpack.h#L218).

The Array API's DLPack import contract permits copies when requested and requires errors when a strict no-copy request cannot be met. A Swift adapter should offer the same explicit distinction, rather than silently materializing under a method named “view.” [DLPack import contract](https://data-apis.org/array-api/latest/API_specification/generated/array_api.from_dlpack.html).

### Kiraa's Swift implementation

Local revision `fc5d957401f70e9d3b6b07270f7f300d488fd39f`, repository `/Users/crabel/Documents/src/kiraa-swift-pandas`.

- `NativeArray.ensureUnique` checks reference uniqueness, creates a separate buffer owner if shared, and relies on `ContiguousArray` storage for eventual detachment. Its mutable-buffer closure checks uniqueness once before bulk work. [NativeArray.swift, lines 95-107 and 219-225](https://github.com/hypermedia-tech/kiraa-swift-pandas/blob/fc5d957401f70e9d3b6b07270f7f300d488fd39f/Sources/SwiftPandas/Core/Array/NativeArray.swift#L95).
- `NullableArray` scalar assignment updates the numeric slot and validity bit, or only clears validity for nil. [NullableArray.swift, lines 228-242](https://github.com/hypermedia-tech/kiraa-swift-pandas/blob/fc5d957401f70e9d3b6b07270f7f300d488fd39f/Sources/SwiftPandas/Core/Array/NullableArray.swift#L228).
- `withUnsafeDoubleBuffer` and related methods lend values and packed validity only for the closure duration. All-valid columns omit the mask argument. Their lifetime is suitable for synchronous kernels, not for a foreign object that retains the pointer. [DataFrame+ColumnarAccess.swift, lines 63-152](https://github.com/hypermedia-tech/kiraa-swift-pandas/blob/fc5d957401f70e9d3b6b07270f7f300d488fd39f/Sources/SwiftPandas/DataFrame/DataFrame%2BColumnarAccess.swift#L63).
- `VectorArray` stores a contiguous row-major Float32 plane, a per-row validity bitmap and cached squared norms. It carries sliced norms through gather instead of recomputing. This is a useful example of separating embedding vectors from scalar table columns. [VectorArray.swift, lines 28-52 and 104-178](https://github.com/hypermedia-tech/kiraa-swift-pandas/blob/fc5d957401f70e9d3b6b07270f7f300d488fd39f/Sources/SwiftPandas/Vector/VectorArray.swift#L28).
- Metal vector search still prepares a Metal buffer and compacts candidates when necessary. Unified memory did not eliminate those source-code copies. [MetalVectorSearch.swift, lines 59-97](https://github.com/hypermedia-tech/kiraa-swift-pandas/blob/fc5d957401f70e9d3b6b07270f7f300d488fd39f/Sources/SwiftPandas/Metal/MetalVectorSearch.swift#L59).
- Lazy filter fusion and projection pushdown aim to reduce intermediate frames. But the group-by pushdown test uses source column names, and join pushdown does not inspect join kind. These are review concerns, not reproduced failures in this research. Copying optimizer rules requires semantic tests for aggregate aliases and outer joins. [QueryOptimizer.swift, lines 129-153 and 180-223](https://github.com/hypermedia-tech/kiraa-swift-pandas/blob/fc5d957401f70e9d3b6b07270f7f300d488fd39f/Sources/SwiftPandas/Lazy/QueryOptimizer.swift#L180).

## Proposed native contracts

These are design recommendations, not APIs implemented by this research.

| Contract | Required information | Primary consumers |
|---|---|---|
| Numeric column view | Scalar type, count, value offset/stride, optional validity, null count, retained owner or scoped borrow | Filters, reductions, joins, Arrow export |
| Dense tensor view | Scalar type, shape, strides with explicit units, byte offset, storage owner, device, writable status | SwiftSci vectors/matrices, Accelerate, MLX adapters, NumPy/DLPack |
| Sparse matrix | Shape, CSR/CSC/COO format, index type, offsets/coordinates, values, sorted/duplicate invariants | Graphs, sparse features, scientific solves |
| Table batch | Schema, equal-length columns, row identity or selection, ownership of each column | Ingestion, preprocessing, chunked interchange |

Do not hide every backend behind one mutable object. A small common ownership layer can support specialized views. Kernel dispatch should check a concrete capability such as contiguous Float32 values or compatible CSR indices. It should not discover layout through per-element dynamic dispatch.

Use a conversion request that states dtype, order, null treatment and copy policy. Null policies should include reject, explicit fill/imputation, dropping rows with returned row mapping, or a separate mask accepted by the destination. Nil and NaN remain distinct. In particular, integer identifiers should not silently lose precision during Float32 feature conversion.

An adapter may either borrow, share a retained owner, transfer ownership, or allocate. Return or record which occurred. A plugin that ports numerical APIs to Swift can consume these native views directly. A plugin that calls Python needs CPython and a compatible object adapter. Shared memory alone does not port SciPy's algorithms or remove Python runtime requirements.

## Mutation strategy to investigate

1. Provide exclusive bulk mutation for a uniquely owned fixed-width column. Detach once if shared, then lend values and validity for the batch. Update cached null count and invalidate dependent caches once.
2. Treat publication as a boundary. Export read-only snapshots by default. A retained foreign buffer keeps the old allocation alive; Swift mutations detach. Do not lend writable foreign access while ordinary Swift value copies promise independence.
3. For explicit writable sharing, use an exclusive lease or move the owner into the adapter. Foreign writes bypass Swift uniqueness checks and can invalidate null counts, norms and indexes.
4. Use builders with reserved capacity for ingest and append-heavy phases. Chunking limits large reallocations and makes sharing snapshots cheaper, but it can add per-chunk overhead to dense kernels. Decide when to consolidate based on the next operation.
5. Treat changing string length and changing sparse structure separately from numeric overwrites. Batched edit logs or chunk replacement are candidates, with extra lookup or compaction costs that must be measured.

## Required validation before choosing the layout

- Whole workflow: read → select columns → filter → sort → materialize one matrix → repeated operation → write results back by row identity.
- Sparse workflow: build coordinates → canonicalize CSR → many value updates and matrix-vector operations → occasional structural edit.
- Mutation matrix: unique/shared owner, no/some nulls, clustered/scattered edits, append growth, small/large chunks, retained foreign view.
- Interoperability: empty arrays, sliced offsets, negative or non-unit strides, read-only buffers, dtype mismatch, large integer identifiers, non-byte-aligned validity offsets and exact release-once behavior.
- Costs: peak resident memory, bytes allocated/copied, conversion latency, full workflow time and cache invalidation work. Include the retained snapshot memory cost.

The architecture should make one deliberate copy possible when it enables many fast operations. “Zero-copy everywhere” is not a useful goal if it leaves every downstream kernel traversing irregular indices or incompatible strides.
