# Compact nullable join resource results

Eight fresh processes per label. CPU includes public CSV construction, requested operations and release. Full output validation is outside timing. All outputs match the original reader. Original is the qualified optional-array reader. Prior preserves compact storage through ordinary selection. Current also preserves it through nullable joins.

| Case | CPU original / prior / current, ms | Held heap original / prior / current, MiB | Peak RSS original / prior / current, MiB |
|---|---:|---:|---:|
| energy-common/serial/read | 241.31 / 243.46 / 245.44 | 285.15 / 176.11 / 176.11 | 421.30 / 312.36 / 312.45 |
| energy-common/serial/join-inner-matrix | 273.60 / 1372.07 / 273.88 | 0.53 / 0.53 / 0.42 | 422.00 / 313.07 / 313.88 |
| energy-common/serial/join-matrix | 695.52 / 1813.08 / 459.30 | 427.67 / 427.67 / 318.62 | 753.25 / 676.76 / 534.31 |
| energy-common/serial/join-right-matrix | 266.53 / 1371.26 / 272.11 | 0.53 / 0.53 / 0.42 | 420.58 / 312.36 / 312.45 |
| energy-common/serial/join-outer-matrix | 696.28 / 1798.23 / 460.40 | 427.67 / 427.67 / 318.62 | 753.25 / 676.75 / 534.31 |
| energy-common/serial/batch | 253.60 / 245.12 / 243.79 | 397.81 / 176.11 / 176.11 | 420.58 / 312.36 / 312.45 |
| energy-common/parallel/read | 268.36 / 268.39 / 271.08 | 285.15 / 176.11 / 176.11 | 422.38 / 314.16 / 314.27 |
| energy-common/parallel/join-inner-matrix | 301.06 / 1405.56 / 300.08 | 0.53 / 0.53 / 0.42 | 422.39 / 314.17 / 314.27 |
| energy-common/parallel/join-matrix | 730.29 / 1826.37 / 487.02 | 427.67 / 427.67 / 318.62 | 755.03 / 678.57 / 536.14 |
| energy-common/parallel/join-right-matrix | 300.03 / 1397.33 / 299.02 | 0.53 / 0.53 / 0.42 | 422.38 / 314.19 / 314.27 |
| energy-common/parallel/join-outer-matrix | 728.36 / 1841.39 / 486.28 | 427.67 / 427.67 / 318.62 | 755.05 / 678.61 / 536.11 |
| energy-common/parallel/batch | 281.35 / 266.44 / 266.91 | 397.81 / 176.11 / 176.11 | 422.38 / 314.18 / 314.27 |
| Aotizhongxin-default/serial/read | 7.96 / 8.08 / 8.11 | 9.95 / 7.09 / 7.09 | 22.83 / 21.75 / 21.78 |
| Aotizhongxin-default/serial/join-inner-matrix | 22.51 / 53.79 / 16.03 | 14.78 / 14.78 / 11.91 | 33.26 / 31.09 / 27.10 |
| Aotizhongxin-default/serial/join-matrix | 22.41 / 53.87 / 15.92 | 14.78 / 14.78 / 11.91 | 33.27 / 31.08 / 27.11 |
| Aotizhongxin-default/serial/join-right-matrix | 22.34 / 53.70 / 15.94 | 14.78 / 14.78 / 11.91 | 33.25 / 31.08 / 27.09 |
| Aotizhongxin-default/serial/join-outer-matrix | 22.48 / 53.57 / 16.04 | 14.78 / 14.78 / 11.91 | 33.26 / 31.08 / 27.12 |
| Aotizhongxin-default/serial/batch | 8.47 / 8.18 / 8.18 | 14.51 / 8.49 / 8.49 | 22.84 / 21.72 / 21.77 |
| Aotizhongxin-default/parallel/read | 11.28 / 11.07 / 11.22 | 9.95 / 7.09 / 7.09 | 23.12 / 22.04 / 22.06 |
| Aotizhongxin-default/parallel/join-inner-matrix | 25.19 / 56.66 / 18.77 | 14.78 / 14.78 / 11.91 | 33.95 / 31.38 / 27.62 |
| Aotizhongxin-default/parallel/join-matrix | 24.94 / 56.93 / 18.82 | 14.78 / 14.78 / 11.91 | 33.55 / 31.76 / 27.77 |
| Aotizhongxin-default/parallel/join-right-matrix | 25.33 / 57.30 / 18.81 | 14.78 / 14.78 / 11.91 | 33.55 / 31.40 / 27.60 |
| Aotizhongxin-default/parallel/join-outer-matrix | 25.26 / 57.03 / 18.98 | 14.78 / 14.78 / 11.91 | 33.53 / 31.73 / 27.41 |
| Aotizhongxin-default/parallel/batch | 11.69 / 11.52 / 11.33 | 14.51 / 8.49 / 8.49 | 23.52 / 22.20 / 22.27 |

Identical-binary flags: []. Flagged cases remain unqualified. These are CPU and allocation measurements, not energy, FLOP or cache measurements.
