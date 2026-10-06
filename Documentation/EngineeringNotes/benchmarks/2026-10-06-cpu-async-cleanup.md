# Asynchronous CPU workspace cleanup

Date: 2026-10-06. Production head: `530151b4fa700cdd55cca95dc43d4d5080469d2a` on `codex/memory-kernel-trial`.

## Decision

The CPU workspace prototype now has an explicit closing state and an asynchronous
close operation. Closing rejects later borrow attempts while existing native work
finishes. Multiple close callers join the same cleanup, including cancelled callers.
The final borrower frees the allocation before close returns, and the surrounding
scope releases its workspace reservation afterward.

Retained fitted models and prediction arrays remain usable after workspace cleanup.
This validates their independence from scratch storage. Persistent result accounting
has not been implemented here. The reservation still covers only workspace capacity.
No production source, allocator policy, public API or GPU lifecycle changed.

## Failing-before test

A standalone probe holds one native borrower open, starts close, then attempts a
later borrow. It requires the later attempt to be rejected before the active borrower
finishes. A watchdog releases the first borrower after two seconds so a blocking
implementation produces a verdict rather than hanging. Worker deadline is ten seconds.
The probe uses a short scheduling delay after the close task starts; the raw verdict
and controller are preserved rather than representing this as a deterministic scheduler.

Against the previous scoped owner, an adapter exposes its synchronous `end()` as an
async method. The old owner fails the contract:

- `late_borrow_rejected_before_active_borrow_finished` is false.
- `late_body_ran` is false in the observed run.
- Owned bytes eventually reach zero, so the failure is close-time admission rather
  than eventual deallocation.

The same probe passes ten fresh runs against the new owner. No watchdog release is
needed for the new owner to reject late work.

## Implementation

The previous owner used one lock across both native computation and close. The new
owner separates a short state lock from the exclusive numerical-borrow lock.

State transitions are open, closing and closed. Close takes the state lock, marks
closing, and either releases idle storage immediately or registers a checked
continuation. It suspends while a borrower is active. It does not hold a lock across
an asynchronous suspension. Existing numerical borrowers remain synchronous.

A borrow checks for open state before waiting for exclusive buffer access, then
checks again after acquiring that access. The second check handles a close racing
with a previously requested borrow. Only an admitted borrower can obtain the raw
partitions. Its defer path runs after either successful computation or a thrown error.

The borrower completion path marks the owner idle. If closing, it frees storage,
marks closed, takes the waiting continuations, and resumes them outside the state
lock. Repeated close calls observe the same completed release. A closed owner cannot
reallocate storage. Lifetime and capacity failures continue to bypass numerical
fallback in the model adapter.

Cancellation of a close caller does not abandon cleanup or free active storage.
Close waits for native completion. This is deliberate because task cancellation
cannot safely interrupt LAPACK or invalidate an outstanding raw pointer.

The state snapshot can now observe closing and active use without waiting for the
entire numerical borrow. Deinitialization remains a fallback for an unclosed owner
with no active borrower. The owner is retained by active methods and awaiting close
calls; raw pointers remain internal to synchronous numerical operations.

## Native race and sanitizer checks

A separate standalone executable repeats the owner lifecycle 100 times in each of
three builds: optimized Release, Address Sanitizer and Thread Sanitizer. All 300
iterations pass. The sanitizers report no detected address errors or data races.
These are owner-level tests, not sanitizer coverage of the entire SwiftSci library,
Accelerate internals, MLX or GPU execution.

Each iteration holds an active borrower, requests a contending borrower, begins
close, starts another close caller, cancels one closer, and attempts another borrow.
The active allocation must remain owned and neither closer may finish early. After
the active borrower exits, the contending request must be rejected, both closers must
finish, and allocation and release counts must each equal one. Half the active
borrowers return normally and half throw. A final weak-reference check verifies ARC
fallback after an unclosed, unborrowed owner is dropped.

## Real-model integration checks

Twenty fresh Release workers pass the expanded cleanup checks. They retain all the
previous independent-owner, overlapping-budget, queued-cancellation and insufficient
capacity checks, and add:

- A fitted model returned from the workspace scope produces the same predictions,
  coefficients and bias after close. Another workspace can fit a different input
  without changing that retained model or the previously exported predictions.
- Close publishes closing while a borrower is still active and the allocation
  remains owned.
- Two additional close callers join scope cleanup. Cancelling one does not release
  the reservation early.
- A new borrow is rejected while closing, before the active borrower exits.
- A waiting budget request remains queued until the final borrower drains and the
  old allocation is released.
- Successful and throwing borrowers both release exactly once. All close waiters
  are resumed and removed. A later repeated close changes no counters.

Each integration worker performs twelve successful scoped model fits, excluding
independent reference fits and deliberately rejected fits. All fitted outputs are
checked against the original array-backed CPU solver. These checks exercise real
model state, not a mock retained result.

## Focused performance comparison

Two fresh workers per profile and policy, with reversed policy order on the second
round. Each worker runs twelve cycles of three fits. The prior scoped-owner binary
and the new asynchronous-close binary are fingerprinted separately. Both retain the
same batch-planned capacities and numerical algorithm.

Peak values are median process peak physical footprint in MiB, observed through the
measured fits. Fit times are median milliseconds for 36 fits. Paired changes compare
new versus prior within each round; negative means faster. These are a regression
smoke comparison, not a formal baseline or a statistical equivalence claim.

| Workload | Prior peak MiB | Async peak MiB | Prior fit ms | Async fit ms | Paired fit change |
| --- | ---: | ---: | ---: | ---: | --- |
| Small shapes | 10.97 | 10.17 | 117.22 | 116.85 | -0.73% to +0.10% |
| Repeated large shape | 82.11 | 82.26 | 4810.18 | 4791.99 | -0.52% to -0.23% |
| Largest shape first | 89.43 | 94.41 | 2755.42 | 2736.98 | -0.73% to -0.61% |
| Increasing shapes | 101.64 | 101.64 | 2676.66 | 2687.77 | -1.59% to +2.47% |

The samples retain complete batch timing, planning and admission time, allocator
statistics, post-release observations and numerical results. One allocation serves
all 36 fits in each planned worker. Every reservation is zero after workspace close.
Physical memory can remain resident after release because allocator-held freed pages
are distinct from live owned allocations.

## Largest-first memory control

The original two largest-first pairs show 4.41 and 5.55 MiB higher peak in the new
binary. The difference is already present at inputs-ready, before arena allocation:
4.42 and 5.86 MiB. Live malloc bytes are nearly identical. Growth during the measured
fits is about 26.4 to 26.7 MiB in both implementations, consistent with the unchanged
25.95 MiB planned workspace plus runtime activity. Logical cleanup returns live
malloc bytes to about 1.27 MiB in every sample.

That observation locates the difference before the workspace borrows or closes; it
does not by itself establish why input preparation retains different physical pages.
A follow-up control runs the same largest-first workload with workspace reuse enabled
and disabled in both binaries. Four workers per combination rotate through every
position. All sixteen workers and their 576 fits pass numerical and cleanup checks.
The control had a Python printing-variable error after its first worker; that completed
worker was preserved and the corrected controller resumed the remaining cases.

| Binary | Workspace reuse | Inputs-ready MiB range | Peak MiB range | Fit growth MiB range |
| --- | --- | --- | --- | --- |
| prior | False | 65.55 to 76.27 | 99.42 to 110.16 | 33.88 to 34.88 |
| new | False | 57.84 to 72.41 | 92.77 to 107.09 | 34.09 to 34.92 |
| prior | True | 69.88 to 80.14 | 96.34 to 107.61 | 26.44 to 27.47 |
| new | True | 65.61 to 82.41 | 92.06 to 109.11 | 26.45 to 27.48 |

The control shows substantial inputs-ready and peak variation in both binaries,
including when the workspace is disabled. The planned-workspace peak ordering
changes between rounds. Fit growth with reuse stays about 26.4 to 27.5 MiB for
both owners, versus about 33.9 to 34.9 MiB with ordinary arrays in this control.
These observations do not support attributing the original larger peak to failed
workspace cleanup or claiming an improvement in whole-process peak.

The control records separate whole-process peaks and growth rather than treating
normalized growth as proof of an unchanged total peak. The exact input-construction
and allocator cause is not isolated here. No physical-memory equivalence claim is
made for the new binary. The original higher peaks remain part of the evidence.
No allocator setting was changed to suppress the difference.

## Leak checks and execution scope

Two separate stack-logged workers run after normal timing. One runs the cleanup
integration checks; the other runs the 36-fit increasing-shape workload. Both
process-exit leak scans report zero leaks and zero leaked bytes. Their workspace
reservations finish at zero. Exit-time scans supplement the explicit lifetime
checks; they do not inspect every intermediate ownership graph.

The initial comparison and memory control contain 1,152 measured fits. The twenty integration workers add 240
successful scoped fits, and the two leak workers add twelve and 36. Total successful
workload fits are 1,440, excluding warmups and independent references. Native lifetime
probes do not train models and are counted separately.

The full isolated Release build passes. Normal measurements remove allocator
diagnostic settings and thread-count overrides, use AC power and check memory
pressure before and after each worker. All observed comparison pressure levels are
normal. Builds, sanitizer executables, comparison workers and leak scans run
sequentially. Concurrency occurs only inside the bounded ownership test workers.
No full production suite or CI run was performed for this disposable snapshot.

## Remaining integration decisions

The numerical borrow remains a synchronous exclusive section. A competing borrow
can still wait on a thread; this phase makes close asynchronous, not every solver
operation. A future async borrow interface needs its own scheduling contract.

GPU completion must use the backend's completion guarantees. This CPU state machine
does not establish a general asynchronous Metal or MLX lifetime mechanism. No global
cache flushing, cache eviction, persistent-owner reservation transfer or full-process
memory cap was added. Those concerns remain separate from safe scratch cleanup.

The implementation snapshot, controllers, source fingerprints and sanitized results
are preserved on the engineering-notes branch. The previous scoped prototype is
unchanged. The validated production executable is restored, the tracked implementation
checkout is clean, and nothing is pushed.
