# Mixed CPU queues: memory savings survive contention

The local experiment is on `codex/dataframe-mixed-throughput`, commit `632fdf75427ebe53f64f05dd0e4509dced1fe517`. It starts from repaired compact-review head `d205cb71c07bb5a94772393571371632cdd00e9e`. Neither existing PR branch changed. No branch was pushed.

The panel completed 128 queues and 2,048 jobs. Every planned queue has the same 16 jobs. Both storage modes match the independently checked native-bit reference fingerprints before and after the panel. The [audit](audit.json) passes all predeclared identical-binary controls.

## Compact storage saves resources without demonstrating more throughput

At eight concurrent callers, compact storage uses 33.0% less sampled worker RSS and 3.6% less charged CPU per job. Throughput differs by 0.1%, which this experiment treats as essentially the same. Resource savings do not automatically increase throughput when memory capacity is not the limiting constraint.

The memory savings appear at every tested caller count. Observed CPU differences at one, two, and four callers are small and remain descriptive. A passing 10% drift control is not a confidence interval for a 1% difference.

| Callers | Storage | Jobs/min | CPU ms/job | Peak RSS MiB | Retained RSS MiB | Resident MiB-seconds |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | optional | 667.5 | 181.77 | 896.7 | 770.3 | 1038.6 |
| 1 | compact | 655.5 | 182.90 | 655.9 | 531.5 | 753.0 |
| 2 | optional | 1177.3 | 186.66 | 1670.4 | 1540.9 | 984.4 |
| 2 | compact | 1171.6 | 184.25 | 1179.9 | 1045.9 | 698.0 |
| 4 | optional | 1859.4 | 202.23 | 2859.6 | 2608.4 | 1022.2 |
| 4 | compact | 1821.2 | 198.72 | 2022.8 | 1772.0 | 730.4 |
| 8 | optional | 2507.7 | 231.09 | 4268.9 | 4268.9 | 1018.9 |
| 8 | compact | 2510.5 | 222.73 | 2858.6 | 2858.6 | 727.8 |

Values are medians of 16 queues per storage and caller count, pooling primary and identical-binary twin labels. Jobs have different sizes, so jobs/min applies only to this fixed queue composition. CPU includes worker user and system time plus controller CPU within the queue. Resident MiB-seconds estimates memory occupancy over queue time.

Increasing callers from one to eight raises throughput about 3.8 times. It also raises CPU per job about 27% with optional storage and 22% with compact storage. More concurrency therefore buys elapsed-time improvement at a processor-work cost. These measurements do not identify a cache, compiler, or scheduling mechanism.

## Queue waiting and response time

All jobs arrive together. Response runs from initial submission through waiting, execution, release, and receipt. Each queue contains only four instances of each case, so its nearest-rank p95 is the largest of four observations. The table reports medians of those per-queue p95 values. It is not a steady-state service-level estimate.

| Callers | Storage | Air read p95 ms | Air sort-matrix p95 ms | Energy read p95 ms | Energy sort-matrix p95 ms |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | optional | 1354.8 | 1214.3 | 1202.8 | 1369.7 |
| 1 | compact | 1383.4 | 1240.3 | 1227.2 | 1391.7 |
| 2 | optional | 617.4 | 556.5 | 612.0 | 815.4 |
| 2 | compact | 619.7 | 553.1 | 622.8 | 819.4 |
| 4 | optional | 291.5 | 291.5 | 414.5 | 516.3 |
| 4 | compact | 294.5 | 295.5 | 412.1 | 527.1 |
| 8 | optional | 104.2 | 25.7 | 202.5 | 382.8 |
| 8 | compact | 106.2 | 28.8 | 203.4 | 382.4 |

## Scope and limits

The air-quality input contains 35,064 rows. Household energy contains 2,075,259 rows. Every job reads a complete schema with the same CSV bytes and null tokens. Sort-matrix adds a stable ascending, missing-last full-frame sort and an owned contiguous row-major Double matrix. Output release is included.

The [earlier reference study](../2026-10-23-csv-sort-closeout/README.md) independently checked these output contracts against pandas, Polars, and DuckDB. This panel compares optional and compact storage within the latest SwiftSci source. It does not compare those external engines concurrently, and it does not compare against the older historical source checkpoint.

Each batch starts fresh persistent workers before timing. The first public operation in each worker remains timed. Jobs run through a shared dynamic queue with one active job per caller process. Native internal parallelism remains enabled. No core affinity, worker-thread cap, GPU workload, or Neural Engine workload is introduced.

Full hashes run outside queue timing before and after the panel. Timed results receive row-count, column-order, type, and matrix-size checks. They are not individually fully hashed. Process startup is excluded. Preflight and repeated reads precede measurement, so these are not controlled cold-disk timings.

The sampler sums live worker residency at approximately 10 ms intervals. The largest observed gap is 28.3 ms, so short peaks can be missed. RSS can double-count shared pages across processes. It is not unique physical memory, allocated heap size, energy, or cache traffic.

Maximum sampled worker residency over the full panel is 4,288.3 MiB, below the 8 GiB experiment ceiling. Existing system swap use is about 5.8 GiB at both boundaries. System counters record zero new swap-ins, swap-outs, or page-outs during the panel. They also record 9,671 page-ins. These are system-wide counters; they do not attribute activity to a specific application. This run does not demonstrate behavior near a RAM ceiling.

AC power is checked before each batch and at both panel boundaries. Background applications remain active and their process snapshots are preserved. Caller and label order rotate. Identical-binary controls retain the original 10% CPU and elapsed-time limits, and 5% plus 8 MiB per caller RSS limit. All four caller configurations pass. Small throughput differences remain inconclusive.

## Validation and shutdown

The Release worker builds from all current SwiftDataFrame sources with matching source, dependency, module, object, and executable hashes. Coverage instrumentation is absent. All 233 benchmark-controller tests pass with the established Metal opt-in and no skips. Production source is unchanged, so no new full-package test claim is made.

A real malformed request stops its worker and the controller drains the other worker. A separate 1-byte test ceiling triggers termination of only the owned benchmark process group. Both checks leave no orphan benchmark workers. Normal completion closes every worker too. This checks bounded shutdown, not indefinite-time leak freedom.

Review added handling for a process-exit race during cleanup after the measured panel. The frozen measured controller is archived and matches its recorded SHA-256. The final source changes only cleanup relative to that controller. A separate final smoke panel and real failure checks pass on the hardened version. The full-panel numbers retain their original fingerprints.

## Next experiment

Use longer queues and a declared memory-budget protocol to test whether compact storage can admit more useful work while holding total memory within the same limit. Keep total CPU per result and response times visible. Then add equivalent external-engine queues. Do not infer a general capacity gain from the present no-swap run.

## Evidence and reproduction

[Summary](summary.json), [audit](audit.json), and [artifact hashes](artifact-sha256.json) accompany the [experiment archive](experiment.tar.gz). The archive contains the frozen measured controller, final benchmark sources, plans, every job receipt, raw memory samples, preflight and postflight checks, system snapshots, compiler receipts and logs, independent expected hashes, smoke runs, cleanup checks, and controller-test output. It excludes CSV bytes, compiled objects, executables, and dependency caches.

Rebuild with `Benchmarks/CPUThroughput/build.py`, then run `run.py` with the recorded input contracts and expected fingerprints. Run `audit.py` afterward. The committed README describes all parameters. Input paths and Release dependency paths are machine-local and must exist or be remapped on another machine. Both full and final smoke runs refuse an existing output directory.
