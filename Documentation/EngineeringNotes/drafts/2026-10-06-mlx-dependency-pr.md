MLX Swift 0.31.6 leaks the captured owner passed to `MLXArray(rawPointer:_:dtype:finalizer:)`. The finalizer can run while its retained capture keeps the backing buffer alive. This blocks our shared-buffer integration.

Update the exact dependency to **0.32.3** and pin revision `19601207e9a0de51e03ee6ec0c3c5f3784275075` in `Package.resolved`. This release includes the fix in [ml-explore/mlx-swift#448](https://github.com/ml-explore/mlx-swift/pull/448). The fix first shipped in 0.32.2; 0.32.3 is the version qualified in our memory work.

Only `Package.swift` and `Package.resolved` change. Other dependency versions, the macOS deployment target, production algorithms, and numerical tolerances remain unchanged. The Arrow import optimization will be a separate PR.

## Validation and draft status

**Release boundary:** 0.32.3 does not include our CPU float16 SIMD comparison fix in [ml-explore/mlx#4602](https://github.com/ml-explore/mlx/pull/4602). It bundles MLX commit `1f8e74e3f12f31365464a6867c6579f0e9b29d85`, which predates that merge. Current `mlx-swift` main bundles the same core revision. This PR therefore upgrades the Swift ownership fix only; it cannot yet serve as the dependency containing both fixes. Keep it in draft while the upstream release or temporary backport route is decided.

- Verified that the manifest and lockfile select the same 0.32.3 release and that only the MLX dependency changes.
- Earlier prototype qualification on 0.32.3 confirmed one finalizer invocation, release of the captured owner, zero remaining tracked owner bytes, and balanced allocation/release counts. This is ownership evidence from the prototype, not a full-suite result for this PR head.
- Earlier upgrade comparison found a negative-context construction crash and two GPU rotary-scaling precision failures. The current memory branch has a local correction for the construction path; its latest full Release run still reproduces both rotary failures, including on the parent before the Arrow changes.
- Exact-head validation and hosted CI are pending. Keep this PR in draft while compatibility work is resolved. This dependency-only PR does not change tests, suppress failures, or relax tolerances.

Release: [MLX Swift 0.32.3](https://github.com/ml-explore/mlx-swift/releases/tag/0.32.3).
