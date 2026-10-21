# Paired resource comparison

Reference: `baseline`. Candidate: `direct`. CPU and elapsed time include CSV read and output release. Memory workers are separate.

| Input | Paired CPU change | CPU ratio range | Peak RSS MiB, reference → candidate | Held heap MiB, reference → candidate |
| --- | ---: | ---: | ---: | ---: |
| csv-quoted 100,000 × 4 | +8.1% | 1.029–1.139 | 26.16 → 20.38 | 6.14 → 6.14 |
| csv-quoted 250,000 × 4 | +2.5% | 1.003–1.052 | 65.16 → 40.70 | 17.63 → 15.33 |
| csv-quoted 1,000,000 × 4 | +5.4% | 1.034–1.086 | 241.38 → 149.84 | 70.31 → 61.08 |
| csv-quoted 1,000,000 × 2 | +6.7% | 1.048–1.123 | 116.19 → 86.78 | 39.78 → 30.55 |
| csv 1,000,000 × 4 | +7.4% | 1.069–1.094 | 159.39 → 159.44 | 61.08 → 61.08 |
