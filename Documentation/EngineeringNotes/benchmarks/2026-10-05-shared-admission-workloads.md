# Shared admission across workload sizes and device mixes

Date: 2026-10-05. Implementation: `9abe66fb18f84299bc1c621770cbcd9b2420f3f3` on `codex/memory-kernel-trial`.

## Decision and interpretation

Retain caller-selected admission limits. Do not introduce an automatic policy
from this study. Memory savings depend strongly on the number and size of CPU
jobs when GPU concurrency is already limited to one.

For heterogeneous CPU-heavy work, width two reduced median peak footprint from
299.78 to 248.94 MiB, saving 50.84 MiB or about 17%. Median batch time rose from
625.4 to 702.6 ms, about 12%. CPU median completion rose only from 216.5 to
226.0 ms. For heterogeneous balanced work, width two saved 25.30 MiB, about 9%,
with a 4% increase in median batch time and nearly unchanged CPU completion.
These are observed medians, not precise estimates of a repeatable timing penalty.

Small inputs saved less than 0.5 MiB by reducing width four to one. Serial
admission also delayed short CPU work behind GPU jobs. In the CPU-heavy small
case, CPU median completion changed from 1.68 ms at width four to 257.84 ms at
width one. Width two retained 1.57 ms completion. There is little memory reason
to serialize this small workload.

GPU-heavy workloads showed small footprint differences. With only one CPU job
and one permitted GPU job, widths two and four cannot produce more than two
admitted jobs. Treat their timing differences as a control for scheduling and
measurement variation, not proof that width four offers useful extra concurrency.

Timing varied substantially. Several observations exceeded twice their
configuration median, including a 2,470 ms run in the large GPU-heavy width-four
case. No runs were discarded. Pressure remained normal, but that alone does not
establish an otherwise idle host or identify the cause of timing outliers. Five
repeats support exploratory comparisons, not fine-grained speed guarantees.

The next useful step is to calibrate per-device, shape-aware byte estimates and
check queue fairness with mixed job sizes. Fixed equal job estimates helped
isolate admission width here, but do not express the actual workspace differences.
Keep memory capacity, GPU concurrency and response-time requirements as separate
caller controls. Do not change production defaults based on these synthetic fits.

## Workload contract

Each batch contains four independent regression jobs and one GPU slot. CPU-heavy
means three CPU jobs and one GPU job; mixed means two of each; GPU-heavy means
one CPU job and three GPU jobs. Shared widths one, two and four control admission
using equal conservative job estimates. Shared prepared inputs stay resident.

Small inputs contain 1,024 rows by 8 columns for both devices. Large inputs contain
16,384 rows by 32 columns for both. Heterogeneous inputs contain 100,000 rows by 32
columns for CPU and 16,384 rows by 32 columns for GPU. All use 128 held-out rows.
CPU fits use Double OLS; GPU fits use Float32 gradient descent. Compare admission
policies within the same size and mix. Changing the job mix also changes the
numerical work, so these results do not compare equivalent CPU and GPU solvers.

Five rounds ran all 27 configurations, using 135 fresh workers and 540 timed fits.
The controller rotated configuration order and reversed alternate rounds. Task
admission order within a batch remained scheduler-dependent. These are synthetic
regression workloads on a shared machine, not a production-wide performance baseline.

## Validation

The Release build, six ownership/admission qualification checks, and 14 controller
regressions passed. Each timed worker checked its actual CPU/GPU job counts and
all fitted results against independent same-device serial references. CPU equality,
GPU relative tolerance and analytical held-out accuracy bounds were unchanged.
Conflicting study profiles were rejected before worker launch.

All shared and GPU reservations returned to zero. All post-batch MLX active-byte
counts were zero. Memory-pressure readings before and after every worker were
normal. The 15-second worker deadline and descendant cleanup remained active.
Admission estimates are not allocator limits, and pressure checks between workers
do not continuously cap host memory consumption.

Production numerical code and default execution policy were unchanged. The full
production suite was not rerun for these benchmark-only changes.

## Batch time and memory

Each triple lists medians at shared widths **1 / 2 / 4**. Batch time excludes shared
input preparation and includes admission, fitting, prediction and private-stream
draining. Setup and setup-plus-batch values are preserved in the raw observations.

| Input | Job mix | Batch time, ms | Peak physical footprint, MiB |
| --- | --- | ---: | ---: |
| small | cpu-heavy | 258.2 / 262.0 / 270.3 | 170.49 / 170.50 / 170.92 |
| small | mixed | 479.2 / 516.6 / 504.8 | 170.58 / 170.92 / 170.92 |
| small | gpu-heavy | 722.5 / 723.8 / 740.3 | 170.81 / 170.91 / 170.92 |
| large | cpu-heavy | 422.4 / 514.0 / 442.3 | 185.58 / 185.67 / 194.53 |
| large | mixed | 722.0 / 777.3 / 674.6 | 185.66 / 185.83 / 190.19 |
| large | gpu-heavy | 1031.9 / 1005.0 / 1028.5 | 185.78 / 185.80 / 185.80 |
| heterogeneous | cpu-heavy | 694.8 / 702.6 / 625.4 | 248.61 / 248.94 / 299.78 |
| heterogeneous | mixed | 937.1 / 1004.3 / 964.8 | 248.83 / 249.11 / 274.41 |
| heterogeneous | gpu-heavy | 1096.5 / 1229.8 / 1184.1 | 248.78 / 249.02 / 249.13 |

Physical footprint is the kernel's lifetime peak captured before serial reference
fits. It includes process initialization, runtime and graphics allocations charged
to the process. It is separate from peak RSS, MLX live bytes, shared input payload
and conservative reservation accounting. A smaller reservation is not proof of
an equal reduction in physical memory.

## Job response time

Each triple again lists widths **1 / 2 / 4**. Each value is the median across workers
of that worker's per-device median completion time. This is not a tail-latency
percentile or an isolated solver time. Queueing and scheduling affect completion.

| Input | Job mix | CPU completion, ms | GPU completion, ms |
| --- | --- | ---: | ---: |
| small | cpu-heavy | 257.8 / 1.6 / 1.7 | 257.5 / 262.0 / 270.3 |
| small | mixed | 127.9 / 1.5 / 1.5 | 366.4 / 394.9 / 387.8 |
| small | gpu-heavy | 226.4 / 1.3 / 1.3 | 479.9 / 493.0 / 501.4 |
| large | cpu-heavy | 401.9 / 46.8 / 37.9 | 379.6 / 514.0 / 442.3 |
| large | mixed | 212.9 / 40.8 / 35.4 | 550.9 / 604.7 / 516.0 |
| large | gpu-heavy | 23.6 / 25.0 / 24.0 | 699.1 / 686.0 / 707.4 |
| heterogeneous | cpu-heavy | 587.0 / 225.9 / 216.5 | 479.1 / 702.6 / 625.4 |
| heterogeneous | mixed | 358.0 / 179.1 / 177.1 | 711.6 / 849.4 / 785.0 |
| heterogeneous | gpu-heavy | 122.9 / 121.9 / 115.0 | 789.7 / 895.4 / 860.6 |

## Observed timing ranges

Five observations per configuration are insufficient to infer a robust tail
distribution. Keep all runs, including slow observations. Ranges provide context
for interpreting small median differences; they are not confidence intervals.

| Input | Job mix | Shared width | Minimum batch ms | Maximum batch ms |
| --- | --- | ---: | ---: | ---: |
| small | cpu-heavy | 1 | 257.2 | 289.1 |
| small | cpu-heavy | 2 | 249.0 | 283.0 |
| small | cpu-heavy | 4 | 239.5 | 281.9 |
| small | mixed | 1 | 453.1 | 522.0 |
| small | mixed | 2 | 465.0 | 521.3 |
| small | mixed | 4 | 451.5 | 529.7 |
| small | gpu-heavy | 1 | 675.0 | 748.8 |
| small | gpu-heavy | 2 | 612.8 | 740.9 |
| small | gpu-heavy | 4 | 667.5 | 808.4 |
| large | cpu-heavy | 1 | 415.2 | 601.4 |
| large | cpu-heavy | 2 | 454.1 | 834.1 |
| large | cpu-heavy | 4 | 372.8 | 487.5 |
| large | mixed | 1 | 706.2 | 812.5 |
| large | mixed | 2 | 721.7 | 846.0 |
| large | mixed | 4 | 670.0 | 1580.1 |
| large | gpu-heavy | 1 | 1021.1 | 2413.0 |
| large | gpu-heavy | 2 | 969.4 | 1780.1 |
| large | gpu-heavy | 4 | 989.0 | 2470.0 |
| heterogeneous | cpu-heavy | 1 | 673.6 | 829.2 |
| heterogeneous | cpu-heavy | 2 | 695.4 | 943.6 |
| heterogeneous | cpu-heavy | 4 | 604.3 | 854.2 |
| heterogeneous | mixed | 1 | 908.8 | 1782.6 |
| heterogeneous | mixed | 2 | 925.4 | 1433.9 |
| heterogeneous | mixed | 4 | 899.7 | 1668.9 |
| heterogeneous | gpu-heavy | 1 | 1088.8 | 1112.3 |
| heterogeneous | gpu-heavy | 2 | 1144.8 | 1310.2 |
| heterogeneous | gpu-heavy | 4 | 1173.4 | 2474.1 |

## Evidence

- [Raw observations](../archive/2026-10-05/shared-admission-workloads/samples.json)
- [Summary](../archive/2026-10-05/shared-admission-workloads/summary.json)
- Binary SHA-256: `5e7d9d4c578c3285e06f434f58a306d11c0fd25a4179bcd0d580f5a59cd76878`
- Original build-manifest SHA-256: `3c60968b217006796e2d6f0431cb7204cc68b1440af8bcb7c7c2ce115892e7fa`
- Raw observations SHA-256: `38a7252875095f0724388a83fd2edd5664aea5655a5ab75002c0354672034835`

The original build manifest remains in the local evidence archive. It records
per-file hashes for the changes built from parent `28249428cd420b06e7925d6b3603f9a389169be0` before
the implementation commit above. Archived numeric observations remain unchanged.
