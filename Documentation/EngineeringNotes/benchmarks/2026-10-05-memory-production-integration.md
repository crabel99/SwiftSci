# Production memory integration

## Decision and scope

Commit `5c092885fd20a80f8b321570cb22de356235882d` integrates the qualified prepared-regression path on `codex/memory-kernel-trial`. The parent prototype remains at `aa5c71968c080f4188357c4cb628389f89ca00a2`. This is local implementation work; nothing was pushed or submitted.

Keep this engineering record only on `codex/engineering-notes`. Public usage is documented in `Sources/SwiftML/SwiftML.docc/PreparedRegression.md`. The evidence archive is `~/local-ai/spl/swiftsci/memory-production-integration-20261005/`.

The prepared path remains opt-in. Its measured benefit is lower peak memory for the larger fixtures, at a small workflow-time cost. The full library still has two GPU numerical failures inherited from the pinned MLX dependency. This integration does not establish a clean production-release gate.

## Implemented interfaces

- `PreparedSupervisedBatch` selects features and targets together, preserving duplicate rows, original row identities and snapshot isolation.
- Prepared requirements on `PreprocessingTransformer` and `RegressorEstimator` provide actual protocol dispatch. StandardScaler and LinearRegression consume compact columns. Existing conformers use compatibility defaults; those defaults can allocate rows. Feature-changing transformers must implement their prepared transform explicitly.
- Row-array and prepared LinearRegression share one solver. CPU QR, compensated refinement, gradient fallback and prediction arithmetic are preserved. Legacy intercept-only CPU fitting and NaN prediction remain supported. Prepared fitting requires finite data and records the named feature order.
- RegressionPipeline preserves fitted schema when prepared validation rejects a refit. Once a refit starts mutating transformers, an error makes prediction unavailable until a successful fit restores a consistent state. Fits, configuration changes and predictions must follow the documented serialization contract.
- `MemoryBudget` admits complete caller-provided `MemoryEstimate` reservations, queues in order, rejects requests larger than the limit and releases on completion or error. Budgeted prepared fit and prediction overloads use it. The prototype now tests this production actor through type aliases.
- Package-private `ScopedGPURead` retains a shared Metal buffer and MLX input until submitted GPU work completes. It shares page-compatible ranges and copies other valid ranges. Shape checks precede Int32 conversion. Newly bound Float storage is initialized explicitly. Qualified regression calls complete within the scope, including thrown cancellation.

Admission governs estimates for participating work. It does not intercept allocators or cap RSS, external caches, unrelated work or persistent outputs. Caller estimates must cover retained inputs, copies, normalized data, solver workspace and a runtime allowance. No general mutable foreign-array API was introduced.

The generated experimental regression source and its generator were removed. The integration benchmark now calls production prepared overloads. Owned-buffer storage and retained/materialized selection variants remain experiments; this commit does not replace every dataframe allocation with Metal storage.

## Validation

| Check | Result |
| --- | --- |
| Complete Release test suite | 1,042 passed, 2 failed, 2 skipped |
| Complete Debug test suite | 1,042 passed, 2 failed, 2 skipped |
| Pre-integration rotary suite | 4 passed, the same 2 failed |
| Compatibility regression workflows | 44 scenarios and 8 additional checks passed |
| Prepared regression workflows | 44 scenarios and 5 additional checks passed |
| Existing NIST contracts | 32 comparisons passed per path, 64 total |
| Interleaved timing runs | All 36 fresh processes passed their result checks |

The two failing test definitions are `LlamaRotaryScalingTests.transitionFrequencies(gpu:)` and `LlamaRotaryScalingTests.rotationOracle(dimensions:gpu:)`. Both fail on untouched pre-integration commit `66aa51b86418c5eedac1908267d3332869f1cf15` under identical Release build settings. Release and Debug integration runs have exactly the same failure signatures as that control. These are failed tests, not accepted numerical conformance.

At frequency 15, the GPU result is `774.8639` against `774.86475`, exceeding the one-ULP allowance. A long-position rotation reports error divided by its budget of `1.5823296156926971`. The cause was previously isolated to MLX 0.32.3 runtime Metal compiler options in [the dependency investigation](2026-10-04-mlx-regression-source.md). No dependency patch or tolerance relaxation was applied in this integration.

The two skipped tests belong to optional pinned-tokenizer parity coverage, enabled by `SWIFTSCI_LLAMA_TOKENIZER_JSON`. That fixture setting was absent. Xcode parameterized test-case executions are separate from the test-definition counts above. Hosted CI was not run.

New integration tests cover concrete and protocol-typed prepared dispatch, feature-order rejection, invalid and partially mutating refits, recovery, legacy conformers, legacy intercept-only fitting, NaN prediction, target alignment, snapshot mutation and budget release. GPU tests cover sharing/copying, errors after submission, unchanged input values and rejected dimensions. Existing registered prototype checks continue to cover asynchronous admission, ownership, cancellation and finalizer behavior.

Both paths pass the eight existing NIST OLS datasets through retained and materialized snapshots against decimal and binary64 contracts. Reference hashes and existing tolerances are unchanged. CPU synthetic fitted parameters and predictions agree exactly between the prepared and row-array paths. GPU comparisons retain their existing tolerance.

All final build manifests match the committed source hashes. Builds used tracked-source snapshots outside cloud sync, leaving unrelated duplicate files out of the build and commit. The initial full Release attempt caught an async dispatch defect; `full-release-final/` and `full-debug/` supersede it.

## Performance and memory

Three fresh-process rounds interleave lanes and storage treatments. The control is the row-array path in this same commit, not an older binary or Python. Workflow time includes selection, conversion or preparation, fitting and prediction. Construction is separate. Admission precedes timing; independent result checks follow timing and the process peak-RSS snapshot. Source input remains retained in both treatments.

Positive time changes mean prepared input was slower. Values are medians without confidence intervals. RSS includes runtime and allocator effects and does not measure exact live GPU ownership.

| Training rows and data | Treatment | Rows ms | Prepared ms | Time change | Rows RSS MB | Prepared RSS MB |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1,000, ordinary | retain | 10.32 | 10.23 | -0.9% | 15.5 | 15.5 |
| 1,000, ordinary | materialize | 10.69 | 10.62 | -0.7% | 15.5 | 15.5 |
| 100,000, ordinary | retain | 82.41 | 85.62 | +3.9% | 53.9 | 45.9 |
| 100,000, ordinary | materialize | 86.35 | 90.01 | +4.2% | 61.1 | 53.2 |
| 100,000, noisy | retain | 81.94 | 86.26 | +5.3% | 53.9 | 45.9 |
| 100,000, noisy | materialize | 86.83 | 90.36 | +4.1% | 61.1 | 53.2 |

At 100,000 rows, prepared input saves about 8 MB of peak RSS, roughly 13% to 15%, with about 4% to 5% longer workflow time. The 1,000-row results are close. This supports exposing the memory tradeoff to callers and retaining the existing default. It does not establish a universal speed improvement.

## Review

### Standards

Three initial ownership and state findings were resolved: rejected refits erased feature-order protection, GPU shape conversion lacked dimension bounds, and new Float storage used assignment before initialization. The final standards review found no remaining actionable findings. Runtime tests verify the corrections.

### Specification

The initial review found that the new shape validation rejected legacy intercept-only regression. That path is restored and tested. The full Release run then caught Swift selecting the async protocol default over a synchronous actor prepared-prediction method. Making that method explicitly async restored intended dispatch; concrete and protocol-typed tests now reject reordered names. The final specification review found no remaining actionable findings.

## Remaining release boundary

The memory integration is implemented and its scoped checks pass. A whole-library release still needs the existing MLX runtime precision defect resolved and the unchanged suite rerun. Broader storage replacement, arbitrary mutable MLX interoperation and a hard process-memory cap remain outside this change.
