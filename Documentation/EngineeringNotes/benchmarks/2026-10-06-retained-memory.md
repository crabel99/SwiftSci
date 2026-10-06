# Retained memory across repeated job sizes

Date: 2026-10-06. Implementation branch: `codex/memory-kernel-trial`.
Experiment commit: `64c7688a3401a2a93ec3e454baef0723d53a6cba`.

## Decision

Keep the memory budget's active-job accounting distinct from process footprint.
The serial CPU-heavy reproduction used a 32 MiB workspace allowance and observed
36.00 MiB of footprint growth with correct results and zero active MLX bytes.
Its footprint-coverage assertion failed as expected. This experiment diagnoses that
difference; it does not fix the original coverage failure or change production defaults.

CPU retention mostly plateaus after the first shape cycle. Repeating one shape
adds about 25 to 27 MiB, while cycling through three shapes adds about 34 MiB.
Malloc bytes in use grow by only about 25 to 37 KiB across those cycles. Returning
from the helper releases the large input allocations, but immediate physical
footprint does not fall by the same amount. This supports separating live ownership
from resident capacity. It does not identify the owner of every retained page.

GPU footprint continues to grow by roughly 5 MiB per three-fit cycle over the
three cycles observed. Clearing MLX's cache lowers the footprint level but does
not stop that growth. Malloc pressure relief reports zero released bytes in every
measured intervention and terminal cleanup. Zero active MLX bytes is therefore
insufficient evidence that all backend memory has returned to its warmed level.

Holding one private stream pair across all nine GPU fits does not remove the growth.
The per-job variant also records one reused GPU stream identity in each worker.
The pinned MLX Swift implementation pools released streams. These observations
reject fresh backend stream creation on every fit as the explanation for this
particular sequence. They do not exclude memory retained by a reused stream.

The next attribution step should inspect VM regions and backend resource lifetimes
at drained fit boundaries. There is no evidence here for adding automatic cache
clears, allocator pressure calls, or larger default reservations to production.

## Method and boundaries

The initial matrix has three profiles, four cleanup treatments and three fresh
processes per combination, totaling 36 workers and 324 measured fits. Two further
GPU-only matrices compare job and sequence stream scopes. Each adds 12 workers
and 108 measured fits, for 60 workers and 540 measured fits overall. Independent
reference fits run after every worker's memory observations and are not included
in those measured-fit counts.

Workers warm both CPU and GPU runtimes, clear the MLX cache, construct shared
inputs and run three cycles of three sequential fits. CPU-same repeats
100,000 × 32. CPU-sizes cycles through 100,000 × 32, 8,192 × 128 and 100,000 × 8.
GPU-sizes cycles through 16,384 × 32, 100,000 × 8 and 1,024 × 8.
CPU uses Double OLS and GPU uses Float32 gradient descent. These are lifecycle
controls within each route, not comparisons of equivalent solver throughput.

The treatments are retain, MLX cache clearing, malloc pressure relief and both.
They act only inside the disposable worker. Inputs remain alive through all job
snapshots. A helper return provides the input-release boundary. Final cleanup is
identical across treatments. Small result arrays and trace records remain alive
for validation. The numerical oracle runs after the observations.

Each worker has a 15-second deadline and process-group cleanup. Workers run
sequentially. All before/after host-pressure readings were normal. Every fit checks
analytical held-out predictions, repeated results and an independent same-device
reference. All completed successfully. The Release builds and 14 Python controller
regressions passed. This benchmark-only change did not rerun the full production suite.

The stream comparison ran all job-scope workers before all sequence-scope workers.
That order limits fine-grained cross-arm comparisons on a shared machine. Within
both arms, the repeated growth remains visible. Stream descriptions add small
trace allocations in those later builds; the initial matrix predates that probe.

## Initial footprint observations

Values are medians across three workers, in MiB above each worker's inputs-ready
current footprint. Malloc in-use growth is a separate, overlapping measurement.
Do not add these counters together. Malloc allocated space is reserved allocator
space and must not be treated as physical footprint.

| Profile | Treatment | Cycle 1 | Cycle 2 | Cycle 3 | Malloc in-use growth |
| --- | --- | ---: | ---: | ---: | ---: |
| cpu-same | retain | 25.39 | 25.44 | 25.28 | 0.025 |
| cpu-same | mlx-clear | 25.97 | 26.03 | -133.87 | 0.024 |
| cpu-same | malloc-relief | 26.77 | 26.77 | 26.22 | 0.025 |
| cpu-same | both | 26.05 | 26.88 | -133.11 | 0.024 |
| cpu-sizes | retain | 33.53 | 33.70 | 33.75 | 0.033 |
| cpu-sizes | mlx-clear | 33.80 | 33.98 | 34.03 | 0.028 |
| cpu-sizes | malloc-relief | 33.55 | 33.59 | 33.95 | 0.035 |
| cpu-sizes | both | 34.69 | 34.70 | 34.73 | 0.028 |
| gpu-sizes | retain | 9.84 | 14.98 | 20.14 | 0.211 |
| gpu-sizes | mlx-clear | 5.34 | 10.58 | 15.77 | 0.102 |
| gpu-sizes | malloc-relief | 9.92 | 15.12 | 20.30 | 0.198 |
| gpu-sizes | both | 5.41 | 10.66 | 15.88 | 0.151 |

Several CPU-same traces drop by approximately 160 MiB near the end, including a
retain run with no intervention. The negative medians preserve that observation.
The cause is unassigned runtime reclamation; the table must not be used to claim
that cache clearing saved 160 MiB. Full traces retain before/after intervention
snapshots so later analysis can inspect where the drop happened.

Input release is visible in malloc ownership counters:

- `cpu-same`: 25.31 MiB median decrease in malloc bytes in use when the input-owning helper returns.
- `cpu-sizes`: 42.46 MiB median decrease in malloc bytes in use when the input-owning helper returns.
- `gpu-sizes`: 11.68 MiB median decrease in malloc bytes in use when the input-owning helper returns.

The median immediate footprint decrease on input release is zero for all profiles.
A CPU-sizes retain example falls from about 44.77 MiB to 2.31 MiB malloc bytes in
use while retaining about 260.28 MiB physical footprint. This disproves the simple
interpretation that the full footprint still represents live input arrays.
It does not prove whether the retained pages belong to malloc pools, mapped backend
resources, driver allocations or another runtime owner.

## GPU stream control

Same units and three observations per treatment. All nine measured fits in each
worker record one GPU stream identity for both scope choices.

| Scope | Treatment | Cycle 1 | Cycle 2 | Cycle 3 |
| --- | --- | ---: | ---: | ---: |
| stream-job | retain | 9.61 | 15.11 | 20.23 |
| stream-job | mlx-clear | 5.70 | 10.86 | 15.81 |
| stream-job | malloc-relief | 9.83 | 14.98 | 20.06 |
| stream-job | both | 5.58 | 10.73 | 15.84 |
| stream-sequence | retain | 9.75 | 14.92 | 20.03 |
| stream-sequence | mlx-clear | 5.66 | 11.09 | 16.20 |
| stream-sequence | malloc-relief | 9.56 | 14.81 | 20.14 |
| stream-sequence | both | 5.36 | 10.75 | 15.89 |

A three-cycle plateau would not prove the absence of leaks. The continued GPU
growth likewise does not establish a leak without longer bounded observations
and resource attribution. The experiment's passed status covers numerical and
lifecycle assertions only.

## Reproduction and evidence

Run the documented `retained_memory.py` controller after rebuilding
`SwiftSciMemoryIntegrationPrototype`. Use `--profiles gpu-sizes` and
`--stream-scope job` or `--stream-scope sequence` for the stream control.
See the prototype README for bounded execution and cleanup details.

Raw observations and summaries are archived under
`../archive/2026-10-06/retained-memory/`. The failed 32 MiB coverage observation is
included as `reproduction.json`. Original build manifests remain in the local
experiment archive. They record source hashes from parent
`04196e699ede889cf208b2c42ff5cd73ad532d9a` before this experiment's commit.

- `attribution`: worker `6697cd976635a45b83d99409618890290f86d85461752bba0f233e441d12a388`; observations `d4d05602ad20fbc4eb88a2aa7abb17d7525afbe0fdc3eef32ce4d7e786fd6690`; build manifest `e1d6e351ba32c3fcd40fba967d335cb2df59cab25db0a0ea24e5ed474d0bd8ad`.
- `stream-job`: worker `9b729fbad60070c86343eeb4bba1032c7ee0ede8ae200e23b083f250290335b4`; observations `7e0aae589fd34ee48dee1e724fd7a354c5f146b0e395e69c9d58a9240863c650`; build manifest `75e5dbd9419dd14d43d791d226414e4e34732b5bc5e9a772128024c122862925`.
- `stream-sequence`: worker `9b729fbad60070c86343eeb4bba1032c7ee0ede8ae200e23b083f250290335b4`; observations `8f7b4085a3bdfca37ebffceb36adbc79253eb9a02f957f5e107e7af816f5ad5d`; build manifest `75e5dbd9419dd14d43d791d226414e4e34732b5bc5e9a772128024c122862925`.

The runtime source inspected was the pinned MLX Swift checkout's
`Source/MLX/Stream.swift`, specifically `StreamPool.newStream`, `releaseStream`,
`withNewDefaultStream` and `Stream.deinit`. Allocator probe contracts came from
the installed Apple SDK's `usr/include/malloc/malloc.h`. No dependency or
production source was changed for these controls.
