# Third memory foundation review

Date: 2026-10-05. Status: local research and design proposal. No production implementation or upstream API approval is implied.

## Decision

Continue the memory trial with a small snapshot and preparation module. Keep typed source ownership, validity and row provenance together. Put layout conversion, destructive workspace and asynchronous lifetime management in consumer adapters. Qualify the complete public scientific pipeline before promoting this design into production.

This review found two reproducible storage behaviors that sharpen the design: composed selections allocate duplicate maps, and an MLX operation can overwrite an imported source when its MLX input handle is released. It also found that the current prototype's regression algorithm omits production numerical refinement. These findings justify a bounded qualification phase. They do not justify a general allocator framework or a wholesale rewrite.

## Scope and provenance

The code reviewed was `codex/memory-kernel-trial` at `59b77f7fd2200e62a1e3b7f4e040804bfb5e5892`. Its preserved parent, `codex/unified-memory-prototype`, remains at `aa5c71968c080f4188357c4cb628389f89ca00a2`. The preceding engineering record was `abad90336f6b82bf2646f17633118e995f7ba4b9`.

The dependency checkout was mlx-swift 0.32.3 at `19601207e9a0de51e03ee6ec0c3c5f3784275075`, with MLX core at `1f8e74e3f12f31365464a6867c6579f0e9b29d85`. Both dependency checkouts had clean tracked files. Device probes linked the existing qualified Release objects and metallib. Their hashes and local compiler commands are in the evidence archive.

Three independent reviews considered a minimal interface, a flexible resource description, and the normal scientific/AI caller. The synthesis applies research, codebase design, foundational thinking and prose review. This was not a multi-model audit.

The local evidence archive is `~/local-ai/spl/swiftsci/memory-foundation-review-20261005/`. It contains reviewer reports, probe sources, compiler records and outputs. This dated note belongs only to `codex/engineering-notes`; it must not enter implementation PRs.

## Constraints from the physical machine

Unified memory gives CPU and GPU access to shared physical memory. It does not remove numerical conversion, cache traffic, packing, synchronization or exclusive-write requirements. Shared storage mode describes accessibility; the consumer still needs an ordering and lifetime contract. See [Apple resource storage modes](https://developer.apple.com/documentation/metal/choosing-a-resource-storage-mode-for-apple-gpus) and [CPU/GPU synchronization](https://developer.apple.com/documentation/metal/synchronizing-cpu-and-gpu-work).

Capacity, sustained memory traffic, arithmetic throughput and completion are separate constraints. A gather or scale operation can have low arithmetic intensity. QR, matrix multiplication and autoregressive decoding have different reuse and workspace requirements. Use the Roofline relation `attainable performance <= min(compute ceiling, sustained bandwidth * arithmetic intensity)` to form testable hypotheses, with bandwidth measured at the relevant memory level. Do not substitute advertised bandwidth or cache bursts for sustained DRAM throughput. The [Berkeley Lab Roofline bibliography](https://amcr.lbl.gov/departments/computer-science-department/ppan/roofline-performance-model/ppan-roofline-publications/) identifies the original work; [STREAM](https://www.cs.virginia.edu/stream/ref.html) provides a reference for sustained bandwidth measurement.

A smaller allocation can run slower if it causes scattered accesses or extra passes. The earlier direct-packing experiment halved tile scratch but commonly slowed complete workflows. The hardware explanation remains unproven. Collect cache and bandwidth evidence before calling it bandwidth-bound. Apple's [memory-bandwidth guidance](https://developer.apple.com/documentation/xcode/measuring-the-gpus-use-of-memory-bandwidth) explains the relevant profiling approach.

No hardware-counter session, STREAM run or broad performance comparison ran during this review. No new speedup is claimed.

## New verified findings

### Imported ownership must include the MLX handle

The MLX core checks its own descriptor and data references when deciding whether an input can donate storage, in `mlx/array.h:294-295`. Its Metal softmax implementation can reuse that input buffer in `mlx/backend/metal/softmax.cpp:24-35`. A custom deleter retaining a Swift allocation does not add an MLX array reference.

A bounded C++ probe imported one page containing 4,096 Float values. It retained the host allocation in both cases, evaluated GPU softmax and synchronized completion. Releasing the input MLX handle allowed output to alias the source and changed all 4,096 source elements. Retaining the input handle prevented output aliasing and preserved every source element. The release callback ran exactly once in each case.

The Swift probe repeated this through the current `Column<Float>` implementation and unchanged copies of the `importedArray` and `mlxAddress` helpers from `Benchmarks/UnifiedMemoryPrototype/Device.swift`. Both imports actually aliased the source. Dropping the imported input changed 4,096 source elements; retaining it changed zero. The probe also required the owner ledger to return to zero live owners with balanced releases. Both cases passed their expected checks.

This is an adapter obligation, not evidence that MLX violates its mutable raw-buffer contract. The current device trial retains its input through execution, so the finding does not invalidate that trial. It blocks a generalized immutable-snapshot import that retains only the Swift owner. The adapter must retain the allocation and an independent imported MLX handle through actual completion, and must not expose a mutable alias that defeats this guarantee.

The Swift diagnostic compiled with optimization and the profiling runtime required by the linked dependency objects. It is a correctness probe, not a timing benchmark. It covers one donation-capable operation and a blocking completion path. Other operations, cancellation, concurrent mutation and arbitrary slices remain unqualified.

### Row maps are material storage

`SelectedTable.selecting` independently composes original row identities and physical source positions in `Benchmarks/UnifiedMemoryPrototype/Storage.swift:198`. Even when equal, the resulting arrays can occupy different allocations.

A Release probe compiled the current storage source and retained 100,000 selected rows. Initial maps shared a buffer. Reversing a retained selection produced two equal but distinct buffers with 800,000 logical bytes each. The value-owner ledger omitted both maps. A materialized selection followed by another selection produced genuinely different identity and physical-position maps, confirming that the two concepts cannot simply be collapsed.

The private representation should distinguish implicit identity/range, one shared map, and two genuinely distinct maps. Preserve ordering and duplicates. A bitmap cannot represent every selection. UInt32 compression is a later checked option; source identity and compact physical position may have different ranges.

The probe's owner-byte figure counts all value owners alive at that observation. It is not the exclusive memory of each snapshot. Array capacities, headers and RSS were not measured. This proves duplicated logical index storage, not the cause of the earlier reuse timing regression.

### The current prototype does not qualify the complete model

The prototype in `Benchmarks/UnifiedMemoryPrototype/Pipeline.swift:265-289` solves QR and predicts with BLAS. Production `Sources/SwiftML/Core/LinearRegression.swift:180-229` computes compensated residual/stationarity corrections and can perform three correction passes. It still needs original normalized features after LAPACK overwrites its workspace. Production also has an analytical-error fallback at lines 123-128 and scalar CPU prediction at lines 371-379.

Consequently, a layout optimization must retain readable normalized data as well as exclusive solver workspace. Removing the former to reduce memory can remove numerical safeguards. A prototype comparison using simpler QR is insufficient evidence for the production endpoint, even if its preparation matches production.

The default model route introduces another boundary. `Sources/SwiftPreprocessing/Core/HardwareRouter.swift:39-40` selects GPU at 1,000 rows. That route converts Double inputs to Float and uses gradient descent. The million-row Double QR trial qualifies an explicit CPU scientific path, not the default model route.

Use the existing public workflow in `Benchmarks/Worker/PublicWorkflows.swift:124-146` and supervised workflow in `SupervisedWorkloads.swift:90-137` as the next acceptance endpoints. They exercise the actual model, training-only preprocessing and held-out prediction.

## Further source findings

| Finding | Design consequence |
|---|---|
| `Source/MLX/WiredMemory.swift` already supplies policy groups, admission decisions and tickets. Its body scope does not itself await arbitrary GPU work. | Reuse dependency policy machinery. Check cancellation before submission and keep completion inside the ticket lifetime. Do not create a competing global wired-limit coordinator. |
| MLX counts imported allocations in `mlx/backend/metal/allocator.cpp:207-217`. | Adding all MLX active bytes to all Swift owner bytes double-counts aliases. Account by allocation identity; report runtime counters separately until overlap can be reconciled. |
| SwiftSci documentation describes byte reservations in `HardwareRouterAndMemory.md:26-38`, but the current manager admits by task count. | Correct that documentation with admission work. Do not claim an enforced byte budget today. |
| `MLXArray+Metal.swift:21-32` exports the current pointer with logical byte length. | Importing a padded parent does not prove arbitrary logical slices can be exported without copying. Qualify import and export separately. |
| `EstimatorPipeline.swift:64-103` dispatches through estimator protocols and nested arrays. | A concrete prepared-input overload alone may never run for the normal pipeline. Test protocol dispatch through the public caller. |
| `StandardScaler.swift:194-206`, `PreparedNumericBatch.swift:112-118` and `DataFrame+Matrix.swift:10-16` can expand prepared values back to optional columns and nested rows. | Integrate prepared input across the complete operation to avoid losing the storage benefit between stages. |
| The active decoder uses concatenating `KVCache`, while the paged cache implementation is a separate path. | Treat token, weight and KV memory as a distinct consumer workload. Dataframe test counts do not qualify decoder memory. |
| The existing `DataBuffer` and `ArrowDataBuffer` abstractions have little or no live production use. Active Arrow conversion expands optional values. | Do not force new ownership through unused raw-buffer abstractions. Qualify a real source adapter when required. |

These are source observations at the recorded revisions, not newly repaired defects. MLX's default admission policies can admit all tickets, and separate groups do not form a shared process budget. SwiftSci still needs semantic estimates for host snapshots, possible mutation copies and CPU workspace. A managed-work budget cannot guarantee a hard cap over unrelated external allocations.

## Alternatives and chosen module boundary

| Alternative | Strength | Cost or limitation | Decision |
|---|---|---|---|
| Minimal typed snapshot, selection and preparation | Centralizes validity, row ordering, conversion and ownership | Requires carefully checked construction and consumer integration | Adopt as the core module |
| General resource-description interface | Can express layouts, aliases, budgets and execution requirements | Makes callers responsible for runtime details and temporary allocations | Keep only a private subset generated by real consumer adapters |
| Consumer-first pipeline integration | Exercises actual numerical behavior and exposes avoidable conversions | Needs protocol-aware migration and compatibility entry points | Use as the first integration and acceptance workflow |

The public caller should normally continue to fit and predict through its existing pipeline. An advanced caller can request reusable preparation when that is useful. The names below describe responsibilities, not final public Swift declarations.

- A typed snapshot owns values, validity and its row domain. Selection preserves original observation provenance separately from physical positions.
- Preparation produces a checked representation for a supported consumer. Missing-value and precision conversions are explicit here.
- A CPU adapter supplies readable normalized data and exclusive destructive workspace. It preserves the production algorithm and fallback rules.
- An MLX adapter supplies the accepted dtype and layout, a qualified import or copy, the retained MLX descriptor and the completion obligation.
- An execution record owns transient reservations and all resources needed until completion. Cancellation of a waiter does not release submitted work early.

This gives the module Depth: callers ask for valid input for an operation without implementing its ownership rules. The Seam is between semantic snapshots and consumer preparation. Adapters provide Locality when runtime import or solver layout changes. Leverage comes from sharing selection and conversion checks among real consumers. Removing this module would force those checks back into scaler, solver and device callers; removing a generic allocator wrapper would not.

Keep representation details private: identity/range maps, bitmap offsets, initialized extent, accessible allocation extent, growth, packing, synchronization and fallback copies. Swift's [Span proposal](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0447-span-access-shared-contiguous-storage.md) offers a direction for nonescaping access, but its compiler and deployment compatibility must be qualified before changing supported versions.

## Numerical and ownership rules

Typed snapshots preserve dtype, valid NaNs, missing values, signed zero, row order and duplicate rows. Consumer conversion is a separate step. The existing scaler's missing-to-NaN behavior is a documented compatibility contract, not evidence that the snapshot should discard validity. Likewise, converting Int64 to Double is not lossless typed storage.

Feature rows and targets must share a checked selection domain. Equal row counts cannot prove alignment. Independently generated zero-based positions are not global observation identifiers. Prediction must preserve fitted feature order; same-count reordered named columns must not silently yield predictions.

Physical capacity, initialized extent and logical view extent are separate. Every reachable address must refer to initialized storage. Allocator padding does not establish additional usable elements. Destructive consumers receive exclusive writable storage. Retained-source and selected-only treatments describe ownership promises, not universal speed claims.

Arrow's [columnar format](https://arrow.apache.org/docs/format/Columnar.html) supports values plus validity as a useful representation precedent. DuckDB's [vector representations](https://duckdb.org/docs/current/internals/vector) show that logical selection need not immediately flatten storage. Neither establishes a universal Apple tile size or an optimal Swift implementation.

## Ordered qualification work

1. Add ownership regression coverage before generalizing device sharing. Include the observed donation case, a second donation-capable operation, exactly-once release and retained source mutation. Preserve the current blocking adapter until completion and cancellation rules are proven.
2. Replace duplicate private row maps with explicit identity/range/shared/distinct cases. Test nested retained and materialized selections, duplicates, empty selections, source release and invalid indices. Keep numerical operations unchanged so storage effects remain attributable.
3. Complete allocation accounting. Include index capacity, validity, padding, conversion output, original normalized data, solver workspace and runtime aliases. Use allocation identities, not reusable pointer values alone. Reserve a whole feasible peak or a nondeadlocking staged plan. A fallback copy must fit the same policy.
4. Integrate the actual public CPU workflow through prepared protocol dispatch. Preserve compensated refinement, analytical fallback, training-only fit and prediction behavior. Validate with analytical answers, noisy and poorly conditioned cases, existing NIST contracts and held-out predictions. Do not loosen tolerances to accommodate a layout change.
5. Qualify the device boundary separately. Cover arbitrary sizes and offsets, actual alias versus copy, conversion limits, cancellation before and after submission, and runtime completion. Compare explicit CPU, explicit GPU and `.auto` at 999, 1,000 and 1,001 rows across widths. Record algorithm and dtype with timing.
6. Measure complete workloads after correctness. Vary width, selection order/density, source retention/release, reuse, working-set size and clustered/scattered mutations. Compare setup-inclusive time, peak footprint and categorized capacity. Establish acceptable regression bounds before collecting comparative results.

Chunked mutation remains optional. Under independent uniform edits over C chunks, E edits touch an expected `C * (1 - (1 - 1/C)^E)` chunks. This derived model explains why widespread edits can erase copy savings while retaining directory and traversal costs. It is not a benchmark result. Test append growth and real edit distributions before adopting chunks by default.

For LLMs, compare the active cache with a capacity-growing implementation in a separate experiment. Current [MLX-LM cache source](https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/models/cache.py) provides a reference, but pin its revision before implementation. Do not choose its growth increment without measuring SwiftSci prompt and decode workloads.

## Validation limits and revisit conditions

This review ran the selection-map Release probe and C++/Swift device donation probes. It did not rerun the full production suite, establish a new performance baseline, test memory pressure, or qualify asynchronous cancellation. Prior prototype counts remain historical evidence at their recorded commits.

Revisit the private consumer model when an actual new adapter cannot express its required ownership or layout. Revisit default storage treatment after complete workflow evidence shows a repeatable benefit under agreed memory and timing limits. Revisit minimum Swift/macOS support only with an explicit compatibility decision. Revisit chunking after scans, mutation distributions and tail growth are measured together.

Production promotion should follow demonstrated preservation of the public workflow and resource lifetime. The next implementation should strengthen these contracts on the preserved trial branch, one verifiable change at a time. No implementation branch was changed, pushed or merged as part of this research.
