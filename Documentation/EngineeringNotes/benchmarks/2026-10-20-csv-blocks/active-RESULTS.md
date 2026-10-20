# Single-pass CSV block trial

The index construction and field lookups are included in CPU and elapsed time. Values include result release. CPU percentages use median paired ratios, while displayed times are medians of worker medians. Memory workers are separate and capture peak RSS before validation.

| Input | CPU ms before → trial | Paired CPU change and ratio range | Elapsed ms before → trial | Peak RSS MiB before → trial | Held heap MiB before → trial |
| --- | ---: | ---: | ---: | ---: | ---: |
| csv-quoted, 100,000 × 4 | 4.92 → 5.14 | +4.3%; 1.005–1.508 | 2.69 → 2.82 | 26.08 → 23.41 | 6.14 → 6.14 |
| csv-quoted, 250,000 × 4 | 11.98 → 12.13 | +0.8%; 0.998–1.041 | 6.73 → 6.49 | 65.09 → 48.52 | 17.63 → 15.33 |
| csv-quoted, 1,000,000 × 4 | 47.99 → 47.88 | -0.1%; 0.986–1.016 | 27.03 → 25.82 | 241.31 → 180.64 | 70.31 → 61.08 |
| csv-quoted, 1,000,000 × 2 | 22.68 → 24.12 | +5.6%; 1.015–1.117 | 16.36 → 17.44 | 116.16 → 102.44 | 39.78 → 30.55 |
| csv, 1,000,000 × 4 | 42.48 → 42.85 | +1.1%; 0.999–1.017 | 9.28 → 9.31 | 159.34 → 159.34 | 61.08 → 61.08 |
