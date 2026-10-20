# Paired resource comparison

Reference: `compact`. Candidate: `packed`. CPU and elapsed time include CSV read and output release. Memory workers are separate.

| Input | Paired CPU change | CPU ratio range | Peak RSS MiB, reference → candidate | Held heap MiB, reference → candidate |
| --- | ---: | ---: | ---: | ---: |
| csv 1,000 × 4 | +0.0% | 0.956–1.021 | 7.06 → 7.06 | 0.08 → 0.08 |
| csv-quoted 1,000 × 4 | -1.9% | 0.952–1.047 | 7.03 → 7.00 | 0.08 → 0.08 |
| csv-quoted 10,000 × 4 | -3.2% | 0.922–1.074 | 8.28 → 8.23 | 0.64 → 0.64 |
| csv-quoted 131,071 × 7 | -2.2% | 0.948–1.028 | 37.12 → 37.11 | 14.13 → 14.13 |
| csv-quoted 75,001 × 13 | -1.1% | 0.946–1.017 | 38.61 → 38.56 | 15.05 → 15.05 |
