# Paired resource comparison

Reference: `baseline`. Candidate: `packed`. CPU and elapsed time include CSV read and output release. Memory workers are separate.

| Input | Paired CPU change | CPU ratio range | Peak RSS MiB, reference → candidate | Held heap MiB, reference → candidate |
| --- | ---: | ---: | ---: | ---: |
| mixed-infer 20,000 × 4 | +3.3% | 0.939–1.060 | 13.86 → 13.33 | 2.06 → 2.06 |
| mixed-known 20,000 × 4 | +2.9% | 0.597–1.097 | 9.94 → 9.38 | 0.97 → 0.97 |
| missing-infer 250,000 × 8 | -10.5% | 0.893–0.943 | 127.41 → 71.80 | 32.94 → 30.64 |
| missing-known 250,000 × 8 | -11.4% | 0.861–0.910 | 127.42 → 71.78 | 32.94 → 30.64 |
| text-infer 2,048 × 2 | +1.2% | 0.987–1.041 | 48.56 → 48.61 | 21.20 → 21.20 |
| text-known 2,048 × 2 | +2.0% | 0.980–1.084 | 44.67 → 44.62 | 20.11 → 20.11 |
| dates-infer 2,048 × 2 | -0.0% | 0.996–1.000 | 9.88 → 9.88 | 0.33 → 0.33 |
| dates-known 2,048 × 2 | +0.3% | 0.993–1.018 | 9.86 → 9.84 | 0.33 → 0.33 |
