# [FEAT] Define compact dataframe storage, numerical buffer interfaces and compatibility policy

Tracking issue: [Nodibell/SwiftSci #40](https://github.com/Nodibell/SwiftSci/issues/40). Implementation branch: `codex/compact-column-storage`, currently unpublished.

## Problem

Following [PR #39](https://github.com/Nodibell/SwiftSci/pull/39), I want to discuss the next stage of dataframe optimization before committing to changes in public APIs or supported toolchains.

The current work optimizes the existing optional-array representation. The next opportunity is to keep data compact through filtering, sorting and preprocessing, then prepare the layout required by numerical operations once. Today, several consumers convert columns into nested Double arrays, reconstruct columns, and finally flatten or transpose the data for Accelerate or MLX.

This affects both execution time and peak memory. On Apple silicon, dataframe allocations also compete with model weights, intermediate tensors and caches for unified memory. Lower memory use is a useful outcome even when an individual operation is not faster.

The implementation target for this work is Apple silicon. I would like maintainer agreement on compiler, deployment and API compatibility before choosing the ownership and buffer interfaces.

## Evidence so far

A standalone compact-storage prototype uses fixed-width numeric values with a separate validity bitmap and prepares column-major Float batches for Accelerate. It does not replace production storage.

On an M4 Max, four million rows with eight numeric features and about 1% missing values produced:

| Measure | Existing dataframe path | Compact column-major batch path |
|---|---:|---:|
| Column payload | 512 MB | 260 MB |
| Peak process memory | 860 MB | 523 MB |
| Repeated preprocessing and linear inference | 37.00 ms | 31.29 ms |
| Warm binary loading and construction | 696 ms | 90 ms |

These are fixture-specific prototype results, in decimal MB. Loading includes representation construction and is not CSV parsing. Inference uses fixed linear weights on the CPU, not an LLM or GPU. The compact path still materializes a Float batch. All 252 edge runs passed, and larger cases compared selected features and predictions against a scalar reference using exactly representable input fractions.

A later storage experiment also found that converting optional arrays to compact storage and immediately back inside one filter was 4.22 to 4.76 times slower in the median million-row cases. That makes downstream integration part of the design: adding conversions around the existing API is unlikely to realize the storage benefit.

The prototype and evidence are preserved on my local, unpublished `codex/compact-column-storage` branch at `713252a14a`. I intend to associate that branch with this issue and publish it after the implementation direction is agreed. This is separate from PR #39.

## Proposed direction

Use common ownership and access contracts with distinct representations for different consumers:

| Representation | Intended use |
|---|---|
| Typed columns with optional validity | Filtering, sorting, grouping, reductions and nullable table interchange |
| Dense vectors and matrices with explicit dtype, shape and strides | Accelerate, LAPACK, dense model inputs and MLX adapters |
| CSR/CSC sparse matrices | Sparse features and numerical operations without dense intermediates |
| Table batches with row identity and selections | Bounded ingestion, preprocessing and result alignment |

Preserve compact columns through transformations. Materialize a matrix when the next consumer requires one, choosing its dtype, memory order and missing-value policy explicitly. Separately allocated columns cannot generally become one contiguous matrix without packing.

The first implementation should prove one complete path:

```text
filter → stable sort → column scaling → prepared matrix → CPU solve/predict
                                                     → results mapped to original rows
```

This includes the consumer changes needed to test the storage design. Broad algorithm changes and migration of every estimator should follow in separate PRs.

## Compatibility decisions requested

### 1. Swift compiler and package minimum

The reviewed manifest declares Swift tools 6.0. Newer ownership APIs, including `Span` and `MutableSpan`, may provide a better way to express scoped reads and exclusive mutation. Their accepted proposals are implemented in Swift 6.2. See [Span-providing properties](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0456-stdlib-span-properties.md) and [MutableSpan](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0467-MutableSpan.md).

Should this work retain Swift 6.0, raise the minimum compiler, or introduce newer APIs conditionally? If we raise it, which release should carry that requirement, and what is the supported Xcode/CI baseline?

### 2. macOS deployment minimum

The reviewed package targets macOS 14. Compiler support and operating-system availability must be considered separately, for each API.

A small typecheck with the installed Swift 6.4 SDK and an arm64 macOS 14 target found that `Array.span` requires macOS 26, while obtaining a span from `ArraySlice` typechecks for macOS 14. This is a compile-time observation on that SDK, not runtime validation on macOS 14 or proof of identical behavior in every Swift 6.2 toolchain.

Should we preserve macOS 14 through compatible interfaces or fallbacks, or intentionally raise the deployment minimum? We should determine the minimum from the chosen APIs and supported configurations rather than assume all modern borrowing APIs have the same requirement.

### 3. Public storage and access APIs

`TypedColumn.values` currently exposes `[T?]`. Keeping the same property as a computed conversion could preserve many source call sites while changing allocation and access costs. It could also undo the benefit if internal consumers continue reading it repeatedly.

Which approach is preferred?

- Preserve `values` as a documented compatibility conversion and migrate internal consumers to borrowed buffers.
- Add an explicit materialization method, deprecate implicit array access, and remove it in an agreed breaking release.
- Introduce a separate compact type first, accepting the maintenance and conversion cost of two public representations.

We also need a policy for existing initializers, concrete `TypedColumn<T>` downcasts, `AnyColumn` implementations, and the nested `[[Double]]` estimator interfaces. Source compatibility, behavioral compatibility, allocation behavior and any promised binary compatibility are separate concerns.

### 4. Mutation and snapshots

Compact fixed-width values do not inherently require expensive mutation. An exclusive owner can overwrite a value and validity bit directly. The harder cases are shared snapshots, capacity growth, structural edits, variable-length values, and outstanding foreign or GPU readers.

I propose:

- Copy-on-write snapshot semantics for public table values.
- Builders with reserved capacity for ingestion and append.
- Exclusive batch mutation that checks ownership once and maintains validity/null counts together.
- Scoped read/mutable access for synchronous kernels.
- Retained buffer leases for foreign objects and asynchronous GPU operations, with explicit completion and release rules.

Is this consistent with the intended API? In particular, SwiftSci's MLP saves earlier weights using Swift array value semantics. A shared mutable replacement must not change those saved snapshots. Parallel bitmap updates also require coordination when different rows share the same bitmap word.

### 5. Numerical conversion policy

Should one prepared-batch interface own the rules for feature order, row mapping, dtype, matrix order, missing values and copy policy?

Current consumers differ: matrix extraction substitutes NaN, clustering substitutes zero, and some statistics drop missing values. The design should make those choices explicit and preserve observation alignment. Integer identifiers must not silently lose precision through Double or Float conversion. A strict no-copy request should fail when the requested layout cannot be shared.

### 6. Interoperability and module ownership

Arrow is already a dependency and fits nullable table interchange. Dense tensor adapters can use native buffer interfaces and, where appropriate, DLPack or a NumPy-facing bridge. A shared-memory protocol does not itself port NumPy/SciPy algorithms or supply a Python runtime.

Should the ownership and descriptor types live within SwiftDataFrame or a small shared module that numerical targets can consume without a dataframe dependency? I propose implementing concrete Accelerate and Arrow/MLX adapters before introducing a general plugin registry.

Metal-compatible buffers must retain their owner and obey CPU/GPU synchronization rules. Before adopting managed raw-pointer MLX import, we also need dependency-specific lifetime tests; the reviewed MLX 0.31.6 finalizer differs from the newer implementation.

## Existing consumer review

The review covered representative code paths in dataframe, statistics, preprocessing, ML, clustering, forecasting, sparse NLP, vision, model selection, explanations, ingestion and LLM caches. It was not a complete audit of every numerical algorithm.

Examples that motivate the boundary:

- [Matrix extraction](https://github.com/crabel99/SwiftSci/blob/4c5bb953547ba5d84c7fd86bf868b1680c5f1811/Sources/SwiftDataFrame/Core/DataFrame%2BMatrix.swift) creates nested rows; target extraction creates an N-by-1 matrix first.
- [StandardScaler](https://github.com/crabel99/SwiftSci/blob/4c5bb953547ba5d84c7fd86bf868b1680c5f1811/Sources/SwiftPreprocessing/Core/StandardScaler.swift) reconstructs column buffers from nested input and creates further intermediates.
- [LinearRegression](https://github.com/crabel99/SwiftSci/blob/4c5bb953547ba5d84c7fd86bf868b1680c5f1811/Sources/SwiftML/Core/LinearRegression.swift) prepares column-major Double workspace for CPU solving or Float tensors for GPU execution.
- [SparseMatrix](https://github.com/crabel99/SwiftSci/blob/4c5bb953547ba5d84c7fd86bf868b1680c5f1811/Sources/SwiftPreprocessing/Core/SparseMatrix.swift) already has CSR/CSC representations that should remain sparse.

These examples support a common data-access contract. They do not imply that every operation should use one physical layout.

## Issue and PR boundaries

| Work | Proposed ownership |
|---|---|
| Compatibility decisions, compact column ownership, validity, mutation and prepared-buffer contracts | This issue and `codex/compact-column-storage` |
| Direct target extraction, column scaling and one matrix consumer needed to validate the full workflow | First implementation under this issue, in reviewable commits or narrowly scoped dependent PRs |
| Migrating additional estimators, sparse features, embedding storage and GPU consumers to the agreed contract | Linked follow-up issues with separate branches/PRs |
| Mathematical algorithm or kernel optimization that works with existing inputs and does not need new storage | Independent issue and branch/PR; link here where relevant |
| Existing numerical correctness defects | Separate regression-fix issues/PRs; do not wait for the storage redesign |

The last category includes reproduced row misalignment in nullable correlation, incorrect Fortran-order NPY-to-dataframe conversion, and Int64 precision loss through that conversion. Numeric feature extraction also lacks support for Float, Int32 and native Int columns. These findings inform our contracts, but their fixes should remain independently reviewable.

The compact prototype branch predates later optimization commits. Before production implementation, carry its prototype forward onto the agreed baseline after PR #39, preserving the experiment and avoiding duplicate optimization changes in the next PR.

## Alternatives considered

Keeping optional arrays avoids a migration but retains their storage and conversion costs. Converting to compact buffers only inside each operation performed poorly in the prototype. Making every column a tensor loses heterogeneous/null-aware table semantics and still leaves layout conversions. Chunked storage or deferred edit buffers may help shared sparse edits, but add indirection and consolidation costs; they need workload evidence before becoming the default.

## Acceptance criteria

- [ ] Agree and record compiler, deployment, architecture and release compatibility policy.
- [ ] Define ownership, borrowing, snapshot and asynchronous lifetime rules before exposing raw buffers.
- [ ] Specify dtype, null, row-order, empty-schema, stride and materialization behavior.
- [ ] Demonstrate the complete filter/sort/scale/matrix workflow with exact row alignment and stated numerical tolerances.
- [ ] Test unique/shared updates, duplicate scatter, first-null creation, bitmap boundaries, append growth and retained views.
- [ ] Preserve training snapshots and exclude concurrent mutation of data used by active kernels.
- [ ] Measure total workflow time, conversion time, copied bytes and peak live/resident memory across varied sizes, widths, null patterns and selection densities.
- [ ] Validate on the agreed minimum toolchain/deployment configurations and the current Apple silicon environment.
- [ ] Document migration and allocate broader consumer and correctness work to linked follow-up issues.

The goal is an agreed, testable storage boundary and a working first integration. No new minimum version or breaking public API is assumed approved by this proposal.
