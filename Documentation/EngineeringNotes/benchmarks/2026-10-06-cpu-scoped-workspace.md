# Scoped CPU workspace ownership

Date: 2026-10-06. Production head: `530151b4fa700cdd55cca95dc43d4d5080469d2a` on `codex/memory-kernel-trial`.

## Decision

The disposable scoped owner passes the bounded lifetime and overlap checks and
preserves the batch-planned workspace's changing-shape memory benefit. It is a
better integration candidate than the process-global trial. Each batch owns one
allocation, supplies that owner explicitly to its models, and holds a workspace
reservation until close has drained synchronous borrowers and freed the allocation.

This phase changes only an isolated source snapshot. Production sources, defaults,
allocator settings and public APIs remain unchanged. The next implementation step
is to move the owner and its lifetime checks into the memory-kernel integration,
with a deliberate policy for synchronous close. Broader estimator coverage and
full production validation still precede adoption.

## Ownership contract

The trial removes the process-global storage, enable flag and lock. Each workspace
has its own planned capacity, pointer, lock and closed state. Models receive an
optional owner through their initializer. Existing callers use the original
array-backed solver. No task-local inheritance or implicit process-wide selection
is involved.

The scope acquires a MemoryBudget reservation before creating the owner. The first
fit allocates the planned capacity. Every subsequent fit borrows partitions of that
same allocation while holding the owner's lock. A second owner has a different
lock and allocation. A nested-borrow check accesses both owners while the first
remains borrowed and verifies distinct pointers and independent contents.

Close takes the same lock as a borrow, waits for any current synchronous borrower,
frees the allocation and permanently marks the owner closed. Repeated close is
safe. Only after close returns does the scope release its reservation. Strong
references retained by a model cannot reopen a closed owner. Attempts to fit with
that owner fail with a distinct lifetime error. Capacity and lifetime errors both
bypass the numerical solver fallback. A failed owner initializer refunds its grant.

Snapshots take the lock and therefore describe a quiescent owner. Their zero
active-borrow field is not evidence of simultaneous execution. Overlap evidence
comes from controlled lifetime gates, two held allocations, independent-buffer
checks, and the separate last-borrow admission check.

The reservation covers the arena only. It excludes prepared inputs, model state,
other solver temporaries, allocator caches and process runtime memory. Freed pages
may remain resident after logical release. This does not establish a process-wide
memory cap or resolve the earlier strict footprint-coverage failure.

## Lifetime and overlap checks

Twenty fresh Release workers each run thirteen check groups. All pass. The groups
cover independent buffers, idempotent close, normal completion, thrown errors,
escaped closed-owner rejection, insufficient capacity without fallback, constructor
failure, overlapping allocated batches, queued cancellation, cancellation isolation,
replacement admission, continued numerical correctness, and final-borrow lifetime.

The overlap scenario uses different 1,024-by-8 and 2,048-by-8 inputs. Each batch
performs three fits, then retains its allocation at a gate. Their shared budget
exactly covers both workspace plans. A third request queues and is cancelled before
its operation can create a workspace. Cancelling the first live batch releases only
its allocation and reservation. A replacement batch can then enter while the second
remains live. The surviving batch performs another fit before closing. Predictions,
coefficients and bias match the original array-backed CPU solver exactly. All ten
successful scoped fits per check worker are accounted for. Independent reference
fits and deliberately rejected fits are excluded from that count.

A separate test returns from the scope's operation while a detached synchronous
borrower still holds the workspace lock. The next reservation must remain queued.
Only after the test releases that borrower may close finish and the next grant be
admitted. The borrower checks its buffer contents before returning. At completion,
the owner is closed, its owned bytes are zero, its use count is one, and all grants
are released. The test-only borrow entry point never exposes raw pointers to the
caller.

Cancellation checks occur at asynchronous checkpoints. They do not interrupt a
running LAPACK call. The implementation waits for synchronous work to return.
The overlap scenario proves independent ownership across live batches, not a
throughput speedup or a prescribed amount of simultaneous LAPACK execution.

## Memory comparison

Three fresh workers per profile and arm, with rotated arm order. All arms execute
36 fits per worker. The array arm and scoped arm use the new executable. The global
planned arm uses the previous fingerprinted executable. Both snapshot manifests
are retained. Unchanged solver numerics and prepared inputs are validated for
every measured worker.

Values are median whole-process peak physical footprint in MiB, observed through
the end of the measured fits. Warmup and input construction are included in the
peak; later independent numerical reference fits are excluded.

| Workload | Arrays | Global planned | Scoped planned |
| --- | ---: | ---: | ---: |
| Small shapes | 11.16 | 10.94 | 10.95 |
| Repeated large shape | 82.09 | 82.13 | 82.09 |
| Largest shape first | 93.70 | 85.30 | 85.28 |
| Increasing shapes | 116.94 | 102.69 | 102.67 |

The scoped owner retains the useful saving for changing shapes. It does not reduce
repeated same-size peak, and the small-case differences are minor. Each planned
batch allocates once, completes 36 workspace uses, and releases its reservation.
The small plan is 1,130,496 bytes. Each large plan is 27,213,824 bytes, below the
trial's 32 MiB capacity ceiling.

## Timing comparison

Median milliseconds for all 36 fits. Fit timing includes fit, prediction, model
state export, device-route inspection and stream drain. Complete batch times,
including planning, admission, input construction, diagnostics and close, remain
in the numeric summary. The paired range compares scoped and global planned
workers within the same round. Negative changes mean the scoped version is faster.

| Workload | Arrays | Global planned | Scoped planned | Scoped versus global paired range |
| --- | ---: | ---: | ---: | --- |
| Small shapes | 105.18 | 103.14 | 104.28 | +0.31% to +2.11% |
| Repeated large shape | 4279.88 | 4219.15 | 4203.88 | -1.98% to -0.30% |
| Largest shape first | 2428.51 | 2370.30 | 2399.33 | -0.16% to +1.23% |
| Increasing shapes | 2348.68 | 2415.07 | 2428.10 | -3.02% to +2.08% |

These small samples do not establish a general speedup or statistical equivalence.
The ownership change does not show a large timing penalty in these workloads.
No overlapping-batch throughput benchmark was run in this phase.

## Leak and numerical evidence

The comparison completes 36 workers and 1,296 measured fits. Every worker checks
128 analytical held-out predictions per fit, exact repeatability, complete finite
model output, and the requested CPU route. After workspace and input release,
independent row-array preprocessing and the original CPU solver must reproduce
predictions, coefficients and bias exactly. These deterministic regression fixtures
are not a substitute for the full numerical certification corpus.

Twenty ownership workers contribute 200 successful scoped fits. Separate stack-logged
leak workers repeat the ownership checks and the 36-fit increasing-shape sequence,
adding ten and 36 successful fits. Total successful scoped/comparison workload fits
are 1,542, excluding warmups and independent references. Both process-exit leak scans
report zero leaks and zero leaked bytes. Exit scans do not prove absence of every
intermediate retained object; the explicit ownership checks address those lifetimes.

The Release build passes. The initial build caught a prohibited semaphore call in
an async test context. The final test uses a nonblocking synchronous poll helper.
No production change was needed. Test workers have a 30-second deadline, comparison
workers 60 seconds, and leak workers 90 seconds. Builds, comparison workers and leak
workers run sequentially. Only the intentional ownership tests overlap tasks within
one bounded worker. All before/after comparison memory-pressure checks are normal.
Normal timing removes malloc diagnostics and thread-count overrides and uses AC power.

## Integration limits

Close currently blocks the calling thread until a synchronous borrow returns. This
is safe for the tested finite CPU solver operations, but it is a scheduling choice
that must be reviewed before broad async use. It is not an asynchronous GPU resource
owner and must not be extended to GPU completion by merely reusing this lock.

The raw-buffer callback is internal to the solver module. Production integration
must retain that restriction and prevent pointer escape or reentrant close from
inside a borrow. The disposable public trial-borrow method exists solely for the
lifetime test and should not become a production API.

No full production test suite, Thread Sanitizer run, Address Sanitizer run or CI
run was performed on this isolated snapshot. There is no production-readiness claim.
The original validated executable is restored after each build. The tracked
implementation checkout stays clean and nothing is pushed.

## Evidence location

The engineering-notes archive includes sanitized results, source fingerprints,
controllers and the complete snapshot patch against the production head. Raw compiler
and leak logs remain local. The engineering-notes branch is kept separate from code
branches and must not be merged into a production PR.
