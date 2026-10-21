# Paired resource comparison

Reference: `baseline`. Candidate: `scoped`. CPU and elapsed time include CSV read and output release. Memory workers are separate.

| Input | Paired CPU change | CPU ratio range | Peak RSS MiB, reference → candidate | Held heap MiB, reference → candidate |
| --- | ---: | ---: | ---: | ---: |
| csv 5,000 × 4 | +0.4% | 0.989–1.019 | 7.73 → 7.66 | 0.33 → 0.33 |
| csv 100,000 × 4 | -3.2% | 0.944–0.979 | 22.33 → 22.36 | 6.14 → 6.14 |
| csv 1,000,000 × 2 | -3.1% | 0.953–0.973 | 87.05 → 87.05 | 30.55 → 30.55 |
| csv 131,071 × 7 | -2.1% | 0.958–0.985 | 41.55 → 41.59 | 14.13 → 14.13 |
| csv 75,001 × 13 | -5.8% | 0.925–0.976 | 43.41 → 43.42 | 15.05 → 15.05 |
