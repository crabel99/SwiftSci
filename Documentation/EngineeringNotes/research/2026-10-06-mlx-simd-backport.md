# Pinned MLX Swift backport

Date: 2026-10-06.

The user approved a temporary fork that combines the managed-buffer ownership fix in official MLX Swift 0.32.3 with their merged CPU float16 SIMD fix, MLX #4602. Official core v0.32.3 predates the October 4 merge. Official Swift 0.32.3 and current Swift main still bundle an older core. A Swift version number alone does not establish inclusion of the core fix.

## Implementation

[SwiftSci PR #60](https://github.com/Nodibell/SwiftSci/pull/60) now pins Swift fork commit `4657976edcdd2c60642424985d474b45ddddb390`, based on official release commit `19601207e9a0de51e03ee6ec0c3c5f3784275075`. The fork changes only `.gitmodules` and the `Source/Cmlx/mlx` gitlink. Swift bindings and mlx-c are unchanged.

The core gitlink points to `ba70087d777b7a0206e620ddda780fb783d0e795`, based on the bundled core `1f8e74e3f12f31365464a6867c6579f0e9b29d85`. The backport and upstream merge `8c56dd880e27b0ed1f9b7be998d153b884f2a5d8` have identical stable patch IDs, `f35c2ef18aa660d3f2b77a04c35012aa046c966a`. Both change only the fallback SIMD header and its operation regression test.

SwiftSci head `93c19c198508ad00510d0f60715f1d127ac0e822` changes only Package.swift and Package.resolved relative to upstream main `0d0de4bea8e892dc1abc32be7878160d7f777109`. Fresh resolution fetched the exact fork and core commits. All other lockfile dependency entries are unchanged. Both forks and the dependency PR branch are published.

## Validation

The direct SIMD regression was preserved from the original submission and compiled separately. It is validation evidence, not an extra change in the minimal backport.

| Check | Result |
| --- | --- |
| Original header, macOS 14 deployment | 500 failed assertions out of 1,216 |
| Patched header, macOS 14 deployment | 1,216 passed assertions |
| Patched implementation, macOS 15 deployment | 1,216 passed assertions |
| Backported core full C++ CPU suite | 252 tests and 3,941 assertions passed; no failures or skips |
| Exact SwiftSci PR head, full Release suite | 1,144 passed test definitions, 3 failed, 2 skipped |

The Release failures are the same invalid-context crash and two GPU rotary-precision failures seen with official 0.32.3. The local memory branch contains a separate invalid-context correction, `aa5c71968c`; it is not included in this dependency PR. GPU numerical tolerances are unchanged. Two optional tokenizer-fixture tests are skipped. No full numerical conformance or external-dataset coverage is claimed.

The host was Apple M4 Max with 128 GiB RAM, macOS 27.0, Xcode 27.0 and Swift 6.4. Deployment-target checks select different compiled SIMD implementations; they do not establish execution on macOS 14 or 15. Swift validation used the established precise Metal build settings and one test runner. Historical finalizer ownership checks on official 0.32.3 remain historical evidence; no new ownership measurement is claimed for this fork.

## Branch boundaries and next steps

The unpushed Arrow branch was restacked to `1d2ebd228cd8911a9097f87d4be1a135f836da98` above the new dependency head. Its two Arrow commits and three-file scope are preserved. Earlier Arrow performance results retain their original fingerprints and are not relabeled as measurements of this new head. The working memory checkout remains at `32badeece6728e9b75054b2f997459c377dfb69e`.

PR #60 remains draft while compatibility failures and hosted checks are unresolved. Return to an exact official Swift release when its bundled core contains the SIMD fix and its Swift bindings retain the ownership fix, then repeat regression and compatibility checks. Engineering records remain only on codex/engineering-notes.

Local evidence: `/Users/crabel/local-ai/spl/swiftsci/mlx-simd-backport-20261006`. This includes source pins, patch comparison, compiler logs, direct regression outputs, full CPU output, and the Release result bundle.
