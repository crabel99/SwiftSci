# Shared prepared-key sort resource results

Eight fresh processes per label. Total CPU includes CSV construction, the requested operation, consumer preparation and release. Operation CPU excludes CSV construction and release. Output validation is outside timing. Original is checkpoint 91c0ff09b7; prior is e1f5f8c305. Every client honors the declared storage choice.

| Case | Total CPU original / prior / current, ms | Operation CPU original / prior / current, ms | Held heap original / prior / current, MiB | Peak RSS original / prior / current, MiB |
|---|---:|---:|---:|---:|
| energy-common/serial/optional/sort-indices | 279.40 / 279.90 / 281.79 | 47.29 / 47.53 / 46.21 | 301.00 / 301.00 / 301.00 | 420.58 / 420.59 / 420.56 |
| energy-common/serial/optional/sort-matrix | 430.96 / 431.20 / 430.55 | 197.00 / 197.15 / 192.99 | 396.00 / 396.00 / 396.00 | 737.47 / 737.48 / 737.48 |
| energy-common/serial/optional/sort-materialize | 409.71 / 409.74 / 412.35 | 179.61 / 179.34 / 177.49 | 285.16 / 285.16 / 285.16 | 626.59 / 626.64 / 626.62 |
| energy-common/serial/compact/sort-indices | 297.52 / 288.29 / 293.36 | 52.17 / 46.70 / 46.29 | 191.95 / 191.95 / 191.95 | 312.38 / 312.41 / 312.37 |
| energy-common/serial/compact/sort-matrix | 419.13 / 411.18 / 414.16 | 173.19 / 167.56 / 167.88 | 302.39 / 286.95 / 286.95 | 503.34 / 503.38 / 503.18 |
| energy-common/serial/compact/sort-materialize | 425.35 / 417.39 / 422.60 | 182.53 / 176.38 / 175.48 | 413.25 / 397.81 / 397.81 | 550.79 / 550.97 / 550.92 |
| energy-common/parallel/optional/sort-indices | 308.16 / 309.47 / 311.99 | 47.57 / 47.81 / 46.13 | 301.00 / 301.00 / 301.00 | 422.38 / 422.44 / 422.34 |
| energy-common/parallel/optional/sort-matrix | 457.62 / 457.15 / 458.12 | 195.44 / 196.24 / 194.58 | 396.00 / 396.00 / 396.00 | 739.19 / 739.22 / 739.16 |
| energy-common/parallel/optional/sort-materialize | 440.13 / 443.49 / 442.45 | 180.15 / 181.02 / 179.65 | 285.16 / 285.16 / 285.16 | 628.31 / 628.31 / 628.33 |
| energy-common/parallel/compact/sort-indices | 318.69 / 328.31 / 323.90 | 52.44 / 47.46 / 46.56 | 191.95 / 191.95 / 191.95 | 314.21 / 313.55 / 313.04 |
| energy-common/parallel/compact/sort-matrix | 438.49 / 432.58 / 434.14 | 173.47 / 165.93 / 167.05 | 302.39 / 286.95 / 286.95 | 504.30 / 504.30 / 504.25 |
| energy-common/parallel/compact/sort-materialize | 449.64 / 444.20 / 445.17 | 182.40 / 176.85 / 176.56 | 413.25 / 397.81 / 397.81 | 551.84 / 551.88 / 551.81 |
| Aotizhongxin-default/serial/optional/sort-indices | 8.69 / 8.68 / 8.66 | 0.71 / 0.70 / 0.70 | 10.24 / 10.24 / 10.24 | 22.90 / 22.91 / 22.84 |
| Aotizhongxin-default/serial/optional/sort-matrix | 13.00 / 12.96 / 12.91 | 5.11 / 5.04 / 5.00 | 14.24 / 14.24 / 14.24 | 33.12 / 33.11 / 33.05 |
| Aotizhongxin-default/serial/optional/sort-materialize | 12.28 / 12.32 / 12.46 | 4.36 / 4.38 / 4.41 | 9.96 / 9.96 / 9.96 | 28.81 / 28.80 / 28.73 |
| Aotizhongxin-default/serial/compact/sort-indices | 8.90 / 8.94 / 8.82 | 0.76 / 0.71 / 0.70 | 7.37 / 7.37 / 7.37 | 21.75 / 21.75 / 21.71 |
| Aotizhongxin-default/serial/compact/sort-matrix | 11.95 / 11.95 / 12.04 | 3.71 / 3.66 / 3.72 | 11.37 / 11.37 / 11.37 | 26.58 / 26.53 / 26.50 |
| Aotizhongxin-default/serial/compact/sort-materialize | 12.43 / 12.03 / 12.24 | 3.97 / 3.71 / 3.77 | 13.10 / 13.10 / 13.10 | 24.72 / 24.40 / 24.07 |
| Aotizhongxin-default/parallel/optional/sort-indices | 11.83 / 11.85 / 11.80 | 0.70 / 0.67 / 0.65 | 10.24 / 10.24 / 10.24 | 23.18 / 23.39 / 23.11 |
| Aotizhongxin-default/parallel/optional/sort-matrix | 16.46 / 16.65 / 16.72 | 5.53 / 5.62 / 5.57 | 14.24 / 14.24 / 14.24 | 33.20 / 33.21 / 33.18 |
| Aotizhongxin-default/parallel/optional/sort-materialize | 15.97 / 16.08 / 16.22 | 4.85 / 4.89 / 5.13 | 9.96 / 9.96 / 9.96 | 28.95 / 28.89 / 28.78 |
| Aotizhongxin-default/parallel/compact/sort-indices | 11.97 / 11.80 / 11.81 | 0.75 / 0.66 / 0.69 | 7.37 / 7.37 / 7.37 | 22.05 / 22.25 / 22.02 |
| Aotizhongxin-default/parallel/compact/sort-matrix | 14.98 / 15.29 / 15.15 | 3.90 / 4.26 / 3.97 | 11.37 / 11.37 / 11.37 | 27.37 / 27.64 / 27.30 |
| Aotizhongxin-default/parallel/compact/sort-materialize | 15.17 / 15.15 / 14.96 | 4.09 / 3.99 / 4.00 | 13.10 / 13.10 / 13.10 | 24.99 / 25.11 / 28.59 |

Identical-binary flags: []. Affected comparisons remain unqualified. CPU is user plus system process time. These measurements do not establish energy, FLOP or cache effects.
