# Single-pass CSV block trial

The index construction and field lookups are included in CPU and elapsed time. Values include result release. CPU percentages use median paired ratios, while displayed times are medians of worker medians. Memory workers are separate and capture peak RSS before validation.

| Input | CPU ms before → trial | Paired CPU change and ratio range | Elapsed ms before → trial | Peak RSS MiB before → trial | Held heap MiB before → trial |
| --- | ---: | ---: | ---: | ---: | ---: |
| csv-quoted, 100,000 × 4 | 4.91 → 5.75 | +16.1%; 1.137–1.210 | 2.69 → 3.46 | 26.08 → 23.41 | 6.14 → 6.14 |
| csv-quoted, 250,000 × 4 | 11.84 → 13.88 | +16.1%; 1.142–1.196 | 6.57 → 8.48 | 65.09 → 48.58 | 17.63 → 15.33 |
| csv-quoted, 1,000,000 × 4 | 47.35 → 54.97 | +15.3%; 1.139–1.169 | 26.61 → 33.24 | 241.34 → 180.66 | 70.31 → 61.08 |
| csv-quoted, 1,000,000 × 2 | 22.21 → 27.01 | +21.5%; 1.191–1.233 | 15.90 → 19.94 | 116.16 → 102.45 | 39.78 → 30.55 |
| csv, 1,000,000 × 4 | 42.52 → 42.80 | +0.8%; 0.997–1.013 | 9.28 → 9.35 | 159.36 → 159.36 | 61.08 → 61.08 |
