# Single-pass CSV block trial

The index construction and field lookups are included in CPU and elapsed time. Values include result release. CPU percentages use median paired ratios, while displayed times are medians of worker medians. Memory workers are separate and capture peak RSS before validation.

| Input | CPU ms before → trial | Paired CPU change and ratio range | Elapsed ms before → trial | Peak RSS MiB before → trial | Held heap MiB before → trial |
| --- | ---: | ---: | ---: | ---: | ---: |
| csv, 1,000 × 4 | 0.33 → 0.33 | -0.6%; 0.958–1.068 | 0.17 → 0.17 | 7.12 → 7.08 | 0.08 → 0.08 |
| csv-quoted, 1,000 × 4 | 0.33 → 0.33 | +1.5%; 0.991–1.068 | 0.18 → 0.19 | 7.08 → 7.03 | 0.08 → 0.08 |
| csv-quoted, 10,000 × 4 | 0.73 → 0.78 | +3.7%; 0.992–1.101 | 0.42 → 0.42 | 8.70 → 8.28 | 0.64 → 0.64 |
| csv-quoted, 131,071 × 7 | 11.67 → 12.15 | +6.1%; 0.976–1.105 | 5.73 → 5.64 | 63.95 → 37.14 | 15.17 → 14.13 |
| csv-quoted, 75,001 × 13 | 18.71 → 14.82 | -21.4%; 0.715–0.855 | 6.89 → 6.10 | 66.97 → 38.61 | 15.05 → 15.05 |
