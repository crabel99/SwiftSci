# Single-pass CSV block trial

The index construction and field lookups are included in CPU and elapsed time. Values include result release. CPU percentages use median paired ratios, while displayed times are medians of worker medians. Memory workers are separate and capture peak RSS before validation.

| Input | CPU ms before → trial | Paired CPU change and ratio range | Elapsed ms before → trial | Peak RSS MiB before → trial | Held heap MiB before → trial |
| --- | ---: | ---: | ---: | ---: | ---: |
| csv, 1,000 × 4 | 0.32 → 0.32 | -2.1%; 0.966–1.012 | 0.17 → 0.17 | 7.12 → 7.14 | 0.08 → 0.08 |
| csv-quoted, 1,000 × 4 | 0.32 → 0.32 | +1.0%; 0.950–1.047 | 0.20 → 0.21 | 7.06 → 7.05 | 0.08 → 0.08 |
| csv-quoted, 10,000 × 4 | 0.75 → 0.74 | -0.4%; 0.971–1.011 | 0.45 → 0.45 | 8.58 → 8.59 | 0.64 → 0.64 |
| csv-quoted, 131,071 × 7 | 12.13 → 11.73 | -0.2%; 0.939–1.018 | 5.82 → 5.61 | 44.31 → 44.33 | 14.13 → 14.13 |
| csv-quoted, 75,001 × 13 | 19.25 → 19.69 | +2.4%; 1.008–1.120 | 6.84 → 7.03 | 46.05 → 46.09 | 15.05 → 15.05 |
