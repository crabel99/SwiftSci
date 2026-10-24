# CSV integration readiness

The local integration branch is `codex/csv-compact-integration` at `bc87628ce1fe8722a716a612d4d3db3d0149b7c8`. Upstream `main` was fetched at `e005efcc1dd55bb40f9e1ad63ac29e2d29de5178` and is already an ancestor. No source merge was needed. No branch was pushed and no PR was created.

## Full package validation now covers all modules

| Check | Result |
|---|---|
| Release build and full package tests | 1631 passed, zero failures or skips |
| Debug build and full package tests | 1631 passed, zero failures or skips |
| Declared native test targets in the test plan | All 15 |
| Benchmark controller tests with Metal enabled | 226 passed, zero failures or skips |
| Formal CPU regression policy | Passed, zero blocking or new failures |
| SwiftSci strict CPU cases | 202 of 202 passed |
| pandas strict CPU cases | 198 of 202 passed, four unchanged Wampler failures |
| New undocumented declarations versus upstream | Zero |
| Long type-check warnings in changed Swift files after cleanup | Zero |

Strict numerical conformance remains failed because the four pandas comparison failures remain failures. Passing the reviewed regression policy does not turn them into passes or certify unseen numerical inputs.

Both full native runs use the final head and include MLX-dependent targets. The existing Llama tokenizer is hash-verified. ONNX tests use the previously pinned ONNX 1.23.2, ONNX Runtime 1.31.0, and NumPy 2.5.4 environment with strict prerequisite checks. This isolated environment does not change the Python environment used for performance comparisons.

The default CI controller command passes with four explicit Metal opt-in skips. A separate run enables `SWIFTSCI_MLX_TEST_GPU=1` on the Mac and passes all 226 tests without skips. These are test results, not new performance measurements.

## Repair the acceptance verifier without weakening its contract

The first local policy attempt correctly rejected a stale CPU coverage fingerprint. A separate setup attempt rejected a stale worker checksum receipt after a package build replaced the executable. The formal snapshot builder then produced a fresh verified worker and receipt. Those unsuccessful setup records remain in the evidence.

The complete conformance capture exposed an integration defect. Workers supplied the new complete CSV schema and passed their checks, but `acceptance.inspect_run` reconstructed requests without `csv_schema`. It therefore rejected valid evidence as `Request contract differs` in three affected profiles.

Commit `671024197e` adds the resolved workload's schema to the independently reconstructed request. The regression fails before the change for all five matched CSV operations. The corrected checker passes the focused tests and still rejects missing schemas, wrong types, and extra columns. Replaying the unchanged capture then recovers complete coverage with exactly the four known numerical failures. Neither raw responses nor certificates were edited.

Commit `411b8e5665` updates only `coverage_sha256` in `known-failures.json`. The old fingerprint matches upstream. The review compares all 404 execution identities, identifies 18 changed CSV case bindings and 104 enclosing-profile bindings, and confirms that every known-failure binding is unchanged. All four failure entries, allowed errors, classifications, reference bindings, and numerical tolerances remain unchanged.

A fresh full policy run on the final head passes with zero blocking failures. The earlier captures, original guard failures, replay, and final run remain separate. No qualification rule or numerical tolerance was relaxed.

## Keep the tests cheap to compile

The first diagnostic builds found two optional ternary expressions that took approximately 0.5 to 1.3 seconds to type-check. Commit `bc87628ce1` gives their map closures explicit Int inputs and Double? outputs and separates nil selection from numeric construction. Fixture values, test assertions, and production algorithms are unchanged.

The final Release and Debug builds report no long type-check warnings in changed Swift files under the same 100 ms expression and 200 ms function diagnostic thresholds. The largest changed Swift test file is 197 lines. This is a local compiler and size check, not a hosted CodeQL or Codecov result. The final full native suites pass after the cleanup.

## Preserve the performance fingerprints

The [reference comparison](../2026-10-23-csv-sort-closeout/README.md) measures `a74f5c3b5e0e511bf5bb69886a40cbae48b28d99` against the pre-compact `5d1f89a961106104757f2d8d0b8faba79487d100` checkpoint. Those fingerprints stay unchanged.

No production Swift, package dependency, worker Swift, or benchmark-support Swift file differs between that performance head and the final integration head. The new commits change acceptance verification, baseline metadata, and two test expressions. The reported CPU and memory tradeoffs remain observations at their recorded source head. This integration work does not remove the previously documented small common-input CPU cost or make compact storage the default.

## Use two ordered review units

The branch contains 43 ingestion and comparison-contract commits through `5d1f89a961`, followed by 13 compact-storage and consumer commits through `a74f5c3b5e`. The three integration fixes are preserved as separate commits.

1. Review the CSV pipeline and matched benchmark contracts first. This includes record discovery, bounded eager and demand-driven streaming reads, inference validation, explicit date formats, selectable column conversion, native gather and radix preparation, and the two acceptance-contract fixes. The original cut touches 77 files. It needs its own validation at the delivery cut before submission.
2. Review selectable compact Double storage and its consumers on top. This includes gathering, joining, filtering, numeric preparation, stable sorting, prepared-key reuse, and the all-missing shortcut. Include the test-inference cleanup here. The original compact cut touches 22 files. Its representative comparison uses the already improved reader as its baseline, so those results must not be described as an upstream-main speedup.

These are proposed delivery boundaries. Separate PR branches have not been cut or submitted. The fully tested integration branch and original experiment checkpoints remain intact. Before submission, validate each delivery cut independently and run hosted required checks on its actual head. Engineering notes, raw experiments, and reports remain on `codex/engineering-notes`.

## Keep existing tooling limitations visible

The documentation script reports 2431 documented declarations out of 2464, or 98.66%. Its final success line incorrectly says 100% because the script gates placeholders rather than the coverage percentage. Upstream has the same 33 undocumented declarations, and all five new declarations are documented. The inaccurate success message is an existing tooling issue outside this source change. This report does not claim 100% actual documentation coverage.

Hosted CodeQL, Codecov, and the remote workflow results have not run for these local commits. Local native test success does not substitute for them.

## Evidence and recovery

[Final audit](final-audit.json), [contract inventory review](contract-inventory-review.json), [baseline metadata review](baseline-review.json), [documentation comparison](documentation-audit.json), and [delivery scopes](delivery-scope.json) retain the concise records.

The [experiment archive](experiments.tar.gz) contains raw requests, responses, certificates, expected outputs, build and test receipts, diagnostic logs, regression evidence, and validation scripts. It excludes virtual environments, compiled binaries, model weights, external input datasets, and xcresult bundles. Reproduction requires restoring the recorded source, dependencies, dataset cache, tokenizer, and output paths. These are environment-specific receipts rather than a portable standalone benchmark package.

The [verified source bundle](integration-source.bundle) preserves all unsubmitted accepted commits relative to the recorded upstream main. The [integration patch](integration-fixes.patch.gz) contains the three commits after the performance checkpoint. Neither artifact belongs in a source PR. [Artifact hashes](artifact-sha256.json) identify the delivered evidence.
