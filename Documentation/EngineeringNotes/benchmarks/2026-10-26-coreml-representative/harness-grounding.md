# Existing Core ML qualification commands

Read-only source inspection at `53063789b1893b28250ea239d5fdca4fed84c4c9`, `/private/tmp/swiftsci-gpu-logistic-correctness-20261026/source`. No experiment ran and source remained clean. Tools inspection initialized Instruments cache after a sandbox denial; it changed no repository file.

## What can be reused

| Command | Measures and proves | Boundary |
|---|---|---|
| `run.py --sweep` | First prediction, warm samples, rows/s, model load, per-sample RSS, process peak RSS, logical packing/output bytes, budget drain, scalar Double agreement, planned devices | Synthetic weights. Input source creation and artifact construction/compilation excluded. Model load can use disk cache. |
| `trained.py` | 66 cases on train-only scaled WDBC/wine MLPs, once-rounded Float32 parameters, independent NumPy forward checked against sklearn, held-out quality, model/input/parameter hashes, public/direct matrix equality | Uses the same worker timing as run.py. Swift starts with standardized columns. Python scaling-plus-inference timing does not measure Swift preprocessing. |
| `covertype.py prepare/run` | 90 cases, 54-feature/7-output trained MLPs with widths 128/256/512, up to 8192 rows. Original disjoint UCI partitions, full test reference quality, stable hashes and public/direct equality | Preparation trains and standardizes outside worker timing. Existing frozen source and prepared artifacts can be reused if all hashes verify. |
| `prepare_models.py` | Matched legacy, Float32-I/O and Float16-I/O ML Program source packages, fixture/file hashes, converter version | ML Programs specify Float16 internal precision. No conversion duration is recorded. |
| `prepared_workflow.py` | Production `CoreMLMatrixPool.prepare` plus full inference burst, 1/2/4/16/64 reuse, CPU/neural policies, 1/1 and 4/2 callers/slots, 1024/8192 rows, direct/retained exact equality, row identities, release and budget checks | Starts after fixture loading, PreparedNumericBatch construction, package compilation, schema probe, pool/model load and preflight. Final asynchronous release is separately timed. It does not call a fitted scaler. |
| `pool_trial.py --models ...` | 24 configurations with trained program32 packages, latency histograms, throughput, sampled RSS, fresh sync/async versus public pool, ownership/admission checks | Compilation/load/preflight excluded. Throughput includes output hashing. Copy/backing observations are not physical allocation measurements. |
| `concurrency.py` | Cancellation, invalid-input recovery, complete output/provenance stability, 15-second sweep and optional sustained five-minute runs | Latency combines queueing, admission, packing, prediction and owned-output copying. |
| `profile_pool.py` | Six bounded real Instruments recordings, four allocations and two Core ML/Neural Engine traces, signed profiling-only copy, same artifact and output hashes as completed program pool reference | Exports TOC only. Requires trace inspection before device or allocation conclusions. Profiling timings are explicitly not performance evidence. |

`CoreMLQualification.swift` compiles every artifact before starting `loadSeconds`, including reference modes. Its first prediction is fresh-process first request, not proven cache-cold inference. Three more warmups precede recorded warm samples. The strict formula remains `abs(actual-expected) <= 1e-5 + 1e-5*abs(expected)`.

`CoreMLComputePlan.swift` reads anticipated preferred placement for neural layers and recursive ML Program operations. Both qualification and concurrency records hard-code `executionTraceVerified=false`. Controllers reject a claim of true. `CoreMLProgramArtifact.swift` hashes every source package file and validates fixed shapes plus matching Float16/Float32 I/O. It loads the model CPU-only to inspect schema, so timing added later must keep that probe outside a claimed cold-load interval.

## Smallest next step

If the roadmap means representative trained inference transport, execute existing trained/Covertype, program pool, prepared-input and profiling commands on a verified committed Release worker. This needs no production API changes. Reuse frozen model artifacts rather than retraining merely to produce new timings. Existing historical evidence may already satisfy some of these cases.

If it requires the complete raw numerical workflow, one narrow benchmark-only extension is needed. Extend the prepared workflow worker or add a small sibling probe that starts with original held-out raw rows, applies training-fitted preprocessing through production APIs, constructs/prepares input, predicts and extracts all outputs. Record separate source construction, transform, retained preparation, prediction, total and release intervals. Preserve an explicit total around the whole preprocessing-to-owned-output path. Measure artifact conversion and Core ML compile/load as separate deployment phases; do not hide them in warm inference or claim an uncached load without controlling disk cache. Keep existing measurement contracts unchanged.

## Bounded acceptance

- Start with one frozen Covertype 54→512→512→7 artifact and 1024 rows, CPU then CPU/Neural Engine. Use one caller/slot, direct and retained input, reuse 1/4/16, three fresh processes. Add 8192 rows only after correctness passes.
- Bind raw row IDs, scaler training split/parameters, fixture binaries, package files, controller/source and uninstrumented Release worker by hashes before/after.
- Check every finite output and row identity, direct/retained exact equality within each artifact/policy, all budget/owner drains. Preserve strict Double mismatch counts and held-out quality; reduced precision exceeds tolerance if it exceeds it. Do not invent an application accuracy threshold from observed outputs.
- Report raw-to-output total, phase durations, first/warm requests, throughput, sampled/peak RSS, logical copy counts and retained reservations. Distinguish logical bytes from actual allocations.
- Run Instruments separately. Export event tables for the exact `CoreML measurement` signpost interval, retain schema/commands/raw trace, verify model/process identity and observed Neural Engine events if making that claim. Missing events are inconclusive, not proof of fallback.
- Existing controller suite is `python3 -m unittest discover -s Benchmarks/CoreMLInference -p 'test_*.py'`. Any new phase validator needs cheap tests rejecting omitted preparation, negative/nonfinite times, wrong row mapping, artifact drift and incomplete output evidence. Existing production tests cover core ownership and preparation behavior; run relevant tests if changing only benchmark code, applicable full local CI before a future PR.

## Local profiling availability

`xcrun xctrace list templates` and `list instruments` succeeded on Xcode 27 after Instruments cache permission escalation. Templates include Allocations, Time Profiler, Core AI and Metal System Trace. Instruments include Core ML, Neural Engine, Points of Interest, Thermal State and VM Tracker. No profiling experiment or device event observation occurred in this investigation.

## Additional complete-workflow controller found during synthesis

`Benchmarks/Worker/FusedCoreMLWorkflow.swift`, `FusedCoreMLCallers.swift` and `Benchmarks/FusedPreprocessingTrial/run_coreml.py` already measure raw-batch production fitted preprocessing, model-typed preparation, pool prediction, owned output and reservation drain together. The previous recommendation for a new sibling probe is superseded: reuse this existing controller/worker. Its source construction is outside timing, as are fitting, compilation/load and preflight. The worker hard-codes Covertype counts and held-out bounds; the Python controller hard-codes 1024/8192 model/fixture names. WDBC/wine require a narrow explicit fixture-contract extension. Its fingerprints also need standard worker/source/build/model/raw binding and independent model-reference checks for the roadmap qualification. Current comparison is exact equality with the native staged path under the same model/policy, which proves transport equivalence. See updated how-synthesis.md.
