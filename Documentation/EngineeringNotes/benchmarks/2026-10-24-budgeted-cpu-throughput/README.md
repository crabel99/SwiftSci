# Fixed-memory queues expose a throughput and CPU tradeoff

The experiment extends `codex/dataframe-mixed-throughput`, commit `c61f4cd08c46af998283335435eb3b4c4ce1f9e3`. Production sources and the existing PR branches remain unchanged. This work is committed locally and has not been pushed.

The full panel completes 96 queues and 12,288 timed jobs. Four separate calibration queues complete another 512 jobs. Each timed queue contains the same 128 jobs. All preflight and postflight native-bit checks match the independent reference. Audit qualification is `True`. [Every quality flag remains in the audit](audit.json).

## Lower memory permits an extra caller, with a CPU cost

At 4 GiB, the frozen rule admits four optional callers or five compact callers. Compact storage completes 14.0% more jobs per minute while using 5.0% more CPU time per result. Its sampled peak worker RSS is 9.5% lower. This is a capacity and latency tradeoff, not a reduction in every resource.

| Worker budget GiB | Storage | Callers | Jobs/min | CPU ms/job | Peak RSS MiB | Retained RSS MiB | Resident MiB-seconds |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | optional | 2 | 1340.5 | 177.04 | 1818.8 | 1565.2 | 9326.3 |
| 2 | compact | 2 | 1320.0 | 178.29 | 1319.5 | 1065.9 | 6676.2 |
| 4 | optional | 4 | 2411.4 | 187.84 | 3502.6 | 3121.9 | 9972.3 |
| 4 | compact | 5 | 2747.9 | 197.29 | 3171.3 | 2665.9 | 7659.2 |
| 8 | optional | 8 | 3366.4 | 217.70 | 6978.3 | 6238.0 | 13278.5 |
| 8 | compact | 8 | 3352.3 | 217.74 | 5022.4 | 4262.1 | 9484.0 |

Tables pool the primary and identical-binary twin labels and report medians of 16 queues for each storage and budget. Every queue has 32 copies of each dataset and workflow combination. Jobs/min can be compared only with that fixed case mix. Charged CPU includes worker user and system time plus controller CPU during the queue.

| Budget GiB | Compact throughput change | CPU/job change | Peak RSS change | Resident byte-seconds change |
| ---: | ---: | ---: | ---: | ---: |
| 2 | -1.5% | +0.7% | -27.5% | -28.4% |
| 4 | +14.0% | +5.0% | -9.5% | -23.2% |
| 8 | -0.4% | +0.0% | -28.0% | -28.6% |

At eight callers, CPU per job is essentially equal on these longer queues. The earlier 16-job panel showed a 3.6% compact CPU advantage at eight callers. That advantage does not persist here. Memory savings do persist. CPU benefits must therefore remain workload-specific.

At 2 GiB and 8 GiB, both modes have the same admitted caller count. Those rows compare storage at matched concurrency. At 4 GiB, storage and allowed concurrency both differ. They test the complete admission policy, and cannot isolate the storage algorithm alone. The eight-caller ceiling also prevents this study from testing additional compact callers at 8 GiB.

## Calibration is fixed before timing

Calibration executes two complete single-caller queues per storage mode, reversing mode order for the second pair. The larger of sampled RSS and the kernel-recorded single-process lifetime peak is retained. The maximum calibration peak receives the same 5% plus 8 MiB allowance in both modes.

| Storage | Largest calibration peak MiB | Reservation per caller MiB |
| --- | ---: | ---: |
| optional | 913.5 | 967.2 |
| compact | 663.9 | 705.1 |

The rule divides a declared budget by this reservation, rounds down, and admits at most eight callers. It is an experimental model for this known queue, not a production memory estimator or a guaranteed allocation bound. Calibration cost is outside timed queues and remains in separate raw receipts. No admission value is retuned using timed results.

Each worker retains its native internal parallelism. Caller creation and readiness finish before timing. The first public operation in each fresh worker is inside timing. Input preparation inside the public API, sorting, matrix allocation, and output release are included. Full-output hashing is outside timing.

## Response times include the entire queue

All 128 jobs enter together. Response includes waiting for a caller, execution, release, and receipt. The following values are medians of per-queue p95 response times. These are longer finite bursts, not a steady arrival stream or a service-level guarantee.

| Budget GiB | Storage | Air read p95 ms | Air sort-matrix p95 ms | Energy read p95 ms | Energy sort-matrix p95 ms |
| ---: | --- | ---: | ---: | ---: | ---: |
| 2 | optional | 5367.0 | 5323.5 | 5327.8 | 5534.9 |
| 2 | compact | 5432.2 | 5344.7 | 5431.6 | 5614.8 |
| 4 | optional | 2902.7 | 2894.1 | 2980.0 | 3081.2 |
| 4 | compact | 2514.1 | 2497.7 | 2615.3 | 2756.2 |
| 8 | optional | 1965.8 | 1942.7 | 2083.7 | 2246.7 |
| 8 | compact | 1965.8 | 1934.4 | 2093.5 | 2253.7 |

## Resource boundaries and controls

A secondary audit conservatively sums the kernel-recorded lifetime RSS peaks for each queue. This sum is an upper bound, not a simultaneous observed peak. Every one of the 96 upper bounds is below its budget. Worst upper bounds are 1,827.2 MiB under 2 GiB, 3,644.3 MiB under 4 GiB, and 7,270.7 MiB under 8 GiB. See [kernel peak bounds](kernel-peak-bounds.json).

The declared budget covers aggregate sampled worker RSS. It excludes the controller and does not emulate a machine with only that much physical RAM. RSS can count shared pages more than once. Sampling can miss short-lived peaks. A sampled overrun kills only the benchmark process groups and fails the panel.

The largest sampling gap is 31.4 ms. The maximum observed queue RSS is 7010.8 MiB. All queues remain within their declared sampled budgets.

Retained RSS includes runtimes and allocator caches after output release. Workers terminate after every queue, so their retained state does not carry into the next measurement. This is bounded shutdown testing, not proof of indefinite-time leak freedom.

System-wide counter changes are {"Pageins": 52785, "Pageouts": 0, "Swapins": 4, "Swapouts": 0}. Swap use starts at `vm.swapusage: total = 7168.00M  used = 5925.31M  free = 1242.69M  (encrypted)` and ends at `vm.swapusage: total = 7168.00M  used = 5925.31M  free = 1242.69M  (encrypted)`. These counters do not attribute paging to benchmark workers. AC power is checked before each queue and at panel boundaries. Background process snapshots remain in the archive.

Eight rotated rounds retain the primary and identical-binary twin labels. Budget order rotates too. The unchanged drift limits are 10% for CPU and elapsed time, and 5% plus 8 MiB per caller for sampled RSS. Passing controls does not make a small difference statistically significant. [Paired round observations](paired-rounds.json) keep consistency and variation visible.

## What the result warrants

Compact storage consistently releases room within this application-level memory budget. Increasing admitted concurrency can use that room to improve completion rate, but can also increase CPU work per result. A resource-economy policy must keep those two decisions separate. This experiment makes no automatic production scheduling or storage-default change.

A matched-caller control at four callers would isolate the storage cost at the 4 GiB boundary. Equivalent external-engine queues remain a separate extension. These results do not certify GPU or Neural Engine behavior, global memory-pressure behavior, energy use, or arbitrary scientific workloads.

## Validation and evidence

The same uninstrumented Release worker and independent reference fingerprints are reused from the [earlier fixed-caller study](../2026-10-24-mixed-cpu-throughput/README.md). All timed outputs receive shape and type checks. Full column and matrix bit hashes pass before and after the panel, but not on every timed job.

All 239 controller tests pass with the established Metal opt-in and no skips. A deliberately tiny 64 MiB sampled guard stops its workers after observing 205.8 MiB and retains the failure trace. That overshoot demonstrates why polling is not a hard allocation cap. No orphan benchmark workers remain.

Controller tests cover identical admission rules, worst-case calibration, caller caps, incomplete full-output checks, changed admissions, and mismatched raw receipts. The shared-quality refactor reproduces the earlier panel audit exactly. Full test and failure-cleanup receipts are archived separately.

[Summary](summary.json), [full audit](audit.json), [paired rounds](paired-rounds.json), [artifact hashes](artifact-sha256.json), and the [experiment archive](experiment.tar.gz) preserve the evidence. The archive includes all raw queues and calibrations, exact measured controllers, protocol snapshots, full-output checks, system counters, input contracts, and source code. It excludes CSV bytes, executables, compiled objects, and caches.

Rebuild the worker with `build.py`, then run `budget.py` using the recorded reference plan, independent expected fingerprints, and a new output directory. Audit with `budget.py --audit`. The source README defines the parameters and measurement boundaries. Absolute input and dependency paths are local and must be present or remapped.
