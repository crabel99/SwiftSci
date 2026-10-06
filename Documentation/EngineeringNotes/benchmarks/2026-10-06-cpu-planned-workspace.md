# Batch-planned CPU workspace and reservation lifetime

Date: 2026-10-06. Production head: `530151b4fa700cdd55cca95dc43d4d5080469d2a` on `codex/memory-kernel-trial`.

## Decision

Keep batch-planned workspace reuse as a promising opt-in candidate. It lowers
whole-process peak memory for the two changing-shape workloads in this experiment,
without the fixed arena's small-job waste or the adaptive arena's repeated growth.
It is not a general speed improvement and should not replace default array-backed
execution on this evidence alone.

The next integration step is an instance-scoped workspace owner with explicit
lifetime and admission. The disposable process-global arena remains unsuitable
for concurrent production batches or independently configured budgets. No production
source, public API, allocator setting or default memory policy changed here.

## What the plan owns

For every known batch shape, the prototype queries LAPACK's scratch requirement,
adds the column-major matrix and right-hand-side storage, rounds the total to the
system page size, then takes the maximum across the sequential batch. It reserves
that capacity before allocation and holds the grant until its final owner releases.
The arena allocates lazily during the first measured fit, exactly once per batch.
Initialization cost remains inside the first fit timing.

The small batch reserves and allocates 1,130,496 bytes, about 1.078 MiB. Each large
batch reserves and allocates 27,213,824 bytes, about 25.953 MiB. The trial keeps the
existing 32 MiB ceiling. Every fit verifies that the current reservation equals
the plan and covers the arena's owned bytes. End-of-batch checks require one
allocation, 36 successful uses, no active borrower and zero reservation after
owner release.

This is a workspace-only reservation using the existing MemoryBudget mechanism.
It excludes prepared inputs, persistent model state, other solver temporaries,
allocator caches and unrelated process memory. It is not a whole-process memory
cap. The previous strict footprint-coverage problem is not erased by this result.

The measured solver still queries its own LAPACK requirement before using the
workspace. If a fit needs more than the planned capacity, the arena rejects it.
The snapshot distinguishes this capacity error from numerical solver errors, so
the existing gradient-descent fallback cannot silently bypass admission. That
error distinction belongs in any eventual integration.

## Peak memory

Four fresh workers per policy and profile. Values are median process peaks in MiB,
observed by the end of the measured fits. They include runtime warmup, input
construction and workspace allocation. Policy order rotates through all four
positions over four rounds. All policies use the same executable and normal
allocator behavior.

| Workload | Arrays | Fixed 32 MiB | Adaptive growth | Planned capacity |
| --- | ---: | ---: | ---: | ---: |
| Small shapes | 11.56 | 41.96 | 11.05 | 11.05 |
| Repeated large shape | 82.13 | 88.20 | 82.20 | 82.13 |
| Largest shape first | 93.26 | 95.85 | 85.84 | 86.31 |
| Increasing shapes | 117.09 | 108.75 | 118.55 | 101.66 |

The planned policy reduces median peak by about 13.2 percent for increasing shapes
and 7.5 percent for largest-first shapes. In every paired round, increasing-shape
peak is lower by 13.45 to 18.50 MiB and largest-first peak by 6.25 to 10.47 MiB.
Repeated same-size work is essentially unchanged. The small-job difference is
minor and varies between rounds.

Unlike the earlier growth-only result, the changing-shape benefit appears in
absolute process peak as well. This is still a bounded, small-sample experiment
on one host. It does not establish a universal memory bound or a formal performance
baseline. Raw growth, current footprint, malloc live bytes, peak and post-release
snapshots remain in the evidence rather than being collapsed into one metric.

Logical workspace release and reservation release both succeed. Physical footprint
does not necessarily fall immediately, because macOS can retain freed allocation
pages. Planning removes resize churn during a batch; it does not replace the
allocator's reclamation policy between batches.

## Timing

Times below are milliseconds for 36 fits. Fit time includes fitting, prediction,
state export, route inspection and stream drain. Complete batch time also includes
planning, admission, input construction, diagnostic checks and explicit release.
Warmup and later independent reference fits are excluded. Setup is the planned
policy's complete pre-measurement setup, including planning and admission; it is
not a separately isolated LAPACK query cost.

| Workload | Arrays fits | Planned fits | Arrays batch | Planned batch | Planned setup | Paired fit change range |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Small shapes | 113.56 | 111.40 | 125.34 | 123.23 | 0.126 | -3.95% to -1.05% |
| Repeated large shape | 4386.50 | 4447.67 | 4433.36 | 4495.40 | 0.131 | -0.52% to +2.99% |
| Largest shape first | 2313.91 | 2325.45 | 2377.26 | 2388.99 | 0.119 | +0.25% to +0.75% |
| Increasing shapes | 2312.33 | 2329.51 | 2376.27 | 2394.05 | 0.132 | -0.98% to +1.02% |

Negative paired changes mean planned is faster. Small jobs are modestly faster
in these samples. Repeated large shapes and increasing shapes vary around parity;
largest-first fits are about 0.25 to 0.75 percent slower in each paired round.
Host timing drifts during the experiment, which makes paired comparisons and the
rotated order important. Do not claim a general speedup or proven equivalence.
The memory benefit is the useful finding.

## Reservation and error checks

Five standalone checks exercise the same planned-workspace helper used by the
benchmark:

1. Successful fit keeps the reservation while the arena remains owned, then
   releases the owner before finishing the grant.
2. An operation that throws after fitting releases both resources.
3. Cancellation after fitting, while the task still holds the workspace, releases
   its allocation and grant. This is cancellation at an asynchronous boundary,
   not interruption of an in-flight synchronous LAPACK call.
4. A cancelled queued batch never enables or allocates a workspace and leaves no
   reservation behind.
5. An intentionally undersized plan reaches the public fit method, returns a
   capacity error, leaves model parameters unset, and releases its reservation.
   It does not fall back to an unreserved gradient-descent fit.

The check budget permits one planned batch at a time. This does not establish
correctness for multiple active workspace instances, independent budgets, or
mixed CPU/GPU concurrency. Those remain integration work.

## Numerical and execution validation

The benchmark completes 64 fresh workers and 2,304 measured fits. Four profiles
run twelve cycles of three sequential fits:

- Small: 1,024 by 8, 4,096 by 32, and 8,192 by 8.
- Repeated large: 100,000 by 32 repeated three times.
- Largest first: 100,000 by 32, 8,192 by 128, and 100,000 by 8.
- Increasing: 100,000 by 8, 8,192 by 128, and 100,000 by 32.

All fits check 128 analytical held-out predictions, complete finite results,
exact repeatability, selected CPU route and zero active MLX bytes. All workspace
variants must record all 36 successful uses, so a silent solver fallback fails
validation. After releasing the workspace and reservation, every worker compares
coefficients, bias and predictions exactly against the original CPU solver through
a separately prepared row-array StandardScaler pipeline. These are deterministic
ordinary regression fixtures, not the full numerical certification corpus.

The separate planned increasing-shape worker passes 36 more fits under stack
logging and `leaks --atExit`. It reports zero leaks and zero leaked bytes, one
allocation, 36 successful uses and zero final reserved bytes. This is an exit-time
leak graph, not proof about every intermediate allocation. Total measured workload
fits are 2,340, excluding warmups, independent references and the standalone
lifecycle-check fits.

The Release build passes. The controller uses a 30-second lifecycle-check deadline,
60 seconds per timing worker, and 90 seconds for the leak scan. Workers and builds
run sequentially. Thread-count overrides and malloc diagnostic settings are removed
from normal measurements. Runs use AC power and all before/after memory-pressure
checks are normal. The leak scan runs only after timing finishes. No full production
test suite or CI run was needed for these disposable snapshot changes.

## Remaining integration work

Replace the process-global trial storage and lock with an explicitly scoped owner.
Tie its backing allocation and borrowed views to a reservation that survives every
active use. Preserve existing array-backed behavior for callers without a plan.
Define capacity errors separately from numerical fallback. Then validate overlapping
batches, cancellation during ownership transitions, repeated batch lifetimes,
and broader regression fixtures before moving the design into production.

A caller should declare its batch or execution scope, not tune allocator internals.
The library can derive backend scratch capacity from known dimensions. This keeps
the choice at a useful application boundary and avoids a global allocator override.

## Evidence

The engineering-note archive includes all samples, summaries, paired changes,
lifecycle and leak-check results, source fingerprints, controllers and the complete
snapshot patch. Full compiler and leak logs remain in the local evidence directory.
The original validated executable is restored after the build. Tracked production
files remain unchanged and nothing was pushed.
