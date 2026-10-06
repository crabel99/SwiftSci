# Arrow validation with required MLX ownership fix

Date: 2026-10-06. Arrow branch: `codex/arrow-import-compatibility` at `d8c13bb662b967999da4c05b5c7f5bb418295126`. Dependency prerequisite: `c4063e83116550ef97b289e4e2423df47072cbe0` in [draft PR #60](https://github.com/Nodibell/SwiftSci/pull/60), based on upstream main `0d0de4bea8e892dc1abc32be7878160d7f777109`.

## Required dependency and PR order

Keep MLX Swift 0.32.3, revision `19601207e9a0de51e03ee6ec0c3c5f3784275075`. MLX Swift 0.31.6 leaks the managed-buffer finalizer capture and therefore retains the backing owner. The [upstream fix](https://github.com/ml-explore/mlx-swift/pull/448) first shipped in 0.32.2; 0.32.3 is the pinned release already qualified by the memory experiment. Matching upstream's older pin is not an acceptable reason to drop the required ownership correction. The user reaffirmed this constraint during validation.

This release does not contain the user's separate CPU float16 SIMD fix in [MLX #4602](https://github.com/ml-explore/mlx/pull/4602), merged October 4. MLX Swift 0.32.3 bundles core revision `1f8e74e3f12f31365464a6867c6579f0e9b29d85`, 126 commits behind that merge. Current Swift main bundles the same core. The finalizer fix and SIMD fix must not be conflated. The user has been asked whether to backport the SIMD patch in a pinned fork or wait for upstream. No temporary fork has been created or selected.

PR #60 contains only Package.swift and Package.resolved. It is a draft because compatibility failures remain unresolved. Its exact head has not had a separate full local test run. Do not present downstream Arrow or memory-branch results as exact-head validation for that PR.

The unpushed Arrow branch now contains two commits above PR #60. Relative to that prerequisite it changes only ArrowTableBridge.swift and two regression-test files. The original memory checkout remains unchanged at `32badeece6728e9b75054b2f997459c377dfb69e`. Engineering notes are not part of either implementation branch.

An initial validation build against upstream's older MLX pin was stopped after the user clarified the dependency constraint. That cancelled run supplies no successful test or benchmark evidence.

## Release validation

The preserved memory branch reported 1,055 passed test definitions, two failures, and two explicit skips. Parameterized execution counts were 1,288 passed, three failed, and two skipped. Both GPU rotary-scaling failures reproduced with identical discrepancies on parent `299221aab3865c57f8220bc8f2f03854708c6c65`, before either Arrow change. They predate the Arrow patch. No test was weakened.

The isolated upstream-plus-MLX-plus-Arrow branch reported 1152 passed, 3 failed, and 2 skipped. The recorded validation head is `cd6b8218b1adcebd0a43d0382270623e902a125e`. Reordering the dependency commit beneath the two Arrow commits produced `d8c13bb662b967999da4c05b5c7f5bb418295126` with the identical Git tree `3430f96c1a061df757961a2e78492d36f1e36c08`. File hashes confirm the same tested source. See archived JSON for parameterized execution counts.

- `GenerationResultTests/invalidRequests(api:)`: Crash: xctest at <deduplicated_symbol>
- `LlamaRotaryScalingTests/rotationOracle(dimensions:gpu:)`: Expectation failed: worstRatio <= 1 worstRatio → 1.5823296156926971 1 → 1.0: dim=64, GPU=true, factor=8.0, traditional=false, length=1, offset=131069, error/budget=1.5823296156926971
- `LlamaRotaryScalingTests/transitionFrequencies(gpu:)`: Expectation failed: abs(actual[index] - expected) <= expected.ulp abs(actual[index] - expected) → 0.0008544922 expected.ulp → 6.1035156e-05: GPU=true, frequency=15, actual=774.8639, expected=774.86475

The earlier memory branch includes local compatibility work absent from upstream, including the invalid-context correction `aa5c71968c`. Its test result must not replace validation of the isolated branch. The dependency upgrade remains required while these compatibility problems are addressed.

Two explicit skips in the preserved memory run require the optional pinned Llama tokenizer fixture. Its log also reports an MNIST file test returning early because the fixture was absent. Passing test counts do not establish external-dataset coverage. No broad numerical certification is claimed.

Validation used Apple M4 Max, 128 GiB RAM, macOS 27.0, Xcode 27.0, Swift 6.4, and the package's macOS 14 deployment target. It used one test runner and the existing precise Metal settings. Actual execution on macOS 14 was not tested.

## Matched Arrow benchmark

Both Release workers use current upstream production code with the required MLX 0.32.3 pin. The only production difference between workers is ArrowTableBridge.swift. The same temporary workload from `c57fb6db02ea45b4f28852d812dcd076bf9a8b95` is added only to exported build snapshots, never to the PR branches.

Each fresh worker imports four numeric Arrow columns, selects rows, gathers values, and constructs a checked row-major Double matrix. Timing excludes fixture construction, memory sampling, and correctness checks. Seven workloads ran in three rounds with alternating before/after order. All 42 complete outputs matched the deterministic oracle.

| Workload | Before, ms | After, ms | Speedup |
| --- | ---: | ---: | ---: |
| 1k rows, one chunk | 0.198 | 0.060 | 3.33× |
| 100k rows, no missing values | 17.924 | 4.607 | 3.89× |
| 1M rows, one chunk | 178.749 | 47.254 | 3.78× |
| 1M rows, 32 chunks | 813.501 | 47.737 | 17.04× |
| 1M rows, 32 chunks, sparse selection | 796.604 | 42.053 | 18.94× |
| 100k rows, five extractions | 33.093 | 5.062 | 6.54× |
| 1M rows, ten extractions | 221.200 | 84.545 | 2.62× |

One-million-row, one-chunk import allocation was 64,029,856 bytes before and 64,029,856 bytes after. This remains an owned-copy API. Import speed does not imply the retained-view experiment's memory savings. Both workers used `ENABLE_TESTABILITY=NO`. An earlier timing pass inherited testability from the test runner; its results were preserved locally and replaced by this normal Release comparison. The benchmark covers in-memory Double/Int64 import through matrix construction, not CSV parsing, arbitrary dataframe workloads, model training, or inference. Other Arrow types have regression coverage but no new performance survey.

## Standards

The independent standards review found no documented-standard violations or substantive code smells in the Arrow changes. The copying helper removes duplication; the signed-date workaround stays in the existing Arrow bridge. Public API and concurrency contracts remain unchanged.

## Spec

The independent specification review found no missing requirements, scope creep, or substantive correctness defects. It checked chunk traversal, null behavior, signed dates, owned values, and source-buffer release. Reviewed Arrow files are byte-identical on the original and isolated branches. The separate dependency update follows the existing ownership qualification and the user's explicit version constraint.

## Next boundary

Resolve the missing SIMD-release boundary and MLX compatibility failures without rolling back the ownership fix. The dependency-source choice remains pending user input. The local invalid-context correction is an existing candidate; GPU rotary accuracy remains separate work. Keep PR #60 in draft until that compatibility work is addressed. The Arrow draft and benchmark evidence are prepared locally; its branch has not been pushed and no Arrow PR was opened.

Date64 round-trip support and retained-view API design remain separate. Raw logs and binaries stay local; compact evidence and this report are archived only on codex/engineering-notes. The preserved integration benchmark binary was restored after test builds relinked it.
