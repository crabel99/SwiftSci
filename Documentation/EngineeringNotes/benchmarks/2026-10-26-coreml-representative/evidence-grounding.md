# Representative Core ML evidence grounding

Read-only exploration on 2026-10-26. Source inspected at `/private/tmp/swiftsci-gpu-logistic-correctness-20261026/source`, commit `53063789b1893b28250ea239d5fdca4fed84c4c9`. No models, datasets, builds, conversions or inference workloads were run. No source or cache files were changed.

## What already exists

`Benchmarks/CoreMLInference/README.md` documents a substantial qualification suite. Calling representative trained-model qualification wholly new would repeat existing work.

- The original six-mode fixture measures a deterministic 256-row, 128-feature linear model against an independent scalar Double reference. It records load, first request, warm samples, copy counters, admission release, RSS, source/model/input fingerprints and anticipated compute-plan placement. CPU/GPU native prediction and four Core ML policies are available.
- The fixed-weight sweep adds 128- and 512-wide MLPs, example batches, public fixed-matrix adaptation and direct Core ML controls. It separates execution completion, strict reference accuracy and application suitability. A completed run alone is not a quality certificate.
- `trained.py` already trains 64x64 ReLU MLPs on checksum-verified frozen WDBC and red-wine datasets, then compares 66 inference cases. Train-only standard scaling, original split IDs, source fixture hashes, rounded Float32 weights, training warnings, original versus rounded scores and constant predictors are retained. It independently checks NumPy forward computation against scikit-learn to `1e-12`. WDBC quality includes accuracy/AUC/log loss. Wine includes RMSE/MAE/R2 after reversing training-only target scaling. CPU/GPU MLX and all four Core ML policies are compared across vector/direct matrix/public matrix calls. This uses Python training, not SwiftSci neural-model training.
- `covertype.py` already prepares three trained 54-to-128/256/512-to-same-width-to-7 ReLU classifiers and runs 90 fresh-process cases. The source is UCI Covertype, DOI `10.24432/C50K5N`, CC BY 4.0. It uses original train `[0,11340)`, validation `[11340,15120)`, test `[15120,581012)` partitions. Early stopping uses training rows only. It fits scaling on training rows, rounds parameters once to Float32, checks independent forward probabilities against scikit-learn, evaluates the complete 565,892-row test partition and fixes 8,192 sampled held-out rows for runtime comparisons. Five sizes, 1/32/256/1024/8192 rows, use row-major little-endian Float64 inputs and seven logits. Quality records accuracy, macro-F1, log loss, per-class recall and confusion. Numerical tolerance and application-quality judgments remain separate.
- Later controllers already cover concurrent callers, admission cancellation, sustained load, retained output ownership, fixed-matrix revision comparison, persistent pools, native async experiments, trained ML Programs, allocation traces and device traces. They are existing investigation mechanisms, not unimplemented requirements.
- `prepared_workflow.py` already compares public direct versus retained prepared inputs for 1/2/4/16/64 repetitions, both CPU and neural policies, and one/four callers. It includes preparation and inference timing and separate release timing.

## Historical evidence that can be cited

The strongest located historical narrative is:

`/Users/crabel/Library/Caches/SwiftSci/engineering-evaluation-20261018/Documentation/EngineeringNotes/benchmarks/2026-10-25-foundation-closeout/roadmap-before-closeout.md`

Relevant lines 21, 37, 53 and 65-67 record completed mixed CPU/GPU/Core ML workflow qualification with retained Covertype inference, train-only preprocessing, source/provenance preservation, output/reference checks, cancellation, draining and capacity reacquisition. The full qualification has 128 measured samples, eight active-cancellation checks and eight queued-cancellation checks. Its Core ML reference bypasses retained sessions/fused packing but shares the same model/framework. This proves integration equivalence, not independent model accuracy or Neural Engine placement.

Lines 244-255 identify shipped Core ML interface/preprocessing/bounded workflows in upstream PRs 65/66/67. Lines 334-344 leave one unchecked item: representative model with independent outputs and recorded actual placement, conversion costs, cold/warm behavior, latency, throughput, memory and accuracy. The surrounding status explicitly says complete verified workflows already shipped and broader placement/policy comparisons remain ongoing.

`.../benchmarks/2026-10-18-pr-resource-audit/README.md` lines 72-75 documents already shipped explicit prepared-input/pool, fitted preprocessing, bounded pipeline and persistent-session costs. These are not missing production abstractions.

`.../benchmarks/2026-09-27-pr41-repairs.md` records a real composite scaler/regressor exporter repair and fresh-process execution checks. The standardized persisted workflow already executes exported scaler/regressor inference, but is a small CPU conformance control.

## Reusable artifacts and provenance contract

Source-repository fixtures are present now:

- `Benchmarks/Fixtures/supervised/inputs/wdbc-supervised-logistic-cpu-epochs32.json`
- `Benchmarks/Fixtures/supervised/inputs/wine-red-supervised-ols-cpu.json`
- Their `Benchmarks/Specs/datasets/*.json` manifests, split files, original WDBC data and red-wine CSV.
- `Tests/SwiftMLTests/Fixtures/CoreMLFloat16/{matrix.mlmodel,vector.mlmodel,manifest.json}` are small test artifacts, not representative trained models.

A prior trained WDBC/wine run is reusable if its `fixtures/{wdbc,wine}-training.json`, row-count JSONs, provenance and requirements are recovered. Those metadata already retain the full trained weights and scaler. However `trained.py main` always calls `prepare` and retrains, so invoking it again does not reuse the old frozen model.

A prior Covertype run is reusable without retraining if its `prepared/provenance.json`, selected indices/labels, `model-512.json`, `fixture-512-{1024,8192}.json`, referenced input/expected `.f64` matrices and source archive/info are retained. The provenance hashes every prepared file. `covertype.py run`, concurrency, pool and prepared-input controllers take already prepared inputs. `Benchmarks/FusedPreprocessingTrial/prepare_covertype.py` extracts raw train/selected rows from the recorded archive without retraining and checks source plus selection hashes.

`prepare_models.py` consumes that frozen fixture, verifies referenced binary hashes, and writes matched legacy Double-I/O plus Float32-I/O/Float16-I/O ML Programs with all artifact-file hashes. Both ML Programs use Float16 internal computation; Float32 transport is not Float32 arithmetic. `requirements-programs.txt` pins coremltools 9.0 and NumPy 2.0.2. The installed isolated conversion environment exists at `/Users/crabel/Library/Caches/SwiftSci/coreml-transport-venv`. A prior `models-1024`/`models-8192` directory is reusable once its `manifest.json` model hashes and fixture hash pass. Conversion is not required just to use already prepared programs.

No complete prior trained/Covertype model-output directory was located in bounded searches of `/Users/crabel/Library/Caches/SwiftSci`, related engineering notes, the primary checkout's benchmark output roots, or matching directories within the Codex workspace. This is a limited search result, not proof that prior artifacts do not exist elsewhere. No historical task-score values or actual execution-event counts can therefore be verified from the located records. Do not invent them from the presence of controllers or README instructions.

## Placement and measurement limits

- `MLComputePlan` describes anticipated/preferred placement. An allowed compute policy never proves device execution.
- `profile_pool.py` already records six bounded Instruments traces, including Core ML/Neural Engine events. Its measurement signpost excludes loading/preflight. Existing code still requires inspecting actual trace events. Missing device events do not prove CPU fallback. A saved trace alone does not establish an execution conclusion.
- Fresh process does not guarantee uncached Core ML loading. Compilation, loading and first/warm requests must remain distinct.
- Adapter copy counters or returned object identity cannot prove zero-copy or absence of internal allocation.
- Request budgets exclude persistent model/runtime memory. Sampled RSS is not a peak allocator bound or leak proof. Profiling runs change overhead and are separate from performance runs.
- The strict scalar Double tolerance remains `1e-5 + 1e-5*abs(expected)` across policies. Reduced-precision mismatches remain observable even if labels agree. No application-quality acceptance threshold is established by the current trained suite.

## Recommendation

Recover and hash-check an existing Covertype 512-wide frozen fixture and its matched programs before preparing anything new. Reuse its independent expected logits and full-partition quality metadata. Scope the next work to one reproducible current-commit public-adapter workflow that closes the remaining attribution/reporting gaps: explicit preprocessing/packing/inference costs, separately defined compilation/load/first/warm intervals, strict numerical plus task-score comparison across policies, and inspected observed device events. Existing scripts can supply most of this. Preserve negative precision results. Record actual-placement unavailability honestly if Instruments does not expose usable events. Do not add another execution interface or repeat the complete 90-case training/sweep unless evidence identifies a missing case.
