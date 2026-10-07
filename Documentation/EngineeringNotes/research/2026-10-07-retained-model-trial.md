# Retained CPU model ownership trial

Date: 2026-10-07

## Scope and decision

Extend the local `codex/retained-memory-accounting-trial` branch with one real CPU regression owner. Keep the submitted prepared-memory PR unchanged while qualifying the ownership interface.

- Previous trial head: `53ee8dbcb86396eac01a1e258ded10ff595d8a2f`.
- New trial head: `dc7b276d137436205dc745a5184d3055212f836e`.
- Production dependency: PR #62, head `2cd1cbe52a12537d472fd2176eae2676e30dcc80`.
- New declarations are package-only. Existing public regression behavior is unchanged.

The owner keeps its fitted `LinearRegression` private. Returned predictions provide immutable scalar access while retaining their reservation. An escaped model, parameter array, or raw buffer cannot bypass that owner. Caller-created copies of scalar values need their own accounting.

## Ownership and failure behavior

A refit reserves its additional peak while the old model remains alive. It builds and fits a separate candidate using the existing CPU solver. Failure or cancellation before publication preserves the previous model. A successful candidate takes ownership of its retained grant before replacing the old state. The owner then frees the old model and returns its grant.

A refit whose old state plus new estimate exceeds the budget fails before queueing. Otherwise it could wait forever for space that only its own completion could release. Other retained results can still block admission; their callers must release them when needed.

The actor rejects overlapping operations while fitting, predicting, or resetting. Reset works in a cancelled task and leaves previously returned prediction owners valid. A completed Swift Task also retains its return value. Releasing a local prediction variable alone does not return that reservation if its Task handle or another owner still exists.

## Validation

The final Release run passed 210 regression and preprocessing test definitions, with 240 parameterized executions, zero failures, and zero skips. Eight new tests exercise complete fit/predict/refit/reset workflows, exact prediction agreement, numerical fitting failure, queue cancellation, cancellation racing admitted work, refit capacity rejection, prediction errors, model destruction, and concurrent prediction readers.

The cancellation race test observes the monotonic admitted peak. It accepts either successful completion or cancellation and checks the corresponding model state and cleanup. It does not claim deterministic interruption inside LAPACK or force cancellation immediately after transfer. The earlier strict post-admission version also passed, but the final test avoids depending on cancellation winning a scheduler race.

This increment ran the real pinned MLX dependency and existing CPU regression implementation. It did not rerun the entire SwiftSci suite or apply sanitizers to the new model owner. The prior handoff-only sanitizer qualification remains evidence for that earlier, smaller scope.

## Comparison

Each fresh worker performs a fit, three predictions whose results stay alive, a refit, and another retained prediction. Direct and retained-owner modes use the same numerical implementation, inputs, and output lifetimes. Five samples per mode and size alternate their execution order. Only one native worker runs at a time.

| Rows × features | Direct median ms | Retained median ms | Direct peak MiB | Retained peak MiB |
| --- | ---: | ---: | ---: | ---: |
| 1,000 × 4 | 10.68 | 10.51 | 19.95 | 20.06 |
| 100,000 × 8 | 63.06 | 62.62 | 37.50 | 37.55 |

The ranges overlap. These results show no clear added overhead for the tested workflow; they do not establish a speedup. Every corresponding prediction matched bit for bit across all 20 workers. Recorded retained-byte totals matched the model and four prediction estimates, and every worker returned its reservations to zero after cleanup.

Input construction and verification are excluded from timing. Process high-water RSS includes input construction and is sampled before verification copies. Coverage instrumentation was absent. Threads used their native environment defaults. The comparison ran on Apple silicon using Swift 6.4 and macOS 27.

Comparison binary SHA-256: `660c32676ed7affd94eff93c3b746e96f791c48433ca177646db64f5222e1a5c`.

`comparison/provenance.json` records the measured source hashes. They match the final source and package files. The final increment after timing changed only cancellation tests. The local evidence directory `retained-model-trial-20261007` retains build commands, test summaries, raw comparison samples, source hashes, and the accounting audit.

## Standards

Independent review found no documented-standard violations or actionable code smells. Actor isolation matches the repository's concurrency guidance. The prediction owner's unchecked Sendable conformance is limited to immutable reads; its only write frees storage after the last owner disappears.

## Spec

Independent review found one partial requirement: cancellation tests initially stopped at queueing. The added admitted-work race test covers both fit and prediction and checks the previous or committed model according to the outcome. Review identified no confirmed ownership, reentrancy, or comparison defect. The test explicitly permits legitimate completion races.

Review totals: zero standards findings; one spec coverage finding addressed. No production defect was confirmed by the review.

## Remaining qualification

Memory estimates still come from the caller. They describe participating live storage, not allocator measurements, cached MLX allocations, or a process RSS cap. Zero remaining reservations proves admission cleanup; it does not prove that every backend cache has returned memory to the operating system.

Before promotion, qualify shared matrix and MLX storage, asynchronous backend completion, and the public ownership interface. Multiple independently retained outputs require plans that avoid double-counting and callers that release outputs before awaiting otherwise impossible work. Keep this trial local and separate from existing PRs until those decisions and the broader integration checks are complete.
