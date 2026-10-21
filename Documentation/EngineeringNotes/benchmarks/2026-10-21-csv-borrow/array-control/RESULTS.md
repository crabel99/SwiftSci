# Paired resource comparison

Reference: `scoped`. Candidate: `arrays`. CPU and elapsed time include CSV read and output release. Memory workers are separate.

| Input | Paired CPU change | CPU ratio range | Peak RSS MiB, reference → candidate | Held heap MiB, reference → candidate |
| --- | ---: | ---: | ---: | ---: |
| csv-quoted 100,000 × 4 | +3.4% | 0.958–1.071 | 20.39 → 20.34 | 6.14 → 6.14 |
| csv-quoted 250,000 × 4 | +5.5% | 0.993–1.108 | 40.67 → 40.64 | 15.33 → 15.33 |
| csv-quoted 1,000,000 × 4 | +6.2% | 1.025–1.132 | 149.84 → 149.80 | 61.08 → 61.08 |
| csv-quoted 1,000,000 × 2 | +8.8% | 1.064–1.177 | 86.78 → 86.75 | 30.55 → 30.55 |
| csv 1,000,000 × 4 | +5.4% | 1.040–1.060 | 159.45 → 159.39 | 61.08 → 61.08 |
