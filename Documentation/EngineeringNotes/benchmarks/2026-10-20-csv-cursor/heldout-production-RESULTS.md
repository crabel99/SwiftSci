# Single-pass CSV block trial

The index construction and field lookups are included in CPU and elapsed time. Values include result release. CPU percentages use median paired ratios, while displayed times are medians of worker medians. Memory workers are separate and capture peak RSS before validation.

| Input | CPU ms before → trial | Paired CPU change and ratio range | Elapsed ms before → trial | Peak RSS MiB before → trial | Held heap MiB before → trial |
| --- | ---: | ---: | ---: | ---: | ---: |
| csv, 1,000 × 4 | 0.33 → 0.34 | +3.7%; 0.942–1.069 | 0.17 → 0.18 | 7.11 → 7.11 | 0.08 → 0.08 |
| csv-quoted, 1,000 × 4 | 0.31 → 0.32 | +2.3%; 0.977–1.046 | 0.21 → 0.21 | 7.05 → 7.08 | 0.08 → 0.08 |
| csv-quoted, 10,000 × 4 | 0.72 → 0.73 | +2.3%; 0.985–1.029 | 0.42 → 0.43 | 8.67 → 8.56 | 0.64 → 0.64 |
| csv-quoted, 131,071 × 7 | 11.70 → 11.84 | +4.0%; 0.980–1.065 | 5.82 → 5.66 | 63.92 → 44.33 | 15.17 → 14.13 |
| csv-quoted, 75,001 × 13 | 18.38 → 19.34 | +2.6%; 0.913–1.173 | 6.54 → 6.57 | 67.05 → 46.09 | 15.05 → 15.05 |
