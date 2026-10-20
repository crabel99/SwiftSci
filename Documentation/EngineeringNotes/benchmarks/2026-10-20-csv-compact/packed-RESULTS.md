# Single-pass CSV block trial

The index construction and field lookups are included in CPU and elapsed time. Values include result release. CPU percentages use median paired ratios, while displayed times are medians of worker medians. Memory workers are separate and capture peak RSS before validation.

| Input | CPU ms before → trial | Paired CPU change and ratio range | Elapsed ms before → trial | Peak RSS MiB before → trial | Held heap MiB before → trial |
| --- | ---: | ---: | ---: | ---: | ---: |
| csv-quoted, 100,000 × 4 | 4.94 → 5.06 | +2.7%; 0.983–1.044 | 2.72 → 2.77 | 26.08 → 20.31 | 6.14 → 6.14 |
| csv-quoted, 250,000 × 4 | 12.28 → 12.45 | +1.4%; 0.977–1.072 | 7.02 → 6.80 | 65.11 → 40.64 | 17.63 → 15.33 |
| csv-quoted, 1,000,000 × 4 | 48.09 → 48.21 | +0.1%; 0.987–1.039 | 27.44 → 26.66 | 241.31 → 149.75 | 70.31 → 61.08 |
| csv-quoted, 1,000,000 × 2 | 23.07 → 24.40 | +6.5%; 0.993–1.130 | 16.41 → 17.94 | 116.14 → 86.73 | 39.78 → 30.55 |
| csv, 1,000,000 × 4 | 42.30 → 43.97 | +3.8%; 1.024–1.045 | 9.21 → 9.75 | 159.39 → 159.33 | 61.08 → 61.08 |
