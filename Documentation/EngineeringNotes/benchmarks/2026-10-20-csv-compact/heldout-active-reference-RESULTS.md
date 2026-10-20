# Single-pass CSV block trial

The index construction and field lookups are included in CPU and elapsed time. Values include result release. CPU percentages use median paired ratios, while displayed times are medians of worker medians. Memory workers are separate and capture peak RSS before validation.

| Input | CPU ms before → trial | Paired CPU change and ratio range | Elapsed ms before → trial | Peak RSS MiB before → trial | Held heap MiB before → trial |
| --- | ---: | ---: | ---: | ---: | ---: |
| csv, 1,000 × 4 | 0.32 → 0.32 | -1.2%; 0.916–1.016 | 0.17 → 0.17 | 7.12 → 7.05 | 0.08 → 0.08 |
| csv-quoted, 1,000 × 4 | 0.33 → 0.33 | -2.6%; 0.973–1.028 | 0.19 → 0.18 | 7.03 → 7.00 | 0.08 → 0.08 |
| csv-quoted, 10,000 × 4 | 0.73 → 0.74 | +1.9%; 0.960–1.052 | 0.40 → 0.40 | 8.56 → 8.25 | 0.64 → 0.64 |
| csv-quoted, 131,071 × 7 | 12.20 → 12.14 | -0.3%; 0.964–1.044 | 5.90 → 5.70 | 44.34 → 37.16 | 14.13 → 14.13 |
| csv-quoted, 75,001 × 13 | 18.66 → 15.25 | -18.6%; 0.782–0.854 | 7.01 → 6.24 | 46.05 → 38.61 | 15.05 → 15.05 |
