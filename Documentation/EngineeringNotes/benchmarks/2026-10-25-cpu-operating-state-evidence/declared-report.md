# CPU counter evidence

Protocol: cpu-counter-evidence-v1.

Original controls passed: False. Performance qualified: False.

Descriptive counters only. Cycles per CPU ns is an accounted execution rate, not direct hardware frequency or energy. Rates and CPU time share a denominator. No causal classification, timing normalization, exclusion, or qualification change.

Method predeclared: True.

[Original comparison report](</private/tmp/swiftsci-cpu-operating-state-evidence-20261025/declared-smoke/comparison/panel/report.md>)

| Condition | Variant | Jobs/min | CPU ms/job | Wall ms/job | Sampled peak MiB | Resident MiB-seconds |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| duckdb | primary | 87.369 | 1958.7 | 686.83 | 2224.8 | 8118 |
| duckdb | twin | 80.67 | 1835 | 750.67 | 2245.1 | 8995 |
| pandas | primary | 48.367 | 3153.7 | 1255.8 | 2720.8 | 10153 |
| pandas | twin | 52.513 | 3046.5 | 1142.8 | 2720.8 | 9459.2 |
| pandas_arrow | primary | 146.59 | 1078.6 | 411.98 | 3130.6 | 5208.6 |
| pandas_arrow | twin | 142.35 | 1117.6 | 423.95 | 3138 | 5248.7 |
| polars | primary | 123.57 | 1244.2 | 521.22 | 1801 | 5146 |
| polars | twin | 112.85 | 1098.3 | 633.42 | 1761.6 | 5757.3 |
| swiftsci_compact | primary | 174.24 | 929.68 | 344.64 | 1417.2 | 2553.4 |
| swiftsci_compact | twin | 152.54 | 918.63 | 393.52 | 1417.8 | 2924.9 |
| swiftsci_optional | primary | 172.71 | 987.23 | 347.46 | 2121.3 | 3534.3 |
| swiftsci_optional | twin | 130.27 | 835.43 | 463.33 | 2122.8 | 4648.3 |

## Work and accounted execution rates

Medians keep primary and twin queues separate. Every ratio is twin divided by primary. Worker values sum processes before dividing; controller work remains separate. Instructions and cycles include user and kernel work on the named core class. Worker P values are permitted kernel work because P-user time must be zero. Ratios against near-zero P work are unstable. None of these columns measures energy.

| Condition | Role | Core | Instructions/job | Twin instruction ratio | Cycles/job | Twin cycle ratio | Cycles/CPU ns | Twin rate ratio |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| duckdb | worker | E | 8.2552e+09 | 0.99507 | 2.3895e+09 | 1.0152 | 1.2408 | 1.0797 |
| duckdb | worker | P | 2.0627e+05 | 6.206 | 1.6885e+05 | 4.326 | 3.6549 | unavailable |
| duckdb | controller | E | 1.4193e+07 | 1.0834 | 2.1706e+07 | 1.2257 | 1.2056 | 1.0957 |
| duckdb | controller | P | 6.0884e+05 | 1.4124 | 1.3889e+06 | 1.3836 | 3.7793 | 0.90272 |
| pandas | worker | E | 1.5568e+10 | 1.0002 | 4.1172e+09 | 1.0066 | 1.318 | 1.0472 |
| pandas | worker | P | 1.5863e+05 | 0.49224 | 3.2724e+05 | 0.42137 | 3.5355 | unavailable |
| pandas | controller | E | 1.6798e+07 | 1.012 | 2.5538e+07 | 1.0359 | 1.2842 | 1.0561 |
| pandas | controller | P | 2.8327e+06 | 0.3613 | 5.984e+06 | 0.38845 | 3.8359 | unavailable |
| pandas_arrow | worker | E | 4.4535e+09 | 0.99968 | 1.3735e+09 | 1.0037 | 1.3022 | 0.96647 |
| pandas_arrow | worker | P | 33184 | 0.026624 | 54853 | 0.037474 | unavailable | unavailable |
| pandas_arrow | controller | E | 8.1035e+06 | 1.0385 | 1.2769e+07 | 1.0822 | 1.2856 | 0.96397 |
| pandas_arrow | controller | P | 1.6179e+05 | 0.067415 | 3.2829e+05 | 0.069581 | unavailable | unavailable |
| polars | worker | E | 5.2836e+09 | 1.0018 | 1.554e+09 | 1.0204 | 1.2716 | 1.1738 |
| polars | worker | P | 0 | unavailable | 0 | unavailable | unavailable | unavailable |
| polars | controller | E | 1.0749e+07 | 1.1437 | 1.6371e+07 | 1.307 | 1.2385 | 1.1988 |
| polars | controller | P | 0 | unavailable | 0 | unavailable | unavailable | unavailable |
| swiftsci_compact | worker | E | 3.5368e+09 | 1.0042 | 1.1534e+09 | 1.025 | 1.2598 | 1.0347 |
| swiftsci_compact | worker | P | 1.5665e+05 | 2.2733 | 1.8989e+05 | 2.1515 | unavailable | unavailable |
| swiftsci_compact | controller | E | 6.1793e+06 | 1.0304 | 9.6296e+06 | 1.067 | 1.2463 | 1.0031 |
| swiftsci_compact | controller | P | 3.1768e+05 | 3.7336 | 4.4045e+05 | 4.7617 | unavailable | unavailable |
| swiftsci_optional | worker | E | 3.5606e+09 | 1.003 | 1.1747e+09 | 1.0895 | 1.2037 | 1.3727 |
| swiftsci_optional | worker | P | 1.2432e+06 | 0.088067 | 1.2909e+06 | 0.090104 | 3.909 | 0.82148 |
| swiftsci_optional | controller | E | 4.5852e+06 | 1.65 | 6.543e+06 | 2.2882 | 1.2092 | 1.4434 |
| swiftsci_optional | controller | P | 2.0174e+06 | 0.55271 | 3.7407e+06 | 0.53633 | 3.2393 | 1.154 |

## Original control failures

- {"label": "swiftsci_optional", "metric": "charged_cpu_ns", "ratio": 0.8462332930503381}
- {"label": "swiftsci_optional", "metric": "elapsed_ns", "ratio": 1.3334750075969437}
- {"label": "swiftsci_compact", "metric": "elapsed_ns", "ratio": 1.1418063954777802}
- {"label": "polars", "metric": "charged_cpu_ns", "ratio": 0.8827260807156885}
- {"label": "polars", "metric": "elapsed_ns", "ratio": 1.2152593367212912}

Direct hardware frequency was not measured in these queue receipts. A separate fixed-loop trace cannot identify the clock state of an earlier queue. Ratios from different libraries can also reflect instruction mix and memory stalls. Do not attribute them solely to frequency.
