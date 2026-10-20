# Single-pass CSV block trial

The index construction and field lookups are included in CPU and elapsed time. Values include result release. CPU percentages use median paired ratios, while displayed times are medians of worker medians. Memory workers are separate and capture peak RSS before validation.

| Input | CPU ms before → trial | Paired CPU change and ratio range | Elapsed ms before → trial | Peak RSS MiB before → trial | Held heap MiB before → trial |
| --- | ---: | ---: | ---: | ---: | ---: |
| csv-quoted, 100,000 × 4 | 5.14 → 5.10 | -0.1%; 0.962–1.036 | 2.85 → 2.79 | 23.38 → 23.41 | 6.14 → 6.14 |
| csv-quoted, 250,000 × 4 | 12.24 → 12.47 | +0.9%; 0.984–1.041 | 6.67 → 6.78 | 48.50 → 48.53 | 15.33 → 15.33 |
| csv-quoted, 1,000,000 × 4 | 48.82 → 48.38 | +0.5%; 0.930–1.027 | 27.06 → 26.45 | 180.64 → 180.67 | 61.08 → 61.08 |
| csv-quoted, 1,000,000 × 2 | 23.87 → 23.31 | -5.3%; 0.935–0.995 | 17.14 → 16.66 | 102.42 → 102.48 | 30.55 → 30.55 |
| csv, 1,000,000 × 4 | 42.66 → 43.31 | +1.0%; 1.001–1.029 | 9.37 → 9.54 | 159.39 → 159.38 | 61.08 → 61.08 |
