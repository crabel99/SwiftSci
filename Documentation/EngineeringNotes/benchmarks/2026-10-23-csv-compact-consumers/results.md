# Compact numerical consumer resource results

Eight fresh processes per label. CPU includes public CSV construction, requested operations and release. Full output validation is outside timing. All outputs match the original reader. Original is the qualified optional-array reader; prior is the first compact prototype; current includes specialization and direct numerical access.

| Case | CPU original / prior / current, ms | Held heap original / prior / current, MiB | Peak RSS original / prior / current, MiB |
|---|---:|---:|---:|
| energy-common/serial/read | 244.26 / 263.01 / 261.42 | 285.15 / 176.11 / 176.11 | 420.58 / 312.41 / 312.39 |
| energy-common/serial/materialize | 242.65 / 1372.32 / 285.45 | 285.15 / 397.81 / 397.81 | 421.28 / 407.41 / 407.38 |
| energy-common/serial/filter-matrix | 245.16 / 306.64 / 301.85 | 25.33 / 25.33 / 25.33 | 420.58 / 431.74 / 431.72 |
| energy-common/serial/gather-matrix | 253.35 / 308.41 / 306.28 | 23.51 / 23.51 / 23.51 | 420.58 / 431.06 / 431.05 |
| energy-common/serial/sort-matrix | 436.84 / 495.77 / 497.89 | 396.00 / 396.00 / 396.00 | 737.48 / 851.06 / 851.03 |
| energy-common/serial/join-matrix | 709.52 / 1846.36 / 1827.74 | 427.67 / 427.67 / 427.67 | 753.28 / 676.78 / 676.75 |
| energy-common/serial/row-scan | 372.36 / 383.09 / 377.55 | 285.15 / 176.11 / 176.11 | 420.58 / 312.39 / 312.36 |
| energy-common/serial/lag-matrix | 396.04 / 431.02 / 400.52 | 443.50 / 334.45 / 334.45 | 452.22 / 565.81 / 343.98 |
| energy-common/serial/matrix | 249.05 / 295.69 / 266.73 | 396.00 / 286.95 / 286.95 | 420.58 / 518.25 / 312.36 |
| energy-common/serial/batch | 247.94 / 297.80 / 243.37 | 397.81 / 288.76 / 176.11 | 420.58 / 518.41 / 312.36 |
| energy-common/parallel/read | 265.38 / 274.44 / 273.43 | 285.15 / 176.11 / 176.11 | 422.38 / 314.23 / 314.20 |
| energy-common/parallel/materialize | 265.42 / 1371.49 / 306.41 | 285.15 / 397.81 / 397.81 | 422.41 / 409.25 / 409.22 |
| energy-common/parallel/filter-matrix | 276.52 / 330.88 / 327.98 | 25.33 / 25.33 / 25.33 | 422.35 / 433.45 / 433.41 |
| energy-common/parallel/gather-matrix | 281.11 / 332.63 / 330.54 | 23.51 / 23.51 / 23.51 | 422.36 / 431.37 / 431.36 |
| energy-common/parallel/sort-matrix | 464.39 / 520.94 / 518.20 | 396.00 / 396.00 / 396.00 | 739.15 / 852.77 / 852.77 |
| energy-common/parallel/join-matrix | 734.57 / 1841.91 / 1833.79 | 427.67 / 427.67 / 427.67 | 755.06 / 678.60 / 678.55 |
| energy-common/parallel/row-scan | 399.60 / 404.86 / 404.22 | 285.15 / 176.11 / 176.11 | 422.40 / 314.23 / 314.17 |
| energy-common/parallel/lag-matrix | 419.38 / 454.29 / 421.92 | 443.50 / 334.45 / 334.45 | 453.95 / 567.64 / 345.81 |
| energy-common/parallel/matrix | 282.65 / 323.46 / 293.79 | 396.00 / 286.95 / 286.95 | 422.39 / 520.08 / 314.17 |
| energy-common/parallel/batch | 279.51 / 323.13 / 271.46 | 397.81 / 288.76 / 176.11 | 422.35 / 520.23 / 314.18 |
| Aotizhongxin-default/serial/read | 8.07 / 8.26 / 8.21 | 9.95 / 7.09 / 7.09 | 22.84 / 21.70 / 21.66 |
| Aotizhongxin-default/serial/materialize | 8.03 / 39.17 / 9.02 | 9.95 / 13.10 / 13.10 | 22.84 / 21.72 / 21.66 |
| Aotizhongxin-default/serial/filter-matrix | 11.84 / 13.48 / 13.62 | 13.52 / 13.52 / 13.52 | 31.88 / 32.81 / 33.03 |
| Aotizhongxin-default/serial/gather-matrix | 9.23 / 10.42 / 10.54 | 1.22 / 1.22 / 1.22 | 22.84 / 21.77 / 21.77 |
| Aotizhongxin-default/serial/sort-matrix | 13.74 / 15.49 / 15.52 | 14.24 / 14.24 / 14.24 | 33.04 / 34.34 / 34.59 |
| Aotizhongxin-default/serial/join-matrix | 23.53 / 54.97 / 55.60 | 14.78 / 14.78 / 14.78 | 33.33 / 31.05 / 31.02 |
| Aotizhongxin-default/serial/row-scan | 10.81 / 10.96 / 10.91 | 9.95 / 7.09 / 7.09 | 22.84 / 21.70 / 21.62 |
| Aotizhongxin-default/serial/lag-matrix | 11.59 / 12.76 / 12.02 | 15.06 / 12.20 / 12.20 | 24.75 / 26.36 / 23.53 |
| Aotizhongxin-default/serial/matrix | 9.20 / 10.36 / 9.55 | 14.24 / 11.37 / 11.37 | 24.44 / 25.51 / 23.22 |
| Aotizhongxin-default/serial/batch | 8.98 / 10.04 / 8.80 | 14.51 / 11.64 / 8.49 | 22.84 / 25.19 / 21.66 |
| Aotizhongxin-default/parallel/read | 11.51 / 11.60 / 11.53 | 9.95 / 7.09 / 7.09 | 23.13 / 22.02 / 21.91 |
| Aotizhongxin-default/parallel/materialize | 11.39 / 43.87 / 12.27 | 9.95 / 13.10 / 13.10 | 23.14 / 22.01 / 21.91 |
| Aotizhongxin-default/parallel/filter-matrix | 15.89 / 17.18 / 17.16 | 13.52 / 13.52 / 13.52 | 31.98 / 34.01 / 34.19 |
| Aotizhongxin-default/parallel/gather-matrix | 12.31 / 13.22 / 13.14 | 1.22 / 1.22 / 1.22 | 23.15 / 22.98 / 23.16 |
| Aotizhongxin-default/parallel/sort-matrix | 17.73 / 18.63 / 18.90 | 14.24 / 14.24 / 14.24 | 33.17 / 35.84 / 35.89 |
| Aotizhongxin-default/parallel/join-matrix | 26.83 / 58.42 / 58.75 | 14.78 / 14.78 / 14.78 | 33.61 / 31.35 / 31.28 |
| Aotizhongxin-default/parallel/row-scan | 14.05 / 13.84 / 13.61 | 9.95 / 7.09 / 7.09 | 23.14 / 21.98 / 21.90 |
| Aotizhongxin-default/parallel/lag-matrix | 14.57 / 15.43 / 14.72 | 15.06 / 12.20 / 12.20 | 25.03 / 26.68 / 23.82 |
| Aotizhongxin-default/parallel/matrix | 12.06 / 13.01 / 11.93 | 14.24 / 11.37 / 11.37 | 24.72 / 25.80 / 23.53 |
| Aotizhongxin-default/parallel/batch | 11.33 / 12.17 / 11.09 | 14.51 / 11.64 / 8.49 | 23.14 / 25.51 / 21.91 |

Identical-binary flags: []. Flagged cases remain unqualified. These are CPU and allocation measurements, not energy, FLOP or cache measurements.
