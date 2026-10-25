# Local processor-class qualification

Machine: Apple M4 Max, 12 performance cores and 4 efficiency cores. OS: macOS 27.0.1, build 26A434. These are diagnostic placement trials, not comparative performance results.

## Public controls and observed execution

The same background QoS clamp launches the diagnostic controller and is inherited by all worker processes. The libraries retain their native internal parallelism. No global scheduling or power setting changes. The clamp is a scheduling preference, not an affinity guarantee.

A one-second default-policy probe demonstrates working P-core time, instruction, and cycle counters. The same probe under a background clamp reports zero P-core usage. The corrected records include a Mach timebase of 125/3 nanoseconds per tick. The initial mislabeled probe is retained and explained separately.

The first real Swift optional queue fails strict acceptance because it records nonzero P-core kernel time. That failed trial remains in core-placement-validation. A separate observation-only trial then collects every condition without accepting any performance result.

## Cross-library observation

Four worker processes complete eight mixed reference jobs per condition. The controller reads each child PID through proc_pid_rusage V6 after its stats response. These snapshots cover the process task and its native threads. They bracket the queue plus boundary bookkeeping. The controller interval also includes worker startup and cleanup.

| Condition | Worker intervals | P-core user ticks | P-core kernel ticks | All worker user time on E cores | Strict total E-only, including controller |
| --- | ---: | ---: | ---: | --- | --- |
| swiftsci_optional | 4 | 0 | 7249 | True | False |
| swiftsci_compact | 4 | 0 | 0 | True | False |
| pandas | 4 | 0 | 351 | True | False |
| polars | 4 | 0 | 0 | True | True |
| duckdb | 4 | 0 | 1369 | True | False |
| pandas_arrow | 4 | 0 | 70757 | True | False |

All 24 worker intervals record E-only application CPU time: True. Controller application time is also E-only in all six conditions. Positive P-core kernel counters prevent a strict total-E-only claim for five conditions. This proves observed accounting for these bounded intervals only. It does not guarantee placement of later work.

## Acceptance remains undecided

The user requires common processor types across library runs. A pending clarification distinguishes E-only application execution with kernel P/E accounting reported separately from strict E-only execution of all charged CPU work. The latter currently fails on this Mac. No zero cross-type tolerance is relaxed, and no unsupported hard-affinity claim is made.

The next formal comparison must capture and audit the selected class for every participating worker and the controller. Mixed, missing, unsupported, or inconsistent counters must fail acceptance. A correct global policy label, configured pool size, or a few profiler samples is insufficient. Kernel P/E usage must remain visible even if application-only placement becomes the accepted rule.

P/E placement is not proven to explain the separate pandas RSS-control failure. Both issues must remain visible. The earlier six-condition full panel lacks placement evidence and remains unqualified.

## Evidence

The archive contains core-counter-reader.c, core-counter-probe.c, corrected positive-P and background JSON records, the strict failed trial, observation-only script and per-queue raw receipts. The source review cites the primary Apple implementations in core-placement.md. A short System Trace of an inert child records successfully; its table of contents is preserved, while the trace bundle is omitted from the archive. No scheduler trace of these library queues is claimed.
