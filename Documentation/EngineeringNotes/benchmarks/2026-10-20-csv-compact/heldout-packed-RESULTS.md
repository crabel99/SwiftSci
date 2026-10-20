# Single-pass CSV block trial

The index construction and field lookups are included in CPU and elapsed time. Values include result release. CPU percentages use median paired ratios, while displayed times are medians of worker medians. Memory workers are separate and capture peak RSS before validation.

| Input | CPU ms before → trial | Paired CPU change and ratio range | Elapsed ms before → trial | Peak RSS MiB before → trial | Held heap MiB before → trial |
| --- | ---: | ---: | ---: | ---: | ---: |
| csv, 1,000 × 4 | 0.32 → 0.34 | +7.1%; 1.003–1.098 | 0.18 → 0.18 | 7.14 → 7.06 | 0.08 → 0.08 |
| csv-quoted, 1,000 × 4 | 0.32 → 0.33 | +0.6%; 0.961–1.038 | 0.18 → 0.19 | 7.05 → 6.98 | 0.08 → 0.08 |
| csv-quoted, 10,000 × 4 | 0.74 → 0.75 | +0.0%; 0.973–1.059 | 0.41 → 0.41 | 8.70 → 8.23 | 0.64 → 0.64 |
| csv-quoted, 131,071 × 7 | 11.92 → 11.96 | -0.1%; 0.995–1.006 | 6.01 → 5.74 | 63.92 → 37.14 | 15.17 → 14.13 |
| csv-quoted, 75,001 × 13 | 19.06 → 14.93 | -20.3%; 0.730–0.833 | 7.03 → 6.19 | 66.97 → 38.58 | 15.05 → 15.05 |
