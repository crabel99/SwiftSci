# Paired resource comparison

Reference: `baseline`. Candidate: `scoped`. CPU and elapsed time include CSV read and output release. Memory workers are separate.

| Input | Paired CPU change | CPU ratio range | Peak RSS MiB, reference → candidate | Held heap MiB, reference → candidate |
| --- | ---: | ---: | ---: | ---: |
| csv 1,000 × 4 | +0.3% | 0.938–1.063 | 7.16 → 7.11 | 0.08 → 0.08 |
| csv-quoted 1,000 × 4 | -1.8% | 0.951–1.073 | 7.09 → 7.06 | 0.08 → 0.08 |
| csv-quoted 10,000 × 4 | -1.9% | 0.948–0.987 | 8.72 → 8.31 | 0.64 → 0.64 |
| csv-quoted 131,071 × 7 | -6.7% | 0.902–0.986 | 63.97 → 37.17 | 15.17 → 14.13 |
| csv-quoted 75,001 × 13 | -33.3% | 0.660–0.714 | 66.98 → 38.64 | 15.05 → 15.05 |
