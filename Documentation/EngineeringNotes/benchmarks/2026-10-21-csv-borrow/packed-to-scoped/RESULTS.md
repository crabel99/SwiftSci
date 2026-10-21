# Paired resource comparison

Reference: `packed`. Candidate: `scoped`. CPU and elapsed time include CSV read and output release. Memory workers are separate.

| Input | Paired CPU change | CPU ratio range | Peak RSS MiB, reference → candidate | Held heap MiB, reference → candidate |
| --- | ---: | ---: | ---: | ---: |
| csv-quoted 100,000 × 4 | -4.8% | 0.919–0.964 | 20.38 → 20.39 | 6.14 → 6.14 |
| csv-quoted 250,000 × 4 | -7.0% | 0.897–0.966 | 40.67 → 40.69 | 15.33 → 15.33 |
| csv-quoted 1,000,000 × 4 | -3.9% | 0.925–0.971 | 149.84 → 149.84 | 61.08 → 61.08 |
| csv-quoted 1,000,000 × 2 | -10.2% | 0.892–0.974 | 86.78 → 86.81 | 30.55 → 30.55 |
| csv 1,000,000 × 4 | -6.6% | 0.920–0.955 | 159.41 → 159.45 | 61.08 → 61.08 |
