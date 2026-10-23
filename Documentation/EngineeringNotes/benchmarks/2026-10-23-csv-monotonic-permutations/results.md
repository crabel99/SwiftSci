# Stable monotonic permutation resource results

Eight fresh processes per label. Total CPU includes CSV construction, the requested operation, consumer preparation and release. Operation CPU excludes CSV construction and release. Output validation is outside timing. Original is checkpoint 91c0ff09b7; prior is 42f0633fd5. Every client honors the declared storage choice.

| Case | Total CPU original / prior / current, ms | Operation CPU original / prior / current, ms | Held heap original / prior / current, MiB | Peak RSS original / prior / current, MiB |
|---|---:|---:|---:|---:|
| energy-common/serial/optional/sort-indices | 278.53 / 281.38 / 277.36 | 46.54 / 46.47 / 46.89 | 301.00 / 301.00 / 301.00 | 420.58 / 420.70 / 420.61 |
| energy-common/serial/optional/sort-matrix | 429.26 / 429.72 / 427.17 | 194.68 / 194.21 / 195.94 | 396.00 / 396.00 / 396.00 | 737.45 / 737.59 / 737.49 |
| energy-common/serial/optional/sort-materialize | 413.19 / 414.17 / 411.43 | 179.95 / 179.33 / 180.30 | 285.16 / 285.16 / 285.16 | 626.61 / 626.73 / 626.63 |
| energy-common/serial/compact/sort-indices | 301.18 / 292.84 / 290.41 | 52.13 / 47.02 / 47.46 | 191.95 / 191.95 / 191.95 | 312.38 / 312.48 / 312.42 |
| energy-common/serial/compact/sort-matrix | 414.42 / 412.56 / 406.92 | 172.56 / 166.74 / 166.97 | 302.39 / 286.95 / 286.95 | 503.11 / 503.34 / 503.16 |
| energy-common/serial/compact/sort-materialize | 425.29 / 423.72 / 420.40 | 182.05 / 177.35 / 178.72 | 413.25 / 397.81 / 397.81 | 550.68 / 550.91 / 550.97 |
| energy-common/parallel/optional/sort-indices | 308.33 / 315.39 / 310.44 | 48.38 / 47.75 / 48.00 | 301.00 / 301.00 / 301.00 | 422.37 / 422.51 / 422.38 |
| energy-common/parallel/optional/sort-matrix | 458.08 / 464.24 / 460.11 | 197.23 / 195.86 / 196.02 | 396.00 / 396.00 / 396.00 | 739.16 / 739.30 / 739.19 |
| energy-common/parallel/optional/sort-materialize | 440.85 / 447.33 / 441.93 | 180.56 / 180.76 / 180.02 | 285.16 / 285.16 / 285.16 | 628.29 / 628.44 / 628.27 |
| energy-common/parallel/compact/sort-indices | 316.64 / 320.67 / 316.60 | 52.83 / 47.45 / 47.85 | 191.95 / 191.95 / 191.95 | 314.16 / 314.29 / 314.22 |
| energy-common/parallel/compact/sort-matrix | 440.47 / 439.74 / 436.75 | 172.96 / 168.30 / 167.64 | 302.39 / 286.95 / 286.95 | 504.30 / 504.38 / 504.35 |
| energy-common/parallel/compact/sort-materialize | 453.11 / 452.19 / 446.62 | 185.20 / 178.05 / 178.47 | 413.25 / 397.81 / 397.81 | 551.85 / 551.98 / 551.93 |
| Aotizhongxin-default/serial/optional/sort-indices | 8.68 / 8.71 / 8.68 | 0.72 / 0.71 / 0.72 | 10.24 / 10.24 / 10.24 | 22.89 / 22.95 / 22.89 |
| Aotizhongxin-default/serial/optional/sort-matrix | 13.20 / 13.11 / 13.15 | 5.21 / 5.11 / 5.14 | 14.24 / 14.24 / 14.24 | 33.13 / 33.14 / 33.11 |
| Aotizhongxin-default/serial/optional/sort-materialize | 12.61 / 12.58 / 12.52 | 4.60 / 4.50 / 4.49 | 9.96 / 9.96 / 9.96 | 28.84 / 28.86 / 28.80 |
| Aotizhongxin-default/serial/compact/sort-indices | 8.95 / 8.89 / 8.91 | 0.79 / 0.70 / 0.71 | 7.37 / 7.37 / 7.37 | 21.75 / 21.79 / 21.77 |
| Aotizhongxin-default/serial/compact/sort-matrix | 11.86 / 11.80 / 11.90 | 3.67 / 3.60 / 3.57 | 11.37 / 11.37 / 11.37 | 26.55 / 26.58 / 26.55 |
| Aotizhongxin-default/serial/compact/sort-materialize | 11.90 / 11.87 / 11.91 | 3.67 / 3.60 / 3.63 | 13.10 / 13.10 / 13.10 | 24.43 / 24.45 / 24.44 |
| Aotizhongxin-default/parallel/optional/sort-indices | 11.71 / 11.86 / 11.79 | 0.66 / 0.66 / 0.66 | 10.24 / 10.24 / 10.24 | 23.37 / 23.41 / 23.18 |
| Aotizhongxin-default/parallel/optional/sort-matrix | 16.82 / 16.61 / 16.97 | 5.58 / 5.42 / 5.93 | 14.24 / 14.24 / 14.24 | 33.22 / 33.33 / 33.21 |
| Aotizhongxin-default/parallel/optional/sort-materialize | 16.09 / 16.28 / 15.93 | 4.79 / 5.07 / 4.82 | 9.96 / 9.96 / 9.96 | 28.98 / 28.92 / 28.87 |
| Aotizhongxin-default/parallel/compact/sort-indices | 12.00 / 11.98 / 11.91 | 0.74 / 0.66 / 0.66 | 7.37 / 7.37 / 7.37 | 22.05 / 22.08 / 22.03 |
| Aotizhongxin-default/parallel/compact/sort-matrix | 14.93 / 15.02 / 15.00 | 3.65 / 3.61 / 3.60 | 11.37 / 11.37 / 11.37 | 26.62 / 26.66 / 26.62 |
| Aotizhongxin-default/parallel/compact/sort-materialize | 14.96 / 15.03 / 14.99 | 3.67 / 3.60 / 3.60 | 13.10 / 13.10 / 13.10 | 24.52 / 24.55 / 24.53 |

Identical-binary flags: []. Affected comparisons remain unqualified. CPU is user plus system process time. These measurements do not establish energy, FLOP or cache effects.
