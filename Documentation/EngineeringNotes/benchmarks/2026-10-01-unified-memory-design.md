# Unified-memory storage design for SwiftSci

Date: 2026-10-01. Status: researched design proposal, not an implemented replacement or measured speedup.

## Recommendation

Prototype **owner-backed typed columns, optional validity bitmaps, row-selection views, and explicit numerical materialization**. Use a common ownership contract across CPU, Arrow and compatible MLX/Metal buffers, with different physical layouts for tables, dense matrices and sparse data. Keep CPU tabular operations independent of Metal. Allocate GPU-shareable storage when the actual next consumer can use it.

The optimization target is fewer live representations and fewer bytes moved through the complete workflow. Unified physical memory makes some processor transfers unnecessary; it does not eliminate dtype conversion, layout packing, lifetime management, synchronization, or contention for memory bandwidth. No proposed structure is established as optimal until compared against the existing implementation on representative workflows.

Research scope covers current storage, mutation, ingestion, numerical consumers and CPU/GPU interfaces. It does not audit every estimator or propose a universal replacement for all model state.

## Source identity and constraints

The inspected SwiftSci checkout is `f9e13de32e492b0a49eb0c6647a2136e9ccf6aa4`, the production-default baseline branch. Its benchmark measured the same library source at `980884dd4c755e19ff0def721ab8b2db3c6343bf`. The resolved MLX Swift dependency is 0.31.6 at `0bb916c67f4b9e5c682cbe02a42c701c93ab5021`; that dependency checkout was clean. Arrow Swift resolves to 21.0.0 at `fb3f3d91be5acd511b7289c7820becc1a68e455d`. See the pinned [package resolution](https://github.com/crabel99/SwiftSci/blob/f9e13de32e492b0a49eb0c6647a2136e9ccf6aa4/Package.resolved).

The maintainer has allowed raising the compiler requirement and is open to a higher deployment target. That removes a policy obstacle, but does not select an implementation. Record the minimum required by the chosen APIs and validate it explicitly. The current manifest still declares Swift tools 6.0 and macOS 14. [Compatibility discussion](https://github.com/Nodibell/SwiftSci/issues/40#issuecomment-5890171931), [current manifest](https://github.com/crabel99/SwiftSci/blob/f9e13de32e492b0a49eb0c6647a2136e9ccf6aa4/Package.swift).

## What the code currently does

These are source observations, not profiling results or proof of the dominant runtime cost.

| Boundary | Observed representation or operation | Design consequence |
|---|---|---|
| Table columns | `TypedColumn<T>.values` is `[T?]`; dense initialization creates optionals | Introduce typed fixed-width values plus separate validity without routing hot loops through optional materialization. [Source](https://github.com/crabel99/SwiftSci/blob/f9e13de32e492b0a49eb0c6647a2136e9ccf6aa4/Sources/SwiftDataFrame/Columns/TypedColumn.swift) |
| Prepared batches | Already use contiguous Double columns, optional bitmaps, and copy-on-write snapshots | Preserve this working contract. Generalize only where a demonstrated consumer needs another dtype or backing owner. [Source](https://github.com/crabel99/SwiftSci/blob/f9e13de32e492b0a49eb0c6647a2136e9ccf6aa4/Sources/SwiftDataFrame/Core/PreparedNumericBatch.swift) |
| Selection and matrix export | `selectingRows` eagerly gathers every selected column; multiple columns require matrix packing | Retain a selection until a consuming kernel needs dense values. Fuse gather, conversion and packing when permitted. [Source](https://github.com/crabel99/SwiftSci/blob/f9e13de32e492b0a49eb0c6647a2136e9ccf6aa4/Sources/SwiftDataFrame/Core/PreparedNumericBatch.swift) |
| Join assembly | Typed join matching is followed by `[Any?]` result arrays and `makeColumn` | Remove type-erased assembly independently of the larger storage migration. Inspect the hash-table and index costs separately. [Source](https://github.com/crabel99/SwiftSci/blob/f9e13de32e492b0a49eb0c6647a2136e9ccf6aa4/Sources/SwiftDataFrame/Core/DataFrame%2BSIMDJoin.swift) |
| Parquet and Arrow ingestion | Parquet decoding uses `[Any?]`; Arrow import loops into optional arrays | Decode into typed builders; retain compatible Arrow owners instead of automatically materializing. File mapping alone does not make decoded columns zero-copy. [Parquet](https://github.com/crabel99/SwiftSci/blob/f9e13de32e492b0a49eb0c6647a2136e9ccf6aa4/Sources/SwiftDataFrame/IO/ParquetReader.swift), [Arrow](https://github.com/crabel99/SwiftSci/blob/f9e13de32e492b0a49eb0c6647a2136e9ccf6aa4/Sources/SwiftDataFrame/Internal/ArrowTableBridge.swift) |
| Existing buffer wrapper | `ArrowDataBuffer` has optional owner retention and unchecked Sendable; production columns do not use it | This is not an established end-to-end ownership layer. A new foreign-buffer owner must retain the actual allocation and define immutability, range checks and release. [Wrapper](https://github.com/crabel99/SwiftSci/blob/f9e13de32e492b0a49eb0c6647a2136e9ccf6aa4/Sources/SwiftDataFrame/Internal/ArrowDataBuffer.swift), [current test](https://github.com/crabel99/SwiftSci/blob/f9e13de32e492b0a49eb0c6647a2136e9ccf6aa4/Tests/SwiftDataFrameTests/DataFrameArrowTests.swift) |
| Scaling | Compact StandardScaler gathers each row into scratch arrays and calls row-width vDSP operations to preserve existing rounding | A column-wise/fused path needs an explicit numerical contract. Storage improvements do not authorize changing rounding silently. [Source](https://github.com/crabel99/SwiftSci/blob/f9e13de32e492b0a49eb0c6647a2136e9ccf6aa4/Sources/SwiftPreprocessing/Core/StandardScaler.swift) |
| Model input | LinearRegression accepts nested Double rows; GPU input flattens and narrows to Float before `MLXArray` creation | Add a concrete prepared-matrix consumer to demonstrate one retained layout across preprocessing and computation. [Source](https://github.com/crabel99/SwiftSci/blob/f9e13de32e492b0a49eb0c6647a2136e9ccf6aa4/Sources/SwiftML/Core/LinearRegression.swift) |
| Memory scheduling | `WiredMemoryManager` limits task count rather than reserving bytes | Track allocation owners, live views, scratch space and in-flight leases before adding a byte-based admission policy. It does not currently wire memory or establish a device-memory budget. [Source](https://github.com/crabel99/SwiftSci/blob/f9e13de32e492b0a49eb0c6647a2136e9ccf6aa4/Sources/SwiftPreprocessing/Core/WiredMemoryManager.swift) |

## Why this architecture has precedent

MonetDB/X100 studied the overhead of tuple-by-tuple execution and the memory bandwidth cost of whole-column intermediates. Its vectorized, incremental processing motivates testing bounded execution batches rather than assuming either tiny scalar calls or full-column materialization is best. Its old hardware results are not forecasts for Apple silicon. [Original paper](https://www.cidrdb.org/cidr2005/papers/P19.pdf).

DuckDB separates logical vectors from physical flat, constant and dictionary representations. Dictionary vectors use selections into child data. Its default execution vector size is 2,048 rows. This supports the proposed separation of ownership and selection, but that size is not an Apple-silicon optimum. [DuckDB execution format](https://duckdb.org/docs/current/internals/vector).

Arrow supplies established value/validity layouts and a release-based C interchange contract. Layout compatibility and valid ownership must both hold before sharing data. This proposal borrows those boundaries, not an assumption that the current Swift bridge already implements them. [Column format](https://arrow.apache.org/docs/format/Columnar.html), [C data interface](https://arrow.apache.org/docs/format/CDataInterface.html).

Use the Roofline model as a diagnostic framework: reduce memory traffic for low-arithmetic-intensity work, and separately measure compute-heavy kernels. Shared DRAM is still a finite resource. Measure achieved throughput and workload traffic rather than multiplying a vendor peak by an assumed efficiency. [Berkeley Lab Roofline publications](https://amcr.lbl.gov/departments/computer-science-department/ppan/roofline-performance-model/ppan-roofline-publications/).

## Proposed structure and boundaries

The following names describe responsibilities, not a committed public API.

| Component | Required contract |
|---|---|
| `BufferOwner` | Stable allocation identity, capacity, alignment, backing kind, release action and asynchronous access leases. Every view retains its actual owner. Typed allocation/deinitialization must be correct; restrict raw numeric storage to explicitly supported fixed-width types. |
| `ColumnStorage<T>` | Typed value regions, count, optional validity region, null count and logical offset. Start with dense numeric columns. Keep variable-width strings and sparse CSR/CSC representations distinct. |
| `RowSelection` | Identity, contiguous range, bitmap or ordered indices. A bitmap cannot represent reordered rows or duplicates. Compose selections with checked row identity; cap indirection depth and retained memory. |
| `SelectedBatch` | Schema and retained column owners plus a shared selection. Table operations can process bounded blocks without gathering all payload columns. |
| `DenseMatrix` | Owner, dtype, shape, byte offset, strides, order and row mapping. Validate overflow and addressable extent. It may borrow compatible storage or own an explicitly materialized result. |
| Consumer adapters | Scoped Accelerate borrows, retained Arrow exports, qualified MLX imports and explicit Metal work. Report whether an operation borrowed, packed, converted or copied, and how many bytes. |

One desired path is:

```text
Typed ingestion builders / retained compatible Arrow columns
    -> compact table owners + validity
    -> filter selection -> stable-sort permutation
    -> selected columns + composed original-row identity
    -> gather + missing-value policy + layout/dtype preparation
    -> owned or borrowed dense matrix
       -> CPU Accelerate / LAPACK
       -> qualified MLX / Metal adapter
    -> results with original-row identity
```

Packing stays explicit. Separate column allocations cannot usually be exposed as one contiguous matrix. A selection can be cheaper to retain than to gather, but random accesses and repeated use can make early packing faster. Fit training statistics only on training rows, then reuse them for held-out data; storage changes must not introduce preprocessing leakage.

Start with internal concrete owners and adapters. Do not introduce a general plugin registry or make every column a tensor before a complete consumer path demonstrates the need.

## Ownership and mutation rules

1. Public values retain snapshot semantics. A unique mutable owner with no active borrows or device readers can update its values and validity in place.
2. Sharing a snapshot or retaining an asynchronous reader prevents mutation of that allocation. Detach the affected ownership unit or wait through an explicit API. Swift array copy-on-write does not automatically protect arbitrary pointers exported to another runtime.
3. A synchronous borrow cannot escape its scope. Span-style compiler enforcement is useful where available; it does not supply GPU completion or own foreign memory.
4. An asynchronous lease retains the owner until the consuming runtime is actually finished. CPU task cancellation is not proof that submitted GPU work stopped. A GPU writer owns an exclusive output until completion publishes the result.
5. Simultaneous immutable reads can share storage. Conflicting reads/writes require ordering. Partitioned CPU writes require disjoint values and validity words; different rows can share one bitmap word. Do not place a global lock or actor hop inside element loops.
6. Fixed-size updates validate before mutation and maintain null counts. Builders reserve capacity and seal batches. Structural edits and append may allocate; define that cost instead of promising universal in-place mutation.
7. A foreign buffer requires a real retained owner or release token. A placeholder object unrelated to the allocation is insufficient. Release exactly once after the last view and execution lease.

Column-level copy-on-write is the simplest first prototype. Compare chunk-level detachment if sparse edits to retained large snapshots dominate. A whole-table slab makes one-row edits capable of retaining or copying unrelated columns; avoid that default.

## Allocation, execution and materialization policy

- CPU-only columns use ordinary owned contiguous storage. Do not page-round every small column solely because a GPU exists.
- Select GPU-shareable allocation when the next consumer accepts its dtype, extent, layout and ownership. MLX-owned and Metal-owned allocations remain distinct implementations under the same lifetime contract.
- Keep logical lengths separate from padded allocation lengths. Query page size and enforce backend requirements; do not treat SIMD alignment, cache-line alignment and Metal no-copy allocation alignment as interchangeable.
- Private GPU intermediates belong to the GPU backend when useful. Compare them against shared allocations for the actual workflow. Avoid copying CPU-populated data into private storage by default on Apple GPUs.
- A proposed `requireShared` request must fail if sharing cannot be proved. A `preferShared` request may copy, but reports the reason. The pinned MLX managed-pointer constructor itself permits fallback copying, so a strict adapter needs stronger verification than selecting that initializer.
- Float64 scientific computation stays on a supported CPU path when required. Float32/BF16 preparation is a declared numerical conversion, never an invisible consequence of choosing GPU execution. Preserve exact integer identifiers outside lossy floating conversion.
- Selection, null handling, dtype conversion and packing may be fused into one output pass. Fuse arithmetic only when the numerical contract permits its rounding behavior. Cache prepared matrices only for immutable versioned inputs, with bounded eviction.
- Budget original allocations, retained snapshots, selections, packed matrices, scratch buffers, model weights and caches together. Count aliases once. Runtime allocator caches and OS pressure remain separate from logical payload bytes. Establish backpressure at batch/task boundaries rather than wiring all available RAM.

## Alternatives worth testing

| Candidate | Advantage | Cost or rejection condition |
|---|---|---|
| Existing prepared batches with targeted typed assembly | Lowest implementation risk; preserves proven contracts | Retains optional table storage and some conversion passes. This is the control, not a straw man. |
| Owner-backed contiguous columns plus selections | Compact scans, explicit sharing, fewer intermediate payload copies | More ownership machinery; retained selections may pin large inputs; irregular access can hurt locality. Preferred hypothesis. |
| Chunked column owners with the same view contract | Bounded builders, smaller snapshot detachment, streaming ingestion | Chunk dispatch and boundaries; matrix consumers still need packing. Add only if measurements justify it. |
| Every table backed by one dense MLX/Metal allocation | Convenient for a narrow homogeneous tensor pipeline | Poor fit for mixed dtypes/nulls, sparse data, independent column edits and Float64 CPU consumers. Do not make this the general table representation. |

GPU acceleration is a consumer of this structure, not its definition. CSV parsing, hash joins and sorting may need algorithm and allocation fixes before GPU execution pays for synchronization and materialization.

## Local feasibility evidence

An isolated Release Swift/Metal probe ran on Apple M4 Max, 128 GiB, Swift 6.4 targeting arm64 macOS 27. The OS reported 16,384-byte pages and a 128-byte cache line. These observations describe this machine, not all Apple-silicon models.

| Element | Dense stride | Optional stride |
|---|---:|---:|
| Double | 8 bytes | 16 bytes |
| Float | 4 bytes | 8 bytes |
| Int64 | 8 bytes | 16 bytes |

For one million nullable Double values, logical storage is therefore about 16 MB as optionals versus 8.125 MB as dense values plus a one-bit validity map, approximately 49.2% less. This calculation excludes allocation capacity, metadata, indices, snapshots and alignment. Creating compact storage while retaining the original optional array can increase peak memory; end-to-end adoption is necessary to realize the saving.

Both a Metal-created shared buffer and a page-aligned externally allocated no-copy buffer passed CPU fill -> GPU update -> explicit completion -> CPU verification for 4,096 Float values. The external buffer's CPU address matched `contents()`. This establishes a basic sharing mechanism. It does not establish MLX interoperability, lifetime safety under concurrency, performance, or absence of hidden driver activity.

## Prototype and acceptance plan

Keep production changes out of the benchmark and engineering-notes branches. Start a separate implementation branch from the agreed integrated code baseline and associate it with issue #40.

1. Establish ownership tests and allocation accounting before replacing storage. Validate bounds, zero-length buffers, nonzero offsets, overflow, null/NaN distinction, snapshots, unique/shared edits and exact release.
2. Implement dense Double/Float/Int64 owners and selection-aware reads behind an internal interface. Compare against the current prepared-batch path. Include random and contiguous selections, repeated indices, null boundaries and retained tiny views into large allocations.
3. Remove `[Any?]` assembly in one concrete join or ingestion path. Measure that separately from backing-store changes so attribution remains possible.
4. Complete filter -> stable sort -> scale -> matrix -> CPU solve/predict with row alignment and independent numerical checks. Test first use and repeated reuse. Add a GPU consumer only after the same layout/lifetime contract is qualified.
5. Gate MLX managed imports on alignment, lifetime, exact-once finalization, fallback detection, offsets, empty/odd shapes, pending graphs, mutation and cancellation tests. An unqualified backend copies explicitly rather than offering an unsafe sharing promise.
6. Compare contiguous and chunked ownership only after the first complete path works. Select thresholds from varied workloads, not one favorable fixture.

For performance, vary 1k/100k/1M rows and bounded larger cases, narrow/wide matrices, null density, selection density, stable/random ordering, unique/shared mutation, and first-use/reuse. Sweep CPU execution block sizes separately from allocation chunk size and GPU dispatch size. Include cache-resident and memory-sized cases without forcing system-wide exhaustion.

Record end-to-end and kernel time, allocations, bytes copied/materialized, owner live bytes, peak process footprint/RSS, active and cached MLX memory, GPU completion and available bandwidth/cache counters. Do not add overlapping process and device metrics as if they were disjoint physical memory. Preserve all numerical failures and count selected/result rows as part of the contract.

Success requires unchanged promised behavior, proven lifetimes, and a measured improvement in complete workflow time or memory capacity across representative cases. A speed/memory tradeoff can be acceptable when recorded. Pointer equality, a lower payload formula, or a faster isolated kernel alone is insufficient.

## Decisions still open

- Whether chunk-level copy-on-write earns its complexity for real editing and snapshot workloads.
- Which compatibility release introduces explicit materialization in place of implicit `.values` access.
- Which public consumers require strided views and which should demand owned contiguous matrices.
- Whether the pinned MLX managed-finalizer and export paths can satisfy the proposed strict sharing contract without dependency changes.
- The minimum OS/compiler combination after availability probes and full qualification, including any modern borrowing conveniences selected.


## Primary-source contract review

The following review records the hardware and dependency contracts underlying this proposal. Source observations are pinned to mlx-swift 0.31.6, not assumed to describe later releases.

### Apple memory contracts


### Shared and private resources

Apple GPUs share system memory with the CPU. A shared Metal resource permits both processors to access it; a private resource permits GPU access. Apple's current Apple-GPU guidance recommends shared storage for CPU-populated buffers, including buffers subsequently accessed frequently by the GPU. It recommends private storage for GPU-owned intermediate results. Memoryless storage applies to textures, not buffers. Private storage should therefore be an option for GPU intermediates, not an assumed universal upgrade over shared table storage. The archived Metal best-practices guide describes a different macOS/discrete-GPU model and should not drive this design. [Apple resource storage guidance](https://developer.apple.com/documentation/metal/choosing-a-resource-storage-mode-for-apple-gpus).

### Wrapping existing bytes

`makeBuffer(bytesNoCopy:length:options:deallocator:)` requires a page-aligned starting pointer and a length defining a page-aligned memory region, within one VM region. It returns an optional buffer. Its deallocator callback allows the application to release the backing allocation when Metal releases the buffer. Passing no deallocator leaves release responsibility with the application. These requirements were checked against Apple's documentation JSON as well as the public documentation page. [Apple no-copy buffer API](https://developer.apple.com/documentation/metal/mtldevice/makebuffer(bytesnocopy:length:options:deallocator:)).

Design consequence: an arbitrary Swift Array pointer, Arrow slice pointer, or 64-byte-aligned allocation is not enough. Store allocation base, byte capacity, logical byte range, alignment, and owner separately. Query page size; do not hardcode 4 KiB or 16 KiB. Keep Metal wrapping tied to the allocation base, then bind an offset for a slice where the API permits it. Check the relevant binding alignment and bounds. Never round a borrowed allocation's length upward unless those bytes belong to the allocation.

Allocating a shared `MTLBuffer` first and using `contents()` for CPU work can simplify ownership for known GPU-bound numeric batches. A CPU allocation first can better serve CPU-only columns. Compare both through the same owner abstraction. Neither strategy establishes that every framework operation shares the allocation.

### Synchronization remains explicit

CPU and GPU access to shared bytes still needs ordering. Apple's CPU/GPU sample uses multiple buffer instances and completion-based admission to avoid writing bytes the GPU is reading. Resource hazard tracking addresses a narrower set of GPU dependencies. Apple's documentation distinguishes tracked directly bound resources on `MTLCommandQueue` from Metal 4's synchronization requirements; do not apply one model to the other. [CPU/GPU synchronization sample](https://developer.apple.com/documentation/metal/synchronizing-cpu-and-gpu-work), [resource synchronization](https://developer.apple.com/documentation/metal/resource-synchronization).

Proposed rule: read access may coexist with read access, but a write lease excludes every other access to its byte range. An asynchronous GPU operation retains an owner and an access lease until completion, including error and cancellation handling. Returning from command encoding is not completion. Cancellation must not free submitted resources. A Swift actor can serialize host decisions but cannot make GPU commands finish. Start with command completion as the conservative boundary; introduce events and narrower range scheduling only after correctness tests.

### Pinned MLX source

### Ordinary initialization and export copy

`MLXArray` initializers taking Swift arrays and ordinary unsafe buffer pointers call `mlx_array_new_data`. The C wrapper constructs typed C++ arrays, whose initializer allocates and runs `std::copy`. Being on Apple silicon does not remove that copy. Conversely, `asArray` evaluates the array, allocates a Swift Array, and copies. `asData` defaults to a contiguous copy. [Swift initializers](https://github.com/ml-explore/mlx-swift/blob/0bb916c67f4b9e5c682cbe02a42c701c93ab5021/Source/MLX/MLXArray%2BInit.swift), [C array wrapper](https://github.com/ml-explore/mlx-swift/blob/0bb916c67f4b9e5c682cbe02a42c701c93ab5021/Source/Cmlx/mlx-c/mlx/c/array.cpp), [C++ copying initialization](https://github.com/ml-explore/mlx-swift/blob/0bb916c67f4b9e5c682cbe02a42c701c93ab5021/Source/Cmlx/mlx/mlx/array.h#L588-L634), [Swift byte export](https://github.com/ml-explore/mlx-swift/blob/0bb916c67f4b9e5c682cbe02a42c701c93ab5021/Source/MLX/MLXArray%2BBytes.swift#L123-L255).

### Ownership import can avoid copying, but can fall back

The public `MLXArray(rawPointer:shape:dtype:finalizer:)` initializer transfers ownership through `mlx_array_new_data_managed_payload`. Its pointer represents contiguous elements in the supplied shape and dtype. C++ first asks the allocator to wrap that pointer. If wrapping returns null, it allocates its own storage, copies, and invokes the supplied deleter immediately. Successful wrapping arranges to call the deleter when the array's storage releases. Thus the API supports opportunistic no-copy import, not a guaranteed no-copy contract. [Managed Swift initializer](https://github.com/ml-explore/mlx-swift/blob/0bb916c67f4b9e5c682cbe02a42c701c93ab5021/Source/MLX/MLXArray%2BInit.swift#L20-L97), [C++ managed constructor](https://github.com/ml-explore/mlx-swift/blob/0bb916c67f4b9e5c682cbe02a42c701c93ab5021/Source/Cmlx/mlx/mlx/array.cpp#L88-L109).

The Metal allocator uses shared storage and untracked hazards. Its `make_buffer` forwards the pointer and size to Metal's no-copy constructor; it does not make arbitrary host pointers eligible. The allocator's usual allocations may use a heap and its normal allocation path rounds larger allocations to pages, but the wrapping path is distinct. Do not treat MLX's internal allocator or synchronization as a stable external interoperability protocol. [Pinned Metal allocator](https://github.com/ml-explore/mlx-swift/blob/0bb916c67f4b9e5c682cbe02a42c701c93ab5021/Source/Cmlx/mlx/mlx/backend/metal/allocator.cpp#L14-L15), [wrapping path](https://github.com/ml-explore/mlx-swift/blob/0bb916c67f4b9e5c682cbe02a42c701c93ab5021/Source/Cmlx/mlx/mlx/backend/metal/allocator.cpp#L208-L219).

A source-level concern needs a focused lifetime test before this becomes SwiftSci's normal import path. Swift retains `FinalizerCaptureState` using `passRetained`; the trampoline obtains it through `takeUnretainedValue` and calls its closure. A local `free` function that releases the retained state exists but is not passed to the C function or otherwise called in this initializer. The C wrapper calls the provided callback only. This is a visible retained-payload imbalance and suggests leaked capture state, potentially including its captured allocation owner. It is not a measured runtime leak in this report. A finalizer that explicitly frees a raw allocation can still execute while the closure capture itself leaks. [Exact initializer and trampoline](https://github.com/ml-explore/mlx-swift/blob/0bb916c67f4b9e5c682cbe02a42c701c93ab5021/Source/MLX/MLXArray%2BInit.swift#L20-L97), [C finalizer bridge](https://github.com/ml-explore/mlx-swift/blob/0bb916c67f4b9e5c682cbe02a42c701c93ab5021/Source/Cmlx/mlx-c/mlx/c/array.cpp#L253-L280).

### Export requires ownership and layout checks

`asMTLBuffer(device:noCopy:)` evaluates the array. With `noCopy: true` and contiguous layout, it passes the raw data pointer and logical `nbytes` to Metal. The caller must retain the MLXArray and prevent mutation for the buffer's entire lifetime, including asynchronous GPU use. For other layouts it makes a contiguous Data copy and then creates a Metal buffer from those bytes, which adds another copy. The no-copy path itself can return nil. It does not explicitly validate or repair the page alignment and logical-size issues described above. [Metal export implementation](https://github.com/ml-explore/mlx-swift/blob/0bb916c67f4b9e5c682cbe02a42c701c93ab5021/Source/MLX/MLXArray%2BMetal.swift).

`asData(.noCopyIfContiguous)` similarly wraps contiguous bytes and otherwise copies. `.noCopy` exposes stride metadata and wraps without retaining the MLXArray through the Data deallocator. In this revision it also sets Data's byte count to logical `nbytes`, so a non-contiguous view deserves bounds testing before consumers address it through strides. Use the copying path until the exact layout, physical extent, and owner lifetime are established. A no-copy flag is not a sufficient proof of safe export. [Byte export implementation](https://github.com/ml-explore/mlx-swift/blob/0bb916c67f4b9e5c682cbe02a42c701c93ab5021/Source/MLX/MLXArray%2BBytes.swift#L179-L255).

### Laziness changes the lifetime boundary

MLX records computation graphs and evaluates on demand. Accessing host values and the exports above trigger evaluation. A lazy expression can still refer to inputs after its construction call returns. Avoid scalar extraction in row loops; submit enough work together to preserve useful batching. Benchmarks must include evaluation and synchronization, not just graph construction. [MLX lazy evaluation documentation](https://github.com/ml-explore/mlx/blob/main/docs/src/usage/lazy_evaluation.rst), [pinned eval wrappers](https://github.com/ml-explore/mlx-swift/blob/0bb916c67f4b9e5c682cbe02a42c701c93ab5021/Source/MLX/Transforms%2BEval.swift).

Proposed external rule: freeze an imported allocation while any MLX graph can consume it. A synchronous Span borrow cannot represent this asynchronous ownership. Retain a separate lease object. Do not expose arbitrary shared mutable bytes to both a dataframe editor and MLX.

### Float64 is a CPU requirement in this version

The pinned MLX core includes `float64`, and Swift exposes `Double` plus explicit float64 initialization. The C++ graph constructor rejects GPU primitives whose input or output dtype is float64. Therefore "MLX has no Double support" is false, while "this pinned MLX GPU path cannot execute float64" is directly supported by source. Merely constructing a float64 array does not prove GPU arithmetic will work. [GPU dtype rejection](https://github.com/ml-explore/mlx-swift/blob/0bb916c67f4b9e5c682cbe02a42c701c93ab5021/Source/Cmlx/mlx/mlx/array.cpp#L19-L40), [dtype documentation](https://github.com/ml-explore/mlx-swift/blob/0bb916c67f4b9e5c682cbe02a42c701c93ab5021/Source/Cmlx/mlx/docs/src/python/data_types.rst).

Preserve scientific Double columns and Double matrices. Dispatch suitable matrix work to Accelerate's BLAS/LAPACK facilities and vector operations to vDSP, with the actual routine's pointer, shape, stride, and overlap contract checked at the call site. Cast to Float only through an explicit precision policy. Avoid assuming that a routine's use of Accelerate promises a particular CPU execution unit. [Apple BLAS](https://developer.apple.com/documentation/accelerate/blas), [Apple vDSP](https://developer.apple.com/documentation/accelerate/vdsp).

### Swift ownership and deployment

`borrowing` and `consuming` express parameter ownership; they do not convert a heap object into uniquely owned storage or protect a captured raw pointer. Span supplies a bounded, nonescaping view into contiguous memory; MutableSpan supplies exclusive mutable access within its lifetime. These help synchronous kernels and make the unsafe pointer boundary smaller. They do not retain storage for an asynchronous GPU operation. [SE-0377](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0377-parameter-ownership-modifiers.md), [SE-0447](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0447-span-access-shared-contiguous-storage.md), [SE-0467](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0467-MutableSpan.md).

The Span family requires Swift 6.2 or later. The type family supports backdeployment to macOS 10.14.4 and corresponding older Apple OS versions; this does not mean every API returning a Span has the same availability. Array and String conveniences and UTF8Span have separate constraints. The installed Swift 6.4 SDK interface confirms the older deployment annotation on Span and MutableSpan. Compile against SwiftSci's actual minimum target before committing to any particular convenience API. [Span author's deployment guidance](https://forums.swift.org/t/supporting-span-in-packages/81667).

Proposed owner API should offer a synchronous read borrow, a unique mutable borrow, and an asynchronous retained lease as distinct operations. Use closure-scoped unsafe buffer pointers where the desired Span accessor is unavailable. Keep the unsafe cast and binding logic inside the owner implementation. An `@unchecked Sendable` declaration cannot replace those ownership rules.

### Arrow representation requirements

Arrow fixed-width values have a separate validity bitmap with least-significant-bit numbering; one means valid. A zero-null column may omit the bitmap. Null payload bytes are unspecified, so null and NaN must remain distinct. UTF-8 strings use offsets plus bytes. Booleans are bit-packed. Arrow recommends 8- or 64-byte alignment and padding, preferring 64; this does not satisfy Metal's page requirement. Chunking can represent data larger than a single array, and the specification recommends keeping individual arrays within signed 32-bit lengths for interoperability. Arrow leaves mutation coordination to implementations. [Arrow format 1.5](https://arrow.apache.org/docs/format/Columnar.html).

The C data interface separately specifies producer-owned buffers, release callbacks, and array offsets. A compatible byte layout alone does not transfer ownership safely. Preserve the producer's release contract and slice offset, and test round trips against the actual arrow-swift 21.0.0 bridge. Do not infer that every feature in the current format specification exists in that older Swift implementation. [Arrow C data interface](https://arrow.apache.org/docs/format/CDataInterface.html), [pinned Swift implementation](https://github.com/apache/arrow-swift/tree/fb3f3d91be5acd511b7289c7820becc1a68e455d).


## Reproduce the local feasibility probe

The complete isolated probe follows. It does not import SwiftSci or MLX. Save it as `main.swift` in a temporary directory, compile with `xcrun swiftc -O main.swift -o probe`, then run `./probe` on a Metal-capable Mac. Compilation or allocation failure is a failed probe, not a skipped success. No benchmark timing is collected.

Probe source SHA-256: `9f0960820dcb35788bfa58d7996d81acad44248ca2a215017321840b1ae2a865`.

```swift
import Foundation
import Metal
import Darwin

enum ProbeError: Error { case unavailable, allocation, execution }
let count = 4096
let pageSize = Int(getpagesize())
guard let device = MTLCreateSystemDefaultDevice(), let queue = device.makeCommandQueue() else { throw ProbeError.unavailable }
let library = try device.makeLibrary(source: """
#include <metal_stdlib>
using namespace metal;
kernel void update(device float *values [[buffer(0)]], uint i [[thread_position_in_grid]]) {
    values[i] = values[i] * 2.0f + 1.0f;
}
""", options: nil)
let pipeline = try device.makeComputePipelineState(function: library.makeFunction(name: "update")!)
func check(_ buffer: MTLBuffer) throws -> Bool {
    let values = buffer.contents().bindMemory(to: Float.self, capacity: count)
    for i in 0..<count { values[i] = Float(i) }
    guard let command = queue.makeCommandBuffer(), let encoder = command.makeComputeCommandEncoder() else { throw ProbeError.unavailable }
    encoder.setComputePipelineState(pipeline)
    encoder.setBuffer(buffer, offset: 0, index: 0)
    encoder.dispatchThreads(MTLSize(width: count, height: 1, depth: 1), threadsPerThreadgroup: MTLSize(width: min(256,pipeline.maxTotalThreadsPerThreadgroup), height: 1, depth: 1))
    encoder.endEncoding()
    command.commit()
    command.waitUntilCompleted()
    guard command.status == .completed else { throw command.error ?? ProbeError.execution }
    return (0..<count).allSatisfy { values[$0] == Float($0) * 2 + 1 }
}
let sharedResult = try autoreleasepool { () throws -> Bool in
    guard let buffer = device.makeBuffer(length: count * MemoryLayout<Float>.stride, options: .storageModeShared) else { throw ProbeError.allocation }
    return try check(buffer)
}
let allocated = ((count * MemoryLayout<Float>.stride + pageSize - 1) / pageSize) * pageSize
var pointer: UnsafeMutableRawPointer?
guard posix_memalign(&pointer, pageSize, allocated) == 0, let raw = pointer else { throw ProbeError.allocation }
let noCopy = try autoreleasepool { () throws -> [String: Bool] in
    guard let buffer = device.makeBuffer(bytesNoCopy: raw, length: allocated, options: .storageModeShared, deallocator: nil) else { throw ProbeError.allocation }
    return ["contents_aliases_input": buffer.contents() == raw, "cpu_gpu_cpu_values_match": try check(buffer)]
}
free(raw)
let output: [String: Any] = [
    "has_unified_memory": device.hasUnifiedMemory,
    "page_size": pageSize,
    "elements": count,
    "shared_cpu_gpu_cpu_values_match": sharedResult,
    "bytes_no_copy": noCopy,
    "stride_bytes": ["Double":MemoryLayout<Double>.stride,"Double_optional":MemoryLayout<Double?>.stride,"Float":MemoryLayout<Float>.stride,"Float_optional":MemoryLayout<Float?>.stride,"Int64":MemoryLayout<Int64>.stride,"Int64_optional":MemoryLayout<Int64?>.stride],
    "scope": "Correctness and CPU-address alias probe only; no performance, MLX, concurrent-access, or driver-copy claim."
]
print(String(data: try JSONSerialization.data(withJSONObject: output, options: [.prettyPrinted, .sortedKeys]), encoding: .utf8)!)
```

Observed output:

```json
{
  "bytes_no_copy" : {
    "contents_aliases_input" : true,
    "cpu_gpu_cpu_values_match" : true
  },
  "elements" : 4096,
  "has_unified_memory" : true,
  "page_size" : 16384,
  "scope" : "Correctness and CPU-address alias probe only; no performance, MLX, concurrent-access, or driver-copy claim.",
  "shared_cpu_gpu_cpu_values_match" : true,
  "stride_bytes" : {
    "Double" : 8,
    "Double_optional" : 16,
    "Float" : 4,
    "Float_optional" : 8,
    "Int64" : 8,
    "Int64_optional" : 16
  }
}
```
