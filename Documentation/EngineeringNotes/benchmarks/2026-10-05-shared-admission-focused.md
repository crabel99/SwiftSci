# Shared admission width with one GPU slot

Date: 2026-10-05. Implementation: `28249428cd420b06e7925d6b3603f9a389169be0` on `codex/memory-kernel-trial`.

## Decision

Keep shared admission width selectable by the caller in this experiment. Do not
change production defaults. Serial admission saved 25.66 MiB, or
9.35% of median peak physical footprint, with a 0.95%
increase in median batch time compared with width four. The batch-time ranges
overlap, so this does not establish a repeatable one-percent timing penalty.

The latency tradeoff matters. CPU median completion was about 328 ms at width
one and 168 ms at widths two and four. Width two saved about 25 MiB while keeping
CPU completion near width four, but its median batch time was about 5% longer.
Width one is a candidate for memory-sensitive batch work; width two is a candidate
when CPU response time matters. These are workload-specific choices to test,
not general scheduling recommendations.

## Workload and checks

Every worker ran two CPU and two GPU regression jobs with one GPU slot fixed.
The shared budget admitted at most one, two or four jobs. Shared prepared inputs
remained resident at every width. CPU inputs were 100,000 rows by 32 columns;
GPU inputs were 16,384 rows by 32 columns. CPU fitting used Double OLS and GPU
fitting used Float32 gradient descent. Compare admission policies within this
workload, not the speed or accuracy of different solvers.

The Release build passed. Fifteen fresh workers completed five repeats per width,
with 60 timed fits and separate same-device reference checks. CPU results matched
their serial references exactly. GPU results met the existing relative tolerance
of `5e-6 * max(1, abs(reference))`. Analytical held-out checks retained their
existing CPU and GPU bounds. Six admission qualification checks and 14 controller
regressions passed. Conflicting focused profiles were rejected before worker
launch. No production numerical code changed; the full production suite was not
rerun for this benchmark-only change.

All shared and GPU grants were returned. Post-batch MLX active bytes were zero
and all before/after worker pressure readings were normal. Each worker retained
the 15-second deadline and process-group cleanup. Pressure checks occur at worker
boundaries; admission estimates do not enforce a process or host memory cap.

## Measurements

Medians across five fresh processes. Device completion columns are medians of
each worker's two job completion times. Batch timing starts after shared input
preparation and includes admission, fitting, prediction and stream draining.
Input preparation took about 37 ms at every width and is recorded separately.

| Shared width | Batch time, ms | Peak physical footprint, MiB | CPU completion, ms | GPU completion, ms |
| --- | ---: | ---: | ---: | ---: |
| 1 | 870.6 | 248.72 | 327.8 | 656.2 |
| 2 | 906.4 | 249.11 | 167.9 | 754.9 |
| 4 | 862.4 | 274.38 | 167.6 | 710.9 |

| Shared width | Batch time range, ms |
| --- | ---: |
| 1 | 861.8 to 921.6 |
| 2 | 890.5 to 931.6 |
| 4 | 853.7 to 881.0 |

Memory is sampled before independent reference fits. The kernel's lifetime peak
physical footprint includes initialization and runtime memory as well as graphics
allocations charged to the process. It is distinct from RSS, MLX live allocations
and admission reservations. Shared cached payload was 29.37 MiB at every width;
conservative reservation estimates were much larger than measured footprint.
Do not treat reservation reductions as measured physical memory savings.

CPU median service time increased from about 106 ms at width one to 167 ms at
width four. GPU median service time also rose with overlap. This is consistent
with resource contention, but this experiment does not isolate its hardware cause.
Lower service time and longer queueing can offset each other in batch totals.

This is a synthetic mixed workload on a shared machine with only five observations
per width. Task admission order is scheduler-dependent. Results support further
workload-specific policy comparisons; they are not a formal production baseline
or evidence of a universal best width. The next useful experiment is to vary input
size and the CPU/GPU job mix before adding any automatic policy selection.

## Evidence

- [Raw observations](../archive/2026-10-05/shared-admission-focused/samples.json)
- [Summary](../archive/2026-10-05/shared-admission-focused/summary.json)
- Binary SHA-256: `604179cfb5a8ea44c703ca8d66fe74c83cc93da81f3f99c06ae4f8e367a669b0`
- Original build-manifest SHA-256: `4d09e89a1578de082f71ae60460d5d0d1aa54e486accb075421ecb31eeef0f86`
- Raw observations SHA-256: `4a52c466d0313a3de6fb0ee5cbbe30c7689f72f38535bed8d9578d29037baf9c`

The original build manifest remains in the local evidence archive. It records
per-file hashes for the changes built from parent `332809996a25cc63c85d64fbe3a5b054f9efff8a` before
the implementation commit above. Archived numeric observations remain unchanged.
