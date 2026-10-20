# Quoted CSV preallocation trial

The extra counting scan is included in CPU and elapsed time. Values include result release. CPU percentages use median paired ratios, while displayed times are medians of worker medians. Memory workers are separate and capture peak RSS before validation.

| Input | CPU ms before → trial | Paired CPU change and ratio range | Elapsed ms before → trial | Peak RSS MiB before → trial | Held heap MiB before → trial |
| --- | ---: | ---: | ---: | ---: | ---: |
| csv-quoted, 100,000 × 4 | 5.05 → 6.40 | +25.5%; 1.226–1.339 | 2.88 → 4.30 | 26.08 → 23.00 | 6.14 → 6.14 |
| csv-quoted, 250,000 × 4 | 12.17 → 15.69 | +29.0%; 1.195–1.365 | 6.75 → 10.63 | 65.09 → 47.06 | 17.63 → 15.33 |
| csv-quoted, 1,000,000 × 4 | 47.26 → 60.55 | +27.7%; 1.249–1.376 | 26.69 → 41.16 | 242.88 → 166.97 | 70.31 → 61.08 |
| csv-quoted, 1,000,000 × 2 | 23.07 → 29.67 | +33.5%; 1.275–1.369 | 17.26 → 24.40 | 116.14 → 90.70 | 39.78 → 30.55 |
| csv, 1,000,000 × 4 | 42.35 → 42.72 | +0.6%; 0.996–1.040 | 9.40 → 9.44 | 159.36 → 159.41 | 61.08 → 61.08 |
