# Equivalent external-engine CPU queues

Smoke validation only.

Controls passed: False. Performance qualified: False.

| Condition | Jobs/min | CPU ms/job | Sampled peak MiB | Resident MiB-seconds |
| --- | ---: | ---: | ---: | ---: |
| swiftsci_optional | 155.4 | 971.90 | 2122.7 | 3958.4 |
| swiftsci_compact | 162.4 | 918.63 | 1417.2 | 2740.5 |
| pandas | 52.5 | 3153.65 | 2720.8 | 9558.9 |
| polars | 123.6 | 1200.81 | 1780.1 | 5146.0 |
| duckdb | 87.4 | 1858.84 | 2229.8 | 8126.4 |
| pandas_arrow | 144.0 | 1104.81 | 3131.3 | 5208.6 |

CPU includes summed worker user and system time and measured controller work. Process startup and full hashes are outside queue timing. Shape checks and output release remain inside. RSS includes runtime and allocator residency and may double-count shared pages.

DuckDB computes a stable row permutation and Arrow gathers the original rows. This preserves signed-zero bits that direct ordered projection can canonicalize. The gathering cost is timed.

The optional pandas_arrow condition parses a complete schema with pyarrow.csv.read_csv and converts to pandas. Conversion is timed; pandas.read_csv(engine=pyarrow) is not used because its wrapper infers parser types.

Every primary condition has its own identical-binary twin. Unqualified results remain visible in audit.json. A smoke run cannot establish comparative performance.

## Verified application core class

Only compute workers are background-clamped and must record zero P-core user time. The ordinary controller includes dispatch, observation, and bookkeeping. Its P/E work is reported separately and remains charged. Raw QoS counters reject inherited restricted controller execution. The profiles are not interchangeable.

| Condition | E user ms/job | P user ms/job | E kernel ms/job | P kernel ms/job |
| --- | ---: | ---: | ---: | ---: |
| swiftsci_optional | 869.746 | 0.350 | 97.123 | 0.288 |
| swiftsci_compact | 834.966 | 0.102 | 79.244 | 0.197 |
| pandas | 2995.162 | 0.973 | 155.922 | 0.465 |
| polars | 1077.037 | 0.000 | 118.473 | 0.000 |
| duckdb | 1699.609 | 0.183 | 158.929 | 0.240 |
| pandas_arrow | 977.681 | 0.003 | 126.685 | 0.003 |

| Condition and role | E user ms/job | P user ms/job | E kernel ms/job | P kernel ms/job |
| --- | ---: | ---: | ---: | ---: |
| swiftsci_optional worker | 865.667 | 0.000 | 94.886 | 0.069 |
| swiftsci_optional controller | 4.726 | 0.350 | 3.076 | 0.219 |
| swiftsci_compact worker | 829.943 | 0.000 | 76.398 | 0.107 |
| swiftsci_compact controller | 4.609 | 0.102 | 3.094 | 0.091 |
| pandas worker | 2981.773 | 0.000 | 149.364 | 0.065 |
| pandas controller | 13.389 | 0.973 | 6.558 | 0.400 |
| polars worker | 1068.387 | 0.000 | 111.906 | 0.000 |
| polars controller | 6.883 | 0.000 | 6.567 | 0.000 |
| duckdb worker | 1690.554 | 0.000 | 148.456 | 0.046 |
| duckdb controller | 9.055 | 0.183 | 9.805 | 0.196 |
| pandas_arrow worker | 971.799 | 0.000 | 121.989 | 0.001 |
| pandas_arrow controller | 5.882 | 0.003 | 4.696 | 0.002 |

Observation requests a 10 ms cadence. Every queue must meet the fixed 50 ms maximum coverage gap and scan duration. Missing boundary scans fail audit. These checks qualify sampling coverage, not an instantaneous memory peak.

| Condition | Sampled footprint MiB | Maximum coverage gap ms | Maximum scan ms | Controller CPU ms/job |
| --- | ---: | ---: | ---: | ---: |
| swiftsci_optional | 2098.3 | 17.828 | 1.373 | 8.822 |
| swiftsci_compact | 1392.4 | 14.101 | 0.807 | 8.624 |
| pandas | 2572.5 | 14.388 | 0.833 | 21.919 |
| polars | 1682.2 | 13.258 | 2.036 | 14.098 |
| duckdb | 2005.2 | 19.428 | 2.520 | 19.777 |
| pandas_arrow | 2835.2 | 13.022 | 1.669 | 10.988 |

Physical footprint supplements RSS. It does not replace the unchanged RSS repeatability gate. Reusable bytes are not available from this unprivileged cross-process probe. Controller CPU charging includes initial/final scans, stats, core reads, and receipt validation. Its wider interval is recorded separately from queue wall timing. Final receipt serialization and disk writes are excluded.

Core counters bracket the queue plus boundary bookkeeping. They cover a wider interval than the wall timer and are not an exact partition of the existing charged_cpu_ns metric. Raw worker and controller snapshots remain in each receipt.
