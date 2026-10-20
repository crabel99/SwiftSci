# Single-pass CSV block trial

The index construction and field lookups are included in CPU and elapsed time. Values include result release. CPU percentages use median paired ratios, while displayed times are medians of worker medians. Memory workers are separate and capture peak RSS before validation.

| Input | CPU ms before → trial | Paired CPU change and ratio range | Elapsed ms before → trial | Peak RSS MiB before → trial | Held heap MiB before → trial |
| --- | ---: | ---: | ---: | ---: | ---: |
| csv-quoted, 100,000 × 4 | 4.96 → 4.99 | -2.0%; 0.758–1.041 | 2.72 → 2.67 | 26.08 → 23.41 | 6.14 → 6.14 |
| csv-quoted, 250,000 × 4 | 12.11 → 12.47 | +2.6%; 1.020–1.052 | 6.77 → 6.88 | 65.08 → 48.53 | 17.63 → 15.33 |
| csv-quoted, 1,000,000 × 4 | 47.53 → 49.24 | +2.5%; 0.969–1.044 | 26.53 → 27.42 | 241.31 → 180.67 | 70.31 → 61.08 |
| csv-quoted, 1,000,000 × 2 | 23.23 → 23.12 | -0.5%; 0.988–1.045 | 16.50 → 16.63 | 116.16 → 102.44 | 39.78 → 30.55 |
| csv, 1,000,000 × 4 | 42.26 → 43.21 | +1.8%; 1.003–1.029 | 9.28 → 9.32 | 159.36 → 159.41 | 61.08 → 61.08 |
