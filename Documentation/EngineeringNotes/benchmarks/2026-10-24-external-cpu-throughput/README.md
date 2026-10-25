# Equivalent CPU queues across dataframe libraries

Benchmark source is `6e101d1ce8020b3ac009767ac1789fa6b57b5606` on local branch `codex/external-cpu-throughput`, based on Swift library head `58db37c4b3c97b287186c377f76f89abcbbb0b0d`. No Swift production code changes and nothing is pushed. Engineering evidence remains on `codex/engineering-notes`.

Performance qualified: True. Controls passed: True. The full panel completes 100 queues, 6,400 timed jobs, and 40 full-output checks.

The panel supports the resource-efficiency goal within these complete reference workflows.

- Against pandas C/round-trip, SwiftSci compact uses 67.7% less CPU and 44.1% less sampled peak RSS. Throughput ratio is 5.38 times the reference.
- Against Polars, SwiftSci compact uses 29.1% less CPU and 12.0% less sampled peak RSS. Throughput ratio is 0.87 times the reference.
- Against DuckDB plus Arrow, SwiftSci compact uses 58.3% less CPU and 41.0% less sampled peak RSS. Throughput ratio is 1.47 times the reference.

Polars completes this queue faster than SwiftSci while using more CPU. Integrated resident byte-seconds are close, nominally 1.6% higher for SwiftSci compact in paired rounds. Lower peak RSS does not establish lower memory occupancy over time. The figures describe these API paths and reference files, not every operation or the best possible configuration of each library. Alternative readers, including pandas with Arrow, need separate equivalent qualification.

## Complete queue resource costs

Every condition uses four persistent caller processes with native internal parallelism. Each queue contains 16 copies of each reference read or read-sort-matrix case, for 64 jobs. Imports, session setup, and process readiness finish before timing. The first public CSV call remains timed. Output release, queue dispatch, sampling, and measured controller CPU are charged.

| Condition | Jobs/min | CPU ms/job | Sampled peak MiB | Retained MiB | Resident MiB-seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| swiftsci_optional | 1768.8 | 231.79 | 3489.7 | 3120.5 | 6292.6 |
| swiftsci_compact | 1725.6 | 231.69 | 2506.3 | 2131.7 | 4549.1 |
| pandas | 317.2 | 717.52 | 4468.4 | 4457.9 | 40986.4 |
| polars | 1979.8 | 323.83 | 2839.8 | 2047.5 | 4428.0 |
| duckdb | 1142.8 | 556.44 | 4251.0 | 3459.4 | 11268.4 |

These are medians pooling each primary condition with its twin. CPU is summed user and system time across worker threads, plus measured controller work. It is not FLOPs, energy, or normalized performance-core and efficiency-core work. RSS can count shared pages more than once. It is not unique physical memory.

## Paired comparisons

Ratios below are SwiftSci divided by the reference library within the same round. Less than 1 means less CPU or sampled RSS. Greater than 1 means higher throughput.

| SwiftSci storage | Reference | CPU ratio | Throughput ratio | Peak RSS ratio | Rounds with less CPU |
| --- | --- | ---: | ---: | ---: | ---: |
| swiftsci_optional | pandas | 0.322 | 5.545 | 0.781 | 10/10 |
| swiftsci_optional | polars | 0.712 | 0.892 | 1.227 | 10/10 |
| swiftsci_optional | duckdb | 0.417 | 1.546 | 0.823 | 10/10 |
| swiftsci_compact | pandas | 0.323 | 5.378 | 0.559 | 10/10 |
| swiftsci_compact | polars | 0.709 | 0.870 | 0.880 | 10/10 |
| swiftsci_compact | duckdb | 0.417 | 1.475 | 0.590 | 10/10 |

Paired medians can differ from ratios of pooled medians. Rounds are not independent statistical samples, and counts are not confidence intervals. A control pass does not certify every small difference. If the full panel is unqualified, these remain observations rather than a validated ranking.

## Operation CPU by complete reference path

| Input and workflow | Swift optional ms | Swift compact ms | pandas ms | Polars ms | DuckDB plus Arrow ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| Aotizhongxin-default/read | 12.80 | 13.01 | 40.00 | 25.50 | 40.14 |
| Aotizhongxin-default/sort-matrix | 17.85 | 17.79 | 45.08 | 34.71 | 62.70 |
| energy-common/read | 286.13 | 304.94 | 1262.81 | 408.00 | 840.71 |
| energy-common/sort-matrix | 604.94 | 589.93 | 1516.17 | 826.53 | 1271.51 |

These measure complete public paths. Read-sort-matrix includes reading, stable full-frame sorting, and owned row-major Float64 output. Subtracting these medians would not establish an isolated sort cost. Shape and type checks and output release are included. Native-bit hashing is outside timing.

## Equivalent work and adapter choices

The inputs contain 35,064 Aotizhongxin air-quality observations and 2,075,259 household-electricity rows. Every engine receives the same CSV bytes, complete ordered schema, declared null list, and native Int64, Float64, and String output contract. Sorting is stable, ascending, and missing-last. Matrices contain the same numeric columns in owned writable C order. Independent output fingerprints match every column and matrix before and after timing.

Pandas uses its C CSV reader with round-trip float conversion. Polars receives a complete schema and requests stable sorting and writable C-order NumPy output. DuckDB materializes Arrow output through a persistent connection. Its stable SQL ordering uses the original row number as a tie breaker, followed by Arrow gathering of the original rows. Every conversion and gather remains in the measured work.

The DuckDB adapter needs this gather to preserve native signed-zero bits. A small live-process conformance fixture fails with direct ordered projection: the input is negative zero, while the ordered value is positive zero. The isolated dependency reproducer and failed-first test log remain archived. Gathering the original row values restores the expected bit pattern. This branch changes the benchmark adapter, not DuckDB production code.

Pandas ordinary Int64 columns do not support missing integers, and its ordinary Float64 null model cannot distinguish valid NaNs from missing values. These reference contracts require neither representation. Inputs needing those semantics must receive new equivalent adapters before comparison. No mismatch is waived.

Official API context: [pandas CSV options](https://pandas.pydata.org/docs/user_guide/io.html), [Polars writable C-order conversion](https://docs.pola.rs/py-polars/html/reference/dataframe/index.html), and [DuckDB ordering](https://duckdb.org/docs/stable/sql/dialect/order_preservation.html). Runtime behavior is checked against the installed versions below.

## Runtime identity and controls

- pandas: pandas 3.0.6, python 3.14.6 (main, Jun 10 2026, 10:03:53) [Clang 21.0.0 (clang-2100.0.123.102)], numpy 2.5.3. Configured pools: {}.
- polars: polars 1.44.2, python 3.14.6 (main, Jun 10 2026, 10:03:53) [Clang 21.0.0 (clang-2100.0.123.102)], numpy 2.5.3. Configured pools: {'polars': 16}.
- duckdb: duckdb 1.5.6, pyarrow 25.0.1, pandas 3.0.6, python 3.14.6 (main, Jun 10 2026, 10:03:53) [Clang 21.0.0 (clang-2100.0.123.102)], numpy 2.5.3. Configured pools: {'duckdb': 16}.

Every worker has the production-default execution policy with inherited thread overrides cleared. Configured pool size is not measured active core use. The full plan uses ten rotated rounds with a separate identical-binary twin for all five conditions. Each primary and twin occupies every order position.

All conditions use the same 8 GiB sampled worker-RSS ceiling. It excludes controller memory and is not an OS-enforced physical-memory limit. Source, interpreter, executable, contract, and runtime identities are checked independently after the panel. The audit recomputes every queue and job, raw CPU accounting, memory summaries, runtime identity, output hashes, and control result.

Qualification limits remain 10% for twin CPU and elapsed-time drift, plus 5% and 8 MiB per caller for sampled peak RSS.

| Control label | Metric | Twin ratio |
| --- | --- | ---: |
| All conditions | All controls pass | |

## Validation and planning history

The 21 focused CPU benchmark tests pass with no skips. The full CI-style controller command passes 243 tests and skips four explicit Metal opt-ins. Running those four separately with `SWIFTSCI_MLX_TEST_GPU=1` passes all four without skips. Thus all 247 controller tests execute successfully across the two configurations. GPU checks run only after CPU timing. The reused Swift source previously passed 447 Debug and 447 Release dataframe tests. No new native Swift run or hosted CI result is claimed.

The initial two-round smoke completes all reference checks. Its DuckDB elapsed control fails at short queue length. Smoke is explicitly unable to qualify performance. The initial smoke source is preserved at all eight original file hashes. A forecast is recorded before the full run and freezes 64 jobs per queue with the original thresholds. No full-run work count, caller count, schema, or tolerance is retuned after observing results.

These are finite bursts after preflight and repeated fixture reads, not cold-disk or sustained-service measurements. They do not measure GPU or Neural Engine work, energy, unique physical memory, or all scientific workloads. Rates cannot be compared directly with the earlier 128-job queue study.

## Evidence and reproduction

[Summary](summary.json), [paired comparisons](comparisons.json), [source provenance](provenance.json), and the [experiment archive](experiment.tar.gz) preserve the evidence. The source branch contains only the reusable benchmark feature and its tests. Engineering decisions and measured results stay on the notes branch.

Rebuild or restore the recorded uninstrumented Swift worker, matching interpreter and comparison dependencies, and the two reference files by SHA256. Run the documented `Benchmarks/CPUThroughput/compare.py` command into a fresh directory without `--smoke`, then its `--audit` command and this archived `summarize.py`. Raw CSVs, executables, object files, caches, and xcresult bundles are excluded from the archive.
