# Deferred sort-cache allocation resource results

Eight fresh processes per label. Total CPU includes CSV construction, the requested operation, consumer preparation and release. Operation CPU excludes CSV construction and release. Output validation is outside timing. Original always has optional storage. Prior, current and twin honor the declared storage choice.

| Case | Total CPU original / prior / current, ms | Operation CPU original / prior / current, ms | Held heap original / prior / current, MiB | Peak RSS original / prior / current, MiB |
|---|---:|---:|---:|---:|
| energy-common/serial/optional/sort-indices | 282.50 / 287.76 / 288.26 | 49.18 / 49.08 / 48.54 | 301.00 / 301.00 / 301.00 | 420.61 / 421.33 / 420.67 |
| energy-common/serial/optional/sort-matrix | 431.28 / 433.24 / 440.00 | 194.10 / 200.98 / 200.40 | 396.00 / 396.00 / 396.00 | 737.52 / 737.52 / 737.60 |
| energy-common/serial/optional/sort-materialize | 417.64 / 420.70 / 417.01 | 182.11 / 183.71 / 179.81 | 285.15 / 285.16 / 285.16 | 626.65 / 626.66 / 626.73 |
| energy-common/serial/compact/sort-indices | 282.44 / 299.12 / 300.92 | 48.18 / 53.98 / 49.04 | 301.00 / 191.95 / 191.95 | 420.61 / 312.42 / 312.47 |
| energy-common/serial/compact/sort-matrix | 454.04 / 438.84 / 441.64 | 206.76 / 187.66 / 180.20 | 396.00 / 302.39 / 286.95 | 737.52 / 503.98 / 503.56 |
| energy-common/serial/compact/sort-materialize | 436.63 / 453.12 / 448.47 | 190.55 / 197.65 / 190.74 | 285.15 / 413.25 / 397.81 | 626.65 / 551.51 / 551.28 |
| energy-common/parallel/optional/sort-indices | 313.62 / 311.45 / 322.73 | 49.15 / 49.13 / 49.96 | 301.00 / 301.00 / 301.00 | 422.41 / 422.42 / 422.51 |
| energy-common/parallel/optional/sort-matrix | 470.27 / 474.62 / 487.25 | 203.51 / 201.29 / 202.26 | 396.00 / 396.00 / 396.00 | 739.23 / 739.16 / 738.52 |
| energy-common/parallel/optional/sort-materialize | 456.93 / 451.90 / 460.68 | 187.11 / 186.50 / 182.69 | 285.15 / 285.16 / 285.16 | 628.32 / 628.31 / 628.41 |
| energy-common/parallel/compact/sort-indices | 322.97 / 339.95 / 330.59 | 52.32 / 57.87 / 51.59 | 301.00 / 191.95 / 191.95 | 421.70 / 313.07 / 314.29 |
| energy-common/parallel/compact/sort-matrix | 465.34 / 448.44 / 453.51 | 200.97 / 175.96 / 172.46 | 396.00 / 302.39 / 286.95 | 739.16 / 504.29 / 504.33 |
| energy-common/parallel/compact/sort-materialize | 445.28 / 454.37 / 454.52 | 182.45 / 184.52 / 179.93 | 285.15 / 413.25 / 397.81 | 628.31 / 551.88 / 551.94 |
| Aotizhongxin-default/serial/optional/sort-indices | 8.73 / 8.75 / 8.88 | 0.71 / 0.71 / 0.71 | 10.24 / 10.24 / 10.24 | 22.91 / 22.92 / 22.92 |
| Aotizhongxin-default/serial/optional/sort-matrix | 12.87 / 13.22 / 12.89 | 4.73 / 5.21 / 4.83 | 14.24 / 14.24 / 14.24 | 33.05 / 33.16 / 33.10 |
| Aotizhongxin-default/serial/optional/sort-materialize | 12.85 / 12.62 / 12.74 | 4.52 / 4.41 / 4.54 | 9.95 / 9.96 / 9.96 | 28.77 / 28.85 / 28.81 |
| Aotizhongxin-default/serial/compact/sort-indices | 8.99 / 9.32 / 9.15 | 0.73 / 0.80 / 0.73 | 10.24 / 7.37 / 7.37 | 22.88 / 21.77 / 21.77 |
| Aotizhongxin-default/serial/compact/sort-matrix | 13.33 / 12.11 / 11.96 | 5.13 / 3.69 / 3.63 | 14.24 / 11.37 / 11.37 | 33.06 / 26.58 / 26.58 |
| Aotizhongxin-default/serial/compact/sort-materialize | 12.83 / 12.05 / 12.00 | 4.50 / 3.72 / 3.69 | 9.95 / 13.10 / 13.10 | 28.77 / 24.47 / 24.45 |
| Aotizhongxin-default/parallel/optional/sort-indices | 11.95 / 11.85 / 11.90 | 0.68 / 0.67 / 0.68 | 10.24 / 10.24 / 10.24 | 23.55 / 23.20 / 23.25 |
| Aotizhongxin-default/parallel/optional/sort-matrix | 17.57 / 17.26 / 17.32 | 6.14 / 5.84 / 5.79 | 14.24 / 14.24 / 14.24 | 33.16 / 33.30 / 33.17 |
| Aotizhongxin-default/parallel/optional/sort-materialize | 15.93 / 15.59 / 16.32 | 4.84 / 4.35 / 5.06 | 9.95 / 9.96 / 9.96 | 28.94 / 28.88 / 28.94 |
| Aotizhongxin-default/parallel/compact/sort-indices | 11.94 / 12.24 / 12.10 | 0.68 / 0.76 / 0.68 | 10.24 / 7.37 / 7.37 | 23.38 / 22.07 / 22.09 |
| Aotizhongxin-default/parallel/compact/sort-matrix | 17.27 / 15.46 / 15.20 | 5.90 / 4.22 / 4.01 | 14.24 / 11.37 / 11.37 | 33.17 / 27.41 / 27.12 |
| Aotizhongxin-default/parallel/compact/sort-materialize | 15.90 / 15.59 / 15.04 | 4.83 / 4.05 / 3.75 | 9.95 / 13.10 / 13.10 | 28.88 / 25.71 / 25.57 |

Identical-binary flags: []. Affected comparisons remain unqualified. CPU is user plus system process time. These measurements do not establish energy, FLOP or cache effects.
