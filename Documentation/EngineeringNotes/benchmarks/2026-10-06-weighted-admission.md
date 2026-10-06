# Counted GPU slots and unequal workspace estimates

Date: 2026-10-06. Branch: `codex/memory-kernel-trial`.

- Count-only GPU gate: `da5f8fb27b97b7c93121a6b7a29573f6f75fea8e`.
- Fixed-budget workload comparison: `04196e699ede889cf208b2c42ff5cd73ad532d9a`.

## Decision

Keep GPU concurrency independent of byte reservations. Every GPU request now
consumes one counted slot regardless of its workspace estimate. The experimental
`DeviceSlots` interface hides unit-cost FIFO accounting behind `acquire()`, active
count and peak count. It reuses the existing cancellation and release mechanics.
CPU jobs bypass this gate. Historical observations retain their original fields;
new observations record slot counts rather than calling those values bytes.

Retain unequal job estimates as a caller policy experiment, with no production
default change. Weighted charging admitted more jobs and often improved CPU
response time, but did not consistently improve batch time. At 48 MiB in the
CPU-heavy case, median CPU completion fell from 492.3 to 175.9 ms while batch time
increased from 538.1 to 571.2 ms. These medians come from three observations per
configuration on a shared machine, so they do not establish precise speed guarantees.

Do not treat the calibrated active-job estimates as a physical-memory bound.
Fourteen of eighteen batches with a 32 MiB workspace allowance exceeded the
observed footprint allowance. The largest observed envelope there was 38.16 MiB.
All 36 observations at 48 and 64 MiB fit their allowances, which is evidence for
these runs only. The limits were fixed before measurement; no exceedances were
discarded, waived or reclassified as covered.

## What failed and what passed

All 216 timed fits passed independent numerical references. Shared reservations
and GPU slot grants returned to zero; slot peaks never exceeded one. Active MLX
bytes after every batch were zero and host pressure readings remained normal.
The summary's `status: passed` describes numerical and admission checks. Its
separate `workspace_covers_all_observations: false` records failed footprint coverage.

The exceedance is not simply excessive concurrency. All three CPU-heavy equal-charge
runs at 32 MiB admitted only one job at a time and still exceeded the footprint
allowance. No pre-batch lifetime peak was above the pre-batch current footprint,
so earlier input-construction peaks do not explain these observations. CPU-heavy
batches retained roughly 35 MiB above their pre-batch footprint after jobs finished,
while their reported MLX cache was only about 0.19 MiB.

Those measurements do not identify the owner of every retained page or prove a
leak. They show that a series of different-sized jobs can retain more process
footprint than the peak estimate of the currently admitted job. CPU allocation
pools, backend workspaces and other runtime retention need separate attribution.
The next useful step is to measure that retained capacity across repeated job-size
transitions before proposing a resident-memory policy or automatic defaults.

## Workloads and comparison contract

Every batch contains four jobs, one GPU slot and a shared input reservation.
The equal policy charges every job the largest candidate estimate in its batch.
The weighted policy charges each job the calibrated candidate for its device and
shape. Both policies receive identical work, shared reservation size and total
capacity at each workspace limit. The controller verifies those equalities.

| Mix | CPU training shapes | GPU training shapes |
| --- | --- | --- |
| CPU-heavy | 100,000 × 32; 8,192 × 128; 100,000 × 8 | 16,384 × 32 |
| Mixed | 100,000 × 32; 16,384 × 32 | 16,384 × 32; 1,024 × 8 |
| GPU-heavy | 100,000 × 32 | 16,384 × 32; 100,000 × 8; 1,024 × 8 |

All shapes retain 128 held-out rows. Identical shapes share their immutable
prepared inputs. CPU fits use Double OLS; GPU fits use Float32 gradient descent.
Compare admission policies within each mix, not different solvers as equivalent work.

The shared reservation covers input preparation and retained results conservatively
and is identical between policies. Workspace allowances of 32, 48 and 64 MiB are
additional to it. GPU slots are counts and are never added to reserved bytes.
A request that cannot fit beside the persistent shared reservation is rejected
before queueing. GPU jobs acquire their slot before requesting shared capacity.
Both constraints retain FIFO semantics, including head-of-line blocking.

Each worker warms CPU and GPU runtimes and clears the MLX cache before the study.
Shared preparation follows warmup. Batch timing excludes preparation but includes
admission, fitting, prediction and private-stream draining. Independent numerical
references follow time and memory measurement. This warmed-runtime study is not
directly comparable with the earlier cold-runtime width measurements.

## Measurements

Medians across three fresh processes. The envelope is the lifetime physical peak
after the batch minus current footprint immediately before it, floored at zero.
It measures process footprint growth, not an isolated allocator trace. CPU completion
is the median across workers of each worker's per-CPU-job median completion time.

| Mix | Workspace MiB | Policy | Batch ms | CPU completion ms | Envelope MiB | Exceedances |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| cpu-heavy | 32 | equal | 534.9 | 502.8 | 34.86 | 3/3 |
| cpu-heavy | 32 | weighted | 604.6 | 179.5 | 36.13 | 3/3 |
| cpu-heavy | 48 | equal | 538.1 | 492.3 | 36.06 | 0/3 |
| cpu-heavy | 48 | weighted | 571.2 | 175.9 | 43.00 | 0/3 |
| cpu-heavy | 64 | equal | 576.7 | 180.8 | 36.00 | 0/3 |
| cpu-heavy | 64 | weighted | 560.0 | 120.4 | 36.20 | 0/3 |
| mixed | 32 | equal | 656.0 | 304.1 | 30.11 | 0/3 |
| mixed | 32 | weighted | 643.4 | 139.5 | 32.05 | 2/3 |
| mixed | 48 | equal | 655.3 | 302.5 | 30.63 | 0/3 |
| mixed | 48 | weighted | 711.8 | 138.9 | 32.83 | 0/3 |
| mixed | 64 | equal | 718.3 | 138.4 | 32.11 | 0/3 |
| mixed | 64 | weighted | 691.4 | 79.3 | 32.09 | 0/3 |
| gpu-heavy | 32 | equal | 1452.3 | 430.3 | 32.95 | 3/3 |
| gpu-heavy | 32 | weighted | 1480.1 | 437.3 | 33.11 | 3/3 |
| gpu-heavy | 48 | equal | 1465.0 | 434.0 | 33.09 | 0/3 |
| gpu-heavy | 48 | weighted | 1498.1 | 129.3 | 33.25 | 0/3 |
| gpu-heavy | 64 | equal | 1519.8 | 128.7 | 33.31 | 0/3 |
| gpu-heavy | 64 | weighted | 1550.8 | 127.1 | 33.64 | 0/3 |

Physical footprint, MLX allocations, shared payload and reservation accounting
remain separate raw measurements. A larger permitted overlap can improve response
time, increase contention or retain more memory. The experiment does not select
one universally best policy.

## Validation and scope

Both Release builds passed. Fourteen controller regressions passed after each
change. Seven slot/admission checks cover submitted-scope ownership, cancellation,
errors, CPU bypass, rejected requests and differently sized jobs consuming one
slot each. Four calibration/FIFO groups passed against the final worker. An earlier
four-fit mixed smoke check also passed against the slot-only commit.

The slot-specific test admits one-byte and 2,048-byte requests under two slots,
then cancels a third queued request. Both active owners retain their grants until
they finish. Numerical comparisons preserve exact CPU equality, GPU relative
tolerance and analytical held-out bounds from calibration. All workers completed
under their 15-second deadline. No numerical production implementation, public
API or production default changed; the full production suite was not rerun.

## Evidence

- [Raw weighted-study observations](../archive/2026-10-06/weighted-admission/samples.json)
- [Weighted-study summary](../archive/2026-10-06/weighted-admission/summary.json)
- [Final slot checks](../archive/2026-10-06/weighted-admission/slot-checks.json)
- [Final FIFO checks](../archive/2026-10-06/weighted-admission/fifo-checks.json)
- [Slot-only smoke observations](../archive/2026-10-06/weighted-admission/slots-mixed-smoke.json)
- Final worker SHA-256: `d30637bacec46dc004cdfd99ec9172573fc8f7a0cff3c4612122cf3c447b22e6`
- Final build-manifest SHA-256: `42675c44d2a2a039092feb963607d3b55f3fa4f0f8226b40c6880f36e9379e64`
- Raw weighted observations SHA-256: `29adbbf23b5a4f957ed599423e0f109fb57c295d24dd6bd3e65fc48fb3f9fef7`
- Slot-only worker SHA-256: `5aa434c289635854ed45481de6b1a21051ec5cb0bc68437ca886dcc2482b6047`

Original build manifests remain in the local evidence archive. The final manifest
records per-file hashes built from parent `da5f8fb27b97b7c93121a6b7a29573f6f75fea8e` before the workload
commit. The archived numeric observations are unchanged.
