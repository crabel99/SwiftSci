# Joined-frame compatibility costs

Every entry lists original / prior / current. CPU includes CSV, left join, optional exports when requested, and release. The joined frame remains retained alongside any exported optional Double arrays.

| Case | CPU, ms | Held heap, MiB | Peak RSS, MiB |
|---|---:|---:|---:|
| energy-common/serial/join-only | 686.21 / 1799.37 / 440.51 | 316.83 / 316.83 / 207.78 | 642.39 / 565.91 / 423.41 |
| energy-common/serial/join-materialize | 682.12 / 1796.98 / 477.23 | 316.83 / 316.83 / 429.48 | 642.40 / 565.94 / 550.17 |
| energy-common/parallel/join-only | 706.24 / 1827.60 / 464.26 | 316.83 / 316.83 / 207.78 | 644.22 / 567.74 / 425.21 |
| energy-common/parallel/join-materialize | 716.48 / 1852.82 / 508.52 | 316.83 / 316.83 / 429.48 | 644.25 / 567.74 / 551.98 |
| Aotizhongxin-default/serial/join-only | 23.59 / 56.56 / 16.78 | 10.50 / 10.50 / 7.63 | 29.62 / 26.81 / 22.83 |
| Aotizhongxin-default/serial/join-materialize | 23.41 / 56.45 / 17.33 | 10.50 / 10.50 / 13.65 | 29.05 / 26.80 / 22.81 |
| Aotizhongxin-default/parallel/join-only | 26.56 / 59.60 / 19.50 | 10.50 / 10.50 / 7.63 | 29.34 / 27.07 / 23.09 |
| Aotizhongxin-default/parallel/join-materialize | 26.53 / 58.39 / 20.07 | 10.50 / 10.50 / 13.65 | 29.34 / 27.17 / 23.11 |

Identical-binary flags: []
