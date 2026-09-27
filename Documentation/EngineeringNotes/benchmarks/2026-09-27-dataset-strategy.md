# SwiftSci benchmark datasets and ML/AI validation

## Current implementation order, September 27

Finish `codex/standardized-benchmarks` before production repairs. The first numerical, exact-model and controlled API fixture packs are implemented. Next are raw supervised splits and training-only preprocessing, dataframe semantics and layout cases, fixed neural inference, and CI/profile integration. Capability gaps must remain explicit. Then create a separate repair branch with one commit per error. Establish the formal performance baseline only after repairs pass the completed suite.

See [the controlled-suite implementation report](2026-09-27-controlled-suite.md) for current results and remaining scope. Earlier suggestions to repair failures before completing the suite are superseded.

Research notes, 2026-09-27. Planning only. No SwiftSci source files changed.

## Recommendation

Use a small collection of public datasets alongside exact synthetic fixtures. A shared dataset makes input comparisons reproducible. It does not make different training algorithms, preprocessing, precision, or timing scopes equivalent.

First establish independent answers with NIST Norris for CPU least squares, a known-spectrum PCA matrix, and a hand-computed Naive Bayes count table. Add KMeans when common initial centroids can be supplied or verified. Breast Cancer Wisconsin Diagnostic and Diabetes then provide small held-out quality tests. Add trained vision and language workloads only after checkpoint loading and numerical inference comparisons pass.

## What the repository currently supports

The [legacy inventory](/Users/crabel/Documents/src/SwiftSci/Benchmarks/Specs/legacy-inventory.json) defers fitted estimators, clustering, explanations, LLM generation, and vision inference because their contracts or output checks are incomplete. Downloading a standard dataset alone does not fix those gaps.

There is also a source change the inventory does not fully capture. [LinearRegression.swift](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftML/Core/LinearRegression.swift:97) now attempts analytical CPU least squares through LAPACK `dgels_`, then falls back to gradient descent. The GPU path casts inputs to Float and uses gradient descent. The default `.auto` route can therefore change both algorithm and precision. Its explicit CPU gradient descent method can help build a matched training experiment, but it is separate from ordinary CPU `fit`.

[KMeans.swift](/Users/crabel/Documents/src/SwiftSci/Sources/SwiftCluster/Core/KMeans.swift:48) accepts cluster count, iteration limit, tolerance, seed, and device. It does not expose an initial-centroids argument in that initializer. A common seed across libraries does not establish common centroids. The initial arrays must become observable or injectable before certifying a shared-initialization comparison.

[LLMBenchmarks.swift](/Users/crabel/Documents/src/SwiftSci/Benchmarks/Swift/LLMBenchmarks.swift) uses newly initialized decoder weights and a toy tokenizer. Its forward pass calls `MLX.eval`, which is useful, but no expected logits are checked. Generation counts stream events, which does not validate token IDs. [VisionBenchmarks.swift](/Users/crabel/Documents/src/SwiftSci/Benchmarks/Swift/VisionBenchmarks.swift) creates YOLO and U-Net models without loading trained checkpoints and feeds constant images. Those workloads can measure execution after their outputs are checked, but cannot establish trained-model quality.

## Proposed coverage and execution tiers

Keep one shared dataset catalog and several profiles that answer different questions:

| Evidence | Cases to add | Acceptance |
| --- | --- | --- |
| API correctness | Empty and all-null frames, null versus NaN, stable sort ties, Unicode/quoted CSV, integer limits, type preservation, mutation/copy-on-write isolation | Exact declared semantics and regression checks |
| Numerical conformance | Remaining NIST ANOVA and compatible least-squares cases; known-spectrum matrices; residual and reconstruction checks | Per-case numerical error bounds with dtype and conditioning recorded |
| Interoperability | CSV/Parquet round trips through an independent reader; feature/target row alignment; matrix layout and ownership | Values, schema, ordering and ownership survive conversion |
| Performance | Pandas-derived shape/type cases, H2O-derived cardinality/skew cases, end-to-end real workflows, bounded large-array sweeps | Correct output first, then latency, throughput and clearly named memory metrics |
| Model quality | Frozen training, validation and test splits on small real datasets | Predetermined quality rule against a simple baseline, with fit and prediction measured separately |
| GPU/model inference | Fixed tensors, weights and tokens; later compatible trained checkpoints | Validated outputs with device, precision and completed execution recorded |

Small semantic fixtures and conformance cases belong in ordinary CI. Larger performance sweeps should run on a named Apple silicon host. Model downloads and larger quality evaluations should be explicit profiles with verified cached inputs. Source fixtures and tiny gold answers may be bundled when permitted; larger assets belong in the cache with versioned manifests.

For memory integration, compare the same end-to-end work at three boundaries: frame to matrix/tensor conversion, repeated computation on prepared tensors, and the complete pipeline. Include narrow and wide matrices, Float32/Float64 where supported, shared versus uniquely owned buffers, and increasing working-set sizes. Keep process peak RSS distinct from backend allocation counters and declared payload bytes. Unified memory does not make these measurements interchangeable.

Certificates should remain named workload-conformance records binding input, implementation, output, tolerance and environment. Numerical stability and model quality are separate claims. The NIST suite does not issue software certification or endorsement.

## The first dataset pack

The dataset-to-API matches and acceptance checks below are recommendations, not existing SwiftSci guarantees.

| Dataset or fixture | Existing operation | What to check |
| --- | --- | --- |
| NIST Norris, 36 observations | `LinearRegression(device: .cpu).fit`, coefficients and predictions | Compare available fitted coefficients and residual results with certified NIST values. Keep it a full-data numerical validation case, without a train/test split. |
| Breast Cancer Wisconsin Diagnostic, 569 rows and 30 inputs | Binary `LogisticRegression`, `LinearSVC`, classification trees | Freeze stratified train/validation/test row IDs. Fit scaling on training rows. Check prediction dimensions, class encoding, probabilities or decision scores, then held-out macro-F1 and ROC-AUC. For SVC use decision scores for AUC; a probability-shaped return value does not establish calibration. |
| Diabetes, 442 rows and 10 inputs | Linear regression, regression trees and boosted trees | Export raw inputs with `scaled=False`, freeze splits, and fit transformations on training rows. Report RMSE, MAE, and R-squared against a training-mean baseline. |
| Frozen well-separated blobs and a small matrix with known singular structure | `KMeans`, `PCA` | Compare centroid sets modulo permutation and independently recompute inertia. For PCA check centered reconstruction, explained variance, and projection subspaces. Component signs and bases in repeated-eigenvalue subspaces need not match. |

NIST supplies certified least-squares parameter estimates and statistics. Norris is a lower-difficulty starting point; Longley is a later multicollinearity stress test. Do not impose the same expected significant digits on every precision or conditioning regime. Passing StRD checks is evidence about those cases, not NIST endorsement or proof for all data. [NIST datasets](https://www.itl.nist.gov/div898/strd/lls/lls.shtml), [certification background](https://www.itl.nist.gov/div898/strd/lls/lls_info.shtml), [StRD FAQ](https://www.itl.nist.gov/div898/strd/general/faq.html).

The classification and regression datasets above are available through scikit-learn. They are small enough for routine checks, but scikit-learn explicitly cautions that its toy datasets often do not represent real workloads. Iris is an optional multiclass smoke test, Wine an optional 13-feature multiclass case, and Digits an optional 64-feature classification/PCA case. They do not need to enter the first pack. [Dataset descriptions](https://scikit-learn.org/stable/datasets/toy_dataset.html), [raw Diabetes option](https://scikit-learn.org/stable/modules/generated/sklearn.datasets.load_diabetes.html).

Generate blobs once and distribute the resulting bytes to every engine. A seeded generator specification remains useful provenance, but each language should not independently regenerate benchmark inputs. Adjusted Rand score can assess clustering against synthetic labels without depending on cluster numbering. It supplements the inertia and centroid checks. [make_blobs](https://scikit-learn.org/stable/modules/generated/sklearn.datasets.make_blobs.html), [adjusted Rand score](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.adjusted_rand_score.html).

For the existing wine-quality workflow, filtering `target >= 6` can support descriptive analysis of that subset. A new predictive test should split the full labeled dataset before fitting transformations and should not filter by the target. Training-only preprocessing avoids leakage. [scikit-learn common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html).

## Keep different questions separate

Implementation correctness needs small examples with independently calculated answers. For Naive Bayes, use nonnegative count matrices with hand-computed smoothing and class probabilities before adding a text corpus. For logistic and linear inference, fixed weights and inputs let the benchmark check direct arithmetic separately from training. For YOLO preprocessing, use constant images, ramps, odd dimensions, and expected padding. These fixtures usually find errors more clearly than a large public dataset.

The deferred forecast APIs need fixed time series and fitting rules. Start Kalman filtering with a short hand-calculated recurrence. Use a deterministic trend plus seasonal signal for decomposition, and explicit model parameters and initial state for ARIMA and Holt-Winters. Chronological train/test boundaries and fixed forecast horizons belong in later quality tests. A famous time series cannot reconcile optimized smoothing parameters with fixed ones.

For `VectorStore` cosine search, freeze vectors and queries, including ties and a declared zero-vector policy. Calculate exhaustive cosine scores independently, sort with a declared tie rule, and check the returned top-k IDs and scores. Time normalization consistently. For an approximate index, add recall@k against that exact answer. Public embeddings are optional performance inputs after this contract passes.

Numerical validation asks whether outputs agree within justified tolerances. NIST least squares, fixed PCA matrices, and matched neural forward passes belong here. Set absolute and relative tolerances from dtype, conditioning, and output scale. A matching final metric can conceal wrong individual predictions.

Model quality asks whether a trained model predicts held-out data well. Keep its thresholds separate from numerical equivalence. Report a fixed-budget training result and, where feasible, time to a declared quality target. Do not invent a universal F1 threshold for all algorithms. Choose the threshold using a reviewed reference run and validation data, then freeze it before evaluating the test split. [Metric definitions](https://scikit-learn.org/stable/modules/model_evaluation.html).

Performance needs explicit timing boundaries. Record fit time and predict time separately, plus an optional end-to-end pipeline time. State whether construction, conversion, normalization, model loading, compilation, and output materialization are inside each measurement. Archive predictions and validation results independently of timing summaries.

For a matched training comparison, pin the exact objective, regularization, intercept handling, optimizer, initialization arrays, batch order, learning-rate schedule, stopping criterion, iteration budget, tree tie rules, histogram bins, bootstrap samples, and thread count as applicable. Otherwise report the result as a comparison of complete implementations at a stated quality target, rather than a speedup for the same algorithm.

## Apple silicon and GPU execution

Record requested and resolved device, chip, memory, operating system, library versions, precision, batch size, and warmup policy. Run explicit CPU and GPU cases when the API supports both. A tiny dataset may measure routing and launch overhead more than computation, so use separate frozen synthetic size sweeps for performance.

MLX builds computation lazily. Complete evaluation of outputs and synchronize the relevant stream before stopping the timer. Warm compilation separately from steady-state inference, and report cold-start time as another result if it matters. Unified memory removes the usual need for explicit host-to-device copies, but conversion and execution boundaries still matter. [MLX lazy evaluation](https://ml-explore.github.io/mlx/build/html/usage/lazy_evaluation.html), [synchronize](https://ml-explore.github.io/mlx/build/html/python/_autosummary/mlx.core.synchronize.html), [unified memory](https://ml-explore.github.io/mlx/build/html/usage/unified_memory.html).

A useful Apple-silicon comparison would use Python MLX as one matched-backend reference for the Swift MLX computation, with independent small arithmetic fixtures for correctness. Agreement between two wrappers over MLX alone is not an independent numerical oracle.

## A later trained-model pack

For YOLO, first load one compatible, versioned checkpoint in Swift and a reference implementation. Verify raw output tensors on a few fixed images, then decoded boxes, class IDs, scores, and NMS. A fixed COCO val2017 image subset can support a quick regression check; full quality claims should use the declared complete evaluation split and evaluator. A subset score is not the full COCO benchmark score. [COCO 2017 task](https://cocodataset.org/dataset/detection-2017.htm).

For U-Net, first establish a compatible trained checkpoint. Oxford-IIIT Pet offers pixel-level trimap annotations suitable for a later segmentation quality test. Pin class mapping, boundary treatment, resizing, and ignored pixels before reporting Dice or IoU. The dataset does not supply a checkpoint for SwiftSci's exact U-Net architecture. [Oxford-IIIT Pet](https://robots.ox.ac.uk/~vgg/data/pets/).

For the decoder, start with fixed tiny weights and token IDs, check logits and cache/no-cache agreement, then verify greedy generation and stopping. Add WikiText-2 only when a compatible trained checkpoint and tokenizer are pinned. Its raw version can support held-out next-token loss or perplexity under a fixed tokenization and context-window protocol. That measures language-model prediction quality, not chat usefulness. [Salesforce WikiText](https://huggingface.co/datasets/Salesforce/wikitext).

MLPerf is a useful design reference because it combines model, dataset, quality requirements, and execution scenarios. MLPerf Training measures time to target quality; inference measures execution of trained models. SwiftSci can adopt those principles without claiming an official MLPerf result. Official submissions require the relevant suite's rules, accuracy checks, and submission process. [MLCommons benchmark scope](https://mlcommons.org/benchmarks/), [inference scenarios and divisions](https://mlcommons.org/benchmarks/inference-edge/), [submission guide](https://docs.mlcommons.org/inference/submission/).

## Dataframe benchmarks

Pandas supplies a benchmark suite with generated and parameterized workloads rather than one canonical dataset for every operation. Its groupby cases vary shapes, types, group counts, and missingness. Adapt selected workload patterns at a pinned source revision, retain attribution, and freeze common input bytes. Use analytic references for expected aggregates and ordering; pandas is a comparator, not the sole correctness oracle. [Pandas benchmarks](https://pandas.pydata.org/community/benchmarks.html), [groupby workload source](https://raw.githubusercontent.com/pandas-dev/pandas/main/asv_bench/benchmarks/groupby.py).

Every fixture manifest should carry source URL, source revision, license and attribution, content hash, schema, units and label mapping, split row IDs, preprocessing definition, expected outputs or quality rule, and permitted numerical tolerances. Keep downloads and transformations outside ordinary timed runs.
## Supervised implementation checkpoint

Local commit `72a20129d4` now provides licensed WDBC and wine sources, frozen duplicate-safe training/validation/test partitions, train-only scaling and complete held-out wine OLS conformance. All 83 controller tests, 6 supervised engine cases and 28 smoke engine cases passed. See [the supervised-suite report](2026-09-27-supervised-suite.md). Stage 4 remains incomplete until controlled classifier training and probability/quality contracts are added. Diabetes is deferred because its original-data redistribution license was not established. Continue suite coverage before production repairs and the formal performance baseline.
## Controlled classification checkpoint

Local commit `31b3cff290` adds WDBC zero-, one- and 32-update CPU logistic checks with complete parameters, probabilities, labels and held-out metrics. All 89 controller tests, 12 supervised engine cases and 28 smoke engine cases passed. See [the classifier report](2026-09-27-classification-suite.md). The initial supervised pack now covers regression and controlled classification. Continue dataframe semantics and layout coverage next. General predictive-quality certification and the formal performance baseline are not claimed. The suite-first, then separate one-commit-per-error repair order is unchanged.

## Dataframe conformance checkpoint

Local commit `e5995732c2` adds 24 bounded dataframe cases for exact integers, nullable comparisons, stable ordering, typed grouping, functional replacement and logical matrix exports. All 97 controller tests, 48 dataframe engine cases and 28 smoke engine cases passed. Both certificate audits passed; 14 unchanged controls passed and 64 intentional wrong-output/input cases were rejected. See [the dataframe report](2026-09-27-dataframe-suite.md). This establishes logical behavior for the covered built-in types, not physical zero-copy layout or a performance baseline. Next, add fixed neural forward-pass fixtures and finish integration coverage before the separate one-commit-per-error production repair branch.
