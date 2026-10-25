# CPU counter evidence

Protocol: cpu-counter-evidence-v1.

Original controls passed: False. Performance qualified: False.

Descriptive counters only. Cycles per CPU ns is an accounted execution rate, not direct hardware frequency or energy. Rates and CPU time share a denominator. No causal classification, timing normalization, exclusion, or qualification change.

Method predeclared: False.

[Original comparison report](</private/tmp/swiftsci-e-core-observer-isolation-20261025/smoke-final/panel/report.md>)

| Condition | Variant | Jobs/min | CPU ms/job | Wall ms/job | Sampled peak MiB | Resident MiB-seconds |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| duckdb | primary | 48.692 | 1691.3 | 1271.2 | 2296.1 | 14564 |
| duckdb | twin | 59.625 | 1677.1 | 1021 | 2268.8 | 11751 |
| pandas | primary | 32.244 | 3250.6 | 1871 | 2720.7 | 14922 |
| pandas | twin | 30.313 | 3024.8 | 1982.7 | 2720.7 | 16953 |
| pandas_arrow | primary | 122.03 | 846.27 | 536.94 | 3125.8 | 6544.2 |
| pandas_arrow | twin | 93.72 | 1104 | 654.88 | 3137.6 | 8045.5 |
| polars | primary | 90.481 | 1359.3 | 664.15 | 1783.8 | 6330.5 |
| polars | twin | 71.35 | 1154.6 | 857.36 | 1790.5 | 8400.3 |
| swiftsci_compact | primary | 121.4 | 913.21 | 495.14 | 1417.7 | 3686.2 |
| swiftsci_compact | twin | 104.19 | 894.47 | 596.12 | 1417.1 | 4509.5 |
| swiftsci_optional | primary | 122.51 | 887.59 | 494.6 | 2121.5 | 5172.1 |
| swiftsci_optional | twin | 143.56 | 744.09 | 422.45 | 2122.8 | 4370.8 |

## Work and accounted execution rates

Medians keep primary and twin queues separate. Every ratio is twin divided by primary. Worker values sum processes before dividing; controller work remains separate. Instructions and cycles include user and kernel work on the named core class. Worker P values are permitted kernel work because P-user time must be zero. Ratios against near-zero P work are unstable. None of these columns measures energy.

| Condition | Role | Core | Instructions/job | Twin instruction ratio | Cycles/job | Twin cycle ratio | Cycles/CPU ns | Twin rate ratio |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| duckdb | worker | E | 8.2395e+09 | 0.99368 | 2.5318e+09 | 0.99795 | 1.5319 | 1.0148 |
| duckdb | worker | P | 4.0902e+06 | 0 | 2.4935e+06 | 0 | unavailable | unavailable |
| duckdb | controller | E | 2.4608e+07 | 0.8771 | 4.7736e+07 | 0.82508 | 1.7197 | 0.92318 |
| duckdb | controller | P | 2.1008e+06 | 0.011549 | 4.4347e+06 | 0.018566 | 3.758 | unavailable |
| pandas | worker | E | 1.564e+10 | 1.0032 | 4.2438e+09 | 1.0196 | 1.3292 | 1.1583 |
| pandas | worker | P | 39992 | 0.1512 | 54221 | 0.20801 | 3.1243 | 0.95953 |
| pandas | controller | E | 2.8468e+07 | 1.0813 | 4.4827e+07 | 1.2804 | 1.3721 | 1.1842 |
| pandas | controller | P | 3.7517e+05 | 0.14381 | 6.0203e+05 | 0.18554 | 3.6835 | 0.8519 |
| pandas_arrow | worker | E | 4.4588e+09 | 1.0017 | 1.4599e+09 | 0.98249 | 1.8799 | 0.70451 |
| pandas_arrow | worker | P | 5123.4 | 0 | 8904.4 | 0 | unavailable | unavailable |
| pandas_arrow | controller | E | 1.0317e+07 | 1.2137 | 1.9981e+07 | 1.0372 | 1.9718 | 0.70086 |
| pandas_arrow | controller | P | 98053 | 0 | 1.8993e+05 | 0 | unavailable | unavailable |
| polars | worker | E | 5.2999e+09 | 0.99854 | 1.5642e+09 | 1.0299 | 1.1658 | 1.3018 |
| polars | worker | P | 14076 | 39.4 | 18087 | 27.422 | unavailable | unavailable |
| polars | controller | E | 1.3205e+07 | 1.1834 | 1.9052e+07 | 1.734 | 1.1755 | 1.4266 |
| polars | controller | P | 78186 | 21.021 | 1.6435e+05 | 23.039 | unavailable | unavailable |
| swiftsci_compact | worker | E | 3.546e+09 | 0.99941 | 1.1927e+09 | 0.97294 | 1.3223 | 1.0167 |
| swiftsci_compact | worker | P | 1.7412e+05 | 3.3069 | 2.5355e+05 | 2.3041 | 3.6782 | 1.013 |
| swiftsci_compact | controller | E | 7.1552e+06 | 1.3294 | 1.1375e+07 | 1.4621 | 1.3799 | 1.0786 |
| swiftsci_compact | controller | P | 1.9106e+06 | 0.68592 | 3.891e+06 | 0.64636 | 3.6493 | 1.0222 |
| swiftsci_optional | worker | E | 3.5611e+09 | 0.99923 | 1.1926e+09 | 1.0888 | 1.3651 | 1.4105 |
| swiftsci_optional | worker | P | 74730 | 20.413 | 66372 | 22.103 | 3.5036 | 1.0236 |
| swiftsci_optional | controller | E | 8.8826e+06 | 0.61846 | 1.3927e+07 | 0.82003 | 1.3678 | 1.4336 |
| swiftsci_optional | controller | P | 3.1165e+05 | 7.4293 | 4.7845e+05 | 9.7278 | 3.7206 | 1.0025 |

## Original control failures

- {"label": "swiftsci_optional", "metric": "charged_cpu_ns", "ratio": 0.8383221802688424}
- {"label": "swiftsci_optional", "metric": "elapsed_ns", "ratio": 0.8541103215391354}
- {"label": "swiftsci_compact", "metric": "elapsed_ns", "ratio": 1.2039292191958595}
- {"label": "polars", "metric": "charged_cpu_ns", "ratio": 0.8493872099474366}
- {"label": "polars", "metric": "elapsed_ns", "ratio": 1.2909289766646812}
- {"label": "duckdb", "metric": "elapsed_ns", "ratio": 0.8031871945440401}
- {"label": "pandas_arrow", "metric": "charged_cpu_ns", "ratio": 1.3045487816487469}
- {"label": "pandas_arrow", "metric": "elapsed_ns", "ratio": 1.2196605177692557}

Direct hardware frequency was not measured in these queue receipts. A separate fixed-loop trace cannot identify the clock state of an earlier queue. Ratios from different libraries can also reflect instruction mix and memory stalls. Do not attribute them solely to frequency.
