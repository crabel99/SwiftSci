# Qualified CSV reads against pandas, Polars, and DuckDB

The comparison completes 1,008 measured workers after 84 strict preflight reads. Every accepted output matches its independent contract. The identical-binary quality check passes, with 0 flags retained in [the audit](audit.json). This measures local SwiftSci commit `5d1f89a961106104757f2d8d0b8faba79487d100`, pandas 3.0.6, Polars 1.44.2, and DuckDB 1.5.6.

CPU, elapsed time, and memory remain separate in [the full result table](results.md). The result is for these public read APIs and configurations, not an aggregate ranking of the libraries or a full application benchmark. No production code changes during this follow-up.

## What the measurements imply

Both Swift policies have lower CPU medians than each measured reference engine in all fourteen case-and-scope combinations. That is a result for this sample and these pinned configurations. It is not proof that SwiftSci is generally more efficient than every alternative.

The household case with the shared eleven-token null list makes the CPU and latency tradeoff clear:

| Scope | Engine | CPU ms | Elapsed ms | Process peak MiB | Read peak increase MiB |
|---|---|---:|---:|---:|---:|
| eager | swift-serial | 240.6 | 240.7 | 420.5 | 414.0 |
| eager | swift-parallel | 259.8 | 116.7 | 422.3 | 415.7 |
| eager | pandas | 1150.1 | 1150.4 | 406.9 | 308.8 |
| eager | polars | 383.0 | 32.4 | 407.3 | 347.3 |
| eager | duckdb | 746.2 | 80.1 | 571.1 | 495.7 |
| stream | swift-serial | 220.3 | 220.4 | 138.8 | 132.3 |
| stream | swift-parallel | 248.0 | 108.3 | 139.4 | 132.9 |
| stream | pandas | 1275.9 | 1277.3 | 186.7 | 88.6 |
| stream | polars | 389.4 | 41.1 | 384.2 | 323.9 |
| stream | duckdb | 651.6 | 590.5 | 220.9 | 145.6 |

Swift's serial eager read uses about 37% less CPU than Polars here, while Polars finishes about 7.4 times sooner. The parallel Swift read narrows that elapsed gap while using somewhat more CPU than serial. This supports keeping CPU cost and completion time separate when choosing an execution policy.

Eager memory remains a visible opportunity. Swift serial adds about 414 MiB above its baseline high water, versus about 347 MiB for Polars in this case. Swift's streamed process peak is much smaller than Polars' batch-delivery peak. pandas streamed peak is higher than Swift's absolute peak, but its increase above the larger Python baseline is smaller. Those are different memory comparisons, so neither should replace the other.

RSS does not separate mapped file pages, private allocations, shared runtime pages, or reclaimable memory. A private-allocation and mapping profile is needed before attributing the eager difference to storage layout or claiming a total system-memory saving. It is not evidence of a leak.

The eleven-token household configuration explicitly recognizes `?`. Its absolute times must not be compared as a code-only improvement over the preceding ten-token Swift-default qualification. The source head is unchanged, and this configuration changes how those numeric fields are handled.

## Equal inputs and explicit configuration

Seven immutable contracts use full Aotizhongxin and Wanliu air-quality files and the full 2,075,259-row household-energy file. They cover original two-token null sets, the default multi-token sets on air-quality data, an extended multi-token set on household data, and explicit parsed dates. Each has eager and streamed scopes. Every engine receives the same bytes, complete logical schema, explicit null tokens, row count, and output order for its case.

The household extended set includes `?` for every engine. This matters because SwiftSci can coerce that invalid numeric field to missing under its default settings, whereas the strict reference readers reject it unless declared null. The new `energy-common` configuration has eleven tokens and is not SwiftSci's ten-token default configuration. No input is rewritten, malformed row skipped, parse error ignored, or tolerance relaxed.

The [frozen plan](plan.json) records every case before measurement. The full schemas and expected native-value hashes are part of those contracts. Int64 reference values are in the exact float64 embedding range, which the Python digest validator checks. Strings and null positions are hashed independently, Float64 bits must match, and parsed dates use the supplied format and exact epoch values. Native output types are checked as well.

## Native readers and CPU policies

| Engine | Measured configuration |
|---|---|
| SwiftSci parallel | Actual qualified standalone reader and module object; native column-conversion workers |
| SwiftSci serial | Same reader with column-conversion workers disabled; other internal work remains native |
| pandas | Native C reader, explicit dtypes and null list, default null list disabled, round-trip float conversion, explicit date format and native date cache |
| Polars eager | Native `read_csv`, complete schema and explicit null list, explicit cached date conversion inside timing |
| Polars streamed | Native `scan_csv` with complete schema, then ordered CPU `collect_batches` delivering complete frames |
| DuckDB | Native connection and CPU pool, complete schema and explicit null list, insertion order preserved; eager Arrow materialization or streamed Arrow record batches |

All use the CPU backend and native library parallelism. There is no core pinning or imposed equal worker count. The serial Swift result is an additional caller policy, not an equal-thread-count comparison with Polars. Runtime versions, observed native pool settings, and actual options remain in every reference response. pandas's Arrow engine is not measured.

[Polars documents that complete schema avoids inference](https://docs.pola.rs/api/python/stable/reference/api/polars.read_csv.html). [pandas 3.0 documents the null, float, and date controls used here](https://pandas.pydata.org/pandas-docs/version/3.0/reference/api/pandas.read_csv.html). Installed API signatures and strict output preflight also verify the configurations.

## Streamed output has a specific contract

Each streamed reader delivers every column in original order, in output frames of at most 10,000 rows. The consumer counts rows and releases frames without retaining the dataset. Full native value and null validation occurs on a separate untimed repeat. A lazy query reduced to a count would not perform this task and is not substituted for it.

The Polars batch API is version-pinned and marked unstable. [Its documentation warns that returning batches is slower than native sinks](https://docs.pola.rs/api/python/stable/reference/lazyframe/api/polars.LazyFrame.collect_batches.html). These results therefore describe public frame delivery, not all Polars streaming operations. The installed wrapper has no public `stop` method; every iterator is fully drained and released. pandas readers and DuckDB Arrow batch readers close through their public context managers.

## Current DuckDB streaming API check

The primary run reused `fetch_record_batch`, which emits a deprecation warning in the installed DuckDB version. That warning is included in its timed call. A separate 84-worker check compares it with the supported `to_arrow_reader(batch_size=10000)` replacement across all seven complete streamed contracts. Every output matches, and current-versus-legacy CPU median changes range from -1.45% to +0.59%, within the predeclared two-sided 10% review threshold.

The supported replacement does not materially change the observed DuckDB resource position in this check. The original balanced comparison remains intact; the supplemental check does not replace selected rows or erase the warning. [Its plan, observations, and decision](duckdb-api-check/decision.json) remain separate from the primary study.

## What timing and memory include

The runtime is imported and caller configuration prepared before timing. File bytes are explicitly warmed outside each round. Twelve cyclic and reversed engine orders balance pairwise position. Each engine gets twelve independent fresh-process observations per case and scope. Repeated reads from one worker are not counted as extra independent samples.

Eager timing adds the public read and output release phases. Full output validation occurs in the gap and is excluded from CPU and elapsed measurements. Memory is captured while the native result is held, before validation. Stream timing includes reader creation, full consumption and output release, followed by an untimed full validation repeat.

CPU is process user-plus-system time during these measured phases. It is not a FLOP count, core-utilization percentage, energy measurement, or whole worker-lifetime cost. The execution policy uses AC power and native scheduling. Our task runs no builds, tests, or profilers concurrently with accepted measurements; unrelated host activity remains uncontrolled.

Process peak RSS includes the runtime. Python workers also import NumPy for validation before measurement. To expose that baseline, the table includes pre-read high water, post-read high water, the increase above that baseline, and held or drained RSS change. These measures are not allocation counts. A zero peak increase does not prove that reading allocated no memory, and post-validation release RSS can include validation buffers and library caches.

## Validation and reproducibility

Initial preflight found seven failures in the untimed DuckDB streamed validator. Arrow Array validity masks cannot provide the requested zero-copy NumPy boolean conversion. The eager ChunkedArray case had allowed copying by default. An explicit `zero_copy_only=False` fixes the validator without changing native reads, expected types, hashes, or tolerances. [The correction record](adapter-correction.json) and initial failed responses remain preserved. All 84 preflight reads then pass before any accepted timing.

[The independent audit](audit.json) recomputes every summary field from raw observations, verifies the balanced schedule, checks exact output digests and chunk bounds, and recomputes identical-binary CPU and memory flags. The control remains two-sided 10% CPU and 5% plus 8 MiB peak memory. Small differences remain descriptive; the study does not prove a general ranking at that scale.

The [isolated reproduction check](reproduction-smoke.json) regenerates the exact frozen plan and Python adapter. Standalone Swift build receipts verify that the reader module import precedes the general dependency directory, avoiding the cached-interface mistake corrected in [the preceding qualification](../2026-10-23-csv-paired-panel/README.md). The production worktree stays clean at the tested head. Nothing is pushed or submitted.

- [All resource results and identical-binary controls](results.md)
- [Ratios for each Swift policy and reference](comparisons.json)
- [Independent audit](audit.json) and [measured-run decision](measurement/decision.json)
- [Frozen contracts and sampling plan](plan.json)
- [Preflight decision](preflight/decision.json) and [adapter correction](adapter-correction.json)
- [Worker counts and uncompressed hashes](worker-index.json)
- [Scripts, input contracts, client receipts, and nonempty error logs](experiments.tar.gz)
- [Artifact hashes](artifact-sha256.json)

Full source datasets remain with their existing owner and are identified by hashes. The archive retains recorded paths and dependency identities; redirect declared paths to reproduce elsewhere. Raw worker JSONL is stored as exact gzip streams. Native binaries and build caches are not committed.
