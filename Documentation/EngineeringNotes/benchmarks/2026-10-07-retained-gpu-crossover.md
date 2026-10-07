# Retained GPU crossover and compiler investigation

Date: 2026-10-07

## Decision

Retain an explicit reuse choice. The measured crossover depends on reuse count and input size, with noise around near-equal cases. The experiment does not support automatic routing from a single row threshold.

Benchmark commit `ad577702e56b983a40fde8856a3e8b6afb85bf51` on `codex/retained-memory-accounting-trial` extends the workflow sweep and adds separate packing diagnostics. Its parent is `6e8ad19ca037fd4b7bbb2b7717428427b6975f6b`. Production code is unchanged. No branch was pushed.

## What creates the difference

Scoped prediction validates and packs the entire input, allocates a shared buffer and imports it into MLX for every prediction. Retained prediction performs this input work once and keeps the owner alive across calls. The retained path also pays admission transfer, ownership setup and an input actor transition. It rebuilds small model-parameter arrays on each prediction.

For small inputs, fixed work and scheduling variation matter more than processing the values. Large inputs spend more time traversing Double columns and packing Float32 rows. Avoiding that repeated work explains the observed reuse advantage. Both paths use the same prediction kernel and return completed Double arrays.

A simple cost model is `scoped = S + K * p_s` and `retained = R + K * p_r`. Retention pays off when `K > (R-S)/(p_s-p_r)`, if the denominator is positive. Setup, per-call time and first-call effects depend on shape and runtime state. The formula organizes the investigation; it does not turn these measurements into a universal threshold.

## Qualified crossover sweep

The final run contains 500 fresh serial workers: ten row counts, five reuse counts, two modes and five rounds. Every case uses 64 features. The existing training-only preprocessing and held-out oracle protocol is unchanged. Timing includes held-out transformation, retained preparation where selected and completed predictions. Fitting, fixture generation, full verification, cleanup and intervening memory snapshots remain outside timing.

Each cell shows the ratio of scoped median workflow time to retained median workflow time, then the number of paired rounds won by retention. Ratios above one favor retention. Pairs are adjacent serial processes in rotating order, not simultaneous observations. Ratios of separate medians and counts of paired wins can disagree in noisy cases.

| Rows | 1 prediction | 2 predictions | 4 predictions | 8 predictions | 16 predictions |
| ---: | --- | --- | --- | --- | --- |
| 63 | 0.67; 1/5 | 0.92; 1/5 | 1.31; 4/5 | 2.02; 3/5 | 1.53; 5/5 |
| 64 | 0.70; 1/5 | 0.93; 1/5 | 1.05; 4/5 | 1.61; 5/5 | 1.29; 5/5 |
| 65 | 0.65; 0/5 | 0.94; 2/5 | 1.10; 4/5 | 1.86; 5/5 | 1.18; 5/5 |
| 256 | 0.62; 0/5 | 0.93; 2/5 | 1.25; 4/5 | 1.49; 4/5 | 1.55; 4/5 |
| 1,024 | 0.71; 0/5 | 1.03; 3/5 | 1.26; 4/5 | 1.88; 5/5 | 2.05; 5/5 |
| 4,095 | 0.88; 0/5 | 0.83; 4/5 | 1.68; 5/5 | 1.98; 5/5 | 2.86; 5/5 |
| 4,096 | 0.86; 1/5 | 1.19; 5/5 | 1.65; 5/5 | 2.29; 5/5 | 3.21; 5/5 |
| 4,097 | 0.87; 0/5 | 1.15; 5/5 | 1.57; 5/5 | 2.01; 5/5 | 3.25; 5/5 |
| 16,384 | 0.94; 0/5 | 1.37; 5/5 | 2.18; 5/5 | 3.26; 5/5 | 5.06; 5/5 |
| 65,536 | 0.99; 2/5 | 1.46; 5/5 | 2.53; 5/5 | 4.13; 5/5 | 6.77; 5/5 |

Small inputs generally lose at one or two predictions and become competitive around four. At 16,384 and 65,536 rows, retention won all five paired rounds from two predictions onward. The 4,095-row neighbor remained noisy at two predictions, while its larger reuse cases all favored retention. These observations describe this kernel and machine. They are not a calibrated routing policy.

An earlier three-round sweep and an earlier five-round sweep are retained locally as preliminary evidence. Their near-boundary results also varied. The qualified tables above use only the final saved drivers and fingerprints.

## Alignment is a real branch, but does not explain the whole crossover

The machine reports 16 KiB pages. With 64 Float32 columns, each 64-row increment produces a whole-page byte extent. Scoped import checks both address alignment and extent. The phase workers verified native MLX pointer sharing at 64, 4,096 and 65,536 rows, and verified a distinct pointer at 63, 65, 4,095 and 4,097 rows. Retained construction pads its allocation and checks its own shared pointer before publication.

This confirms the copy fallback exists at neighboring sizes. It does not establish that the aligned case always has lower end-to-end time. The workflow samples do not show a clean alignment-only performance step, and kernel/runtime variation also changes with shape.

## Diagnostic phases

The final phase run contains 105 serial workers: seven shapes, three packing implementations and five rounds. The table below uses the direct-access diagnostic, with median milliseconds. These are diagnostic phases, not timers inserted into production prediction.

| Rows | Scoped import shared | Validation | Later device/allocation | Zeroing | Packing | Import/completion |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 63 | false | 0.002 | 0.131 | 0.002 | 0.005 | 0.140 |
| 64 | true | 0.002 | 0.118 | 0.002 | 0.005 | 0.144 |
| 65 | false | 0.002 | 0.118 | 0.003 | 0.005 | 0.150 |
| 4,095 | false | 0.082 | 0.124 | 0.060 | 0.435 | 0.208 |
| 4,096 | true | 0.083 | 0.132 | 0.063 | 0.486 | 0.151 |
| 4,097 | false | 0.083 | 0.124 | 0.056 | 0.503 | 0.216 |
| 65,536 | true | 1.126 | 0.146 | 0.815 | 8.822 | 0.231 |

At 65,536 rows, packing took about 8.8 ms, finite validation 1.1 ms, zeroing 0.8 ms, later allocation 0.15 ms and import/completion 0.23 ms in this diagnostic. Packing is the largest measured component. The measurements do not distinguish memory bandwidth, cache misses, address calculation, bounds checks and scalar conversion within that component.

Zeroing touches the destination before packing. The real scoped loop initializes its destination while packing, so this phase separation changes first-touch behavior. The retained constructor runs after the scoped probe, which also changes cache and allocator state. Do not add these medians and present the sum as an instrumented production call.

The field `first_device_setup_ms` is a historical diagnostic name. It measures the first explicit Metal device lookup, page-buffer allocation, zeroing and cleanup after MLX warmup. It does not measure cold GPU startup. Its roughly 19 ms values must not be compared directly with the warmed workflow's per-call allocation cost. Review caught and corrected this interpretation in the documentation and provenance.

## Compiler evidence

Release object code confirms three implementation details:

- The actual scoped packing loop contains an indirect `blr x26` call for each value, followed by scalar `fcvt s0, d0` conversion and a store. LinearRegression calls the separately compiled ScopedGPURead implementation.
- The actual retained direct-packing loop calls `PreparedNumericBatch.columnCount.getter` within its inner loop. Relocations identify the target, rather than inferring it from source alone.
- The diagnostic callback is specialized within its own module, so its inner loop has no indirect callback call. Its timing is not a measurement of the actual library callback overhead. The hoisted-dimension diagnostic calls the getter once before its loops.

Both inspected library packing loops use scalar conversion at these sites. This is evidence about these generated loops, not a claim that Swift or the rest of the library fails to use SIMD.

The scoped regression accessor already reads compact column values directly. The earlier suggestion that this path used nullable-value access was incorrect.

Removing repeated getter calls did not produce a repeatable large-input gain in the diagnostic. At 65,536 rows, direct packing measured 8.822 ms and hoisted packing 8.650 ms in the qualified run. The earlier five-round diagnostic measured 9.378 ms and 9.528 ms respectively. That reversal does not support a claimed optimization. Source simplification and fewer calls alone are insufficient evidence of an end-to-end benefit.

Optimized symbols, relocation-aware disassembly and object fingerprints are preserved with the evidence. Archived text has trailing whitespace removed; raw tool output remains local. They tie these findings to the tested build rather than a hypothetical compiler result.

## Validation and limits

All 224 focused Release tests passed, with no failures or skips. All 500 qualified workflow workers passed their complete output, parameter-hash, oracle and cleanup checks. Maximum oracle error was `4.76837158203125e-7` against the fixed `1e-4` bound. All 105 phase workers passed full packing bit checks, native-pointer checks, retained readback and cleanup checks. The actual retained owner returned its budget reservation, and active MLX bytes and explicitly cleared cache bytes were zero at the recorded checkpoints.

This does not prove absence of all leaks or complete return of RSS to the operating system. Caller arrays remain alive at some checkpoints. The full library suite and sanitizers were not rerun. The sweep holds feature width, kernel and hardware fixed and does not establish a threshold for other algorithms, thermal states or workloads.

Hardware is Apple M4 Max with 128 GiB unified memory, macOS 27.0 build 26A428. The Release arm64 binary targets macOS 14; no macOS 14 runtime was tested. The pinned MLX Swift fork remains `4657976edcdd2c60642424985d474b45ddddb390`. Safe Metal math and precise FP32 settings are captured in the build command. The binary guard confirms coverage instrumentation is absent.

Binary SHA-256: `87f4cfa98e805eb20eac197c1a4d2b3e5adde91c6a33e8d0e2fdc727e18bec1c`.

## Next experiment

Test packing layouts at the same public workflow boundary. Compare the present row-wise traversal of separate columns with a blocked conversion/transpose that preserves contiguous column reads and row-major GPU output. Retain scalar bit equivalence and full workflow validation. Keep dimension hoisting as a small candidate rather than assuming it fixes the bottleneck. Any change to scoped specialization must be measured across the actual module boundary.

Before adding automatic routing, vary feature width and kernel cost, separate first prediction from later predictions, and repeat near the boundary under controlled machine load. Reuse count should remain an explicit caller decision while that evidence is incomplete.

## Evidence locations

Replay commands are in `Benchmarks/RetainedGPUTrial/README.md` on the implementation branch. Local logs and test bundles are under `~/local-ai/spl/swiftsci/retained-gpu-crossover-20261007/`.

The engineering-notes archive contains [workflow summary](../archive/2026-10-07/retained-gpu-crossover/qualification-sweep/summary.json), [workflow samples](../archive/2026-10-07/retained-gpu-crossover/qualification-sweep/samples.json), [phase summary](../archive/2026-10-07/retained-gpu-crossover/qualification-phases/summary.json), and [compiler fingerprints](../archive/2026-10-07/retained-gpu-crossover/compiler-final/fingerprints.json). Provenance accompanies each measurement set. `qualification-sweep`, `qualification-phases` and `compiler-final` are the authoritative artifacts for this report.
