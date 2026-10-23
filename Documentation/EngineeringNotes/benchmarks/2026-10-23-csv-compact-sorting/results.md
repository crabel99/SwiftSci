# Compact Double sorting resource results

Eight fresh processes per label. Total CPU includes CSV construction, the requested operation, consumer preparation and release. Operation CPU excludes CSV construction and release. Output validation is outside timing. Original always has optional storage. Prior, current and twin honor the declared storage choice.

| Case | Total CPU original / prior / current, ms | Operation CPU original / prior / current, ms | Held heap original / prior / current, MiB | Peak RSS original / prior / current, MiB |
|---|---:|---:|---:|---:|
| energy-common/serial/optional/sort-indices | 273.69 / 284.09 / 274.98 | 45.96 / 46.09 / 45.97 | 301.00 / 301.00 / 301.00 | 420.61 / 420.69 / 420.61 |
| energy-common/serial/optional/sort-matrix | 425.79 / 431.28 / 424.68 | 193.76 / 193.39 / 193.26 | 396.00 / 396.00 / 396.00 | 737.51 / 737.52 / 737.53 |
| energy-common/serial/optional/sort-materialize | 408.53 / 418.01 / 409.99 | 177.65 / 179.23 / 179.47 | 285.15 / 285.16 / 285.16 | 626.66 / 626.67 / 626.66 |
| energy-common/serial/compact/sort-indices | 277.96 / 298.91 / 288.65 | 46.40 / 51.32 / 51.45 | 301.00 / 191.95 / 191.95 | 420.61 / 312.48 / 312.41 |
| energy-common/serial/compact/sort-matrix | 423.82 / 419.65 / 411.28 | 192.62 / 169.79 / 169.60 | 396.00 / 318.22 / 302.39 | 737.48 / 519.10 / 503.41 |
| energy-common/serial/compact/sort-materialize | 416.38 / 445.44 / 435.48 | 180.46 / 189.07 / 184.83 | 285.15 / 429.08 / 413.25 | 626.66 / 566.80 / 551.02 |
| energy-common/parallel/optional/sort-indices | 310.04 / 315.18 / 309.57 | 47.93 / 48.09 / 47.94 | 301.00 / 301.00 / 301.00 | 422.42 / 422.50 / 422.45 |
| energy-common/parallel/optional/sort-matrix | 461.07 / 461.28 / 458.04 | 197.32 / 196.80 / 196.49 | 396.00 / 396.00 / 396.00 | 739.19 / 739.25 / 739.24 |
| energy-common/parallel/optional/sort-materialize | 444.93 / 446.03 / 443.34 | 180.19 / 179.90 / 181.41 | 285.15 / 285.16 / 285.16 | 628.31 / 628.39 / 628.39 |
| energy-common/parallel/compact/sort-indices | 310.46 / 326.31 / 321.98 | 47.99 / 52.78 / 52.91 | 301.00 / 191.95 / 191.95 | 422.43 / 314.30 / 314.23 |
| energy-common/parallel/compact/sort-matrix | 459.20 / 444.76 / 441.14 | 196.34 / 170.71 / 173.59 | 396.00 / 318.22 / 302.39 | 739.16 / 520.17 / 504.33 |
| energy-common/parallel/compact/sort-materialize | 455.56 / 463.32 / 471.46 | 190.71 / 187.63 / 193.26 | 285.15 / 429.08 / 413.25 | 628.38 / 567.77 / 551.94 |
| Aotizhongxin-default/serial/optional/sort-indices | 8.75 / 8.74 / 8.81 | 0.72 / 0.71 / 0.71 | 10.24 / 10.24 / 10.24 | 22.91 / 22.94 / 22.90 |
| Aotizhongxin-default/serial/optional/sort-matrix | 13.01 / 12.91 / 13.09 | 4.96 / 4.87 / 5.14 | 14.24 / 14.24 / 14.24 | 33.07 / 33.10 / 33.14 |
| Aotizhongxin-default/serial/optional/sort-materialize | 12.59 / 12.46 / 12.48 | 4.55 / 4.27 / 4.39 | 9.95 / 9.96 / 9.96 | 28.78 / 28.80 / 28.86 |
| Aotizhongxin-default/serial/compact/sort-indices | 8.83 / 9.16 / 9.16 | 0.70 / 0.77 / 0.80 | 10.24 / 7.37 / 7.37 | 22.91 / 21.80 / 21.73 |
| Aotizhongxin-default/serial/compact/sort-matrix | 13.04 / 12.11 / 11.94 | 5.07 / 3.73 / 3.65 | 14.24 / 11.37 / 11.37 | 33.08 / 26.58 / 26.57 |
| Aotizhongxin-default/serial/compact/sort-materialize | 12.34 / 12.03 / 11.96 | 4.26 / 3.73 / 3.66 | 9.95 / 13.10 / 13.10 | 28.75 / 24.47 / 23.91 |
| Aotizhongxin-default/parallel/optional/sort-indices | 12.08 / 11.98 / 11.90 | 0.71 / 0.68 / 0.68 | 10.24 / 10.24 / 10.24 | 23.15 / 23.44 / 23.19 |
| Aotizhongxin-default/parallel/optional/sort-matrix | 17.07 / 17.22 / 17.15 | 5.88 / 5.72 / 5.94 | 14.24 / 14.24 / 14.24 | 33.18 / 33.28 / 33.26 |
| Aotizhongxin-default/parallel/optional/sort-materialize | 16.28 / 16.32 / 16.33 | 5.13 / 5.23 / 5.10 | 9.95 / 9.96 / 9.96 | 28.88 / 28.97 / 28.95 |
| Aotizhongxin-default/parallel/compact/sort-indices | 11.90 / 11.97 / 11.93 | 0.67 / 0.74 / 0.75 | 10.24 / 7.37 / 7.37 | 23.18 / 22.11 / 22.05 |
| Aotizhongxin-default/parallel/compact/sort-matrix | 16.65 / 15.52 / 15.74 | 5.37 / 4.21 / 4.28 | 14.24 / 11.37 / 11.37 | 33.19 / 27.27 / 27.01 |
| Aotizhongxin-default/parallel/compact/sort-materialize | 16.28 / 15.40 / 15.08 | 4.94 / 3.96 / 4.03 | 9.95 / 13.10 / 13.10 | 28.88 / 25.72 / 25.40 |

Identical-binary flags: []. Affected comparisons remain unqualified. CPU is user plus system process time. These measurements do not establish energy, FLOP or cache effects.
