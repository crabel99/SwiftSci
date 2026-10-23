# Compact selection resource results

Eight fresh processes per label. CPU includes public CSV construction, requested operations and release. Full output validation is outside timing. All outputs match the original reader. Original is the qualified optional-array reader; prior includes specialization and direct numerical access; current also preserves compact storage through gathering.

| Case | CPU original / prior / current, ms | Held heap original / prior / current, MiB | Peak RSS original / prior / current, MiB |
|---|---:|---:|---:|
| energy-common/serial/read | 237.39 / 243.96 / 246.96 | 285.15 / 176.11 / 176.11 | 420.58 / 312.36 / 312.38 |
| energy-common/serial/materialize | 240.51 / 288.59 / 288.63 | 285.15 / 397.81 / 397.81 | 420.58 / 407.36 / 407.40 |
| energy-common/serial/filter-matrix | 265.72 / 319.75 / 270.72 | 25.33 / 25.33 / 18.65 | 420.59 / 431.68 / 312.39 |
| energy-common/serial/gather-matrix | 258.52 / 308.22 / 263.14 | 23.51 / 23.51 / 17.06 | 420.58 / 431.08 / 312.39 |
| energy-common/serial/sort-matrix | 456.86 / 530.73 / 447.49 | 396.00 / 396.00 / 310.30 | 737.50 / 851.03 / 511.39 |
| energy-common/serial/join-matrix | 721.63 / 1805.58 / 1823.77 | 427.67 / 427.67 / 427.67 | 753.28 / 676.75 / 676.77 |
| energy-common/serial/row-scan | 371.06 / 378.58 / 376.59 | 285.15 / 176.11 / 176.11 | 420.58 / 312.34 / 312.38 |
| energy-common/serial/lag-matrix | 394.79 / 402.50 / 399.08 | 443.50 / 334.45 / 334.45 | 452.19 / 343.97 / 344.00 |
| energy-common/serial/matrix | 259.83 / 281.56 / 280.90 | 396.00 / 286.95 / 286.95 | 420.58 / 312.34 / 312.39 |
| energy-common/serial/batch | 257.73 / 252.04 / 252.20 | 397.81 / 176.11 / 176.11 | 420.58 / 312.34 / 312.38 |
| energy-common/parallel/read | 268.20 / 272.67 / 275.71 | 285.15 / 176.11 / 176.11 | 422.45 / 314.17 / 314.21 |
| energy-common/parallel/materialize | 268.08 / 309.09 / 313.79 | 285.15 / 397.81 / 397.81 | 422.41 / 409.21 / 409.23 |
| energy-common/parallel/filter-matrix | 278.18 / 330.90 / 295.19 | 25.33 / 25.33 / 18.65 | 422.41 / 433.38 / 314.17 |
| energy-common/parallel/gather-matrix | 283.30 / 333.09 / 287.52 | 23.51 / 23.51 / 17.06 | 422.37 / 431.34 / 314.17 |
| energy-common/parallel/sort-matrix | 483.38 / 537.36 / 459.98 | 396.00 / 396.00 / 318.22 | 738.37 / 852.73 / 520.05 |
| energy-common/parallel/join-matrix | 741.95 / 1823.49 / 1854.66 | 427.67 / 427.67 / 427.67 | 755.04 / 678.59 / 678.55 |
| energy-common/parallel/row-scan | 400.17 / 406.49 / 407.81 | 285.15 / 176.11 / 176.11 | 422.38 / 314.19 / 314.20 |
| energy-common/parallel/lag-matrix | 419.74 / 431.65 / 447.60 | 443.50 / 334.45 / 334.45 | 453.98 / 345.79 / 345.85 |
| energy-common/parallel/matrix | 280.40 / 293.70 / 295.95 | 396.00 / 286.95 / 286.95 | 422.38 / 314.18 / 314.20 |
| energy-common/parallel/batch | 280.36 / 272.76 / 273.53 | 397.81 / 176.11 / 176.11 | 422.39 / 314.15 / 314.22 |
| Aotizhongxin-default/serial/read | 8.00 / 8.15 / 8.16 | 9.95 / 7.09 / 7.09 | 22.84 / 21.70 / 21.72 |
| Aotizhongxin-default/serial/materialize | 7.94 / 8.93 / 9.01 | 9.95 / 13.10 / 13.10 | 22.86 / 21.70 / 21.72 |
| Aotizhongxin-default/serial/filter-matrix | 11.76 / 13.42 / 10.89 | 13.52 / 13.52 / 10.82 | 31.88 / 33.11 / 25.88 |
| Aotizhongxin-default/serial/gather-matrix | 8.61 / 9.71 / 8.78 | 1.22 / 1.22 / 0.92 | 22.86 / 21.88 / 21.73 |
| Aotizhongxin-default/serial/sort-matrix | 13.11 / 14.85 / 11.88 | 14.24 / 14.24 / 11.37 | 33.02 / 34.67 / 26.52 |
| Aotizhongxin-default/serial/join-matrix | 22.39 / 53.00 / 53.36 | 14.78 / 14.78 / 14.78 | 33.30 / 31.05 / 31.09 |
| Aotizhongxin-default/serial/row-scan | 10.38 / 10.45 / 10.40 | 9.95 / 7.09 / 7.09 | 22.86 / 21.70 / 21.72 |
| Aotizhongxin-default/serial/lag-matrix | 11.10 / 11.26 / 11.39 | 15.06 / 12.20 / 12.20 | 24.77 / 23.62 / 23.62 |
| Aotizhongxin-default/serial/matrix | 8.65 / 8.94 / 8.95 | 14.24 / 11.37 / 11.37 | 24.47 / 23.30 / 23.31 |
| Aotizhongxin-default/serial/batch | 8.65 / 8.38 / 8.37 | 14.51 / 8.49 / 8.49 | 22.84 / 21.72 / 21.72 |
| Aotizhongxin-default/parallel/read | 11.11 / 11.15 / 11.29 | 9.95 / 7.09 / 7.09 | 23.16 / 22.19 / 22.03 |
| Aotizhongxin-default/parallel/materialize | 11.25 / 11.91 / 11.97 | 9.95 / 13.10 / 13.10 | 23.54 / 22.21 / 22.22 |
| Aotizhongxin-default/parallel/filter-matrix | 15.44 / 16.53 / 14.40 | 13.52 / 13.52 / 10.82 | 31.98 / 34.23 / 26.62 |
| Aotizhongxin-default/parallel/gather-matrix | 11.81 / 12.89 / 11.84 | 1.22 / 1.22 / 0.92 | 23.15 / 23.38 / 22.04 |
| Aotizhongxin-default/parallel/sort-matrix | 16.71 / 17.73 / 15.21 | 14.24 / 14.24 / 11.37 | 33.16 / 35.92 / 27.36 |
| Aotizhongxin-default/parallel/join-matrix | 25.30 / 56.37 / 56.77 | 14.78 / 14.78 / 14.78 | 33.98 / 31.55 / 31.38 |
| Aotizhongxin-default/parallel/row-scan | 13.14 / 13.11 / 13.24 | 9.95 / 7.09 / 7.09 | 23.52 / 22.20 / 22.02 |
| Aotizhongxin-default/parallel/lag-matrix | 14.04 / 14.09 / 14.12 | 15.06 / 12.20 / 12.20 | 25.27 / 23.91 / 24.40 |
| Aotizhongxin-default/parallel/matrix | 11.52 / 11.96 / 12.00 | 14.24 / 11.37 / 11.37 | 24.95 / 23.62 / 23.82 |
| Aotizhongxin-default/parallel/batch | 11.51 / 11.02 / 11.45 | 14.51 / 8.49 / 8.49 | 23.12 / 22.19 / 22.37 |

Identical-binary flags: []. Flagged cases remain unqualified. These are CPU and allocation measurements, not energy, FLOP or cache measurements.
