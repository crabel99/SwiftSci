# Separate compact storage from caller concurrency

The local experiment is `codex/dataframe-mixed-throughput`, commit `36a93f7dfd54524fc7360fd52930366190db8d01`. Production code and existing PR branches are unchanged. No source branch was pushed.

This panel interleaves optional storage with four callers, compact storage with four callers, and compact storage with five callers. Every configuration has its own identical-binary twin. It completes 72 queues and 9,216 timed jobs. Four separate calibration queues complete another 512 jobs.

Full-output checks match the independent reference before and after the panel. Audit qualification is `True`. [Quality flags remain visible](audit.json).

## Compare matched callers before considering more concurrency

| Storage | Callers | Jobs/min | CPU ms/job | Peak RSS MiB | Retained RSS MiB | Resident MiB-seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| optional | 4 | 2283.8 | 194.98 | 3504.8 | 3126.1 | 10515.6 |
| compact | 4 | 2247.9 | 195.99 | 2511.1 | 2130.8 | 7576.3 |
| compact | 5 | 2620.0 | 201.70 | 3172.4 | 2667.7 | 7980.5 |

Each row pools its primary and twin labels, for 24 queues per configuration. Values are medians. Each queue contains 128 jobs with the same case mix. CPU is worker user and system time plus controller CPU. Shared pages can be counted repeatedly in RSS.

| Comparison | Throughput change | CPU/job change | Peak RSS change | Resident byte-seconds change |
| --- | ---: | ---: | ---: | ---: |
| storage at four callers | -1.6% | +0.5% | -28.4% | -28.0% |
| fifth compact caller | +16.6% | +2.9% | +26.3% | +5.3% |
| combined choice | +14.7% | +3.4% | -9.5% | -24.1% |

At matched four callers, compact storage reduces peak RSS by 28.4%. CPU/job changes by +0.5% and throughput by -1.6%. This panel establishes a substantial memory benefit; it does not establish a CPU-time reduction.

Within compact storage, adding the fifth caller raises throughput by 16.6%, CPU/job by 2.9%, and peak RSS by 26.3%. Both configurations fit 4 GiB. This is a selectable capacity and latency tradeoff.

The earlier capacity study remains unchanged. All ratios here come from the interleaved configurations in this new panel, rather than comparisons across different measurement sessions.

The first comparison holds caller count at four and changes storage. The second holds compact storage fixed and adds one caller. The combined comparison includes both changes. These are distinct engineering choices.

## Keep variation visible

| Comparison | Rounds with higher throughput | Rounds with lower CPU/job |
| --- | ---: | ---: |
| storage at four callers | 2/12 | 6/12 |
| fifth compact caller | 12/12 | 0/12 |
| combined choice | 12/12 | 0/12 |

Round comparisons use the median of each condition and its twin within that round. The [comparison record](comparisons.json) preserves every ratio. Counts describe consistency; they are not confidence intervals or proof of independent observations. Passing a 10% drift control does not certify small differences.

## Examine CPU costs by operation

| Case | Optional/four operation CPU ms | Compact/four operation CPU ms | Compact/five operation CPU ms |
| --- | ---: | ---: | ---: |
| Aotizhongxin-default/read | 10.625 | 10.801 | 11.003 |
| Aotizhongxin-default/sort-matrix | 14.609 | 14.358 | 14.672 |
| energy-common/read | 266.899 | 282.916 | 290.048 |
| energy-common/sort-matrix | 485.539 | 473.315 | 489.715 |

Each value is the median per-queue mean operation CPU for that case. Operation CPU includes public CSV reading, any requested sort and matrix construction, shape checks, memory bookkeeping, and output release. It excludes controller work and request decoding. It therefore differs from whole-queue charged CPU. This is a CPU-time breakdown, not a hardware-counter profile.

## Queue responses include waiting

| Storage | Callers | Air read p95 ms | Air sort-matrix p95 ms | Energy read p95 ms | Energy sort-matrix p95 ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| optional | 4 | 3047.1 | 3025.7 | 3143.5 | 3249.4 |
| compact | 4 | 3118.7 | 3086.2 | 3183.6 | 3311.1 |
| compact | 5 | 2625.0 | 2602.7 | 2700.2 | 2865.3 |

All jobs enter the queue at once. Response includes waiting for a caller, execution, release, and receipt. Values are medians of per-queue p95 responses. This is a longer finite burst, not a steady arrival stream.

## Protocol and memory boundaries

Two reference datasets supply 35,064 air-quality rows and 2,075,259 household-energy rows. Every queue has 32 copies of each read and read/sort/matrix case. Schemas, native types, null tokens, CSV bytes, stable missing-last ordering, and matrix contracts remain unchanged. Full-output hashes run before and after the panel. Timed outputs receive shape and type checks rather than full hashes.

All callers use the same uninstrumented Release worker with native CPU parallelism. Four callers means four worker processes, not four CPU threads. No core affinity or internal thread cap changes. Startup and readiness finish before queue timing; the first public call in each worker remains timed. Calibration and full-hash checks are outside timing.

Separate calibration checks that optional/four, compact/four, and compact/five fit the 4 GiB envelope before timing. Reservations use the maximum kernel-recorded or sampled single-caller peak plus 5% and 8 MiB. The declared caller counts are not retuned. Twelve rotated rounds put every primary and twin label in every position twice.

The audit keeps each condition and twin separate. Limits remain 10% for CPU and elapsed-time drift, and 5% plus 8 MiB per caller for RSS drift. Earlier capacity-panel audits remain unchanged after the controller extension. No default admission or production storage policy changes.

All 72 conservative sums of per-worker kernel lifetime peaks are within 4 GiB. The largest bound is 3650.5 MiB. Such a sum is an upper bound, not a simultaneous observed peak. See [kernel bounds](kernel-bounds.json).

Sampled RSS remains an application-level metric and may count shared pages repeatedly. This does not emulate global memory pressure on a 4 GiB machine. System paging counters and unrelated process snapshots are preserved, without attributing activity to the benchmark. AC power is required before each queue and at panel boundaries.

## Validation and reproduction

The smoke panel and all 242 benchmark-controller tests pass with the established Metal opt-in and no skips. Normal completion leaves no orphan workers. The queue and cleanup controller is byte-identical to the preceding study, so its real guard-failure check remains applicable; that reused evidence is explicitly labelled in the archive. No production Swift sources changed, so this adds no new full-package test claim. The same exact-source worker and reference hashes are reused from the earlier studies.

[Summary](summary.json), [comparisons](comparisons.json), [audit](audit.json), [kernel bounds](kernel-bounds.json), [artifact hashes](artifact-sha256.json), and the [experiment archive](experiment.tar.gz) preserve the evidence. The archive contains exact measured controllers, all raw queues and calibrations, input contracts, source code, and test receipts. CSV bytes, compiled executables, objects, and caches are excluded.

Rebuild with `Benchmarks/CPUThroughput/build.py`, then run `budget.py --matched-control` with the recorded reference plan, independent expected fingerprints, and a new output directory. Audit with `budget.py --audit`. Absolute dependency and input paths must be present or remapped. The source README defines the command parameters.
