# Consuming prepared pipelines under continuous requests

Date: 2026-10-07

## Decision and implementation

Carry prepared-batch ownership through transformer protocol dispatch, nested preprocessing pipelines, and regression fitting and prediction. Callers can explicitly transfer input through `fit(consuming:targets:)` and `predict(consuming:)`. Existing prepared overloads remain available and preserve caller snapshots. Shared column buffers detach through Swift array copy-on-write when a transformer writes them.

Implementation commit: `4c6d91b263bd16cd776eb315f6e1cafd44b6abab`.
Parent: `617c69e841ad78ee5bb0863eb2055bb8213ba54b`.
Branch: `codex/retained-memory-accounting-trial`.
Nothing was pushed. This report and raw results belong to `codex/engineering-notes`, outside implementation PRs.

The new consuming protocol requirement has a compatibility default that calls the conformer's existing prepared transform. RegressionPipeline transfers each completed intermediate through that requirement. It captures feature names and row counts before consuming input, preserving schema checks, output-count checks and failed-fit state handling. Configuration changes and fitting still require serialization.

Preprocessing Pipeline stays in prepared columns only when all steps declare `supportsNativePreparedBatches`. The property defaults to false. StandardScaler and MinMaxScaler opt in, and nested pipelines compute their capability from their steps. Native capability does not promise buffer reuse: MinMaxScaler retains its existing allocating transform. StandardScaler can reuse unique column buffers.

## Compatibility findings resolved

The initial pipeline integration broke a valid legacy sequence: PolynomialFeatures could add a constant bias column, then VarianceThreshold remove it and restore the original shape. Applying the prepared compatibility adapter to each intermediate rejected the temporary expansion. The previous whole-pipeline adapter checked only the final shape.

The corrected Pipeline preserves whole-pipeline row conversion whenever any step is legacy. Direct and nested expansion-then-reduction tests failed before this correction and pass afterward. Empty pipelines also preserve the old conversion of missing entries into numeric NaNs. Their identity path now clears validity metadata without copying value buffers, while shared input metadata remains intact.

Behavior review found the shape-changing case. The subsequent boundary audit found the empty-pipeline missing-value case. Standards review also corrected a method comment that had implied all prepared pipeline calls avoided row arrays. Both review findings are resolved. The pre-correction performance run was stopped and excluded from these results.

## Executable validation

Two initial focused failures demonstrated that nested pipelines copied unique input buffers and forced a prepared-only transformer through row arrays. After implementation, the reviewer-driven regressions exposed two shape-changing failures and four failed assertions for empty-pipeline missing values. All pass in the final build.

The final Release run passed 856 selected tests, zero failures and two optional tokenizer skips. It covers nested ownership transfer, legacy defaults, shared snapshots, concurrent transforms, zero-step pipelines, metadata, schema and finite-value rejection, estimator output counts and consuming training and prediction. An estimator test observes the original column address across the full asynchronous pipeline. Existing CPU regression agreement and failed-refit tests continue to pass.

Seventeen controller tests passed. The new validator rejects missing results, incorrect request shapes, invalid hashes and numeric errors, fabricated rates, capacity mismatches, undrained reservations, excessive memory and failed model cleanup. Smoke controls passed for both storage choices.

This remains the selected nine-module Release suite, not full-library or sanitizer certification. The existing MNIST fixture test returns early without its developer-local file and counts as passed. The two optional tokenizer tests remain skipped.

## Continuous workload

Each worker uses the public RegressionPipeline with a nested Pipeline containing a fitted StandardScaler and a GPU LinearRegression estimator. Training occurs once before measurement. Both storage choices create the same seeded held-out inputs and compute the same analytic answer before prediction. Copy retains its original input through output validation. Owned consumes it. Every returned prediction is checked against the analytic answer and included in a complete output hash.

The small case runs 32,768 requests of 64 rows and 3 columns. Medium runs 16,384 requests of 4,096 rows and 17 columns. Large runs 512 requests of 65,535 rows and 65 columns. Mixed runs 1,024 requests cycling through 8,191, 65,535, 16,383 and 65,536 rows with 65 columns. Twenty-four fresh workers cover three rounds of four cases and two storage choices, totaling 304,128 measured requests. Case and storage order reverse on the middle round.

Two slots continuously replenish requests. The whole-request reservation limit stays at 256 MiB, with the same conservative raw-plus-transformed estimate and analytic-answer capacity for both choices. MLX cache capacity is set to 256 MiB in each benchmark worker only. There is no idle period, cache clearing, profiler intervention or record serialization inside the measured window. Final cleanup releases the model and clears the cache.

This is a bounded in-process linear-inference workload. It does not simulate network serving, disk ingestion, model training or an LLM. Shared model storage, allocator caches and small retained timing/hash records are outside per-request reservations. Reservations are not an RSS cap.

## Results

Throughput is the median requests per second across three fresh workers per cell. RSS is the range measured after completing the continuous window, while the fitted model and normal GPU cache remain present. It includes allocator retention and the small request-metric records. It is distinct from the process-lifetime high-water mark and the post-cleanup sample, both retained in the raw records.

| Case | Copy requests/s | Consuming requests/s | Copy RSS MiB | Consuming RSS MiB |
| --- | ---: | ---: | ---: | ---: |
| small | 5242.4 | 5349.9 | 34.41 to 34.91 | 34.47 to 35.39 |
| medium | 2524.1 | 2527.2 | 35.91 to 39.97 | 34.92 to 35.83 |
| large | 70.6 | 75.2 | 331.08 to 355.20 | 187.16 to 194.94 |
| mixed | 118.8 | 119.5 | 362.89 to 368.86 | 210.20 to 247.23 |

Corresponding prediction hashes match across storage modes and all rounds. Every worker drained its reservations. Measured MLX active allocation returned to the fitted-model baseline after requests; final close returned both active and cached allocation to zero. Individual timing, memory and capacity records remain available for every worker.

These results compare ownership modes within the corrected public pipeline. They do not compare this executable with the parent branch, and they should not be combined with the prior scaler cleanup benchmark. That earlier benchmark cleared the GPU cache and idled between bursts. Here the cache operates normally throughout the continuous measurement.

Use the full paired ranges in validation.json when assessing variability. The final timing windows lasted 5.76 to 8.72 seconds. Three rounds on one machine support a workload-specific engineering decision, not a universal throughput or memory guarantee.

## Reproduction and remaining work

The arm64 Release build targets macOS 14 and runs on Apple M4 Max with 128 GiB unified memory, macOS 27.0 build 26A428. No macOS 14 runtime was tested. MLX Swift remains pinned to `4657976edcdd2c60642424985d474b45ddddb390`. Coverage is disabled; Metal uses safe math and precise FP32 functions.

Worker SHA-256: `77ec3638022b59ab8fa777f038b216fd59b5010ba39c6ef31af172efc807bb87`.

Run commands are in Benchmarks/RetainedGPUTrial/README.md. The local result bundles and full logs are under `~/local-ai/spl/swiftsci/gpu-consuming-pipeline-20261007/`. Archived fingerprints describe the final measured source and binary. The superseded comparison is excluded. Small and medium request counts were increased after a short pilot to lengthen their timing windows. Only the benchmark request-count ceiling changed after the broad library tests. An executable-only build unexpectedly included coverage sections and was rejected by the instrumentation guard before measurement. The final coverage-disabled test build passed nine focused pipeline tests, and the controller tests were rerun. Measurements use that final binary. Raw worker JSON is archived with gzip compression, preserving its original bytes.

Keep admission estimates conservative until more caller patterns and model sizes have been measured. Other native transformers can implement consuming transforms independently; the protocol default preserves them without claiming they reuse storage. Broader production serving and training measurements remain separate work.

- [Paired results and validation](../archive/2026-10-07/gpu-consuming-pipeline/validation.json)
- [Complete worker summary](../archive/2026-10-07/gpu-consuming-pipeline/sustained-comparison/summary.json)
- [Source and binary provenance](../archive/2026-10-07/gpu-consuming-pipeline/sustained-comparison/provenance.json)
- [Previous scaler integration](2026-10-07-consuming-scaler-integration.md)
