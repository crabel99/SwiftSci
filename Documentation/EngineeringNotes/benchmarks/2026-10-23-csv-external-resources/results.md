# Exact CSV resource comparisons

Every row has 12 independent fresh-process workers. Medians use complete known-schema reads with matching null tokens and exact outputs. CPU is process user plus system time during the operation. Elapsed time is separate. Peak is captured before validation.

Baseline peak includes imported runtime and validation dependencies. Read peak increase is the median nonnegative difference between post-read and pre-read high-water marks. A zero increase can occur when import-time peak exceeds read peak; it does not mean zero read allocation. Held RSS delta is also reported for eager outputs. Streaming RSS after draining is not retained-output memory.

| Case | Scope | Engine | CPU ms | Elapsed ms | Baseline peak MiB | Process read peak MiB | Read peak increase MiB | Held or drained RSS change MiB |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Aotizhongxin | eager | swift-parallel | 11.236 | 4.540 | 6.55 | 25.39 | 18.84 | +16.12 |
| Aotizhongxin | eager | swift-serial | 8.418 | 8.442 | 6.55 | 22.84 | 16.30 | +13.58 |
| Aotizhongxin | eager | pandas | 35.627 | 35.770 | 97.88 | 115.90 | 18.00 | +18.00 |
| Aotizhongxin | eager | polars | 21.358 | 2.960 | 60.17 | 80.38 | 20.30 | +18.91 |
| Aotizhongxin | eager | duckdb | 36.508 | 18.688 | 75.42 | 95.92 | 20.46 | +20.46 |
| Aotizhongxin | stream | swift-parallel | 11.166 | 4.128 | 6.52 | 16.34 | 9.82 | +7.10 |
| Aotizhongxin | stream | swift-serial | 7.749 | 7.783 | 6.52 | 14.40 | 7.88 | +5.16 |
| Aotizhongxin | stream | pandas | 37.906 | 38.044 | 97.93 | 117.12 | 18.92 | +18.92 |
| Aotizhongxin | stream | polars | 15.703 | 4.210 | 60.12 | 85.79 | 25.44 | +25.44 |
| Aotizhongxin | stream | duckdb | 22.799 | 18.264 | 75.41 | 86.44 | 10.88 | +10.88 |
| Aotizhongxin-default | eager | swift-parallel | 11.354 | 4.781 | 6.55 | 25.56 | 19.02 | +16.30 |
| Aotizhongxin-default | eager | swift-serial | 8.697 | 8.729 | 6.55 | 22.84 | 16.30 | +13.58 |
| Aotizhongxin-default | eager | pandas | 36.020 | 36.284 | 97.93 | 116.46 | 18.49 | +18.49 |
| Aotizhongxin-default | eager | polars | 25.769 | 3.431 | 59.95 | 80.23 | 20.30 | +17.62 |
| Aotizhongxin-default | eager | duckdb | 43.580 | 21.907 | 75.43 | 95.77 | 20.45 | +20.45 |
| Aotizhongxin-default | stream | swift-parallel | 11.402 | 4.318 | 6.53 | 15.80 | 9.27 | +6.55 |
| Aotizhongxin-default | stream | swift-serial | 8.128 | 8.168 | 6.53 | 16.72 | 10.17 | +7.45 |
| Aotizhongxin-default | stream | pandas | 38.077 | 38.246 | 98.05 | 116.88 | 18.60 | +18.60 |
| Aotizhongxin-default | stream | polars | 20.824 | 5.139 | 60.06 | 86.30 | 26.17 | +26.17 |
| Aotizhongxin-default | stream | duckdb | 26.977 | 21.810 | 75.45 | 87.48 | 11.89 | +11.89 |
| Wanliu | eager | swift-parallel | 10.898 | 4.530 | 6.55 | 24.79 | 18.23 | +15.69 |
| Wanliu | eager | swift-serial | 8.511 | 8.567 | 6.55 | 22.66 | 16.11 | +13.56 |
| Wanliu | eager | pandas | 35.623 | 35.866 | 97.98 | 115.31 | 17.56 | +17.56 |
| Wanliu | eager | polars | 19.539 | 3.187 | 59.93 | 80.12 | 20.18 | +17.63 |
| Wanliu | eager | duckdb | 36.041 | 18.502 | 75.37 | 95.67 | 20.28 | +20.28 |
| Wanliu | stream | swift-parallel | 10.992 | 4.101 | 6.53 | 15.34 | 8.80 | +6.25 |
| Wanliu | stream | swift-serial | 7.864 | 7.897 | 6.53 | 15.95 | 9.42 | +6.88 |
| Wanliu | stream | pandas | 37.648 | 37.814 | 97.88 | 117.56 | 19.70 | +19.70 |
| Wanliu | stream | polars | 15.389 | 4.222 | 60.15 | 85.25 | 25.14 | +25.12 |
| Wanliu | stream | duckdb | 22.927 | 18.501 | 75.41 | 86.07 | 10.73 | +10.73 |
| Wanliu-default | eager | swift-parallel | 11.438 | 4.728 | 6.55 | 25.20 | 18.65 | +16.10 |
| Wanliu-default | eager | swift-serial | 8.709 | 8.748 | 6.55 | 22.66 | 16.11 | +13.56 |
| Wanliu-default | eager | pandas | 36.260 | 36.411 | 97.87 | 114.88 | 17.02 | +17.02 |
| Wanliu-default | eager | polars | 26.114 | 3.818 | 60.02 | 80.37 | 20.30 | +17.90 |
| Wanliu-default | eager | duckdb | 43.194 | 22.020 | 75.29 | 95.36 | 20.00 | +20.00 |
| Wanliu-default | stream | swift-parallel | 11.653 | 4.315 | 6.52 | 15.12 | 8.61 | +6.06 |
| Wanliu-default | stream | swift-serial | 7.970 | 8.037 | 6.52 | 14.25 | 7.73 | +5.19 |
| Wanliu-default | stream | pandas | 37.286 | 37.496 | 97.89 | 117.49 | 19.65 | +19.65 |
| Wanliu-default | stream | polars | 20.525 | 5.206 | 59.99 | 85.12 | 25.12 | +25.12 |
| Wanliu-default | stream | duckdb | 26.591 | 21.564 | 75.30 | 85.74 | 10.48 | +10.48 |
| energy | eager | swift-parallel | 267.345 | 120.326 | 6.53 | 422.27 | 415.74 | +288.93 |
| energy | eager | swift-serial | 245.563 | 245.636 | 6.53 | 420.55 | 414.02 | +287.20 |
| energy | eager | pandas | 1153.200 | 1153.622 | 97.84 | 406.78 | 308.90 | +308.90 |
| energy | eager | polars | 310.764 | 26.296 | 59.91 | 407.41 | 347.34 | +346.72 |
| energy | eager | duckdb | 640.056 | 71.413 | 75.34 | 571.09 | 495.60 | +495.60 |
| energy | stream | swift-parallel | 245.644 | 109.441 | 6.50 | 138.34 | 131.84 | +5.02 |
| energy | stream | swift-serial | 224.738 | 224.814 | 6.50 | 136.47 | 129.97 | +3.16 |
| energy | stream | pandas | 1272.216 | 1272.706 | 98.00 | 186.80 | 88.94 | +87.88 |
| energy | stream | polars | 323.510 | 37.449 | 60.12 | 370.78 | 310.82 | +152.54 |
| energy | stream | duckdb | 552.182 | 500.019 | 75.27 | 220.95 | 145.59 | +145.59 |
| energy-common | eager | swift-parallel | 259.793 | 116.657 | 6.55 | 422.27 | 415.73 | +288.91 |
| energy-common | eager | swift-serial | 240.556 | 240.684 | 6.55 | 420.55 | 414.00 | +287.19 |
| energy-common | eager | pandas | 1150.060 | 1150.430 | 97.98 | 406.89 | 308.84 | +308.84 |
| energy-common | eager | polars | 382.972 | 32.443 | 60.00 | 407.27 | 347.26 | +347.23 |
| energy-common | eager | duckdb | 746.196 | 80.051 | 75.36 | 571.05 | 495.72 | +495.72 |
| energy-common | stream | swift-parallel | 248.019 | 108.259 | 6.52 | 139.37 | 132.85 | +6.04 |
| energy-common | stream | swift-serial | 220.344 | 220.409 | 6.52 | 138.81 | 132.30 | +5.48 |
| energy-common | stream | pandas | 1275.928 | 1277.300 | 97.86 | 186.68 | 88.60 | +87.54 |
| energy-common | stream | polars | 389.394 | 41.072 | 59.98 | 384.16 | 323.89 | +161.49 |
| energy-common | stream | duckdb | 651.604 | 590.500 | 75.35 | 220.88 | 145.55 | +145.55 |
| energy-date-full | eager | swift-parallel | 317.288 | 152.494 | 6.56 | 422.33 | 415.77 | +288.95 |
| energy-date-full | eager | swift-serial | 278.822 | 279.008 | 6.56 | 420.59 | 414.03 | +287.22 |
| energy-date-full | eager | pandas | 1300.741 | 1301.359 | 97.85 | 649.77 | 551.84 | +442.26 |
| energy-date-full | eager | polars | 341.931 | 27.540 | 59.95 | 411.27 | 351.31 | +252.20 |
| energy-date-full | eager | duckdb | 687.630 | 66.802 | 75.42 | 537.08 | 461.73 | +461.73 |
| energy-date-full | stream | swift-parallel | 296.068 | 140.430 | 6.52 | 139.05 | 132.54 | +5.73 |
| energy-date-full | stream | swift-serial | 250.719 | 250.804 | 6.52 | 136.50 | 129.98 | +3.17 |
| energy-date-full | stream | pandas | 1457.174 | 1458.172 | 97.83 | 187.24 | 89.37 | +88.35 |
| energy-date-full | stream | polars | 329.288 | 40.776 | 59.98 | 383.95 | 323.88 | +180.05 |
| energy-date-full | stream | duckdb | 611.745 | 549.326 | 75.30 | 219.65 | 144.24 | +144.24 |

## Identical-binary controls

`swift-twin` launches exactly the same standalone binary and arguments as `swift-parallel`. Values below use independent processes and native hashing. They do not physically share a null-token Set.

| Case | Scope | Twin CPU change | Peak change MiB |
|---|---|---:|---:|
| Aotizhongxin | eager | +0.84% | -2.07 |
| Aotizhongxin | stream | +0.08% | +0.20 |
| Aotizhongxin-default | eager | +0.71% | -0.19 |
| Aotizhongxin-default | stream | -1.19% | +0.40 |
| Wanliu | eager | +1.65% | +0.42 |
| Wanliu | stream | -0.30% | +0.72 |
| Wanliu-default | eager | +2.43% | -0.01 |
| Wanliu-default | stream | +0.84% | +0.68 |
| energy | eager | +0.23% | -0.01 |
| energy | stream | +1.10% | +0.56 |
| energy-common | eager | -0.56% | +0.07 |
| energy-common | stream | -1.32% | -0.11 |
| energy-date-full | eager | -0.22% | -0.04 |
| energy-date-full | stream | +0.12% | -0.13 |
