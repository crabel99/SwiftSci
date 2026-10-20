# Single-pass CSV block trial

The index construction and field lookups are included in CPU and elapsed time. Values include result release. CPU percentages use median paired ratios, while displayed times are medians of worker medians. Memory workers are separate and capture peak RSS before validation.

| Input | CPU ms before → trial | Paired CPU change and ratio range | Elapsed ms before → trial | Peak RSS MiB before → trial | Held heap MiB before → trial |
| --- | ---: | ---: | ---: | ---: | ---: |
| csv-quoted, 100,000 × 4 | 4.94 → 5.25 | +6.3%; 1.026–1.112 | 2.71 → 2.84 | 26.08 → 20.36 | 6.14 → 6.14 |
| csv-quoted, 250,000 × 4 | 12.12 → 12.89 | +5.7%; 1.026–1.088 | 6.82 → 7.00 | 65.11 → 40.69 | 17.63 → 15.33 |
| csv-quoted, 1,000,000 × 4 | 47.98 → 50.20 | +4.4%; 1.032–1.055 | 27.03 → 27.55 | 241.31 → 149.80 | 70.31 → 61.08 |
| csv-quoted, 1,000,000 × 2 | 23.03 → 24.60 | +7.6%; 1.058–1.117 | 16.58 → 17.64 | 116.12 → 86.77 | 39.78 → 30.55 |
| csv, 1,000,000 × 4 | 42.35 → 44.69 | +5.2%; 1.043–1.093 | 9.27 → 9.73 | 159.31 → 159.42 | 61.08 → 61.08 |
