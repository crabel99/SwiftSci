Update the MLX dependency needed for shared-buffer ownership and fix the two SwiftLLM compatibility problems exposed by the upgrade. The full local Release suite passes on `409e6ee545b88c22b83520845660c27ec584125d`.

## Dependency

Official MLX Swift 0.32.3 includes the [managed-buffer finalizer fix](https://github.com/ml-explore/mlx-swift/pull/448), but its bundled core predates the merged [CPU float16 SIMD comparison fix](https://github.com/ml-explore/mlx/pull/4602). Pin a temporary fork containing both:

- Swift fork [`4657976edcdd2c60642424985d474b45ddddb390`](https://github.com/crabel99/mlx-swift/commit/4657976edcdd2c60642424985d474b45ddddb390), based on official 0.32.3 at `19601207e9a0de51e03ee6ec0c3c5f3784275075`.
- Core backport [`ba70087d777b7a0206e620ddda780fb783d0e795`](https://github.com/crabel99/mlx/commit/ba70087d777b7a0206e620ddda780fb783d0e795), based on bundled `1f8e74e3f12f31365464a6867c6579f0e9b29d85`.

The Swift fork changes only the core URL and gitlink. The core backport has the same stable patch ID as merged #4602 and includes its operation regression test. Swift bindings and mlx-c are unchanged. Package.swift and the generated lockfile use the same immutable Swift revision; other resolved dependencies remain unchanged.

## Compatibility corrections

Each correction has its own commit and regression coverage:

- Preserve typed generation errors for nonpositive context limits. Stricter MLX shape checks previously aborted during model construction. Allocate an empty positional embedding for invalid limits while retaining the original configuration, so all three generation APIs return `GenerationError.invalidContextLimit` without emitting output. Coverage includes `Int.min`.
- Derive the cached Llama scaling frequencies on the CPU. GPU power rounding shifted transition-band denominators and exceeded the existing long-position phase budget. The small frequency table is calculated once at initialization; rotation and inference continue on the caller's device. Added bitwise CPU/GPU initialization parity across two head dimensions, two bases and four scaling configurations. Existing checkpoint and Double-oracle tolerances are unchanged.

The SwiftSci diff contains six files: the manifest, lockfile, two production files and their two test files. Arrow and memory-kernel implementation changes remain separate.

## Validation

- Focused suite before corrections: 17 passed, 3 failed. After corrections and the new regression: 21 passed, no failures or skips.
- Full local Release suite on `409e6ee545b88c22b83520845660c27ec584125d`: **1,148 passed, zero failed, 2 skipped**. The skips require the optional pinned tokenizer fixture. Counts are test definitions, including parameterized tests; they do not establish external-dataset coverage.
- Backported MLX C++ CPU suite: 252 tests and 3,941 assertions passed, with no failures or skips.
- Direct SIMD regression: the original macOS 14 fallback failed 500 of 1,216 assertions; the patch passed all 1,216. The macOS 15 implementation also passed all 1,216. Both binaries ran on macOS 27; these checks exercise deployment-target selection rather than actual macOS 14/15 execution.
- Fresh dependency resolution verified both fork commits and unchanged non-MLX dependencies. A separate memory-branch probe rebuilt with this fork verified one finalizer call, one allocation and release, no retained lease, and zero live owner bytes after a completed GPU read. This probe validates the dependency ownership contract; the memory implementation is not part of this PR.

Local validation used Apple M4 Max, macOS 27, Xcode 27, Swift 6.4, a macOS 14 deployment target, precise Metal settings, and one test runner. Hosted Debug and Release builds have passed. Remaining hosted checks are pending; keep the PR in draft until they finish successfully. Hosted safe-mode tests exclude GPU-dependent suites, so the full local run supplies the MLX execution evidence.

## Return to upstream

Replace the fork with an exact official MLX Swift release once its Swift bindings include the finalizer fix and its bundled core includes #4602. Verify the bundled source, rerun regression and compatibility checks, and regenerate the lockfile before switching back.
