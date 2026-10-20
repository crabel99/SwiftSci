# Single-pass CSV block trial

The index construction and field lookups are included in CPU and elapsed time. Values include result release. CPU percentages use median paired ratios, while displayed times are medians of worker medians. Memory workers are separate and capture peak RSS before validation.

| Input | CPU ms before → trial | Paired CPU change and ratio range | Elapsed ms before → trial | Peak RSS MiB before → trial | Held heap MiB before → trial |
| --- | ---: | ---: | ---: | ---: | ---: |
| csv-quoted, 100,000 × 4 | 5.07 → 5.22 | +3.5%; 0.976–1.418 | 2.77 → 2.89 | 23.38 → 23.39 | 6.14 → 6.14 |
| csv-quoted, 250,000 × 4 | 12.27 → 12.28 | +1.1%; 0.968–1.018 | 6.57 → 6.65 | 48.52 → 48.55 | 15.33 → 15.33 |
| csv-quoted, 1,000,000 × 4 | 47.56 → 47.71 | +0.3%; 0.979–1.048 | 25.87 → 25.51 | 180.64 → 180.67 | 61.08 → 61.08 |
| csv-quoted, 1,000,000 × 2 | 23.82 → 24.11 | -0.0%; 0.994–1.049 | 17.16 → 17.15 | 102.42 → 102.44 | 30.55 → 30.55 |
| csv, 1,000,000 × 4 | 42.95 → 43.92 | +2.7%; 0.985–1.042 | 9.43 → 9.77 | 159.36 → 159.36 | 61.08 → 61.08 |
