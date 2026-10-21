# Paired resource comparison

Reference: `baseline`. Candidate: `packed`. CPU and elapsed time include CSV read and output release. Memory workers are separate.

| Input | Paired CPU change | CPU ratio range | Peak RSS MiB, reference → candidate | Held heap MiB, reference → candidate |
| --- | ---: | ---: | ---: | ---: |
| csv-quoted 100,000 × 4 | +0.3% | 0.998–1.028 | 26.11 → 20.38 | 6.14 → 6.14 |
| csv-quoted 250,000 × 4 | +1.0% | 0.987–1.058 | 65.12 → 40.66 | 17.63 → 15.33 |
| csv-quoted 1,000,000 × 4 | -0.2% | 0.979–1.058 | 241.39 → 149.84 | 70.31 → 61.08 |
| csv-quoted 1,000,000 × 2 | +3.3% | 1.017–1.065 | 116.17 → 86.77 | 39.78 → 30.55 |
| csv 1,000,000 × 4 | +2.8% | 1.013–1.039 | 159.41 → 159.41 | 61.08 → 61.08 |
