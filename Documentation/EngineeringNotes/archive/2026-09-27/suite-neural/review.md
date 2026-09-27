# Independent neural suite review

This review used the supplied planning artifacts, the staged and unstaged SwiftSci changes, production decoder source, generated fixtures, current CI workflow, and saved build and runtime evidence. The full run transcript was unavailable, so I could not audit unrecorded choices or verify that every decision-log row maps to the original conversation.

## Findings

### [P1] The planned CPU subset is not run by CI

`Benchmarks/Fixtures/neural/README.md:7` says `neural-cpu-conformance` is the five-case profile for ordinary macOS CI, but `.github/workflows/benchmark-conformance.yml:39-86` never prepares, runs, or audits that profile. The workflow does run controller tests, which cover the NumPy implementation and fixture reconstruction, but it does not execute the Swift worker against any neural dataset. A broken Swift decoder adapter, parameter readback, device scope, synchronization, or cache path can therefore merge while CI stays green.

Add a workflow step that prepares and runs `neural-cpu-conformance` with both engines, audits its output, and uploads the run directory. Keep GPU cases and the known-failing loader profile outside this passing CI gate.

### [P1] The recorded source identity does not include the independent oracle

`Benchmarks/Fixtures/neural/generate.py:37` hashes only `generate.py`. Lines 50-55 write that hash as `source.sha256`, `source_sha256`, and `source_fixture`, even though line 12 imports `reference` from `Benchmarks/Tools/neural_reference.py` and line 44 uses it to create every expected answer. Changing the oracle can regenerate different pinned logits while leaving the declared source identity unchanged. The reconstruction test catches drift only while the current oracle and checked-in references disagree; after regeneration, the manifest no longer proves which oracle produced them.

Record and verify both generator and oracle identities. A small source lock listing each path, byte count, and SHA-256 would fit the repository's existing multi-source provenance pattern. Include `neural_fixtures.py` too if its contract is considered part of fixture generation.

### [P2] The decision trail omits the runtime outcomes and still says the build is pending

`/private/tmp/swiftsci-suite-neural/decisions.tsv:4` ends with "Release build pending," but `/private/tmp/swiftsci-suite-neural/build.log` contains the Release worker path. The trail also omits the direct runtime result in `run.log`, where nine Swift cases pass and `neural-gpu-rope-cached` fails with `-0.024063661694526672` versus `0.0425054856361493`, and the loader result, where both Swift cases fail exact readback at `layers.0.attention.key_proj.weight`. Those are the most consequential results of the work.

Append checkpoint rows for the build, direct profile, and loader profile. Preserve the GPU RoPE cached mismatch as an observed production failure unless later evidence identifies a suite error. Do not fold it into the loader defect or adjust the tolerance.

## Checks that held up

- The scalar oracle independently evaluates full causal logits at 80 decimal digits. Cached expected answers come from full-sequence math rather than the runtime cache implementation.
- The NumPy comparator uses Float32 arrays, an independent incremental cache, full output extraction, and the declared `2e-5` tolerances. The focused seven-test module passes.
- Swift rejects extra or missing parameters, wrong shapes, booleans, nonintegral token IDs, nonfinite weights, and values that are not exact bounded Float32 numbers.
- Both load paths read back the complete actual parameter key set, shape, dtype, and exact Float32 bit patterns before inference.
- Each timed Swift invocation creates a model and cache inside the requested MLX device and stream scopes, evaluates outputs, synchronizes the scoped default stream, validates shape and dtype, and extracts every value.
- The covered cache path is prefix length two followed by single-token steps. The suite states that cached multi-token continuation remains outside scope.
- All 12 dataset manifests match their current input, reference, and declared generator hashes. Limits and claims in the fixture README are appropriately narrow, including the absence of trained-model, hosted-GPU, and performance claims.

## Evidence reviewed

- `/private/tmp/swiftsci-suite-neural/plan.md`
- `/private/tmp/swiftsci-suite-neural/contract.md`
- `/private/tmp/swiftsci-suite-neural/api-review.md`
- `/private/tmp/swiftsci-suite-neural/decisions.tsv`
- `/private/tmp/swiftsci-suite-neural/controller.log`
- `/private/tmp/swiftsci-suite-neural/build.log`
- `/private/tmp/swiftsci-suite-neural/run.log`
- `/private/tmp/swiftsci-suite-neural/loader.log`
- `Benchmarks/Runs/suite-neural-01/`
- `Benchmarks/Runs/suite-neural-loader-01/`

## Attention

reviewed by GPT-6

- The review is artifact-only because the full transcript was unavailable.
- Fix the missing CPU CI execution and incomplete oracle provenance before treating the suite commit as complete.
- Keep the GPU RoPE cached and public-loader failures visible. They are evidence produced by the suite, not reasons to change expected answers or repair production code in this branch.

## Follow-up review, 2026-09-27

The two P1 findings above are resolved in the working change.

- `.github/workflows/benchmark-conformance.yml:80-88` now prepares, runs, and audits `neural-cpu-conformance` with the Swift and NumPy engines. Line 107 retains `Benchmarks/Runs/ci-neural-cpu/` with the other CI evidence.
- `Benchmarks/Fixtures/neural/sources.lock.json` pins `generate.py`, `neural_reference.py`, and `requirements-standardized.txt` by byte count and SHA-256. All 14 neural manifests pin the exact lock bytes, and each reference repeats that lock digest.
- `Benchmarks/Tools/numerical_fixtures.py:105-114` verifies the lock and each listed source before accepting an input. `Benchmarks/Tests/test_neural_fixtures.py:99-112` proves that changing the copied oracle causes rejection through this same path.
- Independent hash checks found no mismatch in the lock entries or manifest bindings. The focused neural test module passes eight tests, and `/private/tmp/swiftsci-suite-neural/controller-final-fixed.log` records 105 controller tests passing.
- The decision trail now records the Release build, the 19-of-20 original direct engine result, the two loader readback failures, the batch-size isolation, and these review fixes. This resolves the earlier P2 trail finding, subject to appending the final rebuilt runtime result.

The two new single-batch GPU RoPE cached fixtures are useful controls. They preserve the failing two-batch case and do not broaden the passing CPU CI gate. The pinned backend-source review identifies a missing batch factor in the specialized Metal single-token RoPE dispatch as the leading cause. That diagnosis is consistent with the repeated isolation evidence, but the suite correctly leaves the dependency unchanged.

Final rebuilt-worker runtime evidence was still in progress during this follow-up. No conclusion here relies on the earlier binary after the provenance-only regeneration.

## Final evidence review, 2026-09-27

No new suite findings. The rebuilt Release worker and regenerated provenance produce complete, internally consistent evidence.

- `suite-neural-03` contains all 12 declared direct cases on both engines. Twenty-three of 24 engine cases pass with two validated samples each. The sole failure is Swift `neural-gpu-rope-cached`, with actual `-0.024063661694526672` versus independent expected `0.0425054856361493`. Both single-batch GPU cached RoPE controls pass on Swift and NumPy, while the original two-batch case remains present and failing.
- `suite-neural-cpu-01` contains all five CPU direct cases on both engines. All 10 engine cases pass with 20 validated samples total. Its certificate is hash-valid, has `status: passed`, and passes the strict artifact audit.
- `suite-neural-loader-02` contains both public-loader cases on both engines. Both NumPy comparisons pass with four validated samples total. Both Swift cases fail before inference because `layers.0.attention.key_proj.weight` was not replaced exactly. The failed certificate is hash-valid, and the strict audit rejects it because the audit only accepts passing certificates.
- `suite-neural-smoke-01` preserves existing coverage. All 28 engine cases pass, its certificate is hash-valid, and the strict artifact audit passes.
- The core failed certificate is also hash-valid and records 46 validated samples from the 23 passing engine cases. Its strict audit rejects the failed status, so the known GPU defect cannot yield a passing certificate.
- The negative-worker pack has 72 results across four representative cases and both engines. Eight untouched controls and eight future-token causal checks pass. All 56 deliberately wrong inputs or expected outputs fail: first and last logit changes, invalid integer and floating token IDs, wrong weight shape, inexact Float32 weight, and changed weight values.

`suite-neural-02` is not runtime evidence. It stopped before execution because the newly added single-batch input was absent from prepared data, and its audit failed because no `run.json` existed. The logs are useful orchestration history only. Preparing the complete profile and rerunning as `suite-neural-03` corrected the setup error.

All 14 final manifests still bind the verified source lock, inputs, and references. The lock entries match the generator, scalar oracle, and dependency requirements by byte count and SHA-256. The runtime results therefore correspond to the provenance-reviewed fixture set and final Release rebuild.

## Final attention

reviewed by GPT-6

- The review remains artifact-only because the full transcript was unavailable.
- Treat `suite-neural-02` as invalid setup evidence and use `suite-neural-03` for final core results.
- Preserve the two failed certificates and their rejected audits. They accurately expose the batched GPU cached RoPE defect and public-loader parameter-name defect without changing production code or expected answers.
- Append one final decision-log checkpoint for run-03, CPU, loader, smoke, and negative-control results. The current last row still says final validation is pending.

## Trail correction

The final decision-log checkpoint was appended concurrently with the preceding review. The trail now ends with the invalid run-02 setup, corrected complete run-03 coverage, exact CPU, loader and smoke results, 105 controller tests, and all 72 negative-control outcomes. The remaining trail finding is resolved.

`commit-verification.json` also ties the reviewed evidence to commit `f8cec1f93ba075892338aef063a7b8d2a101f63d`, which is the current `HEAD`. It records 346 verified committed source files, tested binary SHA-256 `91368edf6493f6c385781d153245c6f86aa028ba8d70bf2a5acabacf86e25274`, and no production source changes. No open review findings remain.
