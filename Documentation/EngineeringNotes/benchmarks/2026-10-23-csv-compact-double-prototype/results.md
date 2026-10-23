# Compact Double CSV resource trial

Medians of 12 fresh processes per label. CPU is user plus system time. Held heap is live malloc allocations, not physical footprint. Peak RSS includes input file mappings. All final frames, matrices and exported arrays match the baseline fingerprints.

| Input / policy / workflow | CPU baseline → prototype, ms | CPU change | Held heap baseline → prototype, MiB | Peak RSS baseline → prototype, MiB |
|---|---:|---:|---:|---:|
| energy-common/serial/read | 248.25 → 254.66 | +2.6% | 285.15 → 176.11 | 421.92 → 313.86 |
| energy-common/serial/materialize | 246.51 → 1377.30 | +458.7% | 285.15 → 397.81 | 421.92 → 408.89 |
| energy-common/serial/filter-matrix | 262.81 → 313.74 | +19.4% | 25.33 → 25.33 | 421.92 → 431.77 |
| energy-common/serial/gather-matrix | 263.71 → 311.34 | +18.1% | 23.51 → 23.51 | 421.21 → 431.12 |
| energy-common/serial/sort-matrix | 465.24 → 520.00 | +11.8% | 396.00 → 396.00 | 738.79 → 852.09 |
| energy-common/serial/join-matrix | 734.35 → 1868.27 | +154.4% | 427.67 → 427.67 | 753.14 → 676.79 |
| energy-common/serial/row-scan | 386.02 → 388.81 | +0.7% | 285.15 → 176.11 | 421.57 → 312.44 |
| energy-common/serial/lag-matrix | 404.17 → 438.29 | +8.4% | 443.50 → 334.45 | 453.55 → 565.84 |
| energy-common/parallel/read | 264.79 → 267.43 | +1.0% | 285.15 → 176.11 | 422.38 → 313.48 |
| energy-common/parallel/materialize | 265.52 → 1401.81 | +428.0% | 285.15 → 397.81 | 422.38 → 408.48 |
| energy-common/parallel/filter-matrix | 278.26 → 328.47 | +18.0% | 25.33 → 25.33 | 422.39 → 431.34 |
| energy-common/parallel/gather-matrix | 284.39 → 331.86 | +16.7% | 23.51 → 23.51 | 422.38 → 430.66 |
| energy-common/parallel/sort-matrix | 474.92 → 527.37 | +11.0% | 396.00 → 396.00 | 739.09 → 852.13 |
| energy-common/parallel/join-matrix | 761.15 → 1881.81 | +147.2% | 427.67 → 427.67 | 755.03 → 678.64 |
| energy-common/parallel/row-scan | 410.04 → 412.31 | +0.6% | 285.15 → 176.11 | 422.38 → 314.34 |
| energy-common/parallel/lag-matrix | 432.24 → 467.86 | +8.2% | 443.50 → 334.45 | 454.00 → 566.95 |
| Aotizhongxin-default/serial/read | 8.48 → 8.67 | +2.3% | 9.95 → 7.09 | 22.80 → 21.77 |
| Aotizhongxin-default/serial/materialize | 8.46 → 40.11 | +373.9% | 9.95 → 13.10 | 22.80 → 21.77 |
| Aotizhongxin-default/serial/filter-matrix | 12.40 → 13.79 | +11.2% | 13.52 → 13.52 | 31.77 → 32.62 |
| Aotizhongxin-default/serial/gather-matrix | 9.08 → 10.39 | +14.4% | 1.22 → 1.22 | 22.80 → 21.91 |
| Aotizhongxin-default/serial/sort-matrix | 14.00 → 15.32 | +9.4% | 14.24 → 14.24 | 32.97 → 34.16 |
| Aotizhongxin-default/serial/join-matrix | 23.78 → 55.75 | +134.4% | 14.78 → 14.78 | 33.19 → 31.12 |
| Aotizhongxin-default/serial/row-scan | 10.68 → 10.73 | +0.5% | 9.95 → 7.09 | 22.80 → 21.78 |
| Aotizhongxin-default/serial/lag-matrix | 11.73 → 12.52 | +6.8% | 15.06 → 12.20 | 24.70 → 26.41 |
| Aotizhongxin-default/parallel/read | 11.86 → 11.86 | +0.0% | 9.95 → 7.09 | 23.05 → 22.06 |
| Aotizhongxin-default/parallel/materialize | 11.68 → 43.15 | +269.4% | 9.95 → 13.10 | 23.07 → 22.05 |
| Aotizhongxin-default/parallel/filter-matrix | 16.79 → 17.75 | +5.7% | 13.52 → 13.52 | 31.85 → 34.41 |
| Aotizhongxin-default/parallel/gather-matrix | 12.61 → 13.78 | +9.2% | 1.22 → 1.22 | 23.05 → 23.35 |
| Aotizhongxin-default/parallel/sort-matrix | 18.04 → 19.42 | +7.7% | 14.24 → 14.24 | 33.03 → 35.95 |
| Aotizhongxin-default/parallel/join-matrix | 27.11 → 58.79 | +116.9% | 14.78 → 14.78 | 33.47 → 31.41 |
| Aotizhongxin-default/parallel/row-scan | 14.21 → 14.13 | -0.6% | 9.95 → 7.09 | 23.07 → 22.05 |
| Aotizhongxin-default/parallel/lag-matrix | 15.20 → 15.98 | +5.2% | 15.06 → 12.20 | 24.95 → 26.70 |

Identical-binary quality flags: []. Differences in flagged cases are not qualified.
