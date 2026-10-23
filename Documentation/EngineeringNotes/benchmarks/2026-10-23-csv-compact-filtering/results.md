# Compact predicate filtering resource results

Eight fresh processes per label. Total CPU includes CSV construction, the requested operation, consumer preparation and release. Operation CPU excludes CSV construction and release. Output validation is outside timing. Original always has optional storage. Prior, current and twin honor the declared storage choice.

| Case | Total CPU original / prior / current, ms | Operation CPU original / prior / current, ms | Held heap original / prior / current, MiB | Peak RSS original / prior / current, MiB |
|---|---:|---:|---:|---:|
| energy-common/serial/optional/filter-indices | 249.94 / 252.03 / 245.51 | 1.06 / 1.03 / 1.03 | 293.08 / 293.08 / 293.08 | 422.05 / 420.61 / 420.62 |
| energy-common/serial/optional/filter-matrix | 262.52 / 263.16 / 260.71 | 26.93 / 27.30 / 26.66 | 25.33 / 25.33 / 25.33 | 422.05 / 422.00 / 422.05 |
| energy-common/serial/optional/filter-materialize | 259.43 / 262.35 / 265.45 | 26.23 / 25.77 / 26.43 | 17.41 / 17.41 / 17.41 | 421.34 / 422.00 / 420.64 |
| energy-common/serial/compact/filter-indices | 247.44 / 255.73 / 256.47 | 1.04 / 5.92 / 1.59 | 293.08 / 184.03 / 184.03 | 420.64 / 312.39 / 312.44 |
| energy-common/serial/compact/filter-matrix | 245.47 / 259.30 / 254.09 | 25.70 / 28.59 / 23.36 | 25.33 / 18.66 / 18.66 | 420.62 / 312.39 / 312.44 |
| energy-common/serial/compact/filter-materialize | 248.18 / 265.10 / 260.41 | 25.19 / 28.56 / 23.74 | 17.41 / 24.19 / 24.19 | 420.62 / 312.39 / 312.44 |
| energy-common/parallel/optional/filter-indices | 268.34 / 269.11 / 270.79 | 1.00 / 0.99 / 1.02 | 293.08 / 293.08 / 293.08 | 422.48 / 422.46 / 422.44 |
| energy-common/parallel/optional/filter-matrix | 273.70 / 276.47 / 277.04 | 25.26 / 25.67 / 25.41 | 25.33 / 25.33 / 25.33 | 422.45 / 422.43 / 422.45 |
| energy-common/parallel/optional/filter-materialize | 275.26 / 278.31 / 277.99 | 24.61 / 23.85 / 24.34 | 17.41 / 17.41 / 17.41 | 422.45 / 422.43 / 422.46 |
| energy-common/parallel/compact/filter-indices | 267.38 / 281.43 / 275.59 | 1.03 / 5.98 / 1.46 | 293.08 / 184.03 / 184.03 | 422.47 / 314.25 / 314.24 |
| energy-common/parallel/compact/filter-matrix | 276.61 / 291.16 / 286.90 | 25.12 / 28.14 / 23.27 | 25.33 / 18.66 / 18.66 | 422.45 / 314.22 / 314.25 |
| energy-common/parallel/compact/filter-materialize | 274.98 / 287.10 / 282.04 | 24.05 / 28.13 / 23.21 | 17.41 / 24.19 / 24.19 | 422.42 / 314.21 / 314.23 |
| Aotizhongxin-default/serial/optional/filter-indices | 8.17 / 8.26 / 8.28 | 0.08 / 0.08 / 0.08 | 10.24 / 10.24 / 10.24 | 22.91 / 22.88 / 22.89 |
| Aotizhongxin-default/serial/optional/filter-matrix | 12.65 / 12.81 / 12.43 | 4.09 / 4.17 / 3.97 | 13.52 / 13.52 / 13.52 | 31.88 / 31.88 / 31.88 |
| Aotizhongxin-default/serial/optional/filter-materialize | 12.14 / 12.47 / 12.22 | 3.46 / 3.74 / 3.48 | 9.39 / 9.39 / 9.39 | 27.72 / 27.77 / 27.76 |
| Aotizhongxin-default/serial/compact/filter-indices | 8.73 / 9.17 / 9.18 | 0.08 / 0.16 / 0.09 | 10.24 / 7.37 / 7.37 | 22.88 / 21.70 / 21.76 |
| Aotizhongxin-default/serial/compact/filter-matrix | 12.92 / 12.03 / 11.85 | 4.20 / 2.95 / 2.77 | 13.52 / 10.82 / 10.82 | 31.87 / 25.94 / 25.92 |
| Aotizhongxin-default/serial/compact/filter-materialize | 12.11 / 11.83 / 11.86 | 3.41 / 2.87 / 2.85 | 9.39 / 12.36 / 12.36 | 27.73 / 24.38 / 24.33 |
| Aotizhongxin-default/parallel/optional/filter-indices | 11.93 / 11.72 / 11.69 | 0.09 / 0.08 / 0.09 | 10.24 / 10.24 / 10.24 | 23.18 / 23.12 / 23.22 |
| Aotizhongxin-default/parallel/optional/filter-matrix | 16.18 / 16.03 / 16.27 | 4.56 / 4.45 / 4.53 | 13.52 / 13.52 / 13.52 | 31.98 / 32.07 / 32.06 |
| Aotizhongxin-default/parallel/optional/filter-materialize | 15.26 / 16.15 / 16.01 | 3.76 / 4.11 / 3.97 | 9.39 / 9.39 / 9.39 | 27.84 / 27.95 / 27.87 |
| Aotizhongxin-default/parallel/compact/filter-indices | 11.76 / 11.94 / 11.74 | 0.09 / 0.16 / 0.09 | 10.24 / 7.37 / 7.37 | 23.19 / 21.99 / 22.06 |
| Aotizhongxin-default/parallel/compact/filter-matrix | 16.68 / 15.21 / 14.99 | 4.83 / 3.32 / 3.21 | 13.52 / 10.82 / 10.82 | 31.96 / 26.18 / 26.31 |
| Aotizhongxin-default/parallel/compact/filter-materialize | 15.18 / 14.68 / 14.71 | 3.79 / 3.13 / 3.04 | 9.39 / 12.36 / 12.36 | 27.82 / 22.42 / 22.30 |

Identical-binary flags: []. Affected comparisons remain unqualified. CPU is user plus system process time. These measurements do not establish energy, FLOP or cache effects.
