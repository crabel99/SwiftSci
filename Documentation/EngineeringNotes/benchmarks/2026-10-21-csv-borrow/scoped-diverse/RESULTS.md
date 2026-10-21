# Paired resource comparison

Reference: `baseline`. Candidate: `scoped`. CPU and elapsed time include CSV read and output release. Memory workers are separate.

| Input | Paired CPU change | CPU ratio range | Peak RSS MiB, reference → candidate | Held heap MiB, reference → candidate |
| --- | ---: | ---: | ---: | ---: |
| mixed-infer 20,000 × 4 | +1.9% | 0.962–1.051 | 13.83 → 13.28 | 2.06 → 2.06 |
| mixed-known 20,000 × 4 | +3.8% | 0.960–1.086 | 9.94 → 9.39 | 0.97 → 0.97 |
| missing-infer 250,000 × 8 | -16.9% | 0.823–0.845 | 127.41 → 71.78 | 32.94 → 30.64 |
| missing-known 250,000 × 8 | -15.3% | 0.821–0.854 | 127.42 → 71.77 | 32.94 → 30.64 |
| text-infer 2,048 × 2 | +0.5% | 0.958–1.032 | 48.55 → 48.50 | 21.20 → 21.20 |
| text-known 2,048 × 2 | +0.2% | 0.958–1.042 | 44.62 → 44.61 | 20.11 → 20.11 |
| dates-infer 2,048 × 2 | -0.1% | 0.990–1.005 | 9.88 → 9.78 | 0.33 → 0.33 |
| dates-known 2,048 × 2 | +0.9% | 0.996–1.012 | 9.86 → 9.77 | 0.33 → 0.33 |
