# Dataframe-to-model candidates

These files add worker adapters and fixtures. They do not change a public library API.

Copy `BoundaryWorkloads.swift` and `BoundarySweepWorkloads.swift` to `Benchmarks/Worker`. Do not copy `WorkerStub.swift` or `typecheck.py`. The stub exists only because the checkout's old indexing build contains duplicate `BenchmarkFailure` declarations.

Copy `boundary_fixtures.py`, `boundary_reference.py`, `boundary_sweep.py`, and `boundary_cases.py` to `Benchmarks/Tools`. Copy `boundary_workloads.py` to `Benchmarks/Python`. Adapt `generate_boundary.py` to the fixture generator location and `test_boundary.py` to the suite's test import setup. The `fixtures` directory contains six generated input/reference pairs. Reference files need the suite's source-lock hash before they become published fixtures.

## Worker dispatch

`dataframe-model` uses `BoundaryInput.decode(data, rows:)` and `Worker.executeBoundary(input)`.

`dataframe-model-sweep` uses `BoundarySweepInput.decode(data, rows:)` and `Worker.executeBoundarySweep(input)`. Decode once before timing. This expands the descriptor and prepares the source frame or evaluated tensors for the requested stage.

Python dispatch calls `boundary_fixtures.validate_input` and `boundary_workloads.prepare/execute` for conformance. Sweep dispatch calls `boundary_sweep.validate_descriptor`, then `prepare/execute`. Python uses pandas and NumPy on CPU even when the descriptor requests GPU. Reports must retain that distinction.

Register both operation names with numerical-fixture routing, manifest validation, output count, expected-value reconstruction, Python operation dispatch, and Swift `NumericalInputs`. Define the conformance reference basis separately from the sweep reference basis. Sweep reference generation must reconstruct the scalar answer from the pinned recipe and oracle, outside sample timing. Descriptors contain no expected values.

Suggested conformance tolerance is absolute and relative 2e-6 for Float32 and 2e-13 for Float64. The included dyadic sweep values are exact through the chosen arithmetic, and all Python stage outputs equal the independent scalar results exactly. Preserve per-dtype tolerances instead of relaxing both to a Float32 threshold.

## Contract and outputs

All source feature, filter, sort and target columns use `TypedColumn<Double>`. Row IDs use `TypedColumn<Int64>`. The adapter filters with `greaterThanOrEqual`, then calls public `sortBy`. Ties preserve input order. Features are exported in the supplied feature order through both public matrix export methods; disagreement fails the run. Targets and row IDs come from the same resulting frame.

The concrete contract permits 2 through 100000 rows, 1 through 64 features, unique row IDs bounded to Int32, and finite numeric values bounded to absolute 1024. Feature order must be a permutation. Every payload must retain at least one row. Missing values are outside this contract; the separate dataframe suite tests them.

Let N be retained rows and D be feature count. The complete conformance output is:

1. N, D, dtype width in bits.
2. N row IDs.
3. N times D Double matrix values in row-major order.
4. N Double target values.
5. N times D actual MLX tensor values in row-major order.
6. N affine predictions, `matrix @ weights + bias`.
7. N residuals, `prediction - target` after dtype conversion.
8. One mutation-isolation result, required to equal one.

Output count is `4 + N * (2 * D + 4)`. Mutation checks modify copies of exported arrays and replace a column on a copied source frame. They read the original source, selected frame, and allocated MLX tensors again. They also read the replacement column to prove the attempted mutation occurred.

The six conformance cases cover ascending and descending ties, reversed feature order, 4 by 2 and 4 by 5 output matrices, and Float32 CPU/GPU plus Float64 CPU. Float64 fixtures include fractional bits that Float32 cannot preserve.

## Sweep scope

The exact descriptor keys are `operation`, `recipe`, `device`, `dtype`, `stage`, `rows`, and `columns`. Operation is `dataframe-model-sweep`, recipe is `dyadic-v1`, rows are 128, 1024 or 8192, and columns are 8 or 64. The row choices are powers of two, so multiplication by 37 modulo row count gives unique row IDs.

The recipe uses feature value `((i*7+j*3)%19-9)/8`, target `(i%17)/4-1`, filter value `i%4` with threshold one, and ascending sort key `i%11`. Feature order is reversed. Weights are `(j+1)/8` and bias is `-0.375`. Exactly three quarters of the rows survive.

- `conversion` starts with a prepared source frame. Timing includes filtering, stable sorting, both matrix exports, target and ID extraction, tensor allocation, evaluation, synchronization, and full matrix tensor readback. It emits output regions one through five, with count `3 + N * (2 * D + 2)`. Weight, bias and target tensors are allocated and evaluated too.
- `prepared` starts with evaluated tensors. Timing includes affine prediction, residual calculation, evaluation, synchronization, dimension/dtype checks and complete prediction/residual readback. It emits actual tensor dimensions/dtype, predictions and residuals, with count `3 + 2 * N`.
- `pipeline` starts with decoded concrete arrays. Timing includes source dataframe construction and the complete conformance execution, including the mutation checks. It emits all eight regions.

Swift currently creates a fresh device stream around each invocation, so stream setup is timed in each stage. These scopes do not isolate kernel throughput, and pipeline time includes validation and mutation readback that conversion and prepared omit. Do not interpret pipeline minus conversion minus prepared as a measured overhead term.

## API evidence and verification

`Sources/SwiftDataFrame/Core/DataFrame+Matrix.swift` supplies `toFeatureMatrix`, `toFlatFeatureMatrix`, and `toTargetVector`. `DataFrame.swift` supplies filter, sort and column replacement. The MLX Swift Double array initializer is unavailable because its convenient alternative downcasts to Float32. Float64 allocation here uses the public typed unsafe-buffer initializer in `MLXArray+Init.swift`. MLX CPU matmul has an explicit Float64 dispatch in `Source/Cmlx/mlx/mlx/backend/cpu/matmul.cpp`. The Metal backend does not support Float64. Both validators reject that combination.

Six Python tests pass, including all 18 combinations of dtype/device, width and sweep stage at 128 input rows. The tests compare every output to the independent Decimal scalar oracle, verify repeated calls, reject malformed inputs and embedded answers, and check stable row alignment. Both Swift files pass standalone typechecking against existing library modules with the local worker/error stubs. The parent must build and run the integrated Swift worker before claiming Swift CPU or GPU conformance.
