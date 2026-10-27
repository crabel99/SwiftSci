# Independent upstream GPU BCE correction

This delivery isolates the existing GPU-gradient correction directly on upstream main `e19db7dda4567c425b7eb002da82e234e6c7980f`. Frozen candidate `506204920a5a073b1e7bc316476875860bacfda0` contains only `Sources/SwiftML/Losses/Losses.swift` and `Tests/SwiftMLTests/BinaryCrossEntropyTests.swift`. Both files are byte-identical to the previously reviewed correction `53063789b1893b28250ea239d5fdca4fed84c4c9`. The original broader qualification remains [separate historical evidence](https://github.com/crabel99/SwiftSci/blob/codex/engineering-notes/Documentation/EngineeringNotes/benchmarks/2026-10-26-logistic-gpu-gradient/README.md).

## Behavior and reproduced failure

For mean binary cross entropy, the logit derivative is `(sigmoid(logit) - target) / count`. The old maximum/absolute-value composition gave the wrong derivative at zero in pinned MLX. GPU logistic regression initializes its parameters to zero, so the error affected its first training update. For one zero feature, target 0 and learning rate 0.25, the old bias remained 0 instead of -0.125.

The correction replaces the nonsmooth composition with `mean(logAddExp(0, logits) - logits * targets)`. The shared helper's only production caller is logistic GPU fitting. Public signatures, CPU fitting, Float GPU precision, device routing, dependencies and numerical-policy allowances are unchanged. Existing incorrect GPU trajectories intentionally change. No performance, convergence or general predictive-quality improvement is claimed.

Three existing analytical regression definitions were copied unchanged onto the actual upstream base. The baseline compiled and all three definitions failed, without skips. The same tests pass after correction. They independently check zero-logit derivatives, mean gradients with finite extreme logits and the first public legacy GPU training update for targets 0, 0.25 and 1. This PR does not require the unmerged prepared classifier or PCA APIs.

## Verification record

`qualification.json` reports passed after `verify-qualification.py` checked the completed artifacts and frozen source. Native Debug and Release each pass 1,659 definitions, with no failures or skips. The focused suite passes 3 definitions. Installed Swift 6.3.3 passes Debug/Release builds, compiles all test targets and passes the safe suite. Xcode 27 remains selected. The full local main workflow passes 8 steps after the controller correction below; Python CodeQL reports zero findings. All 19 benchmark workflow steps pass, including the three MLX CPU profiles and unchanged CPU regression policy. Swift CodeQL completes with one unchanged pre-existing weak-password-hashing finding in `Sources/SwiftDatabase/DatabaseConnection.swift:606`. The actual changed loss was successfully extracted and its archived bytes match the candidate.

Hosted safe tests skip SwiftMLTests, and the existing Codecov configuration excludes SwiftML source. Therefore hosted coverage is not evidence that the GPU loss ran. The fresh native tests execute the actual loss and public GPU path with Metal access. This delivery leaves that existing hosted coverage policy unchanged and does not claim a coverage percentage.

The standard benchmark policy retains its four known strict Python Wampler comparator failures and existing tolerances. Matching-compiler Swift CodeQL analysis uses installed Swift 6.3.3 and disables the manifest sandbox, without changing source or the selected Xcode. The pre-existing PostgreSQL MD5 security finding remains visible; this is not a claim that the whole library is secure. Native execution is on the current Apple silicon host, not every supported macOS runtime.

## Preserved tooling failures

The first workflow controller launch used an absent Homebrew Python 3.13 path and exited 127 before executing the workflow. The retry uses the already installed pinned standalone Python 3.13.17; `controller-launch-failure.json` preserves the initial result.

The first actual main workflow passed its seven upstream steps, then its additional local LCOV assertion exited 127 because `rg` was absent from the constrained tool path. The controller now checks the same nonempty-file and SwiftDataFrame-source-record predicate with Python's standard library. The full eight-step rerun passes in `ci-main-fixed`. The failed original receipt/log and exact original controller remain in `ci-main` and `full-ci-runner-before-coverage-fix.py`. The benchmark controller's dormant copy of this check received the same structural correction before its run. Neither change touches production source or weakens the predicate.

Copied benchmark-cache paths were redirected to an isolated APFS copy before execution, preserving all earlier study objects. `controller-derivation.json` records those substitutions. Copied native build state produced stale-file warnings for old paths, without changing the frozen source; build logs retain those messages. Existing dependency/documentation warnings are not presented as warning-free builds.

## Inspect and replay

`production.patch`, `spec.md`, the two independent code reviews and `red-source-binding.json` bind the delivery scope and before/after evidence. Task-local controllers retain actual commands, versions, source hashes, exit codes and logs. `verify-qualification.py` checks the raw original artifacts and exact new source head. Native result bundles, dependency caches and the full CodeQL database remain local.

Published records compress logs/comparison payloads, replace the machine hostname and native device identifier, and retain authorized filesystem paths. Original-to-published maps preserve the difference from raw captures. Run `python3 verify-publication.py --records PATH` to check a downloaded package without the original build tree. The package is an integrity record, not a fresh numerical rerun. Service uploads, deployment and GitHub-hosted operating systems are outside the local workflow replay.

`delivery-queue.md` separates the remaining fork work into focused future units. No upstream merge or maintainer comment is part of this delivery.
