# Retained shared GPU input trial

Date: 2026-10-07

## Decision and scope

Keep this experiment on `codex/retained-memory-accounting-trial`. Commit `e859aa3128083846d58f568c2fcbe8daa2f58efd` extends CPU trial `dc7b276d137436205dc745a5184d3055212f836e` with package-only shared GPU input storage and seven tests. It does not migrate production callers, change public APIs, or modify PR #62.

The trial uses Metal shared buffers, MLX's existing managed-buffer finalizer, MLX streams, and Swift actor isolation. It adds reservation ownership and a borrowing contract. It does not add an allocator, a buffer cache, a garbage collector, or a GPU scheduler.

## Ownership and completion

The factory reserves a caller-supplied construction peak, allocates page-rounded Metal shared storage, and copies the caller's Float values once. MLX imports the full padded extent and creates a logical view for the requested shape. A native pointer comparison verifies that import and each contiguous offset view share storage.

The construction grant remains active through import, evaluation, stream completion, and pointer verification. This order matters because MLX can copy an external buffer when its Metal no-copy wrapper cannot be created. Only after successful verification does the factory transfer the grant to the smaller retained estimate. The native storage owner receives that reservation before any view becomes available to callers.

One private actor owns all MLX arrays for an allocation. Sendable handles contain a shared actor reference and a view identifier. Creating another view does not acquire another payload grant. Closing the root leaves other views usable. Explicit close and handle destruction remove their own view. The managed-buffer finalizer releases the storage owner and its reservation after the last native reference is gone.

Read callbacks use the allocation's supplied stream. Every read exit synchronizes that stream, including thrown errors and cancellation. Close also completes stream work before dropping its view. Native finalizers never synchronize. Reservation release is asynchronous and conservative while actor cleanup is queued.

The callback must not mutate or export the borrowed input, its pointer, or a no-copy Data or Metal wrapper. Scratch and output allocations need separate estimates. Swift's callback type does not enforce every borrowing restriction. The test suite follows this contract and reserves a separate workspace estimate for its matrix completion probe.

## Findings during implementation

- A version with a separate actor for each view failed Swift's transfer checking because the views share non-Sendable MLX storage. One allocation-scoped actor keeps those objects in one isolation domain.
- Review caught an early reservation transfer before import validation. Keeping the construction grant through validation covers the possible overlap between source storage and an MLX fallback copy. The tests use construction estimates large enough for two padded payloads and estimated metadata.
- The first pointer check used Foundation Data created by MLX's no-copy accessor. A one-element case failed that check. Using MLX's native Float pointer passes for that case and the page-boundary cases. The Data wrapper was an unsuitable allocation-identity probe for tiny values.
- Earlier completion tests performed a later readback or close, which could hide a missing barrier. The final test queries MLX's nonblocking availability flag immediately after scope exit, before any readback or further synchronization.

## Validation

The final focused Release run passed **217 tests, with zero failures and zero skips**, across SwiftPreprocessingTests and SwiftMLTests. It includes the retained CPU model trial and all seven new GPU tests. A prior preprocessing-only run passed 111 tests.

The GPU cases cover:

1. One-element and page-boundary inputs, offset and reshaped views, one shared grant, and reads after other handles close.
2. Submission followed by an error or cancellation, cancellation-safe close, and eventual reservation return.
3. Independent GPU completion observation after normal return, error, and cancellation. Each probe submits a chain of sixteen 512-by-512 matrix multiplications, then reads the native availability flag without waiting.
4. Root destruction while a child view remains usable, followed by final-view destruction.
5. Eight concurrent callers using views of one allocation. The allocation actor serializes their scopes.
6. Invalid shapes and capacities, and cancellation while construction waits for admission.
7. Thirty-two construction, submission, and release cycles. Every cycle returns its reservation, with peak admission bounded by the submitted estimate.

The completion probe stores only the newly computed output under a lock. It uses the pinned C API `_mlx_array_is_available`. The workload improves sensitivity to a missing barrier, but no deterministic missing-barrier mutation test was run.

Independent behavior review found the two earlier defects resolved and no further actionable ownership or accounting finding. Standards review found no actionable violation or code smell. Reviewers did not run builds or modify files.

## Environment and evidence

- Apple M4 Max, 128 GiB unified memory.
- macOS 27.0, build 26A428; arm64 Release with macOS 14 deployment target. This is not a macOS 14 runtime qualification.
- Pinned MLX Swift fork revision `4657976edcdd2c60642424985d474b45ddddb390` retains both the managed-owner correction and the SIMD backport.
- Metal safe math, precise FP32 functions, coverage disabled, test parallelism disabled, two build jobs. One native test worker at a time.
- Local evidence directory: `~/local-ai/spl/swiftsci/retained-gpu-trial-20261007/`.
- `final-release-command.json`, `final-release.log`, `final-release.xcresult`, and `final-release-summary.json` preserve the final run.
- `source-fingerprint.json` records SHA-256 values of both tested files. `commit.json` records the trial commit and the unchanged primary checkout.

## Limits and next step

This verifies ownership and completion for the tested Float32 contiguous inputs and views. It is not a full SwiftSci run, sanitizer qualification, allocator leak scan, memory-pressure stress run, or performance benchmark. The MLX fallback-copy failure path was reviewed but not forced in a test.

The reservation budget accounts for participating estimates. It does not measure process RSS, constrain MLX's cache, or cover unrelated allocations. A zero reservation count is not proof that the process returned all resident pages to the operating system. Views require caller allowance for metadata. The caller's original Swift array is accounted separately from the shared allocation.

Before production integration, compare repeated use of retained shared inputs with the existing scoped input path under equivalent workloads. Measure construction cost, repeated-operation timing, and retained memory separately. The actor and synchronous barriers may affect throughput. Preserve this tested local head while evaluating that tradeoff; do not claim a speed or RSS improvement from these ownership tests.
