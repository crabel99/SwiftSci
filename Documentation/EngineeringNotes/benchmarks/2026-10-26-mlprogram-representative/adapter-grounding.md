# Core ML matrix adapter grounding

Source: `/private/tmp/swiftsci-mlprogram-20261026/source`, verified parent baseline `a1e234d25677d91ce5914062603c41233fe13c09`. Read-only exploration; no builds or source edits performed. All source paths below are relative to this root.

## Components Found

- `PreparedNumericBatch` (`Sources/SwiftDataFrame/Core/PreparedNumericBatch.swift:1-51`): owned compact Double columns, independent validity bits, immutable row provenance, Swift copy-on-write snapshots. Numeric NaN and missing are distinct, although imputation intentionally fills both. Selection keeps duplicates and composes original source indices.
- `CoreMLMatrixPool` (`Sources/SwiftML/Serialization/CoreMLMatrixPool.swift:9-95`): a scoped actor owning one loaded model, a fixed number of exclusive input/output buffer pairs, and a lifetime cooperative admission quota. Existing public API already handles direct and prepared fixed-matrix inference.
- `CoreMLPredictionSession` (`Sources/SwiftML/Serialization/CoreMLPredictionSession.swift:29-82`): validates model descriptions, ordered logical features, array rank/type, and equal input/output row counts; retains model plus an async-only Sendable wrapper.
- `ArrayFeature` (`Sources/SwiftML/Serialization/CoreMLArrayFeature.swift:4-47`): checked schema for positive rank-one/rank-two floating arrays. Rank-two flexible shapes are rejected. Float16 is adapter-gated to macOS 15.
- `CoreMLMatrixStorage` / `CoreMLMatrixBuffers` (`Sources/SwiftML/Serialization/CoreMLMatrixBuffers.swift:7-43`): page-aligned, page-rounded CPU-owned memory wrapped as tightly packed row-major MLMultiArray; one pair per admitted prediction slot. Core ML may return a fallback output rather than supplied backing.
- `CoreMLPreparedMatrix` (`Sources/SwiftML/Serialization/CoreMLPreparedMatrix.swift:6-27,49-105`): immutable model-typed numeric storage and copied row identity under one lifetime reservation. Sendable references share ownership; no mutable pointer escapes. Can outlive a pool and be reused by another compatible pool.
- `CoreMLMatrixInputPreparation` (`Sources/SwiftML/Serialization/CoreMLMatrixInputPreparation.swift:5-47`): immutable schema and column order without model/pool retention; runs fitted preprocessing from caller tasks and returns an owned prepared matrix.
- `StandardPreprocessingPlan` (`Sources/SwiftPreprocessing/Core/StandardPreprocessingPlan.swift:4-32`): immutable training-fitted Imputer then StandardScaler, storing replacements, negative means, and deviations. Existing concrete typed fill entry points serve Float16/Float32/Double without adding another execution layer.
- `StandardPreprocessingRowWriter` and tile normalization (`Sources/SwiftPreprocessing/Core/StandardPreprocessingRowWriter.swift:5-108`; `PreprocessingTileNormalization.swift:3-23`): bounded per-call Double workspace gathers columns, imputes NaNs, applies vDSP Double centering/scaling, then converts once into final model type.

## Flow

### Ordinary fixed matrix request

1. Caller compiles an artifact and calls `CoreMLMatrixPool.withPool` with a model URL, logical column names, selected output name, permitted compute units, budget, and explicit retained/request allowances (`CoreMLMatrixPool.swift:70-95`). Compilation is caller-owned and precedes this scope.
2. Whole quota is admitted **before model loading**: retainedBytes + maximumConcurrentPredictions * requestBytes. Session validates one supported rank-two floating input and a supported rank-two floating output, fixed shapes, matching model width and configured features, and equal rows (`CoreMLPredictionSession.swift:39-82`). Only after checking known pair capacity against retainedBytes are buffer pairs allocated.
3. `pool.predict(batch)` checks fixed row count and matches features by name (`CoreMLMatrixPool.swift:101-106`, `CoreMLPredictionSession.swift:84-110`). Direct prediction allows reordered physical columns. Unknown/missing/duplicate logical feature mappings fail.
4. `CoreMLMatrixRequest.columns` carries the immutable source plus matched column indices. Known request allowance includes source payload, owned Double output, and a complete page-rounded fallback model output (`CoreMLMatrixRequest.swift:15-26`; `CoreMLMatrixBuffers.swift:55-59`). Caller must estimate remaining framework work and metadata; this is no RSS cap.
5. `withSlot` counts pending calls, acquires a one-unit MemoryBudget token, takes one private pair, and keeps ownership through success/error/cancellation (`CoreMLMatrixPool.swift:187-206`). Awaiting the native call permits actor reentrancy; distinct pairs prevent concurrent mutation of one buffer.
6. `packMatrix` checks null counts and every value/conversion for finiteness, processes 16-row tiles, and writes using reported destination strides (`CoreMLMatrixConversion.swift:5-59`). It converts original Double values to declared Float16/Float32/Double.
7. `CoreMLAsyncModel.predict` creates a request-local feature provider and MLPredictionOptions with advisory outputBackings and awaits native async prediction (`CoreMLPredictionSession.swift:10-25`). No Promise/task wrapper creates a second scheduler.
8. Returned output is checked against declared name/type/shape, extracted with reported strides, and converted to owned Double columns. Nonfinite matrix outputs throw (`CoreMLPredictionSession.swift:189-197`; `CoreMLMatrixConversion.swift:61-79`). Result preserves source row indices and generated output names (`result`, or `result[0]` etc.).
9. Completed counters count successfully returned predictions. Output backing identity matches measure only exact MLMultiArray object reuse. They do not prove zero internal copying (`CoreMLMatrixPool.swift:38-41,174-184`).
10. Scope closure rejects new work, releases idle pairs, drains admitted work and queued slot acquisitions, clears session, then releases quota (`CoreMLMatrixPool.swift:215-237`). Cancellation can stop packing/extraction between tiles; submitted native work is awaited before returning ownership. Core ML controls actual device interruption.

### Convert once and reuse

- `pool.prepare(batch,budget:)` validates rows and feature mapping, admits typed storage + metadata before allocation, checks cancellation and rechecks pool after waiting, converts once, copies row provenance (`CoreMLMatrixPool.swift:112-126`; `CoreMLPreparedMatrix.swift:30-35,49-69`).
- `pool.predict(prepared)` validates shape, model element type, and ordered names; it does not bind to model identity or weights (`CoreMLPreparedMatrix.swift:72-77`). A compatible different model may therefore consume it.
- Each prediction still memcpy-copies bytes into its exclusive slot; no conversion repeats (`CoreMLPreparedMatrix.swift:79-85`). Prepared input has its own reservation, so request accounting does not charge it again (`CoreMLMatrixRequest.swift:15-19`).
- Last owner frees private storage and provenance synchronously in deinit, then schedules reservation release asynchronously. Callers/qualification should await observed budget drain rather than assume an assignment to nil immediately updates the actor (`CoreMLPreparedMatrix.swift:100-105`).

### Fused fitted preparation

1. Build `StandardPreprocessingPlan(training:)` **only on training observations**, using existing Imputer fit and scaler fit over imputed training columns (`StandardPreprocessingPlan.swift:21-32`). It stores no later inference statistics.
2. Capture `try await pool.inputPreparation()` (`CoreMLMatrixPool.swift:129-135`). Its model-free value can be shared across caller tasks or survive closure of original pool.
3. Call `preparation.prepare(source,preprocessing:plan,budget:)`. Unlike direct prediction, this path requires exact model column order, exact fixed row count, and fitted plan names/order (`CoreMLMatrixInputPreparation.swift:24-33`). This is intentional because fitted statistics are positional.
4. Admit prepared owner allowance + bounded Double workspace as one peak, check cancellation, allocate final typed storage, fill directly, check cancellation again, reduce reservation to retained owner allowance (`CoreMLMatrixInputPreparation.swift:34-45`). The source and fitted plan need separate lifetime accounting.
5. Typed fill switches on declared model element type and calls corresponding concrete plan entry point. Source NaNs (including compact missing sentinels) get replacements; arithmetic is Double. Output conversion occurs last, then final buffer scan rejects nonfinite values and conversion overflow (`CoreMLMatrixInputPreparation.swift:49-84`; `StandardPreprocessingRowWriter.swift:69-108`; `PreprocessingTileNormalization.swift:11-17`). Float16 finite rounding/underflow is permitted.
6. Tile size uses up to 2048 Double elements when rows>=32 and width<=512; otherwise one row. Workspace allowance covers tile + two width vectors +4096 (`StandardPreprocessingPlan.swift:57-70`). No full imputed or scaled matrix is needed in the fused path.
7. Predict the resulting owner through same existing pool request, validation, slot, async native, extraction and ownership path.

## Files Read

Production, read in full unless noted:

- Sources/SwiftML/Serialization/CoreMLMatrixPool.swift
- Sources/SwiftML/Serialization/CoreMLMatrixInputPreparation.swift
- Sources/SwiftML/Serialization/CoreMLPreparedMatrix.swift
- Sources/SwiftML/Serialization/CoreMLMatrixBuffers.swift
- Sources/SwiftML/Serialization/CoreMLMatrixConversion.swift
- Sources/SwiftML/Serialization/CoreMLArrayFeature.swift
- Sources/SwiftML/Serialization/CoreMLPredictionSession.swift
- Sources/SwiftML/Serialization/CoreMLMatrixRequest.swift
- Sources/SwiftPreprocessing/Core/StandardPreprocessingPlan.swift
- Sources/SwiftPreprocessing/Core/StandardPreprocessingRowWriter.swift
- Sources/SwiftPreprocessing/Core/StandardPreprocessingPlan+Indexed.swift
- Sources/SwiftPreprocessing/Core/PreprocessingTileNormalization.swift
- Sources/SwiftPreprocessing/Core/Imputer.swift (1-170)
- Sources/SwiftDataFrame/Core/PreparedNumericBatch.swift (1-175)
- Sources/SwiftML/SwiftML.docc/CoreMLInference.md
- Sources/SwiftML/SwiftML.docc/FittedMatrixPreparation.md

Tests/qualification read in full:

- Tests/SwiftMLTests/CoreMLFloat16Tests.swift
- Tests/SwiftMLTests/Fixtures/CoreMLFloat16/generate.py
- Tests/SwiftMLTests/CoreMLInputPreparationTests.swift
- Tests/SwiftMLTests/CoreMLInputPreparationAdmissionTests.swift
- Tests/SwiftMLTests/CoreMLPreparedMatrixTests.swift
- Tests/SwiftMLTests/CoreMLTiledPreparationTests.swift
- Tests/SwiftMLTests/CoreMLTestFixtures.swift
- Benchmarks/Worker/FusedCoreMLWorkflow.swift
- Benchmarks/Worker/CoreMLPreparedWorkflow.swift
- Benchmarks/Worker/CoreMLProgramArtifact.swift
- Benchmarks/CoreMLInference/program_pool.py
- Benchmarks/CoreMLInference/prepare_models.py

Test inventory searched by symbols for admission/cancellation/finite/shape assertions, without reading all bodies: CoreMLMatrixPoolTests, CoreMLMatrixPoolAdmissionTests, CoreMLPoolShutdownTests, CoreMLPreparedMatrixAdmissionTests, CoreMLPreparationFiniteTests, CoreMLTrialPackedTests.

## Boundaries

- Public prepared data is Double + logical names + provenance; model boundary converts to explicit declared type. Results return Double + names + original rows. Double output storage is not a claim about internal precision.
- Core ML owns backend execution/device placement. computeUnits permits devices; `.cpuAndNeuralEngine` is not proof of Neural Engine execution. Source qualification must record planned/observed placement separately from API success.
- Adapter supports fixed floating rank-two matrices with equal row counts. It does not support images, rank>2, dynamic/flexible dimensions, arbitrary categorical outputs, stateful models, or inference of row semantics.
- MemoryBudget/MemoryReservation remain the one cooperative admission system. Keep source, plan, returned results, compiled artifacts, model estimates, and retained prepared owner lifetimes explicit. No new runtime/memory manager is needed for the next milestone.
- Package-only `preparePackedForTrial` is an experimental comparison seam, not the public consumer path (`CoreMLMatrixPool.swift:137-164`). Public fused path is `inputPreparation().prepare(...preprocessing:)`.

## Non-Obvious Things

1. **Existing Float16 fixtures already are ML Programs.** `Fixtures/CoreMLFloat16/generate.py:13-18` creates MIL ReLU and converts to mlprogram with Float16 I/O and Float16 compute. Therefore “add ML Program support” would misdescribe current library capability. Missing evidence is representative weighted workloads at relevant shapes and device policies.
2. Existing `CoreMLFloat16Tests.swift:29-49,89-121` prove Float16 packing, two-byte counters, named feature reorder, row identity, rejected overflow, pool concurrency and owned results. These are weight-free [3,2] ReLU smoke/contract tests.
3. Existing fused test `CoreMLInputPreparationTests.swift:17-64` compares public fused and staged prepared inputs through same model, exact output equality, repeated selection [2,0,2], four callers, final owner drain, cancellation race and infinity rejection for 2/4/8-byte types. The Float16 case is already ML Program, but tiny and weight-free.
4. Existing larger tile test (`CoreMLTiledPreparationTests.swift:8-69`) uses [83,64] **Float32 legacy ReLU**, covers partial final tile, genuine missing + NaNs, duplicate row provenance, exact fused/staged prediction equality and peak->retained reservation reduction. It does not qualify weighted Float16 tiled computation.
5. Prepared owner tests (`CoreMLPreparedMatrixTests.swift:26-78`) already exercise 64 repeated concurrent predictions, source mutation, final-owner release, original pool closure, cross-pool reuse, and 2/4/8-byte payload counters.
6. Preparation metadata lifetime and queued cancellation are already covered (`CoreMLInputPreparationAdmissionTests.swift:14-83`). No need to rebuild these ownership mechanisms to qualify representative models.
7. Existing weighted benchmark support already exists. `prepare_models.py:29-65` builds legacy + program16 + program32 artifacts with stored Float32 original weights; program compute is Float16 in both ML Programs. Program32 means Float32 **transport**, not Float32 internal arithmetic. Preserve this distinction in records.
8. Existing representative-shape harness can be reused: CoreMLPreparedWorkflow handles 1024/8192 rows, direct-vs-retained, reuse1/2/4/16/64, 1/4 callers and1..4 slots; it tracks Double-reference error separately from exact direct-vs-retained equality, row mapping, RSS and cleanup (`CoreMLPreparedWorkflow.swift:93-154`). Its request validator currently limits rows but not dataset identity.
9. Existing fused weighted workflow is **Covertype-specific**: 11340 training rows,8192 heldout,54 features inherited from fixture, selected rows15120..581011, callers1/4, slots<=2, CPU/neural policies (`FusedCoreMLWorkflow.swift:89-107`). It compares native, consuming, packed trial, and public fused paths with exact same-model output hash and row identity (`:109-169`). This fixed dataset boundary is the likely benchmark extension seam when adding other representative datasets; generalize only metadata necessary for verified fixture contract.
10. Exact fused-vs-staged equality establishes integration consistency for a chosen typed model. It does not establish Double-reference accuracy or application quality; all paths can share model quantization error. Evaluate prediction/label/probability metrics against existing independent representative fixture separately.

## Open Questions / precise unqualified seams

- No execution was run in this exploration. Existing source tests establish intended checks, not passing results on current device or candidate. Parent must tie new qualification to worker source/build receipt and fresh actual outputs.
- Need representative **trained weighted** ML Program evidence for current representative fixture set (especially typed Float16), rather than only the old Covertype fixture and tiny unit model. Existing production API is sufficient.
- Need public fused preparation evidence on the representative raw training/held-out fixture contract with independent expected data, typed rounding, exact row provenance, changed caller inputs, and compatible pool reuse. Large Float16 tile+weighted model combines seams currently tested separately.
- Need keep three judgments separate: valid adapter execution/ownership, model numeric error versus reference, and application suitability (predicted labels/probabilities/task metric). Transport32 with internal Float16 compute is not a full precision control.
- Exact output-backing adoption and device placement are observations, not preconditions. New representative model may decline backing or map to CPU; qualify resulting fallback and report honestly.
- Compiled source/weights require package digest provenance (`CoreMLProgramArtifact.swift:6-21`); existing test `.mlmodel` helper is unsuitable for weighted package contents without preserving external weights. Existing package worker supports this already.
