MLX Swift 0.31.6 leaks the captured owner passed to `MLXArray(rawPointer:_:dtype:finalizer:)`. Official 0.32.3 includes the [Swift finalizer fix](https://github.com/ml-explore/mlx-swift/pull/448), but its bundled MLX core predates the merged [CPU float16 SIMD comparison fix](https://github.com/ml-explore/mlx/pull/4602). SwiftSci needs both for the shared-buffer work.

Pin a temporary fork based on official MLX Swift 0.32.3. The Swift fork changes only the MLX submodule URL and revision. The core backport applies exactly the two-file diff merged in #4602, including its operation regression test. Swift bindings, mlx-c, and the rest of the bundled core stay at the release versions.

- Swift fork: [`4657976edcdd2c60642424985d474b45ddddb390`](https://github.com/crabel99/mlx-swift/commit/4657976edcdd2c60642424985d474b45ddddb390), based on official `19601207e9a0de51e03ee6ec0c3c5f3784275075`.
- Core backport: [`ba70087d777b7a0206e620ddda780fb783d0e795`](https://github.com/crabel99/mlx/commit/ba70087d777b7a0206e620ddda780fb783d0e795), based on bundled `1f8e74e3f12f31365464a6867c6579f0e9b29d85`.

Only `Package.swift` and `Package.resolved` change in SwiftSci. The manifest uses an immutable revision, and the generated lockfile selects the same revision. Other resolved dependencies, deployment target, production algorithms, and numerical tolerances are unchanged. The Arrow import changes remain separate.

## Validation and draft status

- Clean package resolution fetched the pinned Swift fork and the exact core backport. Verified that all other resolved dependency entries remain unchanged.
- Direct SIMD regression with a macOS 14 deployment target failed 500 of 1,216 assertions against the original bundled header. The backport passed all 1,216.
- The same regression compiled with a macOS 15 deployment target passed all 1,216 assertions. These binaries ran on macOS 27, testing both compile-time implementation selections rather than claiming execution on macOS 14 or 15.
- Full backported MLX C++ CPU suite: 252 tests and 3,941 assertions passed, with no failures or skips.
- Earlier prototype qualification on official 0.32.3 confirmed one finalizer invocation, release of the captured owner, zero remaining tracked owner bytes, and balanced allocation/release counts. This is historical ownership evidence; the Swift fork leaves that implementation unchanged.
- Full local Release validation on SwiftSci head `93c19c198508ad00510d0f60715f1d127ac0e822`: 1,144 passed, 3 failed, 2 skipped. The failures match prior official-0.32.3 integration runs: `GenerationResultTests/invalidRequests(api:)` aborts with `[bits] Negative dimensions not allowed`; `LlamaRotaryScalingTests/rotationOracle(dimensions:gpu:)` and `transitionFrequencies(gpu:)` exceed their GPU precision budgets. The two skips need the optional pinned tokenizer fixture. These are test-definition counts, including parameterized tests. Hosted CI remains pending. Keep this PR in draft pending compatibility work; no test is suppressed and no tolerance is relaxed.

## Return to the upstream dependency

Replace the fork with an exact official MLX Swift release once it includes both the managed-buffer finalizer fix and the CPU SIMD fix in its bundled core. Verify the bundled core source, rerun the regression and compatibility checks, and regenerate the lockfile before switching back. Upgrading the Swift release number alone is not sufficient evidence that a core fix is included.
