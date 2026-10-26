# CPU counter evidence

Protocol: cpu-counter-evidence-v1.

Original controls passed: False. Performance qualified: False.

Descriptive counters only. Cycles per CPU ns is an accounted execution rate, not direct hardware frequency or energy. Rates and CPU time share a denominator. No causal classification, timing normalization, exclusion, or qualification change.

Method predeclared: True.

[Original comparison report](</private/tmp/swiftsci-cpu-operating-state-full-20261025/study/comparison/panel/report.md>)

| Condition | Variant | Jobs/min | CPU ms/job | Wall ms/job | Sampled peak MiB | Resident MiB-seconds |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| duckdb | primary | 97.058 | 1474.7 | 618.92 | 4147.1 | 1.3317e+05 |
| duckdb | twin | 123.39 | 1079.6 | 487.09 | 4211 | 1.0241e+05 |
| pandas | primary | 66.102 | 2165.2 | 907.76 | 3684.7 | 1.6928e+05 |
| pandas | twin | 55.494 | 2627.6 | 1082 | 3683.7 | 1.9865e+05 |
| pandas_arrow | primary | 177.8 | 817.73 | 337.55 | 5075 | 88456 |
| pandas_arrow | twin | 170.77 | 638.02 | 351.61 | 5067.1 | 92688 |
| polars | primary | 140.77 | 912.61 | 426.49 | 2176 | 48770 |
| polars | twin | 204.61 | 822.13 | 294.37 | 2194.5 | 34570 |
| swiftsci_compact | primary | 219.81 | 555 | 273.78 | 2468.3 | 35782 |
| swiftsci_compact | twin | 188.49 | 662.8 | 318.58 | 2468.5 | 41475 |
| swiftsci_optional | primary | 234.15 | 590.28 | 256.34 | 3447.3 | 47608 |
| swiftsci_optional | twin | 199.31 | 722.28 | 301.35 | 3448 | 56548 |

## Work and accounted execution rates

Medians keep primary and twin queues separate. Every ratio is twin divided by primary. Worker values sum processes before dividing; controller work remains separate. Instructions and cycles include user and kernel work on the named core class. Worker P values are permitted kernel work because P-user time must be zero. Ratios against near-zero P work are unstable. None of these columns measures energy.

| Condition | Role | Core | Instructions/job | Twin instruction ratio | Cycles/job | Twin cycle ratio | Cycles/CPU ns | Twin rate ratio |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| duckdb | worker | E | 7.9653e+09 | 1.0016 | 2.3905e+09 | 1.0189 | 1.6292 | 1.4211 |
| duckdb | worker | P | 0 | unavailable | 0 | unavailable | unavailable | unavailable |
| duckdb | controller | E | 1.4176e+07 | 0.77909 | 2.6365e+07 | 0.97329 | 1.6033 | 1.4511 |
| duckdb | controller | P | 5171.5 | 3.4374 | 11102 | 3.7561 | unavailable | unavailable |
| pandas | worker | E | 1.5446e+10 | 1.003 | 4.1525e+09 | 0.99742 | 1.945 | 0.81928 |
| pandas | worker | P | 777.16 | 1.7554 | 1571.1 | 1.2463 | unavailable | unavailable |
| pandas | controller | E | 1.3851e+07 | 1.1672 | 2.6725e+07 | 1.0772 | 1.8924 | 0.84928 |
| pandas | controller | P | 26025 | 0.65784 | 59191 | 0.79197 | 3.6058 | 1.0303 |
| pandas_arrow | worker | E | 4.3247e+09 | 0.99872 | 1.3419e+09 | 1.0603 | 1.663 | 1.3836 |
| pandas_arrow | worker | P | 3111.2 | 0.068088 | 2648.9 | 0.14889 | unavailable | unavailable |
| pandas_arrow | controller | E | 6.3187e+06 | 1.0386 | 1.1471e+07 | 1.1008 | 1.6149 | 1.4565 |
| pandas_arrow | controller | P | 5420.5 | 1.682 | 11299 | 2.2488 | unavailable | unavailable |
| polars | worker | E | 5.2312e+09 | 0.99813 | 1.5746e+09 | 0.99984 | 1.7637 | 1.0887 |
| polars | worker | P | 395.73 | 0 | 710.78 | 0 | unavailable | unavailable |
| polars | controller | E | 8.8742e+06 | 0.64365 | 1.5186e+07 | 0.87564 | 1.6986 | 1.1409 |
| polars | controller | P | 9536.2 | 0 | 18897 | 0 | unavailable | unavailable |
| swiftsci_compact | worker | E | 3.4649e+09 | 1.0002 | 1.2734e+09 | 0.94249 | 2.3927 | 0.77781 |
| swiftsci_compact | worker | P | 16798 | 1.0965 | 18906 | 1.3325 | 3.5693 | 0.98345 |
| swiftsci_compact | controller | E | 4.8421e+06 | 1.1758 | 1.0152e+07 | 1.0415 | 2.4114 | 0.75121 |
| swiftsci_compact | controller | P | 75517 | 0.86211 | 92224 | 0.80862 | 3.6658 | 0.99339 |
| swiftsci_optional | worker | E | 3.4416e+09 | 1.0001 | 1.2854e+09 | 0.93506 | 2.2406 | 0.75744 |
| swiftsci_optional | worker | P | 27905 | 0.33464 | 25134 | 0.48333 | 3.5321 | unavailable |
| swiftsci_optional | controller | E | 4.5762e+06 | 1.1751 | 1.1011e+07 | 0.83962 | 2.2304 | 0.73373 |
| swiftsci_optional | controller | P | 69650 | 0.74142 | 93185 | 0.66811 | 3.6805 | unavailable |

## Original control failures

- {"label": "swiftsci_optional", "metric": "charged_cpu_ns", "ratio": 1.2236125491539322}
- {"label": "swiftsci_optional", "metric": "elapsed_ns", "ratio": 1.1755709585963454}
- {"label": "swiftsci_compact", "metric": "charged_cpu_ns", "ratio": 1.1942229452688047}
- {"label": "swiftsci_compact", "metric": "elapsed_ns", "ratio": 1.1636317287626239}
- {"label": "pandas", "metric": "charged_cpu_ns", "ratio": 1.2135450222374724}
- {"label": "pandas", "metric": "elapsed_ns", "ratio": 1.1919796116070782}
- {"label": "polars", "metric": "elapsed_ns", "ratio": 0.6902162562526978}
- {"label": "duckdb", "metric": "charged_cpu_ns", "ratio": 0.7320606960743552}
- {"label": "duckdb", "metric": "elapsed_ns", "ratio": 0.7870031219435444}
- {"label": "pandas_arrow", "metric": "charged_cpu_ns", "ratio": 0.7802392360332465}
- {"label": "pandas_twin", "max_gap_ns": 50526000, "max_scan_ns": 37394333, "metric": "observation_coverage", "round": 7}

Direct hardware frequency was not measured in these queue receipts. A separate fixed-loop trace cannot identify the clock state of an earlier queue. Ratios from different libraries can also reflect instruction mix and memory stalls. Do not attribute them solely to frequency.
