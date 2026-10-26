# Production Core ML adapter grounding

Read-only exploration on 2026-10-26. Source `/private/tmp/swiftsci-gpu-logistic-correctness-20261026/source`, clean commit `53063789b1893b28250ea239d5fdca4fed84c4c9`. No source edits or builds. Read `CONTRIBUTING.md`; no ancestor AGENTS.md exists at the source location. Applied the how exploration pattern and unslop.

## Components

All source references below are relative to that source root.

- `CoreMLPredictor` is the public actor for scalar, vector-example, and fixed matrix inference. Initialization loads a caller-compiled `.mlmodelc`. Its default route is synchronous. `CoreMLPredictor.swift:26-64`.
- `CoreMLPredictionSession` loads and validates the model, matches prepared columns to the feature contract, converts numeric input, executes Core ML, and copies results. `CoreMLPredictionSession.swift:29-110`.
- `CoreMLMatrixPool` retains one model and private input/output buffer pairs within `withPool`. Each prediction owns an exclusive slot until native inference and extraction finish. `CoreMLMatrixPool.swift:59-95`, `:187-222`.
- `CoreMLPreparedMatrix` owns an immutable converted matrix and original row mapping under a separate lifetime reservation. It can outlive its creating pool and be used by a compatible pool. `CoreMLPreparedMatrix.swift:6-27`, `:49-105`.
- `CoreMLMatrixInputPreparation` captures only immutable input metadata. Its `prepare` applies a training-fitted `StandardPreprocessingPlan` directly into model-typed storage outside the pool actor. `CoreMLMatrixInputPreparation.swift:5-45`.
- `CoreMLBatchPipeline` and `CoreMLBatchSession` compose a bounded pull source, preparation, prediction, and ordered awaited consumption. A retained session reuses the model across sequential runs and releases each run's work quota. `CoreMLBatchPipeline.swift:41-85`, `CoreMLBatchPipelineSession.swift:18-64`, `CoreMLBatchSession.swift:23-60`.

## Flow

### Ordinary prediction

1. Caller compiles the model artifact, selects compute units, ordered input column names, output name, and `.examples` or `.matrix` at initialization. Model loading occurs before request admission on this path. `CoreMLPredictor.swift:36-56`.
2. `predict` checks batch size, matrix row contract, and exact feature-name set. Reordered prepared columns are accepted and mapped to the declared model feature order. `CoreMLPredictor.swift:84-90`, `CoreMLPredictionSession.swift:84-109`.
3. It reserves source payload, owned Double results, bounded input/output buffers, and caller-estimated workspace. This is cooperative admission, not measured RSS. `CoreMLPredictor.swift:91-100`.
4. Example mode calls once per row by default and reuses one input vector. Larger `maximumBatchSize` creates distinct providers/vectors and submits Core ML batch prediction. `CoreMLPredictionSession.swift:123-151`.
5. Matrix mode allocates a complete model-shaped `MLMultiArray`, packs columns in model order, and makes one prediction for all rows. `CoreMLPredictionSession.swift:159-170`.
6. Results become owned Double columns. `replacingNumericColumns` retains input row provenance. Reservation release occurs after native computation and extraction, on success or error. `CoreMLPredictionSession.swift:112-155`, `CoreMLPredictor.swift:101-115`.

### Pool and prepared reuse

1. `withPool` acquires the entire retained-plus-slot quota before loading the model, checks known page-rounded buffer capacity, allocates a private pair per slot, and enters the caller's scope. `CoreMLMatrixPool.swift:70-95`.
2. An ordinary prepared-column request validates names/shape and minimum request bytes before waiting for a slot. It packs numeric values into the slot's input array. `CoreMLMatrixPool.swift:101-105`, `:174-205`, `CoreMLMatrixBuffers.swift:55-67`.
3. `pool.prepare` instead reserves and allocates an immutable model-typed matrix, converts once, and copies row identity. `CoreMLMatrixPool.swift:108-126`, `CoreMLPreparedMatrix.swift:30-69`.
4. Predicting that owner checks shape, dtype, and ordered column names, then copies bytes with `memcpy` into the exclusive input slot. Numeric conversion is avoided; input copying remains. `CoreMLMatrixPool.swift:166-171`, `CoreMLPreparedMatrix.swift:72-84`, `CoreMLMatrixRequest.swift:22-25`.
5. Both routes call native async Core ML with advisory output backing, validate returned shape and dtype, copy finite results to Double columns, then return the slot. Core ML may use a fallback output. `CoreMLPredictionSession.swift:18-24`, `:189-196`, `CoreMLMatrixBuffers.swift:62-77`.
6. Scope exit marks the pool closed, releases idle arrays, waits for all pending slot acquisitions and native work, drops model ownership, and only then releases the parent quota. `CoreMLMatrixPool.swift:215-236`.

### Fitted preprocessing and retained sessions

`inputPreparation()` captures model metadata without the model or pool. Its preparation requires exact source column order and row count, validates the fitted plan, admits output plus plan workspace, fills typed storage, rejects nonfinite converted values, reduces the reservation to the retained input allowance, and returns an immutable owner. `CoreMLMatrixPool.swift:129-134`, `CoreMLMatrixInputPreparation.swift:24-75`.

The bounded pipeline pulls serially until its loaded-but-unconsumed window fills. Child tasks prepare and predict concurrently; completed results can wait in a dictionary until their turn. Consumption is serial and ordered. Each prepared owner is explicitly released after inference before its child returns. `CoreMLBatchPipelineWindow.swift:26-72`. There is no padding, dropping, retry, or implicit transaction; short batches throw. `CoreMLBatchPipeline.swift:43-65`.

`withSession` requires separate lifetime and work budgets. Lifetime capacity covers pool and source/consumer context; each sequential `run` holds a whole work window through callbacks and prediction completion. Overlapping runs on one session throw. A failed run drains and permits another run. Scope exit drains the active run before closing its pool. `CoreMLBatchPipelineSession.swift:18-64`, `CoreMLBatchSession.swift:23-60`.

## Boundaries

- Matrix models must declare exactly one rank-two floating input and a selected rank-two floating output with identical fixed positive row counts. Input width must match the supplied column count. Flexible matrix ranges or multiple enumerated shapes are rejected. Input and output widths and dtypes may differ. `CoreMLPredictionSession.swift:48-75`, `CoreMLArrayFeature.swift:14-45`.
- Supported array dtypes are Double, Float32, and Float16. Float16 needs macOS 15. Example mode supports a fixed rank-one vector or exactly matching named Double scalar inputs. Numeric outputs are Double scalars or supported vectors. Integer/string labels, dictionaries, images, sequences, multiple input tensors, rank-three tensors, and flexible matrix shapes do not have an adapter contract. `CoreMLPredictor.swift:36-43`, `CoreMLPredictionSession.swift:48-75`.
- A matrix request must have exactly the declared row count and `maximumBatchSize == 1`. The rows are already inside the matrix; `maximumBatchSize` is not matrix tiling. `CoreMLPredictionSession.swift:84-88`.
- Missing, nonfinite, and conversion-overflow input values throw. Float16/Float32 rounding and finite underflow are accepted model precision choices. Matrix conversion traverses bounded 16-row tiles using reported strides. Matrix output extraction rejects nonfinite values. `CoreMLMatrixConversion.swift:33-79`. Example extraction validates type/shape but does not reject nonfinite output, unlike matrix extraction. `CoreMLPredictionSession.swift:246-260`.
- Copy counters are logical adapter byte counts. Input array bytes are `rows * inputWidth * inputElementBytes`; output bytes are `rows * outputWidth * 8`. Scalar input reports zero packing bytes. Prepared reuse reports the same input copy count because each invocation still copies into its slot. Counters exclude Core ML allocations, conversions, transfers, providers, boxing, and storage padding. They are not conversion counts or zero-copy proof. `CoreMLPredictor.swift:15-23`, `CoreMLMatrixBuffers.swift:72-76`, `CoreMLInference.md:123-126`, `:233-237`.
- There are no production timing counters or clocks in these paths. Timing a public predict call includes admission wait, packing/copy, Core ML submission/completion, extraction, and reservation/slot finish. Predictor creation/model loading and pool scope setup are separate. Prepared conversion is separate from repeated prediction. Framework compile time is caller-owned. A benchmark must measure these boundaries explicitly rather than label whole-call timing as device inference time.
- `computeUnits` permits hardware choices and fallback. It does not establish executed placement or precision. The public API returns no compute plan. `CoreMLPredictor.swift:31`, `:49`, `CoreMLInference.md:128-140`.
- Reservations cover known capacities plus caller estimates, not an allocator-enforced bound. Direct predictor model storage and escaped results require separate accounting. Pool request minima include source payload for ordinary columns, owned output and one fallback matrix; prepared input avoids the second source-payload charge because it has its own reservation. `CoreMLPredictor.swift:67-72`, `CoreMLMatrixBuffers.swift:55-59`, `CoreMLMatrixRequest.swift:15-19`.
- Cancellation is cooperative. Packing/extraction check between tiles; synchronous native work completes before the post-call check. Async routes await native completion before releasing request owners and slots. Pool closure drains pending work. Consumer side effects from completed earlier batches remain committed. `CoreMLMatrixConversion.swift:41-42`, `:66-67`, `CoreMLPredictionSession.swift:173-185`, `CoreMLMatrixPool.swift:187-236`, `CoreMLBatchPipeline.swift:63-65`.

## Non-obvious

- `CoreMLPreparedMatrix` is compatible by input shape, dtype, and ordered feature names, not by model identity, input tensor name, output schema, or compute units. That is sufficient because it owns input values only. `CoreMLPreparedMatrix.swift:72-76`.
- Prepared copies share immutable storage and one reservation. The last owner frees its arrays and schedules reservation release asynchronously. Public callers cannot explicitly close an owner and invalidate another caller's reference. The bounded pipeline has a private deterministic finish operation on an owner it never exposes. `CoreMLPreparedMatrix.swift:92-104`.
- A shared pool/input budget needs enough headroom for both complete lifetimes. Nested acquisitions under a held quota can deadlock callers through hold-and-wait. The scoped pipeline subdivides an admitted parent quota to avoid reacquiring that parent. `CoreMLMatrixPool.swift:66-68`, `:108-110`, `CoreMLBatchPipeline.swift:75-84`.
- The pool checks supplied output array object identity through package-only counters. Identity reuse does not prove no internal framework copies. `CoreMLMatrixPool.swift:38-41`, `CoreMLMatrixBuffers.swift:76`.
- The public predictor is synchronous even for matrix mode. A package-only initializer enables an async matrix trial. Pool predictions are public native async. `CoreMLPredictor.swift:53-64`, `CoreMLPredictionSession.swift:14-24`.
- Existing `MLPClassifier` and `MLPRegressor` already conform to `CoreMLExportable`, despite stale protocol documentation saying export was deferred. Their exporter builds rank-one Double input/output arrays and stores layer weights/biases as Float32. `CoreMLExportable.swift:36-37`, `:303-345`, `CoreMLProtobuf.swift:619-625`, `:637-674`. This can exercise example-mode inference, but it is not a fixed matrix artifact for the pool. The binary classifier exporter requests numeric sigmoid output rather than an integer label. The multiclass branch requests softmax, but the builder activation switch handles only relu, sigmoid, and tanh; qualification must not assume multiclass export works without running it. `CoreMLExporter.swift:521-550`, `CoreMLProtobuf.swift:688-699`.

## Demonstrated obstacles and open questions

1. No demonstrated production adapter change is needed to run an already-trained tabular MLP artifact that exposes the required fixed rank-two numeric contract. Compilation, trained weights, preprocessing parameters, reference outputs, and exact model input/output names must be supplied by the qualification fixture.
2. SwiftSci's own current MLP exporter creates rank-one examples, not rank-two pool models. Using that exact exporter output for pool qualification fails rank validation. Choose public example-mode qualification for that artifact, or create a fixed matrix Core ML artifact in the benchmark fixture using the same frozen trained weights. This does not establish a need for a new production model abstraction.
3. Existing GLM/tree classifier exports declare integer label outputs through `buildModelDescription`. Those labels are outside this numeric adapter. A numeric probability tensor artifact is needed for classification qualification rather than an implicit label coercion. `CoreMLProtobuf.swift:212-219`, `:281-291`, `:328-337`.
4. Fixed matrix sizes leave final short source chunks to the caller. A representative workload should choose an exact fixed row size or report the tail handling explicitly. The production pipeline will not pad or drop rows.
5. Independent numerics, trained-model suitability, cold/warm timing, preparation amortization, RSS/peak measurements, and executed hardware placement need new experiment evidence. Reading these adapter sources cannot establish them.
