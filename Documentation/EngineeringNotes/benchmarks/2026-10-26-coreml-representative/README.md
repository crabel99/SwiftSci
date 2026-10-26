# Representative Core ML qualification

Source: [`a1e234d25677d91ce5914062603c41233fe13c09`](https://github.com/crabel99/SwiftSci/commit/a1e234d25677d91ce5914062603c41233fe13c09), based on qualified GPU-gradient source `53063789b1893b28250ea239d5fdca4fed84c4c9`. No upstream PR was created.

## The public multiclass exporter now produces a loadable model

The public MLP classifier exporter selected softmax but wrote an empty generic activation. Core ML rejected it with `Nonlinearity type INVALID`. The correction replaces the unused legacy softmax field with SoftmaxND, field 950, and encodes axis -1 for the existing rank-one outputs. Specification version 4, public signatures, binary sigmoid, regression and dependencies remain. Output documentation describes the existing probability vector.

The supplied-parameter and fitted-classifier regressions both failed before the correction and pass afterward. They check independent stable softmax, extreme logits, reordered and repeated rows, class ordering, packing counts and reservation drain. Apple's [SoftmaxND schema](https://apple.github.io/coremltools/mlmodel/Format/NeuralNetwork.html) defines this distinct layer and its axis. A one-variable schema control also compiled before the source change.

## Numerical agreement and model quality are separate results

The existing `trained.py` controller fitted train-only scalers and frozen 64×64 ReLU networks on repository WDBC and red-wine splits. Weights were rounded once to Float32 and shared by every path. Its independent NumPy forward calculation matched scikit-learn at 1e-12 before comparisons. All 66 cells completed and met the unchanged per-output Double requirement, `abs(error) <= 1e-5 + 1e-5 * abs(reference)`, including warmups and 64 measured samples per cell.

The matrix compares MLX CPU/GPU and Core ML example, direct matrix and public matrix adapters under four allowed-device policies. Public and direct matrix outputs matched exactly. Each cell uses one fresh process. The archive retains frozen weights, inputs, split IDs, scaling, task scores, outputs, errors, copy counts, RSS, loading and first/warm timings.

WDBC test accuracy was 0.9603, versus 0.6032 for the constant predictor. Wine test RMSE was 0.9569, worse than the constant predictor's 0.8095. Its optimizer reached 1,000 iterations without convergence. This is a poor frozen regression model, not an inference mismatch. No application acceptance threshold was established. We did not tune against the observed test results.

## Complete raw-data workflows preserve the existing APIs

The public probe fits Swift `StandardScaler` only on training rows, scales raw held-out prepared input and predicts through `CoreMLPredictor`. It independently validates outputs, global source-row indices and reservation drain. Both datasets passed all 36 calls. Swift/Python scaling differences were at most 1.8e-13. It records export, compilation, loading, self CPU work, RSS and thermal state separately. Self CPU work includes validation and telemetry and excludes Core ML service processes.

Local warm medians on Apple M4 Max, macOS 27.0.1, were:

| Dataset | Held-out rows | Public matrix inference ms | Raw scaling + example inference ms | Scaling component ms |
|---|---:|---:|---:|---:|
| WDBC | 126 | 0.0331 | 1.0971 | 0.0100 |
| Wine | 342 | 0.0429 | 3.0290 | 0.0150 |

These are different calling shapes. Matrix inference packs already-scaled inputs, predicts and extracts owned outputs. The raw workflow also scales and batches up to 32 separate examples. Decoding, source construction, fitting, export, compilation and loading are outside repeated prediction scopes and recorded separately where measured. Compilation and fresh-process loading may reuse Core ML caches. These observations are not a production performance baseline.

The library already has a fitted fused preprocessing-to-pool workflow. This study reuses existing inference machinery and adds no production runtime, scheduler, memory abstraction or public API.

## Actual events show CPU dispatches for these artifacts

Four bounded Instruments recordings compare CPU-only and CPU/Neural Engine policies on the full held-out matrix artifacts. The profiling copy changes only signing for profiling access. Model and output hashes match uninstrumented runs.

`inspect-traces.py` binds the launched process, target-scoped Core ML table and `CoreML measurement` interval. Every completed request has one matching prediction and one positive CPU dispatch event inside that interval. Counts were 34,438 and 33,548 for WDBC, and 31,239 and 29,993 for wine. No other Core ML device dispatch occurred in those intervals. Compute plans also anticipated CPU placement. Instrumented timings are excluded from performance comparisons.

This qualifies legacy NeuralNetwork artifacts with Float32 weights. It does not establish Neural Engine acceleration or qualify ML Program/Float16 artifacts. Those existing typed pool paths remain a separate representative qualification item. Raw traces remain at the local paths in the scripts. Published compressed event exports contain target-model events and measurement intervals, without machine identity from the sanitized TOCs. `publication-transforms.json` binds that redaction to the original hashes. Decompress the event XML files to repeat inspection against the sanitized TOCs.

## Verification and limits

All 1,685 native tests pass in Debug and Release, without skips. Swift 6.3.3 passes both builds, compiles all test targets, passes the safe suite and both new runtime regressions. Its LLVM profile records two executions of the corrected softmax branch.

Actual local main and benchmark workflow steps pass, including controller tests, optional engines, reference-policy checks, public-worker challenges and three MLX CPU profiles. Four known Python Wampler failures remain under the unchanged accepted policy. The Core ML controller suite passes 28 tests. Python CodeQL passes. Swift CodeQL remains unavailable with retained Xcode 27 / Swift 6.4.

The main workflow's coverage export check passes as written. Native xccov lists library targets without source coverage, so its aggregate is not a library coverage percentage. The separate LLVM profile proves this correction's execution.

### Standards

No actionable documented violations or heuristic findings. The correction stays within serialization, replaces an unused field constant, preserves signatures and adds public-path tests. See `standards-review.md` for the independent report.

### Spec

No blocking implementation findings. Rank-compatible last-axis softmax matches the successful schema control. Binary sigmoid, regression, shapes and existing tolerances remain. See `spec-review.md` for the independent report. Findings: zero per axis.

## Reproduce and inspect

`qualification.json` is the compact result. `verify-qualification.py` checks source fingerprints, receipts, outputs and dispatch counts. `FILES.sha256` binds published files. Compressed logs retain original hashes in `compression-map.json`. Extract `trained-results.tar.gz` for fixtures, the full comparison report and exact Python requirements.

Scripts preserve the original run for inspection and adaptation to a fresh isolated directory. `run-representative.py` refuses existing output, requires completed check receipts and performs fresh training. Use archived fixtures with the existing `run_case` controller to repeat inference without retraining. `trace-trained.py` and `inspect-traces.py` reproduce capture and event inspection. Keep builds separate from timing runs.

The first study launch stopped before training because its shared environment lacked scikit-learn. The successful run used a separate temporary environment. Its exact dependencies and the original failure log are retained.
