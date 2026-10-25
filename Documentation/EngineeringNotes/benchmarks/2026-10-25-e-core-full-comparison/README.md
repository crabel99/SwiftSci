# Full comparison with E-core application execution

Source `af4e2cd45b53cf1a76253dc174c508e5459b3cf7`, policy e-core-application-v1. Full panel performance qualified: False.

## Qualification

The panel completes 144 queues, 9,216 jobs, 48 full native-output checks, 576 worker intervals, and 144 controller intervals. Application P-core time is zero in every accepted queue interval. Startup, preflight, postflight, and the final audit are outside these receipts. Kernel P/E time remains measured separately. Controls passed: False.

The tables below are provisional observations. The failed controls prevent a validated ranking. No failure or condition is discarded.

| Control condition | Failed control | Observed twin difference | Frozen allowance |
| --- | --- | --- | --- |
| swiftsci_optional | Elapsed time | -18.9% | 10% |
| swiftsci_compact | Elapsed time | -24.3% | 10% |
| pandas | Charged CPU time | +22.1% | 10% |
| duckdb | Charged CPU time | +28.7% | 10% |
| duckdb | Elapsed time | +15.1% | 10% |
| duckdb | Sampled peak RSS | 3706.2 to 3931.3 MiB | 5% plus 32 MiB |
| pandas_arrow | Sampled peak RSS | 3860.6 to 4178.6 MiB | 5% plus 32 MiB |

The [identical-twin diagnostics](repeatability.md) retain instruction and cycle counts. Pandas and DuckDB twins have nearly identical E-instruction counts, but charged CPU differs by 22% and 29%. The counted cycles per accounted ns also differ. These process-counter ratios do not establish core frequency, temperature, energy, or cache misses. Matching application core type was insufficient to qualify this run.

## Complete queue costs

Four persistent callers retain native internal parallelism under one inherited background QoS clamp. Every condition uses the same 64 jobs per queue, complete schemas, native-value contracts, stable missing-last sort, and owned writable row-major Float64 output. Twelve rotated rounds place every primary condition and its identical-binary twin in every position.

| Condition | Jobs/min | Charged CPU ms/job | Peak RSS MiB | Retained RSS MiB | Resident MiB-seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| swiftsci_optional | 154.3 | 670.09 | 3428.5 | 3042.9 | 66006.4 |
| swiftsci_compact | 156.4 | 544.39 | 2455.7 | 2045.2 | 47368.0 |
| pandas | 41.8 | 2578.56 | 3513.7 | 3140.5 | 237524.0 |
| polars | 111.0 | 716.30 | 2116.0 | 1680.8 | 60942.4 |
| duckdb | 77.6 | 1250.75 | 3853.7 | 2741.0 | 144448.1 |
| pandas_arrow | 133.0 | 748.41 | 3933.9 | 3335.5 | 87819.5 |

Medians pool each primary condition and its twin. Charged CPU sums worker user/system time and measured controller CPU. RSS may count shared pages more than once and includes allocator caches. It is not unique physical memory. Resident byte-seconds account for how long memory stays resident; lower peak alone does not establish lower occupancy.

## Resource totals across every recorded queue

Each condition completes 1,536 jobs across its 24 primary and twin queues. The figures below use sums across all those queues. They retain slow runs as well as fast ones and do not change qualification. CPU per job divides total charged CPU by total completed jobs. Aggregate throughput divides total jobs by total queue elapsed time.

| Condition | All-run CPU ms/job | Aggregate jobs/min | Maximum sampled RSS MiB | Recorded resident MiB-seconds/job |
| --- | ---: | ---: | ---: | ---: |
| swiftsci_optional | 735.38 | 142.5 | 3450.0 | 1151.44 |
| swiftsci_compact | 713.34 | 155.1 | 2469.1 | 760.52 |
| pandas | 2551.62 | 39.4 | 4010.8 | 3891.12 |
| polars | 924.89 | 97.8 | 2229.1 | 1080.71 |
| duckdb | 1357.12 | 63.9 | 4258.3 | 2652.37 |
| pandas_arrow | 854.93 | 122.1 | 5069.4 | 1631.80 |

## Application and kernel core accounting

| Condition | E user ms/job | E kernel ms/job | P kernel ms/job | E cycles/job, millions | E instructions/job, millions |
| --- | ---: | ---: | ---: | ---: | ---: |
| swiftsci_optional | 624.809 | 46.720 | 0.070 | 1300.24 | 3452.34 |
| swiftsci_compact | 515.586 | 30.993 | 0.026 | 1325.25 | 3469.58 |
| pandas | 2446.614 | 115.797 | 0.111 | 4290.96 | 15520.11 |
| polars | 631.067 | 79.719 | 0.085 | 1630.79 | 5247.92 |
| duckdb | 1146.026 | 108.356 | 0.681 | 2499.59 | 8015.05 |
| pandas_arrow | 651.626 | 98.928 | 0.198 | 1450.76 | 4427.29 |

P-core user time is zero. Accounted E cycles/instructions include both E-user and E-kernel execution. Accounted P cycles/instructions belong to kernel execution under this rule. Counters are not FLOPs or measured energy. A lower instruction count does not establish less equivalent mathematical work because instruction mixes differ.

Core snapshots bracket queue work plus boundary bookkeeping, wider than the old wall and charged-CPU intervals. These components are not an exact partition of charged_cpu_ns. Every worker snapshot requires zero running threads before and after the read. The controller snapshot follows queue completion and thread teardown. Raw counters, process IDs, and Mach timebase remain in the receipts.

## Paired ratios within each round

Numerator divided by denominator, pooling a condition with its twin within each round before taking the median ratio over 12 rounds. Lower CPU/memory ratios mean less measured resource use; higher throughput ratios mean more completed jobs per minute.

| Numerator | Denominator | Charged CPU | E-user CPU | Throughput | Peak RSS | Resident byte-seconds |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| swiftsci_optional | pandas | 0.299 | 0.289 | 3.503 | 0.974 | 0.302 |
| swiftsci_optional | polars | 0.832 | 0.862 | 1.337 | 1.598 | 1.162 |
| swiftsci_optional | duckdb | 0.551 | 0.564 | 2.056 | 0.888 | 0.450 |
| swiftsci_optional | pandas_arrow | 0.867 | 0.932 | 1.143 | 0.904 | 0.656 |
| swiftsci_compact | pandas | 0.290 | 0.287 | 3.778 | 0.709 | 0.205 |
| swiftsci_compact | polars | 0.814 | 0.854 | 1.459 | 1.151 | 0.746 |
| swiftsci_compact | duckdb | 0.523 | 0.543 | 2.239 | 0.646 | 0.284 |
| swiftsci_compact | pandas_arrow | 0.843 | 0.923 | 1.198 | 0.642 | 0.450 |
| pandas_arrow | pandas | 0.343 | 0.316 | 3.016 | 1.096 | 0.356 |

Paired ratios can differ from ratios of pooled medians. Rounds are not independent samples and do not establish confidence intervals. P/E matching does not fix CPU frequency, cache state, or unrelated system activity. The recorded twin controls remain mandatory. These are finite repeated-data queues, not cold-storage or sustained-service measurements.

## Adapters and scope

Pandas C uses round-trip float conversion. The pandas_arrow condition uses pyarrow.csv.read_csv with an explicit full schema, then converts to pandas; it is not pandas.read_csv(engine="pyarrow"). Conversion is timed. Both pandas conditions share sorting and matrix code. Polars receives the complete schema. DuckDB materializes Arrow output and pays for stable-index sorting plus gathering original values to preserve signed-zero bits.

The two source files contain 35,064 air-quality rows and 2,075,259 household-electricity rows. Every library receives identical bytes and declared nulls. Full output hashes match each native Int64/Float64/String column and matrix before and after timing. No representation mismatch is waived. Inputs needing missing Int64 or valid-NaN-versus-null distinction require additional equivalent adapters.

QoS is a preference, not hard affinity. Acceptance depends on observed counters, positive-P calibration, consistent boot session, and zero application P-time for every participating PID. The 8 GiB sampled worker-RSS ceiling and original 10% CPU/wall and 5% plus 8 MiB-per-caller peak-RSS twin limits stay unchanged.

After timing, 255 unique controller tests passed across normal and explicit Metal configurations. The new validation records before-and-after source hashes and this exact commit. Discovery executes 251 tests and explicitly skips four Metal cases, which the second command runs successfully. Earlier logs remain preserved, but do not independently embed a commit hash. No tests, compilation, or profiling overlap timing. All 51 Swift source hashes still match the previously tested library head. No new Swift production code or hosted CI result is claimed.

## Evidence

Live audit checks the original source, interpreter, worker, calibration binary hashes, current inputs, and every saved queue. The separate verify-archive.py audit uses only preserved files and Python standard-library code. It cannot authenticate stored calibration stdout, replace missing executable bytes, or prove continuous input immutability. Resident byte-seconds remain recorded values because the raw receipt omits the monotonic batch start/end anchors needed for exact integral recomputation. Peak RSS, boundary RSS, sample ordering, and integral bounds can be checked independently.

[Source-bound validation](current-head-validation.json), [portable audit](verify-archive.py), [independent review](review.md), [summary](summary.json), [paired ratios](comparisons.json), [core intervals](core-intervals.json), [provenance](provenance.json), [decision trail](decisions.tsv), and [raw archive](experiment.tar.gz) preserve the reviewable record. A new timing run requires the recorded worker, reference inputs, and comparison environment. Restore inputs by SHA256, use the pinned source, and choose a fresh output directory. launch-full.py preserves the original absolute-path protocol and refuses to overwrite an existing full directory. It requires path adjustments for a relocated workspace. The raw receipt audit is separate from a new timing run. next-panel-plan.json preserves the pre-launch plan unchanged. full-launch.json and full-exit.json record actual execution. Engineering evidence stays on codex/engineering-notes.
