# Paired resource comparison

Reference: `baseline`. Candidate: `borrowed`. CPU and elapsed time include CSV read and output release. Memory workers are separate.

| Input | Paired CPU change | CPU ratio range | Peak RSS MiB, reference → candidate | Held heap MiB, reference → candidate |
| --- | ---: | ---: | ---: | ---: |
| csv-quoted 100,000 × 4 | +4.2% | 0.997–1.052 | 26.16 → 20.41 | 6.14 → 6.14 |
| csv-quoted 250,000 × 4 | +6.1% | 1.018–1.074 | 65.14 → 40.69 | 17.63 → 15.33 |
| csv-quoted 1,000,000 × 4 | +4.0% | 1.017–1.068 | 241.38 → 149.81 | 70.31 → 61.08 |
| csv-quoted 1,000,000 × 2 | +7.5% | 1.032–1.117 | 116.17 → 86.78 | 39.78 → 30.55 |
| csv 1,000,000 × 4 | +2.0% | 1.003–1.052 | 159.41 → 159.41 | 61.08 → 61.08 |
