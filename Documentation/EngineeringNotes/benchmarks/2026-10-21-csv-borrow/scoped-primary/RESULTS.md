# Paired resource comparison

Reference: `baseline`. Candidate: `scoped`. CPU and elapsed time include CSV read and output release. Memory workers are separate.

| Input | Paired CPU change | CPU ratio range | Peak RSS MiB, reference → candidate | Held heap MiB, reference → candidate |
| --- | ---: | ---: | ---: | ---: |
| csv-quoted 100,000 × 4 | -6.7% | 0.925–0.977 | 26.12 → 20.39 | 6.14 → 6.14 |
| csv-quoted 250,000 × 4 | -5.6% | 0.930–0.990 | 65.14 → 40.69 | 17.63 → 15.33 |
| csv-quoted 1,000,000 × 4 | -6.1% | 0.916–1.003 | 241.36 → 149.83 | 70.31 → 61.08 |
| csv-quoted 1,000,000 × 2 | -0.6% | 0.946–1.007 | 116.17 → 86.81 | 39.78 → 30.55 |
| csv 1,000,000 × 4 | -5.3% | 0.934–0.957 | 159.39 → 159.45 | 61.08 → 61.08 |
