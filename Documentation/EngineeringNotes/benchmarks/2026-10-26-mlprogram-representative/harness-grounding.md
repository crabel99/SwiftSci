# ML Program qualification tooling

Read-only inspection on 2026-10-26 of `/private/tmp/swiftsci-mlprogram-20261026/source`. No source edits, training, conversion, build, inference, or profiling ran. Paths below are relative to that source unless absolute. This report is an explorer's factual map.

## Components

- `Benchmarks/CoreMLInference/prepare_models.py` converts an existing trained binary fixture into matched legacy Double-I/O, `program32.mlpackage` Float32-I/O and `program16.mlpackage` Float16-I/O models. It uses the fixture's Float32-rounded weights. Both programs specify Float16 compute. The manifest records source fixture hash, shape, converter versions, and every model/input/reference file hash. It does not record conversion duration.
- `program_pool.py::verify_models` verifies manifests and files for the specific Covertype rows 1024/8192, width54, outputs7 artifacts. `validate_backing_counts` checks successful pool prediction counts and observed output-object adoption without requiring adoption.
- `pool_trial.py` runs 24 fresh-process cells: cpu/neural policies, 1024/8192 rows, one/four callers with one/two slots, synchronous/asynchronous/persistent execution. `--models` always selects program32. Source, builder, binary, Metal, fixture, model and controller fingerprints bind its evidence.
- `concurrency.py::run_case` executes a bounded native `--coreml-concurrency` request. Its public helper already accepts arbitrary valid native request shapes. `validate` checks ownership, cancellations, budget drain, telemetry, output-hash distinction, latency histograms and bounded duration. The `main` command itself is Covertype-specific.
- `Benchmarks/Worker/CoreMLConcurrency.swift::stressCoreML` is generic for rows1...8192, up to1024 fixture columns and fixture-declared output dimensions. It compiles an optional ML Program package, checks transport shape/type, gets planned devices, and dispatches fresh or persistent callers.
- `CoreMLPersistentConcurrency.swift::runPersistentPool` uses `CoreMLMatrixPool.withPool`, verifies original/reversed preflight outputs, bad-input recovery, quota retention, concurrent output identity and final drain. `CoreMLConcurrency.swift::measurePredictions` marks the actual measurement signpost and records RSS once per second.
- `CoreMLProgramArtifact.swift` hashes every package file and probes compiled shape and matching Float16/Float32 I/O through a CPU-only model load. This probe occurs before measurement and invalidates any interpretation of later load as cache-cold.
- `prepared_workflow.py` and `CoreMLPreparedWorkflow.swift` compare direct pool prediction with retained `pool.prepare` on a fixed schedule of reuse1/2/4/16/64. They deliberately reorder columns and repeat/reverse source rows. The current command/request requires 1024/8192 rows and program16 packages.
- `profile_pool.py` captures six bounded Instruments recordings from a completed program32 pool trial: four Allocations traces and two device traces, asynchronous/persistent, four callers and two slots at1024 rows. It signs a copied worker for profiling, preserves the original, verifies matching models/outputs and exports TOCs. Event interpretation remains separate.
- `trained.py` fits WDBC/wine64x64 MLPs and train-only scalers, rounds weights to Float32 once, checks NumPy forward output against sklearn to1e-12, freezes all fixtures and quality records, then runs66 legacy inference cases. Its `main` always retrains, so do not invoke it to reuse frozen models.

## Flow

1. A frozen trained fixture supplies standardized columns, expected Double logits or regression outputs and complete layer weights. `CoreMLQualificationFixture` accepts either inline columns/expected arrays or checksum-bound row-major little-endian f64 binaries.
2. `prepare_models.py` currently requires binary descriptors. It checks referenced binaries, copies them and generates matched artifacts. Layers remain dense/ReLU with a linear final output. WDBC's returned value is a logit; sigmoid belongs in the external task scorer. Wine requires reversing target normalization for task scores.
3. A controller verifies an uninstrumented Release worker and matching build record. The request names the fixture, rows, policy, execution mode, caller/model/slot counts, duration and RSS cutoff. Persistent execution also specifies retainedBytes.
4. `Worker.swift` routes `--coreml-concurrency request.json result.json` to `stressCoreML`. It validates request bounds, loads the fixture, compiles the requested package or equivalent legacy artifact, checks program dtype/shape, and derives byte estimates.
5. Fresh mode constructs `CoreMLPredictor` instances. Persistent mode constructs one scoped public pool. Both preflight normal/reversed inputs and retain reference mismatch counts. Every timed return is hashed completely and checked against the same artifact/policy's preflight hash and source-row identity.
6. The public predictor/pool packs model-compatible transport, runs Core ML and returns owned Double values. Transport is2/4/8 bytes per element for Float16/Float32/legacy. Public source batches and owned outputs remain Double.
7. `measurePredictions` records latency, output checking, RSS, budget state and thermal state. It then requires caller completion, released predictors, independently retained output stability and zero final reservations/queue. Python revalidates the result.
8. Profiling runs separately on a newly signed worker copy. The prior representative `trace-trained.py` provides a generic rows/fixture example and `inspect-traces.py` exports target-process Core ML tables and measurement signposts. Adapt table/device assumptions for ML Programs; its existing exact CPU-dispatch assertions describe the prior legacy run and must not be copied as an expected ML Program conclusion.

## Files

Read source files:

- `Benchmarks/CoreMLInference/{prepare_models,program_pool,concurrency,pool_trial,profile_pool,prepared_workflow,trained}.py`
- `Benchmarks/CoreMLInference/{test_program_pool,test_prepared_workflow}.py`
- `Benchmarks/CoreMLInference/README.md`, `requirements-programs.txt`
- `Benchmarks/Worker/{CoreMLConcurrency,CoreMLPersistentConcurrency,CoreMLPreparedWorkflow,CoreMLProgramArtifact,CoreMLQualificationFixture}.swift`
- First120 lines of `CoreMLQualification.swift`, dispatch matches in `Worker.swift`
- `Tests/SwiftMLTests/{CoreMLFloat16Tests,CoreMLPreparedMatrixTests,CoreMLMatrixPoolTests}.swift`
- `Tests/SwiftMLTests/Fixtures/CoreMLFloat16/{README.md,manifest.json}`
- Source documentation match `Documentation/FoundationContract.md` for typed transport contract.

Read prior records:

- `/private/tmp/SwiftSci-coreml-representative-handoff-20261026.md` and the current chain's relevant next-item matches.
- `/private/tmp/swiftsci-coreml-representative-20261026/notes/Documentation/EngineeringNotes/benchmarks/2026-10-26-coreml-representative/{README,harness-grounding,evidence-grounding,how-synthesis,plan}.md`
- Relevant matches in engineering-notes README/DECISION-RECORDS/RETAINED-FILES.
- `/private/tmp/swiftsci-coreml-representative-20261026/trace-trained.py`, relevant `inspect-traces.py` and `RepresentativeWorkflowProbe.swift` matches.
- Frozen training JSON metadata and fixture shapes described below.

## Boundaries

### Available frozen representative data

Use `/private/tmp/swiftsci-coreml-representative-20261026/trained-results/fixtures`.

| Dataset | Frozen fixture | Shape | Parameter layers | Training metadata SHA256 |
|---|---|---|---|---|
| WDBC | `wdbc-126.json` |126x30 to126x1 |30x64,64x64,64x1 |`fd17a54a798f6fa39ac8e90ab40d11385f18f76c707caff623072a2cbe8dc389` for `wdbc-training.json` |
| Wine | `wine-342.json` |342x11 to342x1 |11x64,64x64,64x1 |`ccfdc0a6ae6fc78f1298c71962ce83125a048355cd3e7827d6ea774e539db947` for `wine-training.json` |

Metadata contains split IDs, heldout row IDs/targets, scaler mean/scale, target mean/scale, full frozen weights, training warnings, original/rounded quality, constant-predictor quality and per-shape fixture hashes. The prior results directory retains all66 comparisons, provenance, exact Python requirements and assessment. Its published archive is `trained-results.tar.gz` inside the representative engineering record directory. Verify fixture hashes and existing qualification before reuse.

The previous bounded search found no complete historical Covertype prepared artifact cache. Nothing in this exploration overturns that finding. Training another Covertype model is unnecessary to qualify existing WDBC/wine representative programs.

### Precision and reference contracts

- Preserve the independent Double formula `abs(actual-expected) <= 1e-5 + 1e-5*abs(expected)`. Float16-compute precision exceedances must remain visible even when labels agree.
- `pool_trial` transport equivalence requires exact hashes within each artifact, shape and policy across modes. Cross-policy exact equality is not required. Model artifact hash must be identical.
- Native concurrency output retains only strict preflight mismatch counts and hashes, not full numeric outputs, maximum errors or task scores. This record alone cannot establish application quality. `prepared` output adds maximum error but still no full task output vector.
- No application acceptance threshold is established in prior records. WDBC heldout accuracy0.9603 versus constant0.6032; wine RMSE0.9569 is worse than constant0.8095. Do not improve the wine model against observed test results or describe inference agreement as a model-quality pass.

### Timing and accounting contracts

- Fresh latency includes actor scheduling, admission wait, packing, prediction and owned-output copying. Full-output hashing is outside individual latency but inside throughput's measured duration.
- Model compilation, loading, schema probing, fixture/source construction and preflight occur outside concurrent measurement. Fresh process does not prove uncached load.
- Prepared workflow total includes one model-typed preparation plus its full prediction burst. It excludes source construction, model load/compilation and validation. Final async reservation release is separately timed.
- Persistent reservation is32MiB retained allowance plus request allowance per slot. Fresh mode accounts only active request allowances. Neither is a physical allocator cap. RSS is sampled, with1GiB cutoff, and cannot prove leak freedom.
- Output-backing identity proves returned-object adoption, not no internal copying. Different objects may share storage.
- `executionTraceVerified` remains false by design in worker/controller records. Actual observed events belong in separate trace assessment. Allowed neural policy and compute plans cannot prove Neural Engine activity.

## Non-obvious

The smallest missing qualification unit requires no new production API. Use the frozen WDBC full heldout model first, generate matched program32/program16 packages, run existing generic native concurrency requests under cpu and neural policies, compare direct and persistent modes and collect complete numeric outputs separately for strict/reference/task assessments. Add wine and concurrent cases after that passes. Reuse the existing raw fitted preprocessing composition if adding complete workflow evidence.

The high-level Python scripts hardcode Covertype, but the native concurrency worker already accepts WDBC/wine unchanged. A task-local controller can import `concurrency.run_case`, `validate` and `program_pool.validate_backing_counts` rather than creating another benchmark framework or changing native source solely for rows. `prepare_models.py` can remain unchanged if a task-local, hash-bound conversion writes equivalent binary descriptors from the frozen inline fixtures, preserving weights and expected outputs. Bind original and derived fixture hashes explicitly.

An explicit WDBC request can use:

```json
{"fixture":"/absolute/frozen/wdbc-126.json","rows":126,"policy":"cpu","execution":"persistent","callers":1,"instances":1,"admissionSlots":1,"seconds":2,"rssLimitBytes":1073741824,"retainedBytes":33554432,"modelPackage":"/absolute/models-wdbc/program16.mlpackage"}
```

Run it with `Worker --coreml-concurrency REQUEST RESULT` through the existing `run_case` timeout/validation helper. Use synchronous/asynchronous requests without retainedBytes for fresh controls. Repeat for both packages and policies. Source/build/Metal/binary/model/fixture binding must surround all cases just as `pool_trial` does.

Existing direct tool commands if verified Covertype artifacts are recovered:

```sh
CONVERSION_PY Benchmarks/CoreMLInference/prepare_models.py --fixture FIXTURE --output MODELS_SHAPE
PY Benchmarks/CoreMLInference/pool_trial.py --worker WORKER --prepared PREPARED --models MODELS --output RESULTS --seconds 8
PY Benchmarks/CoreMLInference/profile_pool.py --worker WORKER --reference RESULTS --output TRACES --seconds 2
PY Benchmarks/CoreMLInference/prepared_workflow.py --worker WORKER --models MODELS --fixtures PREPARED --output PREPARED_RESULTS --repeats 3 --samples 5
PY -m unittest discover -s Benchmarks/CoreMLInference -p 'test_*.py'
```

All output directories must be new. Conversion environment is `/Users/crabel/Library/Caches/SwiftSci/coreml-transport-venv`, pinned coremltools9.0/NumPy2.0.2. This inspection did not execute that environment.

Synthetic tests already cover Float16 ReLU matrix/vector conversion, overflow/nonfinite rejection, row/column order, batching, byte estimates, pool concurrency, retained prepared snapshots, owner release, admission and shutdown. They use weight-free `[3,2]`/`[2]` ML Programs with independent `max(0,Float16(input))` expectations. They do not qualify trained Float16 model accuracy or observed Neural Engine placement. Prior representative legacy qualification likewise explicitly leaves ML Program/Float16 as separate work.

Current evidence supports this next item and no unconditional later feature addition. Subsequent work should be chosen from measured precision, performance, ownership or actual placement defects and consumer needs. The latest handoff explicitly says not to add another runtime, scheduler, memory abstraction or duplicate workflow mechanism. Historical unchecked boxes alone are not current tasks.

## Open questions

- A full task-output assessment is needed alongside native stress records. The prior `RepresentativeWorkflowProbe.swift` saves complete outputs but constructs legacy models. The smallest adaptation can load a package/pool and retain the existing raw scaler checks. Alternatively a narrow benchmark record extension can expose only preflight outputs, not every timed request.
- Existing profiling scripts can be adapted to arbitrary representative requests, but package-qualified trace inspection must discover actual event schema and device dispatches. No ML Program device evidence was collected here.
- Complete raw preprocessing-to-pool costs can use existing fused machinery, but its Covertype row/split assumptions need an explicit fixture-contract extension for WDBC/wine. This is optional after the minimal inference qualification and must not duplicate the production composition.
- Application-specific quality thresholds remain a consumer requirement. Retain observed score differences and the frozen weak wine model rather than inventing thresholds from results.
