# Pinned MLX Swift managed-import lifetime failure

The October 1 prototype reproduces an owner leak in mlx-swift 0.31.6, revision `0bb916c67f4b9e5c682cbe02a42c701c93ab5021`. This finding concerns the Swift managed-pointer wrapper. The direct C callback path passes the prototype's release checks.

## Observed behavior

A 4,096-element Float32 column uses a shared Metal allocation. A read lease retains the allocation. The Swift `MLXArray(rawPointer:shape:dtype:finalizer:)` initializer captures that lease in its finalizer. A GPU operation reads the array, completes, and returns the correct result.

After the arrays leave scope, GPU synchronization and `Memory.clearCache()` complete. The callback counter is one. The weak lease reference is still non-nil and the owner ledger still reports 16,384 live bytes. The reproducer runs in a separate process, so the deliberate retained allocation does not contaminate successful adapter measurements.

The ordinary copying import releases its source. The explicit C managed import shares its pointer and releases its source after completion. A direct managed graph abandoned before evaluation also releases its owner.

## Source explanation

In `Source/MLX/MLXArray+Init.swift`, the initializer transfers `FinalizerCaptureState` with `Unmanaged.passRetained`. `finalizerTrampoline` recovers it with `takeUnretainedValue` and invokes `state.f()`. The retained state is never released by that trampoline. A nested release helper exists in the initializer but is not passed as the callback.

The captured owner therefore remains retained even though the finalizer's body ran. The callback capture itself also remains allocated. Merely setting a captured buffer holder to nil would conceal the larger payload leak without balancing ownership of the callback state.

The likely correction is to consume the retained callback state exactly once, with a regression that checks both callback execution and capture deallocation. That correction was not applied during this sequence. This report does not establish whether a newer upstream revision already fixes the problem.

## Reproducer and qualification

The prototype stores `swiftFinalizerProbe()` in `Benchmarks/UnifiedMemoryPrototype/Device.swift`. The command `SwiftSciMemoryDevicePrototype --mlx-finalizer-probe` returns the observed callback count, weak-reference state and live payload bytes. `device.py` saves the result in `swift-wrapper-defect.json` and requires the pinned failure to remain visible.

The direct adapter calls `mlx_array_new_data_managed_payload` with a retained `ReadLease<Float>` payload and a callback that releases that payload. It uses the public MLX context initializer. The adapter validates its limited shape and alignment contract and proves pointer identity. It remains experimental and tied to the pinned C interface.

This report is evidence for a possible dependency issue, not an already submitted issue or a fix. Production adoption of shared imports remains contingent on a qualified owner-release path and broader cancellation and concurrency tests.
