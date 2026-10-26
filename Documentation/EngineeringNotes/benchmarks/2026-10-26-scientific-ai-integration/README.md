# Combined scientific and inference qualification

October 26, 2026. Source `c4de6cc866fff6f52100535dbcb38dd708558200` is published on [codex/scientific-ai-integration](https://github.com/crabel99/SwiftSci/tree/codex/scientific-ai-integration). It combines the complete prepared PCA PR89 stack at `4f33c76f3938e070105c2a5928c712aa5e067a00` with the later prepared-classification, GPU correction and Core ML continuation at `a1e234d25677d91ce5914062603c41233fe13c09`. The original PR89 branch is unchanged. No upstream merge or new upstream PR is part of this unit.

The only shared production-file reconciliation adds PCA's prepared-matrix replacement operation while retaining the later provenance accessor and error wording. Every other PR89 file matches that reviewed parent exactly. Later SwiftML, SwiftPreprocessing, SwiftLLM and SwiftAgent production files match the inference parent exactly. `pca-parent-comparison.json` and `verify-qualification.py` check those relationships.

## Documentation reporting correction

The old checker printed an unconditional 100% success line even for undocumented or empty sources. Four of five tiny fixture tests fail against that behavior. The correction reports the counted ratio and placeholder result separately, labels the scan as a heuristic, and reports N/A when no declarations match. All five fixture tests now pass and run in CI. Existing placeholder failure behavior is preserved; no documentation threshold is introduced or relaxed.

The combined source reports 2,464/2,497 matched declarations documented, 98.68%. This is not DocC symbol-graph coverage. The exported test coverage and native aggregate coverage are also not a claim of 100% library source coverage.

## Fresh local verification

- All 1,696 native tests pass in Debug and Release with zero failures or skips. The strict ONNX prerequisite and pinned tokenizer are enabled.
- Actual main workflow steps pass: Debug/Release builds, safe tests, nonempty source coverage export, DocC generation and the five documentation regressions.
- Actual benchmark workflow steps pass: controller tests, optional Polars/DuckDB engines, CPU regression policy, adversarial public-worker controls, and all three MLX CPU profiles.
- CPU regression policy passes after evaluating 404 engine executions. Strict conformance has 400 passes and four retained Python Wampler failures; they remain failures, with no new blocking failures and no tolerance or inventory adjustment.
- Swift 6.3.3 passes Debug and Release builds, compiles every test target and passes the safe suite. Native runtime qualification is on retained Xcode 27 / Swift 6.4; the older compiler check is separate.
- Pinned Python CodeQL 2.27.3 reports zero findings. Local Swift CodeQL is unsupported with retained Xcode 27 / Swift 6.4. This unchanged tooling limitation was previously demonstrated and was not rerun for this revision. Hosted analysis is separate.
- Independent standards and specification reviews report no actionable findings. The source remains unchanged throughout these checks.

These are integration and correctness checks on one Mac. They do not requalify old timing studies on this new fingerprint or establish a new speed, RSS, hardware-placement or statistical-quality claim. The earlier representative ML Program study remains bound to a1e234d, with its reduced-precision failures and CPU-only dispatch observations unchanged.

`verify-qualification.py` verifies the original local source, receipts, log hashes and ancestry. `verify-publication.py` verifies this retained evidence package without rebuilding. Raw build caches, executables and xcresult bundles remain local; structured native summaries and compressed logs are retained here. Published metadata redacts the hostname and native hardware identifier while retaining explicitly authorized filesystem paths. Maps preserve original and published digests. Historical paths in runners require restoration or adaptation when reproducing on another machine.

## Attention

Reviewed by gpt-6-astra. No remaining blockers. The audit in `audit.md` checked source ancestry, actual xcresult summaries, workflow evidence and privacy transformations. Four strict-conformance failures and absent fresh local Swift CodeQL remain explicit limits. Later agent work is qualified separately.
