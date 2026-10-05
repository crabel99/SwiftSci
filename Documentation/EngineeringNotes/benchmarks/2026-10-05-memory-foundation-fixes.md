# Memory foundation fixes and qualification

## Decision and scope

Retain the memory trial with the corrected ownership and selection rules. This work qualifies a bounded prototype. It does not promote a new production memory API or establish a hard process-memory budget.

Implementation branch: `codex/memory-kernel-trial`.
Final implementation head: `80e9fcc4e266a313e4cc1a13e51a9a07cd36cb7e`.
Pre-fix comparison head: `59b77f7fd2200e62a1e3b7f4e040804bfb5e5892`.
The parent `codex/unified-memory-prototype` remains at `aa5c71968c080f4188357c4cb628389f89ca00a2`.

This record belongs only to `codex/engineering-notes`. It must not enter an implementation PR. The local evidence archive is `~/local-ai/spl/swiftsci/memory-foundation-fixes-20261005/`.

## Changes

| Commit | Change and reason |
|---|---|
| `0236d346ef` | Retain the imported MLX descriptor and its allocation lease until GPU completion, including errors after submission. A lease alone does not prevent MLX from donating and overwriting the input. |
| `9f2fad6241` | Use implicit ranges for contiguous maps and share equal identity/physical maps for irregular selections. Preserve distinct maps after materialization when positions differ from provenance. |
| `fe0bd23ec3` | Give managed allocations identities and report logical bytes, allocator capacity and allocation categories. Report MLX runtime counters separately to avoid adding overlapping aliases. |
| `4681184048` | Exercise the actual public regression pipeline through snapshots, including target alignment, training-only scaling, fallback and held-out prediction. |
| `373a46c8fa` | Correct hardware-routing thresholds and document that the current memory manager admits concurrent tasks rather than reserving bytes. |
| `80e9fcc4e2` | Reject incomplete prediction results, add NIST and wider routing checks, register foundation tests and remove the redundant index-map wrapper. |

The device import remains private and scoped to internal read-only GPU work. It synchronizes before releasing the retained descriptor. This establishes the synchronous adapter's ownership rule; it does not promise safe arbitrary external mutation or asynchronous cancellation.

A 100,000-row irregular selection now needs one 800,000-byte index payload when identity and physical maps coincide, instead of two equal payloads. Contiguous selections need no explicit index payload. The ledger measures unique owners and allocator capacity, with separate value, validity, row-index, matrix and scratch categories. Allocator padding is measured, never exposed as initialized elements.

## Validation

- The original donation probe reproduced 4,096 overwritten source elements when the imported descriptor was released early. Retaining it preserved every element.
- The new selection test failed on the old representation before the map change.
- The final CPU executable passed 587 scenarios, and the final mutation executable passed 151 scenarios.
- The registered Release test target passed six tests with no failures or skips. Those tests invoke the actual initialization, snapshot, selection, accounting, device-read and finalizer checks, including throwing paths after GPU submission.
- An earlier Address Sanitizer run passed 103 ownership and map scenarios. Its raw result remains attached to the recorded earlier inputs; it is not a new sanitizer run on the final head.
- The final public integration worker passed 44 workflows and eight additional checks. CPU, GPU and automatic routes were exercised at 999, 1,000 and 1,001 training rows with two and eight features.
- All 32 NIST comparisons passed. The eight linear-regression datasets ran through retained and materialized snapshots and an unscaled public CPU regression pipeline. Both original-decimal and binary64 references used the existing locked fixture identities and tolerances, with no new exclusions.
- The pre-review device run passed 13 scenarios and 54 measured processes, including source mutation and completed MLX-to-Metal handoff. The later regular test run revalidated the extracted shared device implementation. Its timing evidence remains historical at the recorded inputs.
- Twelve CSV/Parquet ingestion cases passed at 10,000 and 100,000 rows across three storage strategies earlier in this series.
- The corrected documentation example passed Swift 6 type checking.

The registered tests and first expanded integration run used staged source. Their manifests match the final source except for the later README clarification. The final CPU comparison and public workflow runs record the committed head and complete input hashes. This turn did not rerun every production module test or hosted CI.

## Final comparison against the pre-fix prototype

Three rotating fresh-process rounds used the same workflow and one warmup per process. The preserved control executable's hash was verified before reuse. The candidate was rebuilt at the final head. These are exploratory medians, with no confidence interval or predeclared regression threshold. Positive changes below mean slower execution.

| Input | Control workflow ms | Candidate workflow ms | Change |
|---|---:|---:|---:|
| 1,000 × 4, quantized, selection 90%, nulls 0% | 0.136 | 0.141 | +4.20% |
| 100,000 × 8, continuous, selection 90%, nulls 0% | 19.622 | 20.040 | +2.13% |
| 100,000 × 32, quantized, selection 50%, nulls 1% | 26.324 | 24.086 | -8.50% |
| 1,000,000 × 8, ordered, selection 90%, nulls 0% | 91.033 | 92.273 | +1.36% |

These results do not establish a general speedup. An earlier three-round comparison at `373a46c8fa` ranged from about 2% faster to 1.2% slower. Both runs are retained. The stronger evidence here is the checked ownership and allocation behavior, not small timing differences. Workflow time excludes source construction; the raw records contain construction, preparation and RSS separately.

## Actual public CPU workflow

Three fresh-process rounds rotated retained and materialized storage. Sorting/selection, compatibility conversion, fitting and held-out prediction are included in workflow time. Source construction is recorded separately. Reference calculations run after the timing and RSS snapshot. Both treatments retain the source during this comparison.

| Input | Treatment | Workflow ms | Compatibility bridge ms | Fit ms | Peak RSS MB |
|---|---|---:|---:|---:|---:|
| 1,000 × 4, ordinary | retain | 10.358 | 0.051 | 10.054 | 15.2 |
| 1,000 × 4, ordinary | materialize | 10.496 | 0.052 | 10.157 | 15.3 |
| 100,000 × 8, ordinary | retain | 79.111 | 6.951 | 41.201 | 53.6 |
| 100,000 × 8, ordinary | materialize | 83.972 | 5.585 | 41.549 | 60.9 |
| 100,000 × 8, noisy | retain | 79.495 | 6.437 | 41.079 | 53.6 |
| 100,000 × 8, noisy | materialize | 84.034 | 5.652 | 41.693 | 60.9 |

The consumer still materializes the nested arrays required by existing public protocols. This exposes conversion cost and preserves actual solver refinement, fallback and prediction behavior. It does not claim a zero-copy public regression pipeline. Retained-source results cannot predict workloads that release their source or reuse a gathered snapshot many times.

## Independent review

### Standards and ownership

The reviewer initially found missing normal-suite registration and a redundant map wrapper. Both were resolved. Final inspection found no remaining actionable standards or ownership findings in the reviewed change. The reviewer did not execute tests; the test results above are separate evidence.

### Specification

The reviewer initially found that truncated predictions could pass numerical checks, and that NIST qualification and threshold widths were incomplete. Count guards, negative cases, widths two/eight and the existing NIST contracts resolved those findings. Final inspection found no remaining actionable findings in that review. Numerical comparisons use independently locked answers where available, rather than treating agreement with the same solver as an independent certificate.

## Remaining engineering boundaries

The following work remains before broader production use:

1. Integrate prepared input through public estimator protocols if the goal is to remove nested-array conversion. Preserve current APIs and numerical behavior.
2. Design admission for managed peak bytes, including runtime workspace and fallback copies. Current accounting excludes Swift object metadata, compatibility arrays and external solver/runtime workspace; it is not total-process accounting.
3. Qualify arbitrary offset/extent imports and copy fallbacks, and cancellation before/after submitted work, before exposing a broader asynchronous device adapter.
4. Test memory pressure, source release, repeated reuse and real workload distributions before choosing default storage policies or chunked mutation.
5. Treat active LLM KV-cache growth and token/weight ownership as a separate consumer. Dataframe and regression checks do not qualify decoder memory.

No production tolerance, public numerical algorithm or deployment minimum changed. No branch was pushed, merged or submitted by this implementation task.
