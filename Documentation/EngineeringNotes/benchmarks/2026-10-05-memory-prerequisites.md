# Memory prerequisites before production integration

## Scope and decision

The three prerequisites are implemented and qualified on `codex/memory-kernel-trial`. Final head: `66aa51b86418c5eedac1908267d3332869f1cf15`. Production files under `Sources/` are unchanged from `80e9fcc4e2`. The parent prototype remains at `aa5c71968c080f4188357c4cb628389f89ca00a2`.

Commits:

- `bca786d631` adds whole-operation byte reservations and asynchronous ownership checks.
- `66aa51b864` adds the prepared-column experiment, completes range and test-cleanup checks, and records reproducible comparison entry points.

Keep this decision record only on `codex/engineering-notes`. Evidence is archived locally at `~/local-ai/spl/swiftsci/memory-prerequisites-20261005/`. Production interface integration remains a separate next step.

## Byte-budget admission

`ByteBudget` reserves a whole declared peak before starting an operation. A request larger than the configured limit fails immediately. Waiting requests acquire no partial reservation. The actor processes its queue in order, removes cancelled waiters, returns a grant if cancellation wins the handoff race, and releases each reservation idempotently.

Four real prepared-model jobs share one budget in the qualification checks. Device operations hold a reservation across submission and completion. Scope exits, including errors, release it. Input plans include retained data, possible copies, normalized columns, solver workspace and an explicit runtime allowance.

This enforces the sum of declared reservations for participating operations. It does not intercept allocators or guarantee a hard limit on RSS, MLX cache, operating-system overhead or unrelated work. Conservative estimates must be reviewed for each consumer before production adoption. In particular, the model trial uses a stated workspace/runtime allowance rather than claiming exact accounting for every internal library allocation.

## Asynchronous ownership

The device checks cover cancellation before admission, cancellation after submission, errors after submission and ordinary completion. A host-side gate exposes the lifetime between submission and scope completion; it does not force the GPU itself to remain busy. The imported descriptor, source owners and reservation remain retained until synchronization, including when the task is cancelled.

Subrange checks cover 15 nonempty offset/length combinations and eight rejected ranges. Page-compatible ranges share their actual pointer; other ranges take the copying path. Empty, negative and past-end extents fail before importing. Tests check every result value, unchanged source values and balanced owner release.

The reviewed consumer remains private and read-only. Arbitrary escaping mutable foreign arrays are not supported by this contract.

## Prepared input without nested row compatibility copies

`PreparedTrial.swift` selects features and targets through one snapshot, prepares compact columns once, scales through the existing prepared StandardScaler and dispatches to an experimental regressor protocol. Its CPU fit and prediction path does not construct nested row arrays. Counters require zero calls to the row-compatibility entry points.

The model adapter is generated from source-pinned production `LinearRegression` and loss implementations. It preserves QR, compensated refinement, gradient fallback and operation order while changing feature access. Both source hashes and equality with the checked-in generated artifact are verified by the benchmark build. The generated code belongs only to the experimental executable. No production protocol or public interface was changed.

Column preparation, normalized columns, GPU dtype conversion and solver workspace still require allocations. The claim is removal of nested-row compatibility copies from the measured candidate path, not allocation-free execution or zero-copy access for every consumer.

## Validation

- Nine registered Release tests passed, with zero failures or skips. They include admission, owner initialization, snapshots, row maps, allocation accounting, GPU reads, asynchronous ownership, ranges and finalizers.
- The unchanged compatibility path passed 44 workflows and 32 NIST comparisons.
- The prepared path passed 44 workflows, five additional checks and 32 NIST comparisons. Additional checks cover the underdetermined fallback, three invalid-input cases and shared admission for four model jobs.
- CPU fitted parameters and held-out predictions matched the unchanged production model exactly in the synthetic workflows. GPU comparisons retained their existing tolerance.
- Both decimal and binary64 NIST contracts passed at their existing tolerances. No numerical tolerance or exclusion changed.
- All 36 interleaved timing processes passed their result checks.

Validation ran on staged input files whose hashes match the final commit. The normal test scheme compiled the checked-in generated adapter; the benchmark build additionally regenerated and verified it. This was targeted prerequisite validation, not a full hosted-CI or whole-library certification run.

## Interleaved comparison

Three fresh-process rounds interleaved compatibility/prepared lanes and retained/materialized treatments. Both lanes passed their contracts before timing. Workflow time includes selection, preparation, fitting and prediction. Construction is reported separately. Admission precedes the timed candidate workflow; reference calculations run after timing and the RSS snapshot. Source input remains retained in both treatments.

Positive timing changes mean the prepared candidate was slower. These are exploratory medians without confidence intervals.

| Rows and data | Treatment | Compatibility ms | Prepared ms | Time change | Compatibility RSS MB | Prepared RSS MB |
|---|---|---:|---:|---:|---:|---:|
| 1,000, ordinary | retain | 8.19 | 9.11 | +11.2% | 15.3 | 15.3 |
| 1,000, ordinary | materialize | 8.73 | 8.39 | -3.9% | 15.4 | 15.3 |
| 100,000, ordinary | retain | 77.53 | 80.55 | +3.9% | 53.7 | 45.7 |
| 100,000, ordinary | materialize | 81.19 | 83.48 | +2.8% | 61.0 | 52.9 |
| 100,000, noisy | retain | 77.59 | 80.96 | +4.3% | 53.7 | 45.6 |
| 100,000, noisy | materialize | 81.71 | 82.77 | +1.3% | 61.0 | 52.9 |

At 100,000 rows, the candidate saved about 8 MB of peak RSS and reduced bridge time, with about 1% to 4% higher total workflow time. The 1,000-row retained case was about 11% slower, while its materialized counterpart was about 4% faster. These results support a memory-versus-time choice; they do not establish a universal faster default.

## Review

### Standards and ownership

The reviewer found missing empty-range handling and test cleanup that could leave a worker suspended after a failed assertion. Empty/invalid ranges now fail before import. Error cleanup cancels the worker, opens its gate and awaits completion. Queue polling has a deadline and cleanup. Final review found no remaining actionable findings in those fixes.

### Specification

The reviewer found that the original runner did not invoke the new prepared endpoints. The prepared option now selects those checks, NIST contracts and timing cases. The comparison runner requires both paths to pass before measuring either. It also verifies zero row-compatibility calls. Final review found no remaining actionable findings.

## Next decision

Use this evidence to choose the production prepared-input interface and admission-estimate ownership. Preserve existing callers, supported algorithms and numerical contracts during that integration. The current experiment proves the prerequisite mechanisms and their tradeoff; it does not choose a new production default.

No changes were pushed or submitted.
