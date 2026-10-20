# Single-pass CSV block trial

The index construction and field lookups are included in CPU and elapsed time. Values include result release. CPU percentages use median paired ratios, while displayed times are medians of worker medians. Memory workers are separate and capture peak RSS before validation.

| Input | CPU ms before → trial | Paired CPU change and ratio range | Elapsed ms before → trial | Peak RSS MiB before → trial | Held heap MiB before → trial |
| --- | ---: | ---: | ---: | ---: | ---: |
| csv, 1,000 × 4 | 0.33 → 0.32 | -0.9%; 0.938–1.050 | 0.17 → 0.18 | 7.09 → 7.11 | 0.08 → 0.08 |
| csv-quoted, 1,000 × 4 | 0.32 → 0.33 | -0.3%; 0.991–1.049 | 0.22 → 0.21 | 7.03 → 7.08 | 0.08 → 0.08 |
| csv-quoted, 10,000 × 4 | 0.74 → 0.74 | -0.1%; 0.980–1.038 | 0.44 → 0.43 | 8.55 → 8.59 | 0.64 → 0.64 |
| csv-quoted, 131,071 × 7 | 12.17 → 12.21 | +0.1%; 0.899–1.101 | 5.92 → 5.91 | 44.31 → 44.34 | 14.13 → 14.13 |
| csv-quoted, 75,001 × 13 | 18.37 → 18.82 | -1.2%; 0.940–1.024 | 6.69 → 6.64 | 46.05 → 46.05 | 15.05 → 15.05 |
