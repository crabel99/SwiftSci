# Reusing existing memory implementations

Date: 2026-10-06. Source reviewed: SwiftSci `530151b4fa700cdd55cca95dc43d4d5080469d2a`, branch `codex/memory-kernel-trial`. This is a design audit, not a measured replacement or an implementation change.

## Decision

Reduce SwiftSci's responsibilities to scientific data semantics, operation planning, ownership across backends, and tested admission policy. Use backend allocators, completion mechanisms, and supported containers for their established responsibilities. The highest-confidence opportunities are already dependencies or Apple frameworks. Adding another general-purpose memory manager is not justified by this review.

## Findings in the current source

### MLX memory management

The Xcode dependency checkout is pinned to MLX Swift 0.32.3, commit `19601207e9a0de51e03ee6ec0c3c5f3784275075`. Its tracked files are clean. `Source/MLX/WiredMemory.swift` exists in that commit. A separate `.build/checkouts/mlx-swift` checkout has a different revision; API claims here refer to the Xcode checkout and the root Package.resolved pin.

MLX already implements active and reservation tickets, policy-based admission, process-wide wired-limit updates, buffer recycling, cache limits, and memory snapshots. Use those implementations for MLX-owned memory rather than writing another MLX buffer pool or wired-limit controller. Retained-model reservations are a candidate use of its reservation tickets, but they must follow actual storage ownership, including shared views. A ticket size is an estimate, not an automatic measurement of all model allocations.

This is not a direct replacement for SwiftSci's MemoryBudget. The inspected MLX manager groups admission by policy identity, resumes all waiters, and does not promise our strict FIFO ordering. Its default sum and max policies allow admission and compute a wired limit; they do not establish a hard byte cap. Its scoped ticket helper still invokes the body if waiting for admission was cancelled. An adapter must check cancellation before starting admitted work and reject requests that cannot fit. A single shared policy identity is needed if several callers are intended to share one budget. Avoid creating separate managers that independently manipulate the process-global wired limit.

Our existing MemoryBudget is 130 lines and implements explicit byte reservations, FIFO waiting, oversized-request rejection, cancellation, and completion-driven release. Keep that policy until a replacement passes the same behavioral tests. Rebuilding FIFO and diagnostics around MLX could cost more code than retaining this small actor.

Sources: [MLX wired memory](https://github.com/ml-explore/mlx-swift/blob/19601207e9a0de51e03ee6ec0c3c5f3784275075/Source/MLX/WiredMemory.swift), [MLX memory and caching](https://github.com/ml-explore/mlx-swift/blob/19601207e9a0de51e03ee6ec0c3c5f3784275075/Source/MLX/Memory.swift).

### Remove redundant SwiftSci policy before adding wrappers

SwiftSci's WiredMemoryManager and WiredMemoryTicket total 174 source lines, including documentation. They limit task count and clear MLX's global cache on explicit finish; they do not reserve bytes or set a wired limit. A search of Sources found no production callers outside their own definitions. They are public, so absence of internal callers does not prove absence of external users.

Prefer deprecation and eventual removal under the project's compatibility policy. If legacy behavior must remain, isolate it as compatibility code rather than adding it to the new execution module. If an actual algorithm requires a task-count limit, define that requirement independently from memory accounting.

MLX already has a recycling pool. Evaluate a bounded cache policy instead of clearing its entire cache after each legacy ticket. This is a proposal requiring workload comparison, not a measured speedup. Do not change global cache settings independently for overlapping operations, and do not interpret cache clearing as device completion.

Local sources: `Sources/SwiftPreprocessing/Core/WiredMemoryManager.swift`, `WiredMemoryTicket.swift`, and `MemoryBudget.swift`.

### Reuse Arrow buffers at the dataframe seam

Apache Arrow Swift 21.0.0 is already a direct dependency at `fb3f3d91be5acd511b7289c7820becc1a68e455d`. It includes C import/export and buffer-owner lifetimes. The Arrow C Data Interface specifies shared column buffers, validity, offsets, and release callbacks. Use that established interchange contract rather than inventing separate ownership handshakes for every external dataframe library.

SwiftSci currently imports Arrow columns by iterating values into new optional Swift arrays in ArrowTableBridge.toDataFrame. ArrowDataBuffer has a retained-owner design but no construction caller was found elsewhere in Sources. This is a concrete integration gap. A retained, read-only Arrow view could replace those materializations for compatible columns. Mutation would then detach into owned storage when needed. It must preserve missing values, chunk boundaries, slicing, row identity, and public value semantics.

The pinned Arrow importer rejects nonzero offsets, nested children, dictionary arrays, and unknown null counts. Its internal ArrowBuffer initializer is not a public allocator interface. Therefore Arrow is not a drop-in replacement for our mutable Metal-backed storage. Start with supported flat numeric columns, test release callbacks and slices, and measure conversion copies. Dense solver packing or dtype changes can still require a copy.

Sources: [Arrow C Data Interface](https://arrow.apache.org/docs/format/CDataInterface.html), [pinned Swift importer](https://github.com/apache/arrow-swift/blob/fb3f3d91be5acd511b7289c7820becc1a68e455d/Arrow/Sources/Arrow/ArrowCImporter.swift), and SwiftSci `Sources/SwiftDataFrame/Internal/ArrowTableBridge.swift` and `ArrowDataBuffer.swift`.

### Reuse backend completion and ownership

ScopedGPURead already uses MLXArray's managed raw-pointer initializer, captures the Metal owner, and waits for the GPU stream before leaving its synchronous scope. Preserve its extent, shape, alignment, and lifetime checks. Prefer the supported MLX interface over a second permanent C-level finalizer adapter once the pinned dependency's release regression passes.

For custom Metal work, build any asynchronous completion adapter over Metal command completion. Do not maintain an independent polling model of GPU completion. An MLX graph does not give our caller ownership of its underlying Metal command buffers, so Metal completion alone cannot replace MLX stream semantics. Keeping backend-specific completion adapters is justified.

CPU and GPU buffer lifetimes still need to connect to SwiftSci reservations. Neither a managed-pointer finalizer nor a command completion callback chooses our result-retention or cancellation policy. Those remain coordination responsibilities.

Sources: SwiftSci `Sources/SwiftPreprocessing/Core/ScopedGPURead.swift`; [MLX managed-pointer initializer](https://github.com/ml-explore/mlx-swift/blob/19601207e9a0de51e03ee6ec0c3c5f3784275075/Source/MLX/MLXArray%2BInit.swift); [Metal command completion](https://developer.apple.com/documentation/metal/mtlcommandbuffer/addcompletedhandler(_:)).

### Keep numerical kernels in Accelerate

The current CPU regression solver already calls LAPACK dgels_, including its workspace-size query. BLAS, LAPACK, and vDSP should remain the numerical implementations wherever their semantics and precision meet the operation's contract. Our reusable CPU arena supplies workspace and lifecycle; it does not replace LAPACK. A general tensor dependency solely to allocate Double scratch would add conversion and policy work without an established benefit.

Local source: `Sources/SwiftML/Core/LinearRegression.swift`.

## Proposed replacement order

1. Separate and deprecate the unused legacy task-count manager. Inventory external compatibility obligations before removal.
2. Consolidate MLX configuration and telemetry around the existing Memory and wired-ticket interfaces. Preserve the small CPU/shared FIFO budget unless a tested adapter actually reduces complexity.
3. Prototype retained Arrow views for supported numeric columns. Test validity, release, slice, chunk, mutation, and conversion behavior before expanding the format set.
4. Evaluate standard-library or Swift Collections storage for the CPU-only owner. Require the same alignment, lifetime, allocation-count, and numerical results. Keep newer compiler/runtime requirements explicit.
5. Use native Metal and MLX completion adapters for GPU integration. Consider heaps only after measurements show a suballocation problem; they do not remove the need to track active users.

Each accepted replacement must remove the superseded implementation and retain meaningful public behavior tests. Measure source reduction after the prototype, including adapter and compatibility code. This audit makes no claim that a larger upstream implementation is necessarily safer or faster for our workload.

## What remains SwiftSci's responsibility

Scientific null and precision semantics, data layout selection, retained-result ownership, whole-operation capacity estimates, and cross-backend release ordering remain local. Persistent-result accounting and asynchronous GPU integration are still incomplete. The validated asynchronous CPU workspace is a disposable experiment, not a production replacement.

No code or dependencies changed, no benchmarks were run, and nothing was pushed for this audit. Findings belong only on codex/engineering-notes.

## External interface details

See [the primary-source interface survey](2026-10-06-memory-library-reuse-sources.md) for Swift Collections, Span, Mutex, Metal heap, and deployment constraints.
