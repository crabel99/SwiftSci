# Single-pass CSV block trial

The index construction and field lookups are included in CPU and elapsed time. Values include result release. CPU percentages use median paired ratios, while displayed times are medians of worker medians. Memory workers are separate and capture peak RSS before validation.

| Input | CPU ms before → trial | Paired CPU change and ratio range | Elapsed ms before → trial | Peak RSS MiB before → trial | Held heap MiB before → trial |
| --- | ---: | ---: | ---: | ---: | ---: |
| csv-quoted, 100,000 × 4 | 4.88 → 5.05 | +2.2%; 0.991–1.455 | 2.70 → 2.87 | 26.11 → 24.92 | 6.14 → 6.14 |
| csv-quoted, 250,000 × 4 | 12.04 → 11.96 | -0.7%; 0.969–1.039 | 6.75 → 6.62 | 65.12 → 63.80 | 17.63 → 15.33 |
| csv-quoted, 1,000,000 × 4 | 47.77 → 48.03 | +0.3%; 0.988–1.031 | 27.01 → 27.07 | 241.34 → 241.72 | 70.31 → 61.08 |
| csv-quoted, 1,000,000 × 2 | 23.19 → 23.34 | +0.4%; 0.955–1.060 | 16.91 → 16.91 | 116.12 → 132.95 | 39.78 → 30.55 |
| csv, 1,000,000 × 4 | 42.60 → 42.42 | +0.5%; 0.986–1.013 | 9.28 → 9.33 | 159.34 → 159.36 | 61.08 → 61.08 |
