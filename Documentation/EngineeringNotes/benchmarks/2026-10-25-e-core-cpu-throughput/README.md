# Verified E-core application benchmark profile

Implementation commit `af4e2cd45b53cf1a76253dc174c508e5459b3cf7` on local branch `codex/e-core-cpu-throughput` builds on `624fc7e08638b0a80647753d8f8dbe44eb37ef80`. The user selected this rule on 2026-10-25: require E-core application execution and report kernel P/E time separately. Nothing is pushed.

## Qualification result

The committed controller completes 24 smoke queues, 192 jobs, and 48 full native-output checks across SwiftSci optional, SwiftSci compact, pandas C, pandas via explicit-schema Arrow, Polars, and DuckDB plus Arrow. All 96 worker intervals and 24 controller intervals record zero P-core application time. All worker counter boundaries pass the idle-thread checks. Kernel P-core execution remains recorded and allowed.

This validates the selected placement rule and the reusable controller path. It does not qualify performance. Smoke never establishes a ranking, and its CPU/elapsed repeatability controls also fail. These failures stay visible; no limits, case counts, memory ceiling, caller counts, or schemas change.

## Implementation

The launcher builds a small C reader against the installed SDK, using rusage_info_v6 and proc_taskinfo instead of guessed structure offsets. It demonstrates positive P-core counters before starting the comparison under one inherited background QoS clamp. The calibration is bound to the OS boot session and records source, compiled-reader, and probe fingerprints.

Each worker must have zero running threads before and after its resource snapshot. A bounded wait fails if the worker does not become idle. The controller uses its own snapshots after all queue work and controller threads have completed. The independent audit binds counters to actual worker/controller PIDs, checks positive work and monotonic/consistent counters, rejects any P-core user time, and recomputes the four time components from raw Mach ticks.

QoS is a scheduling preference, not affinity. Acceptance depends on observed counters. Kernel time is classified separately into P and E time; it does not fail the application-only rule. Core counters bracket queue work plus boundary bookkeeping and are not an exact partition of the older charged_cpu_ns interval. Raw values and the Mach timebase remain preserved. CPU time is not measured energy.

The source README documents the new compare_e_cores.py entry point and separate audit. Existing unrestricted plans remain identifiable as unverified for core class. Neither historical results nor the earlier failed Arrow panel gains placement evidence retroactively.

## Test evidence

The 29 focused CPU tests pass. The complete controller discovery executes 255 tests: 251 pass and four require Metal opt-in. Those four pass separately with SWIFTSCI_MLX_TEST_GPU=1. All 255 execute successfully across the two configurations. Tests run after CPU timing. The C reader and positive-P probe compile with -Wall -Wextra -Werror.

New tests cover E-only application time with allowed P-kernel time, P-user rejection, unsupported zero P calibration, invalid/negative counters, wrong PIDs, incomplete/duplicate worker receipts, idle-boundary rejection, and timeout. A live negative-path test confirms a rejected queue preserves its raw counters and closes its worker.

All 51 measured Swift source hashes are unchanged from library head 58db37c4b3c97b287186c377f76f89abcbbb0b0d, which previously passed 447 Debug and 447 Release dataframe tests. No new native Swift or hosted CI run is claimed.

## Remaining performance work

The formal six-condition E-core panel remains to run. Its fixed protocol has 12 rotated rounds, 144 queues, 64 jobs per queue, four callers, the same 8 GiB sampled worker-RSS ceiling, independent output hashes, and unchanged twin limits. The first smoke gives a rough two-hour runtime forecast for that work on four E cores. This is planning, not a scaling result or permission to retune the work.

The short committed smoke has the following control failures:

| Condition | Metric | Twin ratio |
| --- | --- | ---: |
| swiftsci_optional | elapsed_ns | 2.431 |
| swiftsci_compact | elapsed_ns | 1.200 |
| polars | elapsed_ns | 0.494 |
| duckdb | charged_cpu_ns | 1.245 |
| pandas_arrow | charged_cpu_ns | 1.181 |
| pandas_arrow | elapsed_ns | 0.823 |

The initial pre-commit smoke is retained separately with its 11 exact controller-source snapshots. It predates the idle-boundary guard; the committed smoke above is the validation of that stronger guard. The earlier Arrow panel and its RSS failure remain in the prior engineering-notes record.

## Evidence and reproduction

[Summary](summary.json), [source provenance](provenance.json), [validation](validation.json), [accepted process intervals](core-intervals.json), and the [experiment archive](experiment.tar.gz) preserve exact measured sources, raw before/after counters, calibrations, output checks, runtime metadata, controls, and test logs. The archive excludes binaries, raw datasets, and caches.

Restore the recorded worker and input contracts by SHA256. Run compare_e_cores.py under normal scheduling with the documented comparison arguments and --pandas-arrow --smoke. It compiles and calibrates before applying the clamp to the child controller. Audit the panel subdirectory with compare.py --audit. Remove --smoke only for the full fixed panel.

Primary API context: [Apple Recount](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/doc/observability/recount.md), [SDK process task fields](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/sys/proc_info.h), and [Apple scheduling guidance](https://developer.apple.com/news/?id=vk3m204o). Engineering conclusions remain on codex/engineering-notes.
