# Bounded CPU workspace reuse trial

Date: 2026-10-06. Production head: `530151b4fa700cdd55cca95dc43d4d5080469d2a` on `codex/memory-kernel-trial`.

## Decision

Do not make a reusable CPU arena the default based on this experiment. Neither
fixed capacity nor automatic growth improves all tested workloads. Reuse has a
useful role when a caller or batch planner knows the required capacity in advance,
but its ownership and retained capacity must be explicit in admission accounting.
That planned-capacity case is the next hypothesis, not an implemented result.

The trial completes 2,052 measured fits across 57 workload workers, plus three
standalone lifecycle-check processes. Every measured fit passes its numerical
checks, and the separate adaptive-workspace leak scan reports zero leaked blocks.
Production sources, public APIs, memory budgets and allocator settings are unchanged.

## What was tested

The first disposable Release build compares the current array-backed solver with
one 32 MiB reusable buffer. It completes five fresh workers per arm and profile,
for 20 workers and 720 fits. The fixed arena takes about 2 to 2.5 percent less
median fit time in those two profiles, but adds about 6 MiB of retained growth
when a single large shape repeats. That result motivates the second build.

The second build compares three policies in the same executable:

- Arrays use the existing production solver and temporary Swift arrays.
- Fixed owns one fully initialized 32 MiB buffer until the measured sequence ends.
- Adaptive queries LAPACK's required scratch size, allocates the combined matrix,
  right-hand-side and scratch capacity rounded to a system page, and grows only
  when needed. It retains its largest allocated capacity, bounded by 32 MiB.

Both reusable variants use one exclusive synchronous lease. The trial uses a lock
around the complete solve; it does not suspend while a pointer is borrowed.
This serializes callers and is deliberately limited to sequential-workspace
research. It is not a production concurrency design or a registered MemoryBudget
reservation. Capacity counters describe only this arena, not process memory.

The second build moves the LAPACK workspace-size query before matrix construction
for both reusable variants. LAPACK documents `LWORK=-1` as a query that returns
scratch requirements without solving. The reference implementation returns before
reading matrix data. The trial uses scalar placeholders for that query and then
constructs the complete matrix in its allocated workspace. The actual solve,
stationarity refinement and result conversion remain the existing algorithm.
See [DGELS workspace-query contract and implementation](https://github.com/Reference-LAPACK/lapack/blob/master/SRC/dgels.f).

## Memory results

The second comparison uses three fresh workers per policy and profile, with policy
order rotated by round. Values below are medians in MiB. Growth is the difference
between the last measured fit and inputs-ready footprint within each worker.
Peak is the absolute process peak observed by the last measured fit, including
warmup and input construction. Separate-column medians need not subtract exactly.

| Workload | Arrays growth | Fixed growth | Adaptive growth | Arrays peak | Fixed peak | Adaptive peak |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Small shapes | 1.36 | 32.34 | 1.38 | 10.84 | 41.84 | 10.91 |
| Repeated large shape | 26.41 | 32.48 | 26.41 | 82.05 | 88.09 | 82.03 |
| Largest shape first | 34.95 | 33.58 | 27.42 | 92.67 | 92.24 | 93.39 |
| Increasing shapes | 42.27 | 34.84 | 43.64 | 116.06 | 108.64 | 118.42 |

The adaptive arena retains 1.078 MiB for the small profile and 25.953 MiB for the
large profiles. It allocates once for the repeated and largest-first profiles,
twice for the small profile, and three times for increasing shapes. All leases
finish before snapshots; releasing the workspace owner sets owned capacity to zero.
Immediate physical footprint does not drop by the same amount under the normal
allocator. Reuse has not removed the allocator's reclamation policy.

The largest-first case illustrates a measurement trap. Adaptive growth is lower,
but its sampled inputs-ready footprint is higher, and its whole-process peak is
not lower. The allocator's placement and retained input-construction pages vary
between fresh workers. Report both normalized growth and absolute footprint;
this experiment does not establish a whole-process peak reduction for that case.

Increasing shapes reveal another limit. Adaptive growth is worse than arrays in
the median sample, despite owning only 25.953 MiB at the end. Replacing the arena
can leave previously freed capacity resident in the allocator. This is consistent
with the preceding VM attribution study, but this trial does not separately map
every old arena's pages. The fixed arena avoids resizing and has the lowest peak
in that profile, while wasting roughly 31 MiB for small jobs.

## Timing results

Times are the sum of 36 complete fit operations in milliseconds. An operation
includes fit, prediction, state export, route inspection and stream drain.
Input preparation, post-fit validation and memory snapshots are outside this timer.
The first allocation and initialization are included; no pool is allocated during
warmup. Negative paired changes mean the reusable policy is faster than arrays.

| Workload | Arrays ms | Fixed ms | Adaptive ms | Fixed paired change range | Adaptive paired change range |
| --- | ---: | ---: | ---: | --- | --- |
| Small shapes | 104.16 | 106.54 | 107.04 | -1.55% to +2.91% | -1.95% to +5.37% |
| Repeated large shape | 4290.14 | 4194.49 | 4238.71 | -2.23% to -0.89% | -1.20% to -0.14% |
| Largest shape first | 2438.45 | 2341.76 | 2424.86 | -3.99% to +0.19% | -1.15% to -0.30% |
| Increasing shapes | 2440.98 | 2421.66 | 2426.57 | -1.11% to -0.17% | -0.69% to -0.45% |

These are small sequential experiments on a shared host. The changes are mostly
small and are not a formal throughput baseline or evidence of a general speedup.
The broader whole-process and concurrency costs remain relevant to integration.

## Workloads and checks

Each worker runs twelve cycles of three fits, using prepared standardized columns:

- Small: 1,024 by 8, 4,096 by 32, and 8,192 by 8.
- Repeated large: 100,000 by 32, three times per cycle.
- Largest first: 100,000 by 32, 8,192 by 128, and 100,000 by 8.
- Increasing: 100,000 by 8, 8,192 by 128, and 100,000 by 32.

CPU warmup precedes enabling the trial pool. The worker warms no GPU fit, retaining
the correction from the previous memory investigation. The CPU route still uses
MLX compatibility objects and stream synchronization. All workers use normal
allocator behavior; the controller removes malloc diagnostic environment variables
and thread-count overrides. Workers run one at a time on AC power with normal
before/after memory-pressure readings. Each has a 60-second deadline and owned
process-group cleanup. Builds finish before measurements start.

Every measured fit checks 128 held-out predictions against the analytical fixture,
checks exact repeatability, verifies the CPU route and zero active MLX bytes, and
checks complete finite results. After observations, the worker disables the pool
and compares coefficients, bias and predictions exactly against the original CPU
solver using a separately prepared row-array StandardScaler pipeline. The data
are deterministic ordinary regression fixtures. Noisy, rank-deficient, extreme
scale and broader certification data are not covered by this trial.

Reusable variants must record all 36 successful workspace uses, zero active leases,
and owned capacity within the ceiling. This detects a silent solver fallback in
these measurements. The helper checks cover reuse after a throwing operation,
over-capacity rejection, and explicit release. They do not validate concurrent
cancellation or scheduling. In the disposable solver, the existing outer catch
still falls back to gradient descent on errors. A production capacity policy
must distinguish admission failure from numerical fallback; this prototype is
not a memory bound for oversized public-API calls.

A separate increasing-size adaptive worker runs 36 fits with stack logging and
`leaks --atExit`, under a 90-second deadline. It reports zero leaks and zero
leaked bytes after three allocations and complete workspace release. The graph
is an exit-time check, not a proof about all intermediate ownership paths.
No full production suite or CI run was performed for these isolated source snapshots.

## Integration boundary

Keep the production solver unchanged for now. A useful next trial should plan
workspace capacity from known batch dimensions, query the backend's scratch needs,
reserve that capacity for its actual lifetime, and release or reuse it according
to the caller's scope. It should avoid unbounded process-global pools, hidden
serialization and automatic per-fit purges. Test varying order, repeated batch
lifetimes and concurrent jobs before choosing a default.

The result is evidence for explicit workspace lifetime and capacity planning, not
for one universal caching policy. The current allocator already handles repeated
same-size work well. A new memory layer must improve the whole workload to justify
its complexity.

## Reproduction assets

Engineering-note archives retain numeric samples, summaries, build fingerprints,
controllers and complete source patches for both snapshots. Full compiler logs
and the leak log remain local. The diagnostic executables are separate cache
copies. The original validated worker is restored after each build. All profiling
processes have exited. Nothing was pushed and no prototype change entered the
implementation branch.
