# Regression workspace calibration and mixed-size FIFO

Date: 2026-10-06. Implementation: `22abe5596dfef28ebbb1be91a3a061202718bfcf` on `codex/memory-kernel-trial`.

## Decision

Retain the new estimates as experimental per-job regression workspace candidates.
All 30 observed envelopes fit within the candidates. Do not promote them to hard
allocation bounds or production defaults. These measurements cover warmed runtime,
one job at a time, five input shapes and the current CPU OLS and GPU gradient-descent
implementations. Concurrent jobs, cold runtime, other models and other devices
remain outside this evidence.

The production byte queue already implements FIFO. Tests confirm that a smaller
request cannot pass an older blocked request, and that cancelling the queue head
lets a fitting successor proceed. Keep that contract. A future latency-sensitive
scheduler must make an explicit choice about bounded bypass or separate queues;
silently changing the byte budget to opportunistic admission would discard its
current starvation protection.

The next integration step is to compare these unequal estimates under the same
shared byte limit with mixed-size jobs. Keep GPU concurrency as a separate count
constraint. The previous experiment reused byte estimates for GPU admission only
because every job had the same estimate. With unequal estimates, a byte-denominated
GPU budget no longer means a fixed number of GPU slots.

## What the estimates mean

Shared prepared input, per-job workspace and process/runtime memory are separate
quantities. This change estimates per-job workspace. It records shared payload
and the runtime baseline separately and does not change any actual allocation.
The 100,000 × 32 CPU candidate is 28.48 MiB; the largest observed increase was
25.31 MiB. The older equal-width experiment used a roughly 360 MiB conservative
job estimate for that shape. Reducing an estimate is not a physical memory saving.

CPU source accounting starts with the augmented column-major Double matrix
and right-hand side allocated by `LinearRegression.fitCPUAnalytical`. It adds
allowances for the queried LAPACK workspace, refinement vectors, results and
allocator overhead. GPU accounting starts with the Float32 feature matrix created
by `ScopedGPURead.withMatrix`, allowing a possible import copy, and adds allowances
for targets, autodifferentiation vectors, parameters, predictions and allocator
overhead. The GPU graph and backend can allocate further internal workspace.

The formulas were fixed before measurement. Their components are preserved in
each raw record and in `Integration/MemoryCalibration.swift`. Some components
are conservative allowances, not exact buffer counts. In particular, the CPU
solver-workspace allowance is not an exact LAPACK workspace query, and the GPU
allowances are not a static analysis of MLX's allocation graph. Wide and small
cases leave substantial headroom; do not tighten it from three observations alone.

## Measurement boundary

Each fresh worker warms the selected runtime using a small prepared regression,
drains its private streams, drops that input and clears the MLX cache. It then
constructs the measured input and records current and lifetime peak physical
footprint immediately before fitting. The measured fit includes prediction and
stream draining. Numerical reference work starts after the memory measurement.

The observed envelope is lifetime peak after the fit minus current footprint
before the fit, floored at zero. Earlier peaks can inflate this envelope; the
worker preserves the pre-fit lifetime peak so this is visible. None of these
30 runs had a prior lifetime peak above its pre-fit current footprint. This is
still an observed process-footprint envelope, not an isolated allocator trace
or proof that all workspace will scale additively under concurrency.

## Results

Three fresh processes per shape and device. Candidate and maximum observed
envelope are in MiB. Underestimates count observations exceeding the candidate.

| Device | Training shape | Candidate MiB | Maximum envelope MiB | Underestimates |
| --- | --- | ---: | ---: | ---: |
| cpu | 1,024 × 8 | 2.12 | 0.16 | 0 |
| gpu | 1,024 × 8 | 8.14 | 0.22 | 0 |
| cpu | 16,384 × 32 | 6.79 | 4.20 | 0 |
| gpu | 16,384 × 32 | 13.06 | 2.41 | 0 |
| cpu | 100,000 × 32 | 28.48 | 25.31 | 0 |
| gpu | 100,000 × 32 | 38.58 | 25.97 | 0 |
| cpu | 8,192 × 128 | 18.28 | 9.25 | 0 |
| gpu | 8,192 × 128 | 16.75 | 4.55 | 0 |
| cpu | 100,000 × 8 | 9.67 | 6.97 | 0 |
| gpu | 100,000 × 8 | 20.22 | 7.98 | 0 |

All measurements retain 128 held-out rows. CPU uses Double OLS and GPU uses
Float32 gradient descent. The table compares each workspace estimate with its own
observations; it is not a comparison of equivalent CPU and GPU algorithms.

## Validation and queue behavior

The Release build and 14 controller regressions passed. All 30 measured fits
passed independent row-based, same-device serial references with unchanged CPU
equality, GPU relative tolerance and analytical held-out bounds. Each worker also
ran a warmup fit. MLX active bytes returned to their pre-fit values, all pressure
readings were normal, and workers completed under the 15-second deadline.

Four new qualification groups cover shape growth for both devices, overflow
rejection for both devices, FIFO ordering with different request sizes, and
progress after cancelling the queue head. The six existing device-admission
checks also passed against the rebuilt worker.

The FIFO scenario holds 60 of 100 bytes, then queues requests for 80, 30 and 10.
Although either small request could fit initially, neither bypasses the 80-byte
head. Releasing the original grant admits 80 bytes first. The 10-byte newcomer
still cannot pass the waiting 30-byte request. Releasing the large grant then lets
both smaller requests proceed. The cancellation scenario removes the blocked
80-byte head and admits 30 bytes alongside the existing 60-byte owner, verifying
that cancellation does not release another owner's reservation.

This establishes ordering under releasing owners and demonstrates head-of-line
blocking. It does not establish bounded latency, fairness across unrelated
budgets, or recovery from an owner that never releases its grant.

Production numerical code, queue behavior and execution defaults did not change.
The full production suite was not rerun for this benchmark-only experiment.

## Evidence

- [Raw observations](../archive/2026-10-06/memory-calibration/samples.json)
- [Summary](../archive/2026-10-06/memory-calibration/summary.json)
- [Estimate and FIFO checks](../archive/2026-10-06/memory-calibration/checks.json)
- [Existing device-admission checks](../archive/2026-10-06/memory-calibration/existing-admission-checks.json)
- Binary SHA-256: `c713bcdb50ec6372a4aa92256e29c6f97dfce19d9be22b78141709326cdebe92`
- Original build-manifest SHA-256: `9bbf6a5751a63f7f4428f7b04bd270e51b8a1fb464e233923db97e4b66c96c75`
- Raw observations SHA-256: `683f0962428b34e9e08897c2162e2f649d40e15b6c53a1a5c94fecdccc445ffd`

The original build manifest remains in the local evidence archive. It records
per-file hashes built from parent `9abe66fb18f84299bc1c621770cbcd9b2420f3f3` before the implementation
commit above. The archived numeric evidence is unchanged.
