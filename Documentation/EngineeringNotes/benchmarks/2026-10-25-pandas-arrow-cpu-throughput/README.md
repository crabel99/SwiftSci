# Schema-explicit pandas via Arrow CPU comparison

Benchmark commit `624fc7e08638b0a80647753d8f8dbe44eb37ef80` on local branch `codex/pandas-arrow-cpu-throughput` extends `6e101d1ce8020b3ac009767ac1789fa6b57b5606`. Swift production code is unchanged from `58db37c4b3c97b287186c377f76f89abcbbb0b0d`. Nothing is pushed.

The full panel completes 144 queues, 9,216 jobs, and 48 complete native-output checks. Performance qualified: False.

## Qualification decision

The full panel is unqualified. Its identical pandas C-reader control has median peak RSS of 4,061.3 MiB versus 4,335.2 MiB, a 6.74% difference. The frozen allowance is 5% plus 32 MiB across four callers. The high value exceeds that allowance by 38.8 MiB. All CPU and elapsed twin controls pass; the other memory controls pass. Every output check passes.

The following performance tables are provisional observations, not a validated ranking. No condition or failed round is discarded. The original limits and 64-job queue remain unchanged. A passing earlier panel does not validate this one.

Both peak and retained pandas residency vary. Worker histories differ because the shared queue assigns jobs dynamically. The receipts do not identify an allocator mechanism or prove a leak. Before another performance claim, qualify a common processor class and isolate per-worker job history and retained allocations. The [memory-control analysis](memory-control.json) preserves every pandas queue and worker history.

## Processor-class requirement

This full panel records native CPU parallelism but does not measure or constrain P-core versus E-core placement. Matching backend and power settings does not prove matching core classes. It cannot establish efficiency under the subsequently clarified same-core-type requirement, independently of the failed RSS control. P/E scheduling has not been shown to cause the RSS difference.

The [processor-class investigation](core-placement.md) and [local counter trials](core-placement-results.md) examine a supported way to measure placement. No replacement performance panel is accepted while the application-versus-kernel core rule is undecided.

## Reader qualification

Installed pandas 3.0.6 passes an empty column_types mapping to Arrow even when the caller supplies dtype. Its wrapper applies conversion after parsing. Both its ordinary Arrow entry point and an explicit-schema Arrow-to-pandas pipeline preserve every value in these two reference files. The latter also disables parser inference for every declared column, so that is the measured condition. This is not pandas.read_csv(engine="pyarrow").

The archived qualification script captures actual parser options and complete native column hashes. A regression test checks that the adapter passes the full schema and preserves numeric-looking text, Int64 limits, and negative zero. Existing persistent-worker tests cover stable missing-last sorting, full Float64 matrix bits, and independent writable output for both pandas readers.

Parsing and table.to_pandas conversion are timed. Subsequent sort_values and matrix construction use exactly the same pandas code as the C-reader condition. Arrow uses its default CPU pool; the benchmark does not set its size. Imports and process startup finish before queue timing. The first CSV read remains timed.

API references: [pandas CSV options](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html) and [Arrow conversion options](https://arrow.apache.org/docs/python/generated/pyarrow.csv.ConvertOptions.html). Installed source and live parser calls establish the version-specific behavior above.

## Provisional complete queue costs

Four persistent callers serve 64 jobs per queue: 16 copies of each read or read-sort-matrix workflow on the air-quality and household-electricity datasets. All six conditions and their twins occupy every position across 12 rotated rounds. Every condition uses the same 8 GiB sampled worker-RSS ceiling and native internal CPU parallelism.

| Condition | Jobs/min | CPU ms/job | Sampled peak MiB | Retained MiB | Resident MiB-seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| swiftsci_optional | 2016.8 | 212.46 | 3461.3 | 3118.4 | 5499.5 |
| swiftsci_compact | 1999.8 | 205.84 | 2480.4 | 2127.9 | 3889.1 |
| pandas | 336.0 | 675.44 | 4107.7 | 4107.7 | 38962.3 |
| polars | 2476.4 | 299.28 | 2840.0 | 2084.6 | 3612.6 |
| duckdb | 1336.0 | 496.98 | 4205.9 | 3428.8 | 9569.2 |
| pandas_arrow | 2009.5 | 296.11 | 5073.3 | 5073.3 | 7974.7 |

CPU sums worker user and system time plus measured controller CPU. It is not FLOPs or measured energy. RSS includes allocator residency and may count shared pages repeatedly. Resident MiB-seconds integrate sampled RSS over queue time; a lower peak does not imply lower occupancy.

## Provisional comparisons within the same round

Ratios divide the numerator by the denominator. Lower CPU, RSS, and resident byte-seconds mean less measured resource use. Higher jobs/min means higher throughput. Each ratio uses the median of a condition and its twin within a round, then the median of those 12 paired ratios.

| Numerator | Denominator | CPU ratio | Throughput ratio | Peak RSS ratio | Resident byte-seconds ratio | Less CPU, rounds |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| swiftsci_optional | pandas | 0.314 | 5.903 | 0.824 | 0.143 | 12/12 |
| swiftsci_optional | polars | 0.711 | 0.813 | 1.207 | 1.539 | 12/12 |
| swiftsci_optional | duckdb | 0.427 | 1.505 | 0.830 | 0.575 | 12/12 |
| swiftsci_optional | pandas_arrow | 0.716 | 0.995 | 0.684 | 0.694 | 12/12 |
| swiftsci_compact | pandas | 0.305 | 5.976 | 0.588 | 0.100 | 12/12 |
| swiftsci_compact | polars | 0.690 | 0.816 | 0.868 | 1.086 | 12/12 |
| swiftsci_compact | duckdb | 0.415 | 1.503 | 0.594 | 0.403 | 12/12 |
| swiftsci_compact | pandas_arrow | 0.696 | 0.996 | 0.491 | 0.488 | 12/12 |
| pandas_arrow | pandas | 0.439 | 5.889 | 1.204 | 0.206 | 12/12 |

Rounds are not independent samples and do not establish confidence intervals. Results apply to these complete public paths and inputs. Historical C-reader results remain unchanged; this panel measures all readers together and does not divide timings from different days.

## Provisional complete operation CPU

| Dataset and workflow | Swift optional ms | Swift compact ms | pandas C ms | Polars ms | DuckDB plus Arrow ms | pandas via Arrow ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Aotizhongxin-default/read | 12.48 | 11.87 | 37.46 | 23.53 | 37.28 | 15.64 |
| Aotizhongxin-default/sort-matrix | 17.39 | 16.38 | 42.06 | 33.91 | 58.27 | 19.64 |
| energy-common/read | 262.99 | 269.14 | 1192.57 | 367.59 | 756.25 | 465.57 |
| energy-common/sort-matrix | 555.41 | 524.63 | 1424.77 | 770.91 | 1142.30 | 681.06 |

These are complete path costs, not isolated sort measurements. Native fingerprints run outside timing. Output shape/type checks, materialization, owned writable row-major Float64 matrices, and output release remain inside. Every engine receives identical raw bytes, ordered schema, declared nulls, stable ascending missing-last sort, and independent expected output.

DuckDB retains the earlier stable-index sort and Arrow gather, including their cost, to preserve signed-zero bits. No production algorithm changes. Ordinary pandas Int64 and Float64 null-representation limits remain; neither reference file requires missing integers or distinguishing valid NaN from null.

## Controls, runtime, and validation

The smoke ran before the source commit, and its recorded head remains unchanged. All eight measured controller hashes match the committed full-panel source. The smoke passes all controls but cannot qualify performance.

Twin limits remain 10% CPU and elapsed drift, plus 5% and 8 MiB per caller for sampled peak RSS. Smoke cannot qualify performance and stays in the archive regardless of its control results. No limit, work count, schema, or caller count is tuned after the full panel starts. Runtime identity, contracts, all measured controller sources, Swift source hashes, interpreter, and binary are rechecked after timing.

- pandas: pandas 3.0.6, python 3.14.6 (main, Jun 10 2026, 10:03:53) [Clang 21.0.0 (clang-2100.0.123.102)], numpy 2.5.3. Configured pools: {}.
- polars: polars 1.44.2, python 3.14.6 (main, Jun 10 2026, 10:03:53) [Clang 21.0.0 (clang-2100.0.123.102)], numpy 2.5.3. Configured pools: {'polars': 16}.
- duckdb: duckdb 1.5.6, pyarrow 25.0.1, pandas 3.0.6, python 3.14.6 (main, Jun 10 2026, 10:03:53) [Clang 21.0.0 (clang-2100.0.123.102)], numpy 2.5.3. Configured pools: {'duckdb': 16}.
- pandas_arrow: pandas 3.0.6, pyarrow 25.0.1, python 3.14.6 (main, Jun 10 2026, 10:03:53) [Clang 21.0.0 (clang-2100.0.123.102)], numpy 2.5.3. Configured pools: {'pyarrow': 16}.

Configured pool sizes are not active core measurements. Inherited thread overrides are cleared by the existing production-default worker policy.

The 23 focused CPU tests pass without skips. The full controller discovery executes 249 tests: 245 pass and four require explicit Metal opt-in. Those four pass separately with SWIFTSCI_MLX_TEST_GPU=1. All 249 execute successfully across the two configurations; logs and exact commands are archived.

The unchanged Swift source previously passed 447 Debug and 447 Release dataframe tests. No new native or hosted CI run is claimed for this Python-only feature. CPU timing does not overlap the controller tests or optional Metal tests.

## Evidence

[Memory-control analysis](memory-control.json), [summary](summary.json), [paired ratios](comparisons.json), [provenance](provenance.json), [validation](validation.json), and [archived experiment](experiment.tar.gz) preserve raw receipts, logs, exact measured source snapshots, the parser qualification, and reproduction scripts. Restore the recorded worker/interpreter and reference inputs by SHA256. Run compare.py with --pandas-arrow into a fresh directory, then --audit and the archived summarize.py. Binary files, raw CSVs, and caches are excluded.

These finite queues repeat cached reference files. They do not establish cold-storage performance, sustained-service throughput, GPU/NPU performance, physical memory, energy, or a universal dataframe ranking. Engineering results stay on codex/engineering-notes.
