# GPU logistic gradient correction, October 26, 2026

Commit `53063789b1893b28250ea239d5fdca4fed84c4c9` on `codex/fix-logistic-gpu-gradient` corrects GPU logistic training at zero logits. Its parent is the prepared classification contribution, `8926829bf2952a8f981a8be199be9ee9c3f7c458`. Production code and these engineering records remain separate.

## Demonstrated error and correction

The original shared BCE helper composed `maximum(logits, 0)` and `abs(logits)`. In pinned MLX, both primitives have derivative zero at zero, so the composed loss's zero-logit derivative was `-target` rather than `0.5 - target`. All zero-initialized logistic models encountered that incorrect derivative on their first update.

The minimal public-API reproduction uses one zero feature, target zero, learning rate 0.25 and one GPU epoch. Original bias remained 0; the analytical result is -0.125. Direct evaluation of the actual loss helper confirmed the derivative error at zero while nonzero logits agreed. `loss-probe.log` also records the smooth reference and primitive derivatives.

The production change replaces that composition with `mean(logAddExp(0, logits) - logits * targets)`. This is the stable smooth formula already used by the pinned MLXNN implementation. It removes intermediate operations rather than adding a custom derivative or optimizer exception. The shared helper's only production caller is logistic GPU fitting.

For the original 1,000-row fixture at learning rate Float(0.05), original GPU bias after one update was 0.022600000724196434 instead of -0.002400000035762787, an error of 0.025000000759959222. The corrected GPU result is -0.002400000113993883, within 7.823109608035006e-11 of the analytical result. The independent CPU result is unchanged.

## Qualification

`qualified-commit.json` is the authoritative completion receipt. Packaging requires that file and all requested checks to have passed.

| Check | Outcome |
| --- | --- |
| Failing before | All 3 new regression tests failed, with 9 failing parameter cases |
| Targeted after | All 11 loss and prepared-logistic tests passed |
| Full native Debug | 1,683 passed, zero failures or skips |
| Full native Release | 1,683 passed, zero failures or skips |
| Older compiler | Swift 6.3.3 Debug and Release builds passed; every test target compiled; 77 XCTest and 740 Swift Testing safe tests passed |
| Main workflow | Actual build, safe-test, coverage-export, all-module documentation and existing verifier commands passed, plus a real coverage-content check |
| Public GPU workflow | Debug and Release, 12 fresh processes total, WDBC 569 rows and 30 features, fixed splits 328/115/126, 0/1/32 epochs |
| Independent public comparison | 14,028 numerical fields checked; maximum NumPy/SciPy difference 7.961420289692711e-8; row/prepared arrays, labels and provenance match exactly |
| CPU regression policy | Passed all 404 engine-case executions under the existing policy; four known Python Wampler strict-conformance failures remain failed, zero blocking regressions |
| Benchmark workflow | Passed optional Polars/DuckDB profiles, worker certification, checkpoint preflight, inventory, public-worker challenges and all three MLX CPU profiles and audits |
| Python CodeQL | Passed with zero findings |
| Reviews | Standards and Spec reviews found zero remaining findings |

Native tests used the pinned tokenizer fixture and strict ONNX prerequisites. Native coverage was enabled. Safe SwiftPM testing deliberately excludes the same GPU/MLX suites as hosted CI, while the native runs execute every target. No numerical tolerance, frozen fixture, known-failure allowance, dependency pin, routing rule or CI policy changed. New GPU comparison tolerances are 1e-6; existing CPU tolerances remain 1e-14.

Some receipts were captured before the source commit was created. `finalize.py` checks their recorded input hashes against the final clean committed files and verifies the linked probe object hashes. The standardized worker is separately certified at the final commit. Debug public-probe link flags came from the initial complete build log; the linked objects are the later corrected objects, recorded by hash and bound to the successful native Debug build. Release flags and objects came from the final Release build.

## Compatibility and limits

Public calling interfaces, CPU arithmetic, Float GPU precision, device routing, zero-epoch behavior and stored-parameter prediction are unchanged. GPU fitting intentionally changes its previously incorrect trajectory, including `.auto` and `.ane` requests that resolve to GPU. The guide states that change. The independent CPU reference now checks all routes; obsolete assertions pinning the erroneous GPU trajectory were removed.

Both configurations use the same fixed public fixtures and an independent Double NumPy/SciPy implementation. GPU comparisons use Float-appropriate tolerances. These measurements do not establish performance, convergence or general model-quality improvements, nor bitwise CPU/GPU equality. Runtime qualification is one Apple M4 Max host on macOS 27; compiling with a macOS 14 deployment target is not a macOS 14 runtime test.

Xcode 27 remains selected. Swift 6.3.3 and SDK 26.5 were used per-process without changing global defaults. Swift CodeQL tracing is unsupported with this Xcode and compiler, so no complete security-workflow or all-GitHub-Actions claim is made. This was rechecked against [GitHub's October 19 compatibility notice](https://github.blog/changelog/2026-10-19-codeql-changes-for-macos-27-xcode-27-and-swift-6-4/). No older Xcode was installed. No upstream PR was created by this task.

All-module documentation conversion passed with preexisting warnings. The existing verifier reports 98.67% documented public declarations and zero placeholders, despite its final message saying 100%; this record does not claim 100% documentation coverage or warning-free docs.

## Reproduce and inspect

- `production.patch` is the exact source commit; `spec-review.md` and `standards-review.md` record review scope.
- `reproduce-initial.py`, `original-rerun.json` and `original-proof.json` preserve the original failing signal. The original probe and its compiled-library proof are in the preceding prepared-classification record. `link-original-probe.py`, `MinimalProbe.swift` and `LossProbe.swift` describe the local diagnostic links.
- `reproduce.py --probe PATH --metal PATH` checks the same analytical first step against a newly linked `verification/RegressionProbe.swift` executable.
- `validate-native.py Debug TAG` and `validate-native.py Release TAG` build and test all targets. Extra arguments select suites for a focused run. Existing output directories are retained rather than overwritten.
- `check-swift633.py` records compiler identity and each compatibility command.
- `full-ci-runner.py` executes workflow shell steps with explicit versions and redirected evidence. `benchmark-ci-final-runner.py` uses an isolated package/build cache. These remain task-local qualification tools, not new production APIs. They check source hashes and preserve commands, exit status and logs. Service uploads/deployment and GitHub runner operating systems are not reproduced locally.
- `verification/link-public-probe.py` links the public probe against actual qualified objects. `verify-public-workflow.py Debug` or `Release` executes the GPU workflows and independent reference. Probe proofs retain binary/object hashes, not binaries.
- `package-records.py` copies selected evidence, compresses logs/coverage without altering their contents, and writes a SHA-256 manifest. Model weights, dependency caches, binaries, CodeQL databases and large xcresult bundles are excluded. Scripts preserve the original local paths; adjust them for another checkout.

Earlier attempts are retained: the first new-test build was stopped to correct a test initializer; copied compiler module caches initially retained an old absolute path and were discarded in the isolated copy; an additional local coverage check initially lacked `rg` on PATH; and the first benchmark build rejected a mid-build commit change. These are not hidden source failures. The successful benchmark run is the final rerun against the stable commit.
