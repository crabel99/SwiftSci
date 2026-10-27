# Prepared classification upstream delivery

Frozen source `3fd462155a10fa78a1cf6b98b56ea926d43ef112` adds the existing prepared classification workflow above the exact GPU BCE prerequisite `506204920a5a073b1e7bc316476875860bacfda0`, on upstream `e19db7dda4567c425b7eb002da82e234e6c7980f`. The full upstream diff contains two commits and 13 files. The classification commit changes 11 files. All 11 match their prior reviewed versions byte for byte, including the corrected independent GPU expectations from the scientific integration work. `source-reconciliation.json`, `classification.patch` and `production.patch` retain those boundaries.

Merge GPU PR90 before this feature. Prepared PCA PR89 remains a separate contribution. The qualification-only merge with its current exact head is an integration check, not an upstream merge or an addition to this delivery branch. Core ML export PR91, documentation-reporting PR92 and agent changes are outside this source. Package pins, workflow files, Codecov settings, benchmark contracts and numerical policies are unchanged from upstream.

## Public behavior

ClassifierEstimator and ClassificationPipeline accept prepared numeric columns for fitting, labels and class probabilities. Existing classifiers retain row-based compatibility defaults. LogisticRegression reads compact columns directly through the same private CPU row/column kernels. CPU prediction and gradient buffers are reused across epochs without changing accumulation or update order. GPU fitting retains Float MLX computation and the prerequisite's corrected analytical gradient.

Prepared fits retain ordered feature names, reject missing or nonfinite values and verify target alignment and row identity. Named inference enforces the fitted order. Positional row and supplied-parameter models retain their existing interpretation. Zero epochs, finite soft targets, strict probability thresholds and legacy CPU intercept-only rows remain supported. Failed direct logistic fits preserve the previous complete fitted state.

ClassificationPipeline uses short locked state transitions. No lock spans an await. Active fits exclude competing fits and predictions; configuration generations prevent stale fit commits. Failed post-mutation pipeline refits require recovery before prediction. Tests cover native and compatibility dispatch, consuming transformations, snapshots, schema and row provenance, probability shapes and explicit concurrent lifecycle transitions. The public DocC guide demonstrates training-only preprocessing and held-out inference. No warm starts, partial fitting, new classifier or generic matrix framework is introduced.

## Qualification boundaries

The retained receipts and `verify-qualification.py` bind every check to the frozen source. Full native Xcode 27 Debug and Release each pass 1,683 definitions with zero failures or skips, including actual CPU/GPU numerical paths. The complete local main workflow passes eight steps and benchmark workflow passes 19, including optional Polars/DuckDB, actual-worker challenges and three Python MLX CPU profiles. The existing checker still prints its misleading unconditional coverage message because its independent correction is PR92; that line is not treated as real DocC or code coverage evidence here.

The benchmark regression policy passes across 404 engine cases. Strict conformance retains four Python Wampler comparator failures, with no changed tolerance or failure inventory. Passing policy is distinct from full conformance. Python CodeQL reports zero findings; matching-compiler Swift CodeQL completes with one unchanged unsuppressed legacy PostgreSQL MD5 finding. Every extracted repository Swift file is compared with archived and current bytes. Static-analysis completion is not a clean security result.

Installed Swift 6.3.3 with SDK 26.5 builds production Debug and Release, compiles all test targets, runs the CI-safe suite and executes all 27 focused prepared/logistic/BCE/lifecycle tests across five suites. Focused execution explicitly uses `--no-parallel`; individual pipeline concurrency tests still run their own concurrent tasks. The test binary uses the compiled Metal resource from the same clean pinned MLX revision under retained Xcode 27. This establishes host-code compatibility on this Mac, not an older-Xcode Metal build or older-OS runtime coverage.

The qualification-only PCA integration runs all eight selected suites and passes 33 definitions without failures or skips. Actual test-tree identifiers establish that every requested suite ran, including both prepared PCA routes, overflow/workspace regressions and prepared classification/lifecycle tests. Both shared prepared-batch helpers survive the clean merge. This is a focused integration run, not another full-package qualification of the merged tree.

## Complete public CPU workflow

Nine fresh processes exercise the public WDBC workflow at 0, 1 and 32 epochs. Each checks the prior row API, candidate row API and candidate prepared API. The frozen input has 569 rows and 30 features, with fixed training/validation/test splits of 328/115/126. StandardScaler fits only training rows; every split reuses those statistics. All weights, bias, probabilities, labels and original row positions are checked.

The legacy and prepared numerical outputs match the baseline exactly. Across 10,521 numerical fields, the maximum absolute difference from independent NumPy/SciPy full-batch calculations is 1.1102230246251565e-15 under the existing 1e-8 absolute and 1e-9 relative comparison. Output hashes, fixture hashes, binary/object proofs and independent expected-output hashes are retained. The baseline probe is freshly compiled, linked and executed against the previously qualified GPU-prerequisite library objects; the baseline library build itself is historical. Candidate objects come from this unit's fresh exact-source benchmark build. This CPU Double comparison makes no GPU equality, model-quality, speed or memory-bound claim.

## Preserved failed attempts and cold-start limitation

The first qualification-only PCA checkout failed before building because nested local Git object references exceeded traversal depth. The repair lists every reachable object store deepest-first and retries in a fresh checkout. The failed setup and repair metadata remain. The frozen source does not change.

The first older-compiler focused runtime attempt failed after successful builds and safe tests because SwiftPM had no compiled Metal library. The corrected controller checks equal clean pinned MLX revisions and copies the native resource beside the test binary. The original controller and failed receipts/logs remain separately named.

The subsequent combined five-suite cold-start run blocked. Its stack sample shows a real MLX initialization lock cycle: an evaluation holds the MLX evaluation lock while waiting for one-time global stream initialization, while another thread owns stream initialization and waits for the evaluation lock. The unchanged pinned dependency contains that inversion. The task's sampled helper was explicitly terminated and its attempt retained. Explicit serial suite starts passed the bounded probe and the complete compatibility rerun. Concurrent cold-start MLX safety remains unqualified. No baseline reproduction or explanation for why the full native runs avoided the hang is claimed. This is a retained runtime hazard, not a production fix in this PR.

## Evidence and replay

Standards and spec reviews report no source findings. Independent evidence and publication audits remain separate files. Source, original logs, receipts, controller hashes, exact patches and original-to-published transformations make the work inspectable. Machine hostname and native hardware identifier are redacted; authorized filesystem paths remain. Raw task transcript, caches, native result bundles, probe binaries, linked objects and full CodeQL database remain local.

Run `python3 verify-publication.py --records PATH` on a downloaded package to check retained bytes. Qualification/build controllers require their original artifacts and dependencies. Retained local paths describe execution provenance, not a portable fresh-build environment. Native runtime qualification covers one Apple silicon host. Hosted safe tests and Codecov keep their existing SwiftML exclusions. No upstream approval or hosted completion is implied by local success.
