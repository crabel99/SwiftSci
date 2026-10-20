# Single-pass CSV block trial

The index construction and field lookups are included in CPU and elapsed time. Values include result release. CPU percentages use median paired ratios, while displayed times are medians of worker medians. Memory workers are separate and capture peak RSS before validation.

| Input | CPU ms before → trial | Paired CPU change and ratio range | Elapsed ms before → trial | Peak RSS MiB before → trial | Held heap MiB before → trial |
| --- | ---: | ---: | ---: | ---: | ---: |
| csv, 1,000 × 4 | 0.32 → 0.33 | +5.1%; 1.003–1.078 | 0.18 → 0.19 | 7.11 → 7.09 | 0.08 → 0.08 |
| csv-quoted, 1,000 × 4 | 0.32 → 0.32 | -0.3%; 0.948–1.010 | 0.21 → 0.20 | 7.05 → 7.03 | 0.08 → 0.08 |
| csv-quoted, 10,000 × 4 | 0.72 → 0.73 | +1.7%; 1.004–1.043 | 0.44 → 0.44 | 8.70 → 8.55 | 0.64 → 0.64 |
| csv-quoted, 131,071 × 7 | 11.89 → 11.62 | -1.4%; 0.941–0.993 | 6.07 → 5.62 | 63.95 → 44.34 | 15.17 → 14.13 |
| csv-quoted, 75,001 × 13 | 18.25 → 18.42 | +1.5%; 0.952–1.029 | 6.58 → 6.85 | 66.94 → 46.08 | 15.05 → 15.05 |
