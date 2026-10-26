# Prepared classification qualification, October 26, 2026

Prepared classification now carries named compact inputs through train-only preprocessing, logistic training and held-out labels or probabilities. The contribution is commit `8926829bf2952a8f981a8be199be9ee9c3f7c458`, on `codex/prepared-classification-workflow`, based on upstream `e19db7dda4567c425b7eb002da82e234e6c7980f`. It is independent of the unmerged prepared PCA contribution.

ClassifierEstimator declares prepared requirements with compatibility defaults for existing classifiers. LogisticRegression uses native batches and shared numerical loops, without converting features to nested rows. CPU prediction and gradient scratch buffers are reused across epochs. GPU conversion uses the existing scoped owner and completion boundary. Existing routing, Float controls, Double CPU arithmetic, Float GPU updates, zero epochs, strict thresholds, soft targets and positional row callers remain supported.

A direct logistic fit publishes parameters, feature names and resolved device together after successful computation. ClassificationPipeline protects configuration and lifecycle with NSLock, mutates local transformer snapshots during fits, rejects overlapping fits/predictions and checks configuration generation before committing. Predictions retain configuration snapshots; configuration changes after fitting require refitting. No lock crosses an await. Prepared transforms must preserve row identity. A package-only view of existing provenance avoids allocating an identity array or retaining feature buffers solely for that check.

## Qualification

| Check | Actual outcome |
| --- | --- |
| Native Xcode 27 Debug | 893 tests passed, zero failures and skips |
| Native Xcode 27 Release | 893 tests passed, zero failures and skips |
| Swift 6.3.3 | Debug and Release production builds passed; all final test targets compiled; 77 XCTest plus 740 Swift Testing CI-safe tests passed |
| Complete WDBC workflows | Nine fresh processes, 569 rows and 30 features, fixed train/validation/test split 328/115/126, epochs 0/1/32 |
| Original versus candidate | Original rows, candidate rows and candidate prepared results match exactly; labels and row positions match exactly |
| Independent NumPy/SciPy | 10,521 numerical field comparisons passed at unchanged workload tolerances; largest absolute difference 1.1102230246251565e-15 |
| Standardized supervised conformance | Six frozen cases across SwiftSci and Python reference engines, 12 engine-case runs passed; certificate audit passed |
| Documentation | Final SwiftML DocC archive and new guide generated; existing unrelated documentation/link warnings remain |
| Reviews | Spec and Standards reviews found no remaining actionable source findings after the pipeline synchronization correction; final trail review is stored alongside them |

Native tests required the existing ONNX Python prerequisites, with STRICT_ONNX_CI enabled. The target set was SwiftMLTests, SwiftDataFrameTests and SwiftPreprocessingTests. The older compiler safe run intentionally excludes the same GPU/MLX suites as hosted CI, while still compiling every test target. All runtime qualification is on one Apple M4 Max host running macOS 27; compiling for the macOS 14 deployment target is not a runtime test of macOS 14.

The implementation improves representation integration and eliminates per-epoch scratch allocation. It makes no general speed, peak-memory reduction, convergence or classification-quality claim. The fixed-step fixtures do not establish a fully trained model for every application.

## Preserved GPU behavior and limits

The new test initially assumed CPU/GPU finite-step numerical equivalence. A probe linked against the verified original library objects proves the difference already exists. For the 1,000-row synthetic fixture after four epochs, original CPU bias is -0.009412758577808177 and original GPU bias is 0.014662409201264381. Prepared and row GPU paths preserve the original GPU results within 1e-6; CPU results also match the independent NumPy reference.

The inferred zero-logit gradient explanation is recorded in `design/gpu-contract-analysis.md`. This contribution does not fix or qualify the GPU gradient against an independent mathematical implementation. Treat that as a separate investigation before making CPU/GPU equivalence claims. Finite Double input also does not guarantee representable Float GPU input. Explicit `.cpu` retains the qualified Double route.

Original sigmoid clamping also makes a legacy NaN row prediction return `[0, 1]`. The compatibility test pins the observed original behavior rather than inventing a new NaN contract. Prepared inputs reject nonfinite values.

## Reproduce the evidence

`production.patch` preserves the exact contribution. `verification/qualified-commit.json` binds final source hashes to both native test builds. Native build/test commands and result summaries are under `native-debug/` and `native-release/`. The earlier failed run is retained under `native-debug-initial/`; its failures were the stale diagnostic wording and two incorrect new compatibility-oracle assumptions. Logs are compressed without alteration.

`verification/generate-reference.py` regenerates the small independent numerical fixture. `verification/link-public-probe.py` takes an Xcode build log and links the public workflow probe against that build's actual library objects. Use a fresh baseline build and a candidate build with the pinned dependencies. The `--prepared` switch enables the new overloads. Its proof records command arguments and object/binary hashes. `verify-public-workflow.py` records the nine public-data executions and compares parameters, probabilities, labels and provenance to the original and NumPy/SciPy. Its local paths describe the executed experiment and can be changed when rerunning elsewhere.

`verification/capture-baseline.py` records the separate historical CPU/GPU compatibility fixture. It verifies original solver hashes against upstream and links the original qualified objects; its proof and the original worker build receipt are retained. Binaries, dependency caches and model weights are not committed here.

The standard workflow uses `Benchmarks/Tools/bench.py prepare --profile supervised-conformance`, `bench.py build`, `bench.py run --profile supervised-conformance --engines swiftsci,pandas`, and `bench.py audit`. The retained worker receipt binds its frozen source snapshot to the committed contribution. No frozen fixture, solver tolerance, failure inventory or hardware router rule was changed.

## Delivery boundary

Production code and engineering records stay on separate branches. No new upstream PR has been submitted by this task. The user stopped the prior PCA CI recovery and requested this next numerical contribution. Future submissions must run the full applicable local workflow and record tool/version limits. These qualification checks are not a claim that every GitHub workflow was replicated locally.

Xcode 27 remained selected. Swift 6.3.3 and the existing 26.5 SDK supplied separate compiler compatibility checks; no older Xcode was installed. GitHub currently documents that Swift CodeQL tracing is unsupported with Xcode 27 and Swift 6.4, so this record makes no new local Swift CodeQL pass claim. See [GitHub's compatibility notice](https://github.blog/changelog/2026-10-19-codeql-changes-for-macos-27-xcode-27-and-swift-6-4/).

All available reviewer models are in the GPT family. The final trail reviewer was requested as GPT-5.6-sol but its text identified itself as GPT-6; actual runtime identity is unverified. This review establishes neither exact model identity nor independence across model families. No active transcript path was exposed, so the audit uses saved artifacts and task context.
