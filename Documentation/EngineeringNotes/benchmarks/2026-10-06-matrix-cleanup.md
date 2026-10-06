# Production matrix autorelease cleanup

Date: 2026-10-06. Branch: `codex/memory-kernel-trial`.
Commit: `530151b4fa700cdd55cca95dc43d4d5080469d2a`. Parent: `64c7688a3401a2a93ec3e454baef0723d53a6cba`.

## Outcome

The production `ScopedGPURead.withMatrix` helper now encloses its allocation,
fill and synchronous operation in a local autorelease pool. `withBuffer` drains
submitted GPU work before that pool closes. No suspension point crosses the pool.
This releases temporary Objective-C/Metal owners at the operation boundary.

After nine GPU fits, median footprint growth falls from
16.05 MiB to 0.78 MiB across
three fresh workers per build. The isolated Metal regression remains flat after
success, throwing completion and cancellation. All selected production tests and
all 126 measured fits pass. This resolves the observed GPU matrix retention;
it does not resolve or reclassify the separate CPU allocator-retention question.

## Failure before the change

A fresh-process regression repeatedly imports a 4,096 × 4 matrix and a
4,097 × 4 matrix. They exercise aligned aliasing and the copy fallback.
After each cycle it drains work, clears the MLX cache and reads Metal's process
allocation counter. The original production helper reports 1,671,168,
1,818,624 and 1,966,080 bytes across three cycles. The assertion that completed
cycles must not accumulate allocations fails. The CLI exits with its expected
uncaught assertion error, recorded before editing production code.

With the fix, successful and throwing cycles each report 1,523,712 bytes throughout.
For cancellation, another task cancels while the synchronous scope is held open
after GPU submission. That scope must remain open until the test releases its
gate. Cancellation then propagates after draining, and Metal allocation returns
to 1,523,712 bytes, the level before the cancelled operation.

The check runs in its own process because Metal counters include other work in
the same process. It is available as `--matrix-lifetime-checks` on the integration
worker. It is not an in-process unit assertion that can be contaminated by tests
running concurrently. The normal `ScopedGPUReadTests` also covers constructed
values and post-submission throwing operations at singleton, aligned and unaligned
sizes. The fresh-process memory check still needs explicit invocation in any CI
job that is intended to enforce this retention property.

## Validation

- Release build passed before and after the production change.
- The new memory regression failed before the fix and passed after it.
- Three matrix-lifetime groups passed: success, throw and cancellation.
- Three existing external-buffer ownership/admission groups passed.
- Seven GPU admission groups passed, including queued cancellation and unequal
  byte requests sharing counted slots.
- Selected Release production tests passed: 106 tests and 131 executions after
  expanding parameterized cases, with no failures, skips or expected failures.
- The unprofiled comparison completed 24 fresh workers and 126 measured fits.
  All numerical references and applicable reservation/slot cleanup checks passed.

The production test selection covers all preprocessing tests, regression fitting,
prepared regression integration, routing, estimator pipelines and the registered
memory prototype ownership tests. The full repository suite was not rerun.
Builds and tests use tracked-file snapshots, excluding unrelated untracked files.

## Memory and timing comparison

Three observations per arm and case, on AC power. Worker order alternates by
round. Thread-count overrides are removed and before/after host-pressure checks
remain normal. Timed workers run after the test process has exited.

The retention case runs three cycles of three GPU shapes, holding inputs alive
through the last job snapshot. Both arms clear the MLX cache and request malloc
relief after every fit. The snapshot is physical footprint growth relative to
inputs-ready current footprint; it is not an exact live-buffer byte count.
Independent same-device references follow the observations.

| Build | Cycle 1 growth MiB | Cycle 2 | Cycle 3 |
| --- | ---: | ---: | ---: |
| Original | 5.344 | 10.500 | 16.047 |
| Fixed | 0.312 | 0.500 | 0.781 |

The timing cases use the existing four-job weighted-admission workload with
48 MiB workspace and one GPU slot. Both arms receive identical shapes, admission
policy and numerical checks. Medians in milliseconds follow. Positive change
means longer batch time.

| Mix | Original ms | Fixed ms | Change |
| --- | ---: | ---: | ---: |
| cpu-heavy | 546.47 | 549.67 | +0.58% |
| mixed | 685.93 | 707.72 | +3.18% |
| gpu-heavy | 1506.12 | 1456.26 | -3.31% |

The observed timing ranges overlap in every mix. These three-observation samples
show no clear throughput regression, but do not establish speed equivalence or a
new formal performance baseline. The direct evidence for this patch is cleanup
and numerical correctness. No tolerance or reservation limit was relaxed.

## Scope and evidence

The production change is confined to `ScopedGPURead.withMatrix`. External-buffer
borrowing, numerical algorithms and admission policies retain their existing
contracts. Strong owners and submitted work must remain alive until the operation
completes; the pool is not a replacement for that ownership.

The implementation commit contains the fix, ordinary tests, the fresh-process
regression and usage documentation. This report and raw comparison evidence remain
on `codex/engineering-notes` only. No branch was pushed in this step.

Evidence is archived under `../archive/2026-10-06/matrix-cleanup/`.
Original build manifests and the Xcode result bundle remain in the local
`matrix-cleanup-20261006` archive. Per-file hashes were verified before committing.

- Original worker SHA-256: `187337dbf3cda9836fe47ccf3f8eb1accda0c55bf57f85252f9aab31edef78de`.
- Fixed worker SHA-256: `8cf4eb7b76a17f1f8bd202cf140f9512423c21fdced7ca8bfe2c4302fe1bf22d`.
- Comparison observations SHA-256: `017a98d25859ae17d0740275b7274249f7d84a68fcf435266286bf3d2ceca75d`.

Reproduce the memory assertion with the integration worker's
`--matrix-lifetime-checks`. The original workload is
`--retained-memory gpu-sizes both 3 sequence`. Timing cases use
`--weighted-admission MIX weighted 48`, with `MIX` set to `cpu-heavy`, `mixed`
or `gpu-heavy`. Run each comparison arm in a fresh process and preserve all
observations, including failed footprint-coverage flags from other policies.
