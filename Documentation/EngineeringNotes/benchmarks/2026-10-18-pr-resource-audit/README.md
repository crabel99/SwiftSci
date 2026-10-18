# Resource-efficiency audit of our SwiftSci PRs

Reviewed October 18, 2026 against the [library-wide engineering objective](../../CHARTER.md#resource-efficiency-across-the-library). Scope is all 27 merged `Nodibell/SwiftSci` PRs authored by `crabel99`, plus the separate MLX SIMD repair. The upstream snapshot is `e005efcc1dd55bb40f9e1ad63ac29e2d29de5178`.

Subsequent measurement: the [first matched CPU/memory study](../2026-10-18-pr-resource-metrics/README.md) now qualifies selected workloads from #39, #45, #70, and #82. It records CPU reductions as well as memory gains and two remaining memory tradeoffs. The retrospective findings below retain their original evidence boundary.

## What the audit establishes

We have made several explicit resource tradeoffs and accepted some workload-specific latency losses. The evidence does not establish that our production changes generally increased CPU cost per correct result. Many changes remove conversions, copies, temporary arrays, repeated device setup, or repeated model loading. Those reductions remain valuable under the revised objective.

The main weakness is measurement. Most performance qualifications established elapsed-time improvements, numerical agreement, and ownership behavior. They did not establish total CPU cost per request. Process peak memory often includes model fitting and fixture construction, so it cannot consistently isolate the operation's live storage. Lower latency and lower process RSS are useful evidence, but neither establishes lower total resource cost by itself.

The highest-priority defaults to requalify are CSV parsing and parallel dataframe gathering. Reusable inputs, model sessions, and stronger arithmetic require a different decision: use them only when the workload justifies their retained memory or precision cost. We should preserve those choices and measure their break-even points.

No code was reverted, no benchmark was rerun, and no PR was changed for this audit. Historical results and acceptance rules retain their original meaning. These engineering notes stay on `codex/engineering-notes`.

## Concrete costs found in the record

### More concurrency can consume much more CPU

The eight-model CPU admission experiment has operation-batch CPU measurements. For the same eight wide jobs and shared scaled input, allowing eight concurrent jobs instead of one changed the median batch from **953.48 to 302.91 ms**, while aggregate CPU time increased from **0.963 to 2.323 seconds**, about **141% more CPU time**. Peak process memory increased from **94.4 to 283.4 MB**. These are decimal MB.

The larger GPU experiment gained no throughput by increasing admitted GPU fits from one to four. Batch time changed from **1,336.74 to 1,354.57 ms**, host CPU time rose from **0.692 to 0.837 seconds**, and peak process memory rose from **33.5 to 40.8 MB**. Host CPU excludes the GPU's own resource cost.

These were caller-selected admission experiments associated with the APIs introduced in [#62](https://github.com/Nodibell/SwiftSci/pull/62), not a change that silently increased default concurrency. They support conservative resource budgets, not removal of concurrency support. CPU accounting sums process user and system time around the task batch, after shared-input setup and before independent reference checks. The results do not measure energy.

Sources: [CPU admission study](../2026-10-05-concurrent-admission.md), [mixed-device study](../2026-10-05-mixed-device-admission.md), and [preserved selected raw records and medians](admission-evidence.json).

### Prepared storage is beneficial only for the right lifetime

[#83](https://github.com/Nodibell/SwiftSci/pull/83) explicitly offers compact prepared prediction inputs alongside existing transformed-input workflows. For 4,096 selected rows and 128 features, its recorded hot-cache sequence used **30.42 MiB** process peak instead of **54.38 MiB**, but took **38.08 instead of 31.03 ms**. At 8,192 rows, compact preparation used about 46% less process peak memory and about 39% more elapsed time. Those are single memory probes for each route, not repeated allocation distributions.

The compact option repeats transformation work that a transformed cache has already paid for. A snapshot can also retain a large source table for a small selection. Its benefit depends on reuse, selection density, source lifetime, and eviction. Existing prediction defaults were unchanged. This is a useful caller choice whose total CPU cost remains to be measured.

The device-reuse study underlying [#63](https://github.com/Nodibell/SwiftSci/pull/63) also recorded mixed retained-input process RSS rising from **316.0 to 333.5 MiB**, while large consumed-input RSS fell from **209.7 to 187.7 MiB**. The production change retains one Metal device, not request buffers. The observed increase does not isolate a leak, driver allocation, or cache effect. [Device qualification](../2026-10-07-device-production.md).

Core ML input pools and persistent sessions in [#65](https://github.com/Nodibell/SwiftSci/pull/65) and [#68](https://github.com/Nodibell/SwiftSci/pull/68) make a similar trade: retain model/input capacity to avoid repeated setup. Idle retained storage still consumes capacity. A reservation ledger is a policy accounting mechanism, not a measurement of physical allocation.

### Some elapsed-time regressions were accepted and disclosed

- [#82](https://github.com/Nodibell/SwiftSci/pull/82) improved throughput but increased saturated eight-caller dense P95 latency by about **10–15%**. Its separate fixed-arrival study improved response time and backlog. Neither study establishes lower CPU time per completed request.
- [#84](https://github.com/Nodibell/SwiftSci/pull/84) slowed the one-row, seven-feature CPU control by about **0.6 microseconds**. Larger workloads improved. It also changed converted-input finite validation from early exit to a full reduction, so malformed input near the beginning is a useful adverse case for resource measurement.
- [#44](https://github.com/Nodibell/SwiftSci/pull/44) accepted a small large-input variance timing cost while removing an input-sized temporary and correcting difficult numerical cases. The old wrong answer is not an equivalent cheaper alternative. Compensated dot products and original-decimal ANOVA remain explicit accuracy choices.

These are specific costs, not evidence that each complete PR made the library less efficient. See the [precision comparison](../2026-09-28-performance-comparison.md) for the accuracy contracts and historical timings.

### The latest parallel sort is not a merged PR

The local radix experiment reduced million-row sort time from **21.08 to 12.18 ms**, while aggregate CPU time increased from **33.48 to 42.95 ms**, about **28.3%**. It is already parked as a latency alternative under the revised objective. Do not attribute that experiment to one of the merged PRs. [Recorded experiment](../2026-10-18-dataframe-evaluation/parallel-sort-results.md).

## PR-by-PR assessment

“CPU unmeasured” means this review did not establish a matched, operation-scoped before/after CPU result. It does not mean the code is inefficient. Source reductions establish fewer explicit allocations or passes, but not a measured net CPU saving. Detailed source and receipt references are retained in [the findings](findings.json).

| PR | Scope and caller effect | Resource assessment | Disposition |
| --- | --- | --- | --- |
| [#38](https://github.com/Nodibell/SwiftSci/pull/38) | Existing descending sort with missing values | Restores correct ordering. No resource regression established. | Keep correctness fix. |
| [#39](https://github.com/Nodibell/SwiftSci/pull/39) | Default dataframe, CSV, sorting, grouping, filtering | Removes repeated conversions and materialization. CSV gains a two-pass record index and up to eight workers; sufficiently large gathers parallelize columns. Wall-time/RSS wins do not establish total CPU savings. | Highest-priority default resource requalification. |
| [#41](https://github.com/Nodibell/SwiftSci/pull/41) | Validation and benchmark infrastructure | Production source paths are a byte-identical CLI file rename. Added benchmark targets and fixtures cost development/CI resources, not ordinary dataframe execution. | Keep; budget suite execution separately. |
| [#42](https://github.com/Nodibell/SwiftSci/pull/42) | Existing Parquet read/write correctness | Correct page layout, schema, and Boolean packing. Present Boolean payload shrinks from bytes to bits and a concatenation copy disappears. CPU cost unmeasured. | Keep; profile valid Parquet workloads separately. |
| [#43](https://github.com/Nodibell/SwiftSci/pull/43) | Numerical, model-state, persistence repairs | Residual refinement and scaled cosine add work for correctness. Other changes repair state and persistence. No equivalent-correctness CPU regression established. | Keep; investigate a cheaper correct algorithm only with the same accuracy gate. |
| [#44](https://github.com/Nodibell/SwiftSci/pull/44) | Default numerical repairs plus opt-in precision | Default variance removes a large temporary but has a measured small latency cost; stronger dot/decimal paths are explicit. CPU savings unproven. | Preserve accuracy choice and memory reduction. |
| [#45](https://github.com/Nodibell/SwiftSci/pull/45) | Compact numeric batches and existing conversions | Direct extraction and flat storage remove nested arrays and conversion work. Prepared storage has construction and retention costs. | Keep; measure complete reuse and mutation lifetimes. |
| [#48](https://github.com/Nodibell/SwiftSci/pull/48) | Pages CI | Avoids inappropriate fork deployments. No runtime change. | Keep. |
| [#49](https://github.com/Nodibell/SwiftSci/pull/49) | MLX and checkpoint benchmark tools | No production source/dependency change. Experimental precision costs were not silently adopted. | Keep experiments separate from production claims. |
| [#50](https://github.com/Nodibell/SwiftSci/pull/50) | Native Llama correctness and completion reporting | Correct inference plus bounded prefill, compact KV, tied embeddings, and final-position projection reduce storage/work. One 32,768-token diagnostic records 13.76 to 4.74 GiB peak MLX allocation; no total resource qualification. | Keep; qualify complete generation at matched quality. |
| [#52](https://github.com/Nodibell/SwiftSci/pull/52) | Polars/DuckDB and production-default benchmarks | No runtime change. Native thread scheduling improves comparison fairness but does not measure aggregate CPU efficiency. | Add resource dimensions without rewriting historical results. |
| [#60](https://github.com/Nodibell/SwiftSci/pull/60) | MLX dependency and compatibility | Required SIMD correctness/ownership fixes plus compatibility changes. Dependency upgrade is not a measured general efficiency gain. | Keep required fixes; isolate dependency effects in future comparisons. |
| [#61](https://github.com/Nodibell/SwiftSci/pull/61) | Existing Arrow imports | Removes per-row chunk lookup while retaining owned-copy semantics; fixes signed dates. No extra retained Arrow owner. | Keep; structurally less lookup work, total CPU not quantified. |
| [#62](https://github.com/Nodibell/SwiftSci/pull/62) | Prepared regression, explicit memory admission, GPU cleanup | Columnar flow removes row materialization. Admission and completion cleanup add necessary bookkeeping. Caller concurrency can greatly increase CPU and peak memory. | Keep ownership guarantees; calibrate caller budgets by resource cost. |
| [#63](https://github.com/Nodibell/SwiftSci/pull/63) | Prepared columns and GPU input/device reuse | Removes copies and repeated device setup. Some retained workflows have higher observed process peak. CPU/device cost remains incomplete. | Keep measured structural gains; recheck retention and one-shot cases. |
| [#65](https://github.com/Nodibell/SwiftSci/pull/65) | Opt-in scoped Core ML and reusable input | Retains prepared input and pool slots; still copies into each leased slot. Reuse amortizes conversion, but a one-use path can cost more. | Use explicit reuse/lifetime policy. |
| [#66](https://github.com/Nodibell/SwiftSci/pull/66) | Opt-in fitted preprocessing to Core ML | Removes full transformed-column and packed intermediates; bounded Double work remains for numerical semantics. | Keep reduced materialization; measure host and device separately. |
| [#67](https://github.com/Nodibell/SwiftSci/pull/67) | Opt-in end-to-end Core ML batch pipeline | Bounded windows limit pending and completed results; larger windows retain more storage for overlap. | Treat window size as resource policy, not automatic speed improvement. |
| [#68](https://github.com/Nodibell/SwiftSci/pull/68) | Opt-in persistent Core ML sessions | Removes repeated model/pool loading; keeps model and slot capacity resident between runs. | Use explicit residency/eviction budgets. |
| [#69](https://github.com/Nodibell/SwiftSci/pull/69) | Existing empty row selection | Preserves schema, requiring per-column work instead of a schema-less empty result. Existing nonempty dispatch unchanged. | Keep required output semantics. |
| [#70](https://github.com/Nodibell/SwiftSci/pull/70) | Default sufficiently large MLP prediction | Batches BLAS calls and adds bounded per-call scratch up to 256 KiB. Fewer calls and faster elapsed time; aggregate CPU unmeasured. | Requalify batch size against total CPU and concurrency, preserve small path. |
| [#71](https://github.com/Nodibell/SwiftSci/pull/71) | Opt-in prepared numeric matrices | Direct matrix preparation removes intermediate nested rows; retained matrices must pay for their reuse. | Keep; include creation and release in comparisons. |
| [#72](https://github.com/Nodibell/SwiftSci/pull/72) | Opt-in fitted preprocessing of matrices | Avoids row-array rebuilds; column-major scaled workflows record 9–16% longer elapsed time. | Choose layout for downstream consumers; measure complete conversion path. |
| [#81](https://github.com/Nodibell/SwiftSci/pull/81) | ONNX decoding correctness | Standard fields and packed doubles decode correctly. No measured CPU regression. | Keep interoperability fix. |
| [#82](https://github.com/Nodibell/SwiftSci/pull/82) | Existing compact gathers, extraction, matrix/scaler paths | Fewer copies and up to eight gather workers. Saturated tail latency worsens; matched-demand throughput/response improves. CPU efficiency unknown. | Highest-priority parallel default requalification. |
| [#83](https://github.com/Nodibell/SwiftSci/pull/83) | Opt-in fitted prediction snapshots | Compact retention saves measured process peak versus transformed caching but repeats preprocessing and can retain a large source. Churn and tiny calls lose. | Keep caller choice; qualify CPU cost and actual retained ownership. |
| [#84](https://github.com/Nodibell/SwiftSci/pull/84) | Existing selected preprocessing internals | Fewer borrow/offset operations and blocked gathers; full finite reduction loses early rejection. Tiny CPU elapsed control loses about 0.6 µs. | Preserve useful gains; measure tiny and early-invalid boundaries. |

The separate [MLX #4602](https://github.com/ml-explore/mlx/pull/4602) fixes lane masks in the macOS 14-targeted NEON fallback. Loading the complete comparison mask replaces broadcasting the first lane. No performance measurement establishes a resource regression. Returning correct mixed-lane comparisons is mandatory, including on newer macOS when running a binary built with that deployment target.

## What to do next

1. Requalify the default CSV/gather dispatch in #39 and #82. Compare serial and bounded parallel execution on identical complete outputs. Include narrow/wide tables, missing values, multiple simultaneous callers, and fixed request rates. Measure total process CPU per correct result, live scratch, retained bytes, elapsed time, and completed throughput under a fixed budget.
2. Add the same accounting to the #70 batched predictor. Batching can remove repeated work as well as exploit parallelism; the present elapsed-time results do not distinguish those effects.
3. Measure the retention choices in #63, #65–68, and #83 across one use, repeated use, churn, and tiny selections from large sources. Charge the actual ownership lifetime, including idle model and source retention. Keep physical memory separate from admission estimates.
4. Check the small and adverse-input costs in #72 and #84. Avoid adding thresholds solely to erase a tiny benchmark loss. A simpler implementation that reduces total work is preferable when it meets the workload's latency constraint.
5. Continue numerical correctness gates for #38, #42–44, #50, #60, #69, and #81. Stronger algorithms can be optimized, but the earlier wrong result is not a valid baseline.

This audit does not justify a broad rollback. It justifies correcting the optimization approval criteria and measuring the defaults most likely to consume extra resources. Reduced copying and explicit ownership remain central to the design.

## Audit method and reproducibility

The [inventory](inventory.json) records every PR's actual merge, first parent, changed production paths, and patch hash. GitHub's abbreviated file list omits paths beyond its first 100 entries. The audit therefore compares each merge commit with its first parent using Git, rather than attributing a stacked PR's inherited changes to it again. A source-path count is not a count of changed algorithms; #41 is a verified byte-identical rename.

The [collector](collect.py) is read-only with respect to Git and the network. Given a frozen GitHub snapshot and local merge objects, it regenerates the complete review files:

```sh
gh pr list --repo Nodibell/SwiftSci --state all --author crabel99 --limit 1000 \
  --json number,title,state,createdAt,mergedAt,url,baseRefName,headRefName,headRefOid,mergeCommit,body,files,additions,deletions \
  > /tmp/swiftsci-pr-snapshot.json
python3 collect.py --snapshot /tmp/swiftsci-pr-snapshot.json \
  --repo /path/to/SwiftSci --output /tmp/swiftsci-pr-review
```

A fresh query may contain later PRs or edited descriptions. The committed merge identities and original snapshot hash define this audit's scope. The original snapshot, complete diffs, and individual review outputs remain in `~/local-ai/spl/swiftsci/pr-resource-audit-20261018/`. The committed findings and selected CPU records preserve the conclusions without copying benchmark datasets into a production branch.

This audit adds no energy or hardware-counter measurements. Historical whole-process counter receipts cannot attribute the cost of an individual kernel. CPU seconds are a resource-use proxy across heterogeneous cores. Low host CPU alone does not account for GPU or Neural Engine work. Reported process peak memory is not an allocation trace, and explicit retained ownership must be accounted for separately.

## Verification of this audit

The collector was rerun against the frozen snapshot. All 27 merge identities, production path inventories, and patch hashes matched. The report contains exactly one row per PR. Local report links and 79 pinned GitHub source citations resolve to the reviewed files and line ranges. Admission medians reproduce from the preserved selected records. The collector passes Python compilation and the notes pass the Git whitespace check. No new performance or production test result is implied.
