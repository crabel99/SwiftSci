# Evaluating dataframe execution and storage choices

Status: evaluation protocol, recorded 2026-10-18. This record belongs to `codex/engineering-notes` and must not be merged into an implementation PR. It applies the [scientific computing charter](../../CHARTER.md) and the [decision record format](../../DECISION-RECORDS.md).

The objective is lower execution and memory cost for scientific and local-model workflows on Apple silicon. Polars is a reference implementation and an alternative source of algorithms. Beating one Polars timing is not the acceptance criterion.

## Decision order

A candidate first meets its behavior, precision, ownership, compatibility, and resource constraints. Compare costs only among candidates that pass those constraints. Keep speed and memory results separate when one improves at the other's expense. A weighted overall score needs an actual deployment workload and agreed weights.

Use these stages in order:

1. Qualify the comparison and its independent expected results.
2. Explain the proposed bottleneck and predict the change in work or storage.
3. Test one implementation change against a frozen SwiftSci control.
4. Check complete public workflows and interactions with other work.
5. Select a default, an explicit alternative, further research, or rejection.

A missing measurement is unresolved. It is not a passing gate.

## Freeze what the caller needs

Record the following before implementation. Use the same contract for control, candidate, and external references.

| Constraint | Required statement and check |
| --- | --- |
| Values and types | Preserve native integer widths and declared floating-point precision. Check large Int64 values with the existing lossless dataframe encoding, not a conversion to Double. |
| Missing values | Declare null handling separately from valid NaNs and infinities. Define which inputs belong to a timing contract. Undefined ordering cannot support a performance ranking. |
| Ordering | Declare sort direction, stable ties, null placement, column order, row identity, and signed-zero handling. |
| CSV responsibilities | Separate provided-schema ingestion from inference. Declare header, delimiter, quoting, encoding, malformed-input behavior, and which validation is timed. |
| Materialization | Declare the returned object, readiness, copies, dtype conversions, synchronization, and when the output owner is released. |
| Ownership | Preserve snapshots, alias isolation, mutation behavior, asynchronous lifetimes, cancellation, and cleanup. Count shared owners once. |
| Compatibility | State whether public interfaces and supported deployments change. A hidden full-array conversion is a cost, even if a source-compatible property hides it. |
| Resource limits | Declare maximum owned live bytes, retained bytes, concurrent requests, and failure behavior when admission fails. |

These are constraints on results and responsibilities. Implementations may choose different algorithms and native parallelism. UInt32 row positions do not authorize Float32 values or a smaller public row limit.

The current general column exposes `[T?]`; its compatibility behavior needs an explicit decision before a storage migration. Existing prepared numeric batches use Double values and validity words. They are a useful implementation precedent but do not authorize implicit Int64-to-Double conversion in the general dataframe.

## Explain the physical cost before tuning

For each alternative, record element strides, value and validity bytes, field metadata, permutation width, scratch buffers, and allocation ownership. Describe access order and the actively reused working set per task. Include the count of simultaneous tasks and in-flight chunks.

Predict the minimum logical bytes read, written, copied, or retained. Distinguish those counts from measured DRAM traffic. Cache reuse, shared allocations, allocator behavior, and processor caches can make them different.

Name the suspected limit: instruction work, branches, memory latency, memory bandwidth, allocation, synchronization, or insufficient independent work. Use profiling to challenge that explanation. Do not infer a cache miss, bandwidth saturation, or P-core placement from wall time alone.

For sequential stages, a time decomposition is useful. For overlapping CSV discovery and decoding, inspect the critical path and total elapsed time. Adding overlapping stage durations double-counts work.

The Roofline model provides a useful connection between work and sustainable memory bandwidth, but floating-point intensity alone does not model CSV parsing or sorting. Include their branches, indexing, and synchronization costs. [Williams, Waterman, and Patterson](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2008/EECS-2008-134.pdf).

## Use three levels of experiments

| Level | Purpose | Required output |
| --- | --- | --- |
| Mechanism | Determine whether a specific change reduces the predicted cost. | Kernel time, work or buffer counts, profiles, and a control that can falsify the explanation. This level cannot establish a public-workflow speedup. |
| Public operation | Measure complete CSV reading or stable sorting through the supported interface. | Full native output alive at timer stop, independent value and type checks afterward, preparation costs declared. |
| Complete workflow | Determine whether the intended application benefits. | CSV through selection, sorting or joining, matrix construction, and a checked numerical result or prediction, including packing, synchronization, and owner lifetime. |

Reuse existing scientific-workflow, persisted-workflow, boundary, and dataframe conformance definitions from the implementation branch. Qualify their actual adapters before using them as timing evidence. A correctness fixture is not automatically a matched performance benchmark.

For candidate comparisons, keep the downstream model, weights, precision, and backend fixed. This isolates the data-handling change. For external-library workflows, define the same mathematical result and timed responsibilities before comparing native implementations.

## Cover the operating regimes without testing every combination

The existing tiny, medium, and large tabular fixtures contain 129, 100,000, and 1,000,000 rows. Use them as anchors. Add bounded intermediate sizes around an observed crossover. Larger stress sizes require a declared memory budget.

Cover narrow and wide tables, duplicate-heavy and ordered keys, reverse and nearly ordered input, missing values, and mixed types. CSV cases include unquoted numeric input, quoted separators, escaped quotes, embedded newlines, uneven records, and encoding boundaries. Only benchmark behaviors with a defined common contract.

Choose representative combinations before tuning. Test interactions when the cost model predicts them, such as table width with chunk count or concurrency with workspace size. Reserve different seeds, sizes, and distributions for confirmation. Do not tune a threshold against its confirmation cases.

Evaluate one request, repeated requests, and bounded concurrent requests. Record the same outer request count for each implementation. Native inner parallelism remains permitted under `production-default`; configured pools are not measured active threads.

## Measure independent costs

| Metric | Scope and limitation |
| --- | --- |
| Elapsed time | Report per-case process medians and their spread. Keep mechanism and complete-workflow timings separate. |
| CPU work | Use process CPU-time deltas when available. Lower elapsed time can consume more CPU work. |
| Peak owned storage | Count live buffers and capacities through owners, including outputs, scratch, queues, and retained snapshots. A byte budget is based on live ownership. |
| Retained storage | Measure after declared completion and owner release, and over sustained repetitions. Allocator-retained RSS is not itself proof of a leak. |
| Process memory | Report fresh-process high-water RSS separately. It includes preparation, validation, and runtime overhead. Subtracting two high-water values does not isolate an operation's allocation peak. |
| Allocation and copying | Record allocation counts and logical copied bytes. Label source-based estimates and profiler measurements distinctly. |
| Energy and interference | Measure energy only with a suitable instrument. Otherwise mark it unmeasured. Check concurrent workload latency before claiming better system efficiency. |
| Complexity and maintenance | Record new interfaces, invariants, unsafe regions, fallback paths, dependencies, and obsolete code removed. Do not equate fewer lines with simpler behavior. |

Profiled and sanitizer runs establish mechanisms or safety. Use separate uninstrumented optimized builds for timing.

## Freeze the measurement plan before confirmation

Reuse the existing controller, checksummed datasets, worker receipts, and artifact audit. Do not create a second benchmark runner.

Record exact source and binary fingerprints, dependency versions, contracts, power source and settings, cache policy, backend, warmups, repetitions, engine order, and output lifetime. Separate requested compute units from observed CPU, GPU, or Neural Engine execution. Record fallbacks and unverified placement. Different precision or readiness requirements need separate contracts. Require AC power for this campaign. Stop or disqualify a run whose power settings change.

Screen with at least five independent process rounds. The current operation comparison uses two warmups and five timed samples in each process. Confirmation starts with ten paired process rounds, using counterbalanced control/candidate order. Set the final repetition plan from a pilot before confirmation; do not stop when a desired result appears.

Treat fresh-process rounds as the independent observations. Samples within one process share initialization and caches. Report paired effects, absolute saved time, and process-level uncertainty. A process-pair bootstrap interval is an analysis choice to preregister, not proof that five rounds guarantee a reliable interval. Keep exploratory case selection separate from confirmation. [Kalibera and Jones](https://kar.kent.ac.uk/33611/).

Before confirmation, write the minimum useful absolute improvement for each primary workflow and the tolerated slowdown for protected cases. Also write the live-memory budget and allowed retained storage. There is no universal five-percent rule. A large percentage on a microsecond operation can be less useful than a small percentage on a frequent large operation. Unset budgets or usefulness thresholds prevent promotion.

## Promotion gates and outcomes

| Gate | Pass requirement |
| --- | --- |
| Comparable | Identical timed responsibilities, required outputs, types, backend class, and declared environment policy. |
| Correct | Independent expected results and adverse cases pass without relaxing the contract or tolerances to fit the candidate. |
| Safe | Relevant ownership, mutation, lifetime, bounds, concurrency, and cancellation checks pass. |
| Within budget | Peak owned and retained bytes, concurrency, and workspace remain within the experiment's limits. |
| Compatible | Public behavior is preserved, or the proposed change has a separately resolved compatibility decision. |
| Repeatable | Independent confirmation supports the preregistered useful effect. Noise and adverse cases are reported. |
| Useful in context | Complete target workflows meet the declared benefit and protected-case bounds. |
| Maintainable | The implementation and its fallbacks have a clear owner, an explicit rationale, and reproducible evidence. |

Among feasible candidates, retain the choices that offer a useful tradeoff in time, CPU work, memory, or maintenance. A candidate worse in every relevant measured cost has no performance case. A materially faster but more memory-intensive candidate can be an explicit policy, subject to the same safety and budget gates. A default change needs evidence for its intended operating regime.

A size-dependent dispatcher needs a stable crossover on confirmation cases, including the cost of detecting the regime. A narrow kernel win with no useful workflow effect remains research. A noise-limited result is inconclusive. Record rejection and simplification as valid outcomes.

## Initial experiment register

[experiments.tsv](experiments.tsv) owns the initial questions and sequence. Every row is planned work, not an implemented or accepted change. Each experiment gets its own implementation commit and the existing [decision record](../../DECISION-RECORDS.md) before promotion. Combine winners only after separate qualification, then measure the combination and remove one change at a time to identify interactions.

Q0 now has [matched streaming and wine ingestion evidence](workflow-qualification.md), with complete output validation and scientific/persisted CPU conformance controls. Broader application-scale timing and memory qualification remain open. [S1 screening](row-gather-results.md) found specialization gains and a size-dependent row-parallel result. Its current dispatcher is not promoted. [Serial specialization confirmation](serial-specialization-results.md) isolates a smaller change with held-out mixed-table gains, a recorded small numeric-sort loss, and qualified production coverage. The four-case operation comparison alone does not qualify a new storage or scheduling policy.

## Check the current operation baseline

[check-tabular-baseline.py](check-tabular-baseline.py) reuses the implementation branch's artifact audit. It additionally rejects CSV v1, verifies actual schema evidence, checks source-map consistency, and checks unchanged AC power. It deliberately reports workflow, memory-tradeoff, and energy qualification as incomplete.

Run with the Python environment used by the benchmark and the current implementation checkout:

```bash
python check-tabular-baseline.py --repo /absolute/path/to/implementation \
  --run /absolute/path/to/matched-comparison/run.json
```

The qualifying implementation snapshot is local commit `7fb74d1982ae5e80b5896c87d2db211c6595e931`. Its source fingerprint is `886c4dbc723c4f7cf34e20c3a892694e4f02ca13008d17c5fe0368679d0c41f0`. The measured worker receipt retains its original working-tree provenance. Source equivalence was checked when that work was committed.

This record defines the evaluation process. The linked Q0 report records the completed ingestion qualification. Execution experiments, expanded application coverage, uncertainty analysis and promotion gates remain open.
