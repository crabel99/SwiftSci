# Paired resource comparison

Reference: `baseline`. Candidate: `inlined`. CPU and elapsed time include CSV read and output release. Memory workers are separate.

| Input | Paired CPU change | CPU ratio range | Peak RSS MiB, reference → candidate | Held heap MiB, reference → candidate |
| --- | ---: | ---: | ---: | ---: |
| csv-quoted 100,000 × 4 | +5.7% | 1.008–1.080 | 26.11 → 20.38 | 6.14 → 6.14 |
| csv-quoted 250,000 × 4 | +4.0% | 1.008–1.059 | 65.12 → 40.70 | 17.63 → 15.33 |
| csv-quoted 1,000,000 × 4 | +5.5% | 1.009–1.070 | 241.39 → 149.81 | 70.31 → 61.08 |
| csv-quoted 1,000,000 × 2 | +1.7% | 0.987–1.066 | 116.17 → 86.78 | 39.78 → 30.55 |
| csv 1,000,000 × 4 | -5.7% | 0.941–0.971 | 159.41 → 159.42 | 61.08 → 61.08 |
