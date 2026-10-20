# Single-pass CSV block trial

The index construction and field lookups are included in CPU and elapsed time. Values include result release. CPU percentages use median paired ratios, while displayed times are medians of worker medians. Memory workers are separate and capture peak RSS before validation.

| Input | CPU ms before → trial | Paired CPU change and ratio range | Elapsed ms before → trial | Peak RSS MiB before → trial | Held heap MiB before → trial |
| --- | ---: | ---: | ---: | ---: | ---: |
| csv-quoted, 100,000 × 4 | 5.03 → 5.44 | +5.1%; 1.046–1.153 | 2.86 → 3.02 | 26.11 → 20.34 | 6.14 → 6.14 |
| csv-quoted, 250,000 × 4 | 12.21 → 12.85 | +5.5%; 1.031–1.077 | 6.90 → 6.89 | 65.09 → 40.62 | 17.63 → 15.33 |
| csv-quoted, 1,000,000 × 4 | 48.63 → 50.16 | +1.7%; 0.999–1.062 | 27.85 → 26.88 | 241.31 → 149.75 | 70.31 → 61.08 |
| csv-quoted, 1,000,000 × 2 | 23.75 → 24.59 | +2.4%; 1.007–1.081 | 17.27 → 17.42 | 116.12 → 86.77 | 39.78 → 30.55 |
| csv, 1,000,000 × 4 | 42.57 → 44.30 | +4.2%; 1.016–1.052 | 9.33 → 9.79 | 159.38 → 159.36 | 61.08 → 61.08 |
