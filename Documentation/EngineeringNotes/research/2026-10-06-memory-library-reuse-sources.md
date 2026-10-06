# SwiftSci memory reuse research

Research checked 6 October 2026. No repository files or Git state changed. Applied the unslop self-audit.

The most useful replacements are narrow. MLX already owns a recyclable buffer allocator, Metal already reports GPU completion, and Arrow defines how to retain exported column buffers. Swift Collections can replace ordinary CPU storage and queue machinery. None removes SwiftSci's responsibility for snapshot semantics, admission estimates, or keeping allocations alive until asynchronous consumers finish.

## MLX memory management

SwiftSci pins mlx-swift 0.32.3 at `19601207e9a0de51e03ee6ec0c3c5f3784275075`. I fetched source directly at that revision to avoid relying on the stale `.build/checkouts/mlx-swift` checkout, whose HEAD is `0bb916c67f4b9e5c682cbe02a42c701c93ab5021`. The main agent separately verified that the Xcode dependency cache matches the pin.

MLX already recycles buffers and exposes active, cached, and peak memory measurements, `cacheLimit`, `memoryLimit`, and `clearCache`. Use these for MLX allocations instead of adding another tensor buffer pool. A bounded cache is worth benchmarking against clearing it after every operation, because clearing removes reusable buffers. `memoryLimit` can make allocation wait for scheduled work. It is not a hard cap on CPU arrays, Arrow storage, or total process memory. MLX counters must not be added to SwiftSci counters when both include the same imported allocation. [MLX Memory source](https://github.com/ml-explore/mlx-swift/blob/19601207e9a0de51e03ee6ec0c3c5f3784275075/Source/MLX/Memory.swift)

The pinned `WiredMemoryManager` coordinates active and reservation tickets through a shared process manager. Custom `WiredMemoryPolicy.canAdmit` can express a byte or task-count threshold. However, the supplied sum/max policies admit everything by default. Admission considers one policy group; the wired limit is the maximum across groups, not their sum. Waiters live in a dictionary and wake together, so strict FIFO is absent. Cancellation of admission does not throw; `withWiredLimit` still invokes its body, which must check cancellation before doing work. Oversized request errors and checked arithmetic remain application responsibilities. These APIs can remove a custom manager if SwiftSci accepts those semantics. They do not directly replace the current strict FIFO `MemoryBudget`. [Pinned wired-memory implementation](https://github.com/ml-explore/mlx-swift/blob/19601207e9a0de51e03ee6ec0c3c5f3784275075/Source/MLX/WiredMemory.swift)

For the unused legacy task-count manager, first consider deprecation or removal under the project's compatibility policy. Replacing unused code with a new abstraction would save little. For the active byte budget, retain its small implementation unless a measured need justifies changing fairness and cancellation behavior.

## MLX ownership and Metal completion

The pinned `MLXArray.init(rawPointer:_:dtype:finalizer:)` transfers ownership of contiguous data with the supplied shape and dtype. Its finalizer can retain an existing owner, then release it when MLX no longer needs the buffer. The source explicitly requires a pointer compatible with the computational backing, such as Metal. It includes the balanced `passRetained`/`takeRetainedValue` finalizer fix. This supports a small ownership adapter, not arbitrary borrowing of an array pointer. It does not add striding, null masks, dtype conversion, or concurrent mutation safety. [Pinned initializer](https://github.com/ml-explore/mlx-swift/blob/19601207e9a0de51e03ee6ec0c3c5f3784275075/Source/MLX/MLXArray%2BInit.swift)

Metal's `addCompletedHandler` runs after command execution and must be registered before commit. A completion closure can retain the owner and release the operation's reservation after the GPU finishes. This can remove custom completion polling, but it does not prevent the CPU from overwriting the buffer too early. Keep the ownership and mutation contract explicit. [Apple completion contract](https://developer.apple.com/documentation/metal/mtlcommandbuffer/addcompletedhandler(_:))

`makeBuffer(bytesNoCopy:length:options:deallocator:)` wraps existing storage, but requires a page-aligned region in one VM allocation. A normal Swift allocation or Collections array does not promise that layout. Prefer allocating shared Metal storage first when both CPU and GPU will use it. [Apple no-copy buffer requirements](https://developer.apple.com/documentation/metal/mtldevice/makebuffer(bytesnocopy:length:options:deallocator:))

`MTLHeap` provides suballocation and aliasing for Metal resources. It can replace custom GPU slab allocation if allocation churn warrants a pool. It cannot replace CPU ownership, operation admission, or MLX's allocator. Reusing aliased memory still requires correct synchronization. Introducing heaps solely to reduce Swift code is unlikely to help. [Apple resource heaps guide](https://developer.apple.com/library/archive/documentation/Miscellaneous/Conceptual/MetalProgrammingGuide/ResourceHeaps/ResourceHeaps.html)

## Swift Collections and language support

| Candidate | Actual replacement | Constraint |
| --- | --- | --- |
| `Deque` | An array used as a FIFO queue. Removes repeated front-element shifting. | Cancellation searches and middle removal still need policy code. It does not provide an async semaphore or memory admission. |
| `RigidArray` | Fixed-capacity CPU scratch storage and its element initialization/destruction. | Noncopyable; no implicit growth. Does not supply shared snapshots, Metal allocation, leases, or accounting. |
| `UniqueArray` | Growable, uniquely owned CPU storage without copy-on-write. | Growth may allocate and copy/move storage. Does not preserve stable addresses across mutation or replace a shared owner. |

Both array types shipped in Collections 1.3.0, but their source explicitly makes them unavailable below Swift 6.2. The package's Swift 6.0.3 minimum does not imply those types work on Swift 6.0. Collections itself adds no minimum OS deployment target. SwiftSci currently declares Swift tools 6.0 and macOS 14, so make the compiler support decision before adopting the arrays. The standard-library `UniqueArray` proposal is separate from this already shipped package API. [RigidArray 1.3 source](https://github.com/apple/swift-collections/blob/1.3.0/Sources/BasicContainers/RigidArray.swift), [UniqueArray 1.3 source](https://github.com/apple/swift-collections/blob/1.3.0/Sources/BasicContainers/UniqueArray.swift), [Collections compatibility and types](https://github.com/apple/swift-collections)

`Synchronization.Mutex` arrived in Swift 6.0, but requires macOS 15 on Apple platforms. It can put ledger state and its lock together; it does not replace byte-budget actors or GPU fences. Raising the macOS 14 floor for this small substitution is not justified by code reduction alone. [Swift Mutex proposal](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0433-mutex.md), [Swift maintainer explanation of availability](https://forums.swift.org/t/use-of-mutex-within-the-stdlibs-concurrency-module/81191/5)

`Span` belongs to the Swift standard library, not Synchronization. It requires Swift 6.2 and provides bounds-checked, lifetime-checked borrowing of contiguous storage. The span family back-deploys to macOS 10.14.4, although individual conveniences such as `Array.span` have stricter availability. Spans can replace unsafe pointer parameters inside synchronous kernels. They do not own memory or replace an escaping lease retained by GPU work. [Span availability from its implementer](https://forums.swift.org/t/supporting-span-in-packages/81667), [Apple explanation of Span ownership](https://developer.apple.com/videos/play/meet-with-apple/281/)

## Arrow relevance

The Arrow C Data Interface is an ABI for exchanging columnar data with length, offset, null count, buffers, and a producer release callback. The producer retains backing allocations until the consumer calls release; exported buffers should be immutable. That is a useful boundary for a retained, read-only Arrow-backed column. It does not implement a pool, mutation semantics, device completion, or memory admission. Supporting the ABI also does not prove a particular Swift importer accepts every Arrow layout. [Arrow C Data Interface](https://arrow.apache.org/docs/format/CDataInterface.html)

SwiftSci already depends on Arrow. The next comparison should keep supported Arrow input buffers alive instead of materializing each scalar into an optional Swift array, with an explicit copy fallback for unsupported layouts. That has a more direct chance of removing data copies than replacing the entire storage layer. Verify the pinned importer's offsets, children, dictionaries, and chunk behavior before making a broad zero-copy claim.

I would test Arrow retention and bounded MLX cache reuse first. Use Metal completion directly wherever a custom completion mechanism exists. Treat Collections storage as a CPU-only simplification experiment. Keep the current byte-budget contract until a replacement proves the same behavior or the project explicitly chooses a different one. No defensible line-count reduction or performance percentage can be promised without that comparison.
