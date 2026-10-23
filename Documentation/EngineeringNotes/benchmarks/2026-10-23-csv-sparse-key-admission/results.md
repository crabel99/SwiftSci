# Shared-key sparse admission resource results

Eight fresh processes per label. Total CPU includes CSV construction, the requested operation, consumer preparation and release. Operation CPU excludes CSV construction and release. Output validation is outside timing. Original is checkpoint 91c0ff09b7; prior is b982028c59. Every client honors the declared storage choice.

| Case | Total CPU original / prior / current, ms | Operation CPU original / prior / current, ms | Held heap original / prior / current, MiB | Peak RSS original / prior / current, MiB |
|---|---:|---:|---:|---:|
| energy-common/serial/optional/sort-indices | 304.24 / 309.05 / 308.95 | 54.95 / 53.39 / 53.56 | 301.00 / 301.00 / 301.00 | 420.59 / 421.31 / 420.62 |
| energy-common/serial/optional/sort-matrix | 438.91 / 436.28 / 452.31 | 201.43 / 197.00 / 202.33 | 396.00 / 396.00 / 396.00 | 737.45 / 737.50 / 737.49 |
| energy-common/serial/optional/sort-materialize | 432.48 / 436.67 / 439.90 | 187.27 / 186.12 / 188.22 | 285.16 / 285.16 / 285.16 | 626.59 / 626.64 / 626.66 |
| energy-common/serial/compact/sort-indices | 298.49 / 296.57 / 299.31 | 53.26 / 47.64 / 48.31 | 191.95 / 191.95 / 191.95 | 312.99 / 312.38 / 312.39 |
| energy-common/serial/compact/sort-matrix | 426.84 / 419.60 / 423.25 | 181.65 / 169.92 / 168.63 | 302.39 / 286.95 / 286.95 | 503.62 / 503.39 / 503.48 |
| energy-common/serial/compact/sort-materialize | 429.29 / 433.02 / 434.33 | 185.02 / 181.43 / 178.86 | 413.25 / 397.81 / 397.81 | 550.80 / 550.97 / 551.18 |
| energy-common/parallel/optional/sort-indices | 313.07 / 312.46 / 319.72 | 48.75 / 47.45 / 46.88 | 301.00 / 301.00 / 301.00 | 422.38 / 422.41 / 422.41 |
| energy-common/parallel/optional/sort-matrix | 462.97 / 462.37 / 468.80 | 199.03 / 196.79 / 196.89 | 396.00 / 396.00 / 396.00 | 739.16 / 739.20 / 739.20 |
| energy-common/parallel/optional/sort-materialize | 466.77 / 467.64 / 471.83 | 192.70 / 190.25 / 189.71 | 285.16 / 285.16 / 285.16 | 628.34 / 628.32 / 628.34 |
| energy-common/parallel/compact/sort-indices | 329.38 / 326.75 / 329.28 | 57.29 / 50.87 / 48.65 | 191.95 / 191.95 / 191.95 | 314.24 / 314.24 / 314.25 |
| energy-common/parallel/compact/sort-matrix | 442.31 / 441.29 / 449.21 | 174.40 / 169.63 / 169.51 | 302.39 / 286.95 / 286.95 | 504.27 / 504.33 / 504.31 |
| energy-common/parallel/compact/sort-materialize | 458.99 / 455.50 / 460.81 | 185.85 / 180.50 / 179.99 | 413.25 / 397.81 / 397.81 | 551.86 / 551.84 / 551.91 |
| Aotizhongxin-default/serial/optional/sort-indices | 8.87 / 8.80 / 8.84 | 0.72 / 0.71 / 0.70 | 10.24 / 10.24 / 10.24 | 22.90 / 22.88 / 22.86 |
| Aotizhongxin-default/serial/optional/sort-matrix | 13.06 / 13.19 / 13.19 | 5.02 / 5.14 / 5.00 | 14.24 / 14.24 / 14.24 | 33.10 / 33.05 / 33.03 |
| Aotizhongxin-default/serial/optional/sort-materialize | 12.62 / 12.81 / 12.74 | 4.52 / 4.63 / 4.58 | 9.96 / 9.96 / 9.96 | 28.82 / 28.77 / 28.73 |
| Aotizhongxin-default/serial/compact/sort-indices | 9.16 / 8.94 / 9.09 | 0.79 / 0.70 / 0.70 | 7.37 / 7.37 / 7.37 | 21.77 / 21.73 / 21.72 |
| Aotizhongxin-default/serial/compact/sort-matrix | 12.20 / 12.09 / 11.95 | 3.71 / 3.67 / 3.62 | 11.37 / 11.37 / 11.37 | 26.55 / 26.55 / 26.45 |
| Aotizhongxin-default/serial/compact/sort-materialize | 12.25 / 11.97 / 12.00 | 3.81 / 3.66 / 3.59 | 13.10 / 13.10 / 13.10 | 23.91 / 23.87 / 23.82 |
| Aotizhongxin-default/parallel/optional/sort-indices | 12.03 / 11.87 / 12.13 | 0.68 / 0.67 / 0.69 | 10.24 / 10.24 / 10.24 | 23.18 / 23.16 / 23.14 |
| Aotizhongxin-default/parallel/optional/sort-matrix | 17.06 / 16.82 / 16.72 | 5.87 / 5.61 / 5.67 | 14.24 / 14.24 / 14.24 | 33.21 / 33.21 / 33.16 |
| Aotizhongxin-default/parallel/optional/sort-materialize | 15.99 / 16.34 / 16.52 | 4.94 / 4.99 / 5.16 | 9.96 / 9.96 / 9.96 | 28.91 / 28.87 / 28.80 |
| Aotizhongxin-default/parallel/compact/sort-indices | 12.30 / 11.90 / 12.04 | 0.74 / 0.66 / 0.66 | 7.37 / 7.37 / 7.37 | 22.05 / 22.02 / 21.97 |
| Aotizhongxin-default/parallel/compact/sort-matrix | 15.20 / 15.08 / 15.00 | 4.15 / 3.94 / 3.99 | 11.37 / 11.37 / 11.37 | 26.97 / 26.90 / 26.98 |
| Aotizhongxin-default/parallel/compact/sort-materialize | 15.49 / 15.23 / 15.27 | 4.23 / 4.11 / 4.19 | 13.10 / 13.10 / 13.10 | 24.44 / 27.02 / 25.56 |

Identical-binary flags: []. Affected comparisons remain unqualified. CPU is user plus system process time. These measurements do not establish energy, FLOP or cache effects.
