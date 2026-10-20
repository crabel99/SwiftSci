# Single-pass CSV block trial

The index construction and field lookups are included in CPU and elapsed time. Values include result release. CPU percentages use median paired ratios, while displayed times are medians of worker medians. Memory workers are separate and capture peak RSS before validation.

| Input | CPU ms before → trial | Paired CPU change and ratio range | Elapsed ms before → trial | Peak RSS MiB before → trial | Held heap MiB before → trial |
| --- | ---: | ---: | ---: | ---: | ---: |
| csv-quoted, 100,000 × 4 | 5.21 → 5.58 | +4.5%; 0.994–1.115 | 2.91 → 3.13 | 23.36 → 20.33 | 6.14 → 6.14 |
| csv-quoted, 250,000 × 4 | 12.51 → 12.78 | +1.8%; 1.003–1.104 | 6.83 → 6.91 | 48.52 → 40.67 | 15.33 → 15.33 |
| csv-quoted, 1,000,000 × 4 | 48.65 → 49.89 | +2.2%; 1.007–1.096 | 27.00 → 27.02 | 180.67 → 149.77 | 61.08 → 61.08 |
| csv-quoted, 1,000,000 × 2 | 23.97 → 24.53 | +2.3%; 0.993–1.118 | 17.09 → 17.22 | 102.42 → 86.73 | 30.55 → 30.55 |
| csv, 1,000,000 × 4 | 42.81 → 44.61 | +4.0%; 1.036–1.051 | 9.34 → 9.79 | 159.34 → 159.38 | 61.08 → 61.08 |
