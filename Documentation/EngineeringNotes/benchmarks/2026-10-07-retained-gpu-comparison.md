# Retained GPU input comparison

Date: 2026-10-07

## Decision

Keep retained inputs as a candidate for repeated GPU work on large, immutable inputs. The measured large cases favor retaining the imported input, especially when it avoids an offset copy. Small cases do not justify replacing the scoped path universally.

Commit `4193a7cc7ce18e32f33190b6ea15540f741a098f` adds the benchmark and its replay instructions to local branch `codex/retained-memory-accounting-trial`, based on GPU ownership commit `e859aa3128083846d58f568c2fcbe8daa2f58efd`. Production source is unchanged. Nothing was pushed and no PR was changed.

## Protocol

Compare `ScopedGPURead.withBuffer` and `RetainedGPUInputTrial` with the same caller-owned Float32 values, page-rounded Metal allocation, admission estimates, GPU arithmetic, and output checks. Both copy source values into shared storage once. The retained path imports and constructs its logical view at setup. The scoped path constructs an MLX input on each read.

Fixtures have 64 columns and either 64 or 65,536 rows. Each runs an affine transform and a dense projection to eight columns. An aligned variant starts at element zero; an offset variant starts at element one. Untimed native-pointer checks confirm that the scoped aligned variant shares its input and the offset variant copies. The retained implementation checks pointer identity for its imports and views.

Each worker performs a tiny GPU initialization, measures input construction, warms its actual kernel twice, and times 32 completed operations. Timing includes reduction and scalar readback, with each operation completed before the next begins. Projection constructs the same small weight matrix in both paths. Caller-array generation, full output validation, and cleanup are outside the construction and repeated-operation timing.

Five independent processes run per mode and case, with modes alternating. There are 80 measured processes. Every process has a 90-second timeout, and the controller checks system memory pressure before starting the next worker. Only one native worker runs at a time.

The final executable has no coverage instrumentation. Build configuration is arm64 Release with safe Metal math and precise FP32 functions. The machine is an Apple M4 Max with 128 GiB unified memory, running macOS 27.0 build 26A428. The macOS deployment target is 14; this does not validate a macOS 14 runtime. The pinned MLX fork revision is `4657976edcdd2c60642424985d474b45ddddb390`.

## Results

Times are medians for all 32 timed reads, in milliseconds. The ratio is scoped time divided by retained time, so values above one favor retained reuse. RSS columns are median process high-water measurements taken before full validation.

| Rows | Layout | Kernel | Scoped ms | Retained ms | Ratio | Scoped peak MiB | Retained peak MiB |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 64 | aligned | affine | 10.618 | 9.974 | 1.06 | 23.22 | 23.67 |
| 64 | aligned | projection | 12.044 | 10.984 | 1.10 | 23.48 | 23.89 |
| 64 | offset | affine | 10.342 | 9.991 | 1.04 | 23.33 | 23.77 |
| 64 | offset | projection | 9.503 | 10.384 | 0.92 | 23.81 | 24.02 |
| 65,536 | aligned | affine | 24.510 | 13.155 | 1.86 | 55.42 | 55.70 |
| 65,536 | aligned | projection | 20.242 | 13.931 | 1.45 | 55.78 | 55.91 |
| 65,536 | offset | affine | 22.829 | 12.646 | 1.81 | 87.36 | 56.19 |
| 65,536 | offset | projection | 21.082 | 19.492 | 1.08 | 71.47 | 56.25 |

The large aligned affine and projection cases improve repeated-operation time by about 46% and 31%. Their median peak RSS is effectively unchanged, within about 0.3 MiB. Those scoped inputs already share their storage; the trial removes repeated import and wrapper work while adding actor dispatch.

For large offset inputs, the affine median improves by about 45% and projection by about 8%. Median peak RSS falls by about 31.2 MiB and 15.2 MiB. The reduction is consistent with avoiding the verified copy path and reducing cached temporary allocations. These RSS differences do not establish the exact ownership of every resident page.

Small inputs show mixed results and overlapping process timing ranges. The offset projection median is about 9% slower with retention. There is no reliable general small-input performance win here.

Construction is a separate cost. Large retained construction medians are about 0.07 to 0.82 ms above scoped construction; small retained construction is about 0.69 to 1.35 ms higher. Both paths spend roughly 19 to 21 ms in measured construction on this machine. Do not apply the repeated-read ratios to a complete one-shot workflow.

The full ranges and individual samples are preserved. These are exploratory local measurements under ordinary desktop conditions, not a formal performance baseline or a statistical claim about all machines.

## Numerical and release checks

All 80 measured workers passed full-array comparison with an independent CPU oracle. Dyadic fixture values avoid ambiguity from decimal rounding. Output SHA-256 values matched between modes and all repetitions for each case. All timed scalar checksums were finite and repeatable.

All 80 workers returned reservation counts to zero and reported zero MLX active bytes after closing the input. After the separate cache-clear step, both MLX active and cache counters were zero. The largest measured pre-validation peak RSS across workers was 87.72 MiB.

The 217 focused Release tests from the preceding ownership commit remain the unit-test evidence for unchanged production and trial ownership code. This turn built the package for testing and exercised the benchmark; it did not rerun the full unit suite or sanitizers.

## Memory interpretation

This MLX version counts an imported external buffer in `activeMemory` while its MLX wrapper lives. The pinned native `MetalAllocator.make_buffer` increments active memory by buffer length, and `release` subtracts it. The retained wrapper stays alive between calls. The scoped wrapper is destroyed between calls, so its external input is absent from that counter at the sampled boundary even though the caller's Metal buffer still exists.

The explicit `payload_bytes` and retained `mlx_active_bytes` fields overlap. Adding them would double-count the shared payload. Process RSS, explicit payload, and MLX active/cache counters answer different questions and are reported separately.

The admission budget covers participating estimates. It is not an RSS cap and excludes the caller's original array. The benchmark uses the same construction and retained estimates in both modes, plus a separate 64 MiB work estimate. Full validation arrays remain alive during post-close snapshots, so post-close RSS cannot establish input-buffer reclamation. Zero reservations and native active counts support ownership cleanup, not a claim that every resident page returned to the operating system.

## Review and measurement corrections

The preflight guard rejected an initially instrumented executable. No timings from it were collected. The benchmark was rebuilt through Xcode's test-build action with coverage disabled, then checked again at the Mach-O section level.

The initial smoke run and code review exposed an incorrect assumption that MLX counters exclude imported storage. Documentation and provenance were corrected before the measured runs. The driver now uses validation that remains enabled under Python optimization. Metal resource hashes are verified, while expected compiler settings are labeled as expectations and the actual build command/log is retained separately.

An initial 80-process measurement used only the scoped helper's alignment flag. The final run supersedes it with native-pointer verification outside timing. Standards review found no actionable rule or smell violation. Behavior review's accounting and pointer-evidence concerns are resolved.

## Evidence and next step

Final binary SHA-256: `2ba4f529a96ef0392f50198f112a84bbfd724aaab3f9bbd89391016fcce28cc3`.

Replay instructions live in `Benchmarks/RetainedGPUTrial/README.md` on the local implementation branch. Local raw evidence is in `~/local-ai/spl/swiftsci/retained-gpu-comparison-20261007/`. The authoritative measurement directory is `final-comparison`; `smoke-v2` and `comparison` are preliminary evidence.

This engineering-notes branch retains the final [summary](../archive/2026-10-07/retained-gpu-comparison/summary.json), [samples](../archive/2026-10-07/retained-gpu-comparison/samples.json), and [provenance](../archive/2026-10-07/retained-gpu-comparison/provenance.json). Full build logs and native worker output remain local.

Next, test one representative repeated-use model or preprocessing workflow with retained inputs and equivalent output ownership. Measure its construction, steady-state work, and close behavior before choosing which production callers to migrate. Preserve the scoped path for one-shot work until that workload provides evidence for a change. This trial does not establish results for strided tensors, mutation, large LLMs, or concurrent GPU scheduling.
