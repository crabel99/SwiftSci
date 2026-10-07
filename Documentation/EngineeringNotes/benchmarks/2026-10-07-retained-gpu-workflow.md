# Retained input regression workflow

Date: 2026-10-07

## Decision

Retaining a standardized GPU input helps repeated prediction in this workflow, but it costs setup time and increases peak memory in the current implementation. Keep the experiment local. The next candidate is direct packing from prepared columns into shared storage, avoiding the temporary row-major Float array. Measure that change before deciding which production callers should use retention.

Implementation commit `df2388f1e31a546c9442b47cf8ab10466b1bd588` is on `codex/retained-memory-accounting-trial`, based on `4193a7cc7ce18e32f33190b6ea15540f741a098f`. It adds a package-only prediction entry and shares the existing GPU matmul-plus-bias kernel with the public MLX overload. Existing callers continue to use their current path. No push or PR change was made.

## Workflow

Use the public StandardScaler and CPU ordinary least squares APIs to fit 512 training rows with 64 features. Construct a GPU model from the learned coefficients. Generate independent held-out inputs with a different deterministic seed, and transform them using only training statistics.

Compare the existing prepared-batch prediction API with a retained GPU input for 64 or 65,536 held-out rows. Run either one prediction or sixteen. Both paths keep every returned Double prediction array alive through the measured memory snapshot, then verify every batch.

The public path checks finite values and packs Double columns into a shared Float matrix on every call. The retained path validates and packs once. The package-only prediction entry snapshots Double model parameters before awaiting the input actor, creates its small MLX parameter arrays within that actor, and returns a completed Double result. This avoids transferring non-Sendable MLX arrays between actors. Parameter changes during suspension affect subsequent calls.

The benchmark includes the retained entry's per-call parameter-array construction. It does not duplicate the prediction algorithm. Column names are still supplied separately by the caller, and generic retained storage does not encode finite-value validation. A production adapter should own validated schema and storage together.

## Timing and memory contract

Training and fixture generation are excluded. The GPU model is warmed on training-sized data before timing. Preparation includes transforming held-out data and constructing retained storage where selected. Total workflow time is preparation time plus the prediction phase. The memory snapshot between those phases is excluded.

Full numerical verification and cleanup occur after the measured memory snapshot. The two modes reserve the same conservative 128 MiB work allowance; retained construction acquires and transfers its additional input grant. The budget is an admission estimate, not an RSS cap. Caller-owned data and fitted model state are not globally intercepted by it.

Five fresh processes per mode and case give 40 measured workers. Mode order alternates. Workers run serially with a 90-second timeout and a system memory-pressure check before each start. Build coverage is disabled and the Mach-O guard confirms the benchmark is uninstrumented. Metal settings use safe math and precise FP32 functions.

## Results

Times are median total workflow milliseconds, including held-out preparation. A ratio above one favors retention. Memory columns are median process high-water RSS sampled before full validation.

| Held-out rows | Predictions | Scoped ms | Retained ms | Ratio | Scoped peak MiB | Retained peak MiB |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 64 | 1 | 0.682 | 1.078 | 0.63 | 24.53 | 24.94 |
| 64 | 16 | 10.101 | 6.254 | 1.62 | 24.72 | 25.05 |
| 65,536 | 1 | 21.691 | 30.313 | 0.72 | 107.81 | 147.36 |
| 65,536 | 16 | 194.041 | 37.748 | 5.14 | 115.67 | 153.45 |

For large inputs and sixteen predictions, retention reduced median workflow time from 194.041 ms to 37.748 ms, about 5.14 times faster. Peak RSS increased from 115.67 MiB to 153.45 MiB, about 37.78 MiB more.

For one large prediction, the existing path won at 21.691 ms versus 30.313 ms. Retained preparation took 29.062 ms versus 9.946 ms, while its prediction itself was faster. The setup cost must be amortized across reuse.

Small repeated prediction also improved in this run, while single prediction favored the existing path. This is a different comparison from the earlier import-only kernels: the public workflow also pays per-call validation, packing, and buffer/device acquisition. Do not attribute the full speedup to GPU arithmetic or the memory-owner abstraction.

The retained preparation helper currently builds a row-major Float array with flatMap, then copies it into Metal storage. That temporary array, its construction capacity, the shared allocation, and allocator residency can contribute to peak memory. The measurements do not assign every extra resident byte to a specific allocation. Direct packing is a candidate to test, not an established memory saving.

## Correctness and cleanup

- 220 focused Release tests passed, with no failures or skips. Three new tests cover training-only scaling, held-out accuracy, parity with public prediction, schema and shape errors, cancellation, concurrent calls, refitting, and output lifetime after closing the input.
- All 40 measured workers passed the analytic raw-data oracle. Maximum absolute error was `4.76837158203125e-7`, below the predeclared `1e-4` Float32-to-Double bound.
- Complete output hashes and learned-parameter hashes matched across modes and repetitions. Every returned prediction batch matched the final batch in its worker.
- Every worker returned reservations to zero and reported zero MLX active bytes after closing input and model owners. Explicit cache clearing then returned cache bytes to zero.

Prepared source arrays and prediction arrays remain alive during post-close snapshots. Those snapshots cannot establish that all resident process memory was returned to the operating system. MLX active memory counts imported external storage while its wrapper lives, so it overlaps explicit shared-payload accounting.

The broader SwiftSci suite and sanitizers were not rerun for this experiment. The benchmark is a deterministic regression workflow, not validation of arbitrary datasets or a formal performance baseline.

## Review and evidence

Standards review found no actionable issue. Behavior review found that the initial total timer included memory-sampling overhead. The final implementation excludes that interval. Review found no parameter-transfer or GPU-completion defect.

Hardware is Apple M4 Max with 128 GiB unified memory, macOS 27.0 build 26A428. The binary targets macOS 14; no macOS 14 runtime was tested. The MLX fork remains pinned to `4657976edcdd2c60642424985d474b45ddddb390`.

Final binary SHA-256: `60eaa474af59b3935b1bea34136c8ce7727fcfd8cb7e520090d686f0b295a417`.

Replay instructions are in `Benchmarks/RetainedGPUTrial/README.md` on the implementation branch. Local logs and test bundles are under `~/local-ai/spl/swiftsci/retained-gpu-workflow-20261007/`. `comparison` contains the final five-round measurement; `smoke` is preliminary.

The notes branch preserves the [summary](../archive/2026-10-07/retained-gpu-workflow/summary.json), [samples](../archive/2026-10-07/retained-gpu-workflow/samples.json), and [provenance](../archive/2026-10-07/retained-gpu-workflow/provenance.json). Engineering findings remain separate from implementation changes.
