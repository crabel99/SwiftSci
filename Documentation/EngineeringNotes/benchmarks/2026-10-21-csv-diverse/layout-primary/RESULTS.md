# Paired resource comparison

Reference: `packed`. Candidate: `direct`. CPU and elapsed time include CSV read and output release. Memory workers are separate.

| Input | Paired CPU change | CPU ratio range | Peak RSS MiB, reference → candidate | Held heap MiB, reference → candidate |
| --- | ---: | ---: | ---: | ---: |
| csv-quoted 100,000 × 4 | +9.4% | 1.072–1.107 | 20.38 → 20.39 | 6.14 → 6.14 |
| csv-quoted 250,000 × 4 | +4.8% | 1.031–1.068 | 40.67 → 40.69 | 15.33 → 15.33 |
| csv-quoted 1,000,000 × 4 | +2.5% | 1.008–1.077 | 149.84 → 149.84 | 61.08 → 61.08 |
| csv-quoted 1,000,000 × 2 | +0.2% | 0.975–1.051 | 86.80 → 86.78 | 30.55 → 30.55 |
| csv 1,000,000 × 4 | +3.0% | 1.007–1.037 | 159.41 → 159.42 | 61.08 → 61.08 |
