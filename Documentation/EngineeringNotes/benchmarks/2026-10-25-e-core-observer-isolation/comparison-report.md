# Equivalent external-engine CPU queues

Smoke validation only.

Controls passed: False. Performance qualified: False.

| Condition | Jobs/min | CPU ms/job | Sampled peak MiB | Resident MiB-seconds |
| --- | ---: | ---: | ---: | ---: |
| swiftsci_optional | 131.7 | 883.95 | 2122.8 | 4781.8 |
| swiftsci_compact | 119.8 | 913.21 | 1417.1 | 3765.6 |
| pandas | 30.7 | 3250.63 | 2720.7 | 15685.2 |
| polars | 84.1 | 1359.28 | 1790.5 | 6726.4 |
| duckdb | 54.8 | 1691.27 | 2290.8 | 12946.9 |
| pandas_arrow | 97.2 | 1050.21 | 3128.4 | 7401.7 |

CPU includes summed worker user and system time and measured controller work. Process startup and full hashes are outside queue timing. Shape checks and output release remain inside. RSS includes runtime and allocator residency and may double-count shared pages.

DuckDB computes a stable row permutation and Arrow gathers the original rows. This preserves signed-zero bits that direct ordered projection can canonicalize. The gathering cost is timed.

The optional pandas_arrow condition parses a complete schema with pyarrow.csv.read_csv and converts to pandas. Conversion is timed; pandas.read_csv(engine=pyarrow) is not used because its wrapper infers parser types.

Every primary condition has its own identical-binary twin. Unqualified results remain visible in audit.json. A smoke run cannot establish comparative performance.

## Verified application core class

Only compute workers are background-clamped and must record zero P-core user time. The ordinary controller includes dispatch, observation, and bookkeeping. Its P/E work is reported separately and remains charged. Raw QoS counters reject inherited restricted controller execution. The profiles are not interchangeable.

| Condition | E user ms/job | P user ms/job | E kernel ms/job | P kernel ms/job |
| --- | ---: | ---: | ---: | ---: |
| swiftsci_optional | 786.162 | 0.088 | 95.623 | 0.096 |
| swiftsci_compact | 827.704 | 0.418 | 83.962 | 0.412 |
| pandas | 3066.943 | 0.050 | 182.251 | 0.024 |
| polars | 1214.584 | 0.147 | 143.764 | 0.226 |
| duckdb | 1531.719 | 0.020 | 157.636 | 0.015 |
| pandas_arrow | 919.910 | 0.000 | 129.702 | 0.000 |

| Condition and role | E user ms/job | P user ms/job | E kernel ms/job | P kernel ms/job |
| --- | ---: | ---: | ---: | ---: |
| swiftsci_optional worker | 782.086 | 0.000 | 92.780 | 0.026 |
| swiftsci_optional controller | 4.426 | 0.088 | 3.118 | 0.070 |
| swiftsci_compact worker | 822.826 | 0.000 | 80.466 | 0.094 |
| swiftsci_compact controller | 5.296 | 0.418 | 3.777 | 0.255 |
| pandas worker | 3045.116 | 0.000 | 171.519 | 0.008 |
| pandas controller | 22.020 | 0.050 | 10.732 | 0.017 |
| polars worker | 1206.186 | 0.000 | 135.955 | 0.072 |
| polars controller | 9.390 | 0.147 | 8.745 | 0.154 |
| duckdb worker | 1518.584 | 0.000 | 145.095 | 0.000 |
| duckdb controller | 13.135 | 0.020 | 14.444 | 0.015 |
| pandas_arrow worker | 912.511 | 0.000 | 123.419 | 0.000 |
| pandas_arrow controller | 7.399 | 0.000 | 6.283 | 0.000 |

Observation requests a 10 ms cadence. Every queue must meet the fixed 50 ms maximum coverage gap and scan duration. Missing boundary scans fail audit. These checks qualify sampling coverage, not an instantaneous memory peak.

| Condition | Sampled footprint MiB | Maximum coverage gap ms | Maximum scan ms | Controller CPU ms/job |
| --- | ---: | ---: | ---: | ---: |
| swiftsci_optional | 2098.4 | 14.909 | 1.145 | 8.674 |
| swiftsci_compact | 1392.3 | 14.842 | 0.478 | 10.307 |
| pandas | 2566.4 | 14.937 | 2.008 | 34.048 |
| polars | 1692.7 | 14.879 | 1.589 | 19.161 |
| duckdb | 2070.9 | 19.998 | 8.767 | 28.903 |
| pandas_arrow | 2823.2 | 15.026 | 2.428 | 14.257 |

Physical footprint supplements RSS. It does not replace the unchanged RSS repeatability gate. Reusable bytes are not available from this unprivileged cross-process probe. Controller CPU charging includes initial/final scans, stats, core reads, and receipt validation. Its wider interval is recorded separately from queue wall timing. Final receipt serialization and disk writes are excluded.

Core counters bracket the queue plus boundary bookkeeping. They cover a wider interval than the wall timer and are not an exact partition of the existing charged_cpu_ns metric. Raw worker and controller snapshots remain in each receipt.
