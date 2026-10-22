# long key controls results

CPU is process user-plus-system time. Peak RSS is a whole-process high-water mark. Elapsed time is separate.

| Scope / case | Policy / candidate | CPU before ms | CPU after ms | Change | Elapsed before / after ms | Peak before / after MiB |
|---|---|---:|---:|---:|---:|---:|
| eager / one-long-nulls-0 |  parallel | 66.683 | 66.728 | +0.1% | 21.448 / 21.509 | 32.65 / 32.70 |
| eager / one-long-nulls-0 |  serial | 34.188 | 34.618 | +1.3% | 34.244 / 34.673 | 32.53 / 32.56 |
| eager / one-long-nulls-50 |  parallel | 39.499 | 39.600 | +0.3% | 13.543 / 13.667 | 25.02 / 25.05 |
| eager / one-long-nulls-50 |  serial | 21.975 | 22.276 | +1.4% | 21.993 / 22.331 | 24.88 / 24.89 |
| eager / pair-long-nulls-0 |  parallel | 51.521 | 51.437 | -0.2% | 17.573 / 17.705 | 32.74 / 32.77 |
| eager / pair-long-nulls-0 |  serial | 34.895 | 35.304 | +1.2% | 34.939 / 35.393 | 32.53 / 32.56 |
| eager / pair-long-nulls-50 |  parallel | 34.842 | 34.822 | -0.1% | 12.375 / 12.430 | 25.04 / 25.09 |
| eager / pair-long-nulls-50 |  serial | 22.378 | 22.666 | +1.3% | 22.419 / 22.713 | 24.83 / 24.89 |
| eager / pair-unicode-nulls-0 |  parallel | 52.054 | 52.465 | +0.8% | 17.810 / 17.930 | 32.74 / 32.77 |
| eager / pair-unicode-nulls-0 |  serial | 34.791 | 35.236 | +1.3% | 34.846 / 35.261 | 32.53 / 32.56 |
| eager / pair-unicode-nulls-50 |  parallel | 52.567 | 52.194 | -0.7% | 17.292 / 17.449 | 25.27 / 25.27 |
| eager / pair-unicode-nulls-50 |  serial | 35.945 | 36.491 | +1.5% | 36.004 / 36.557 | 25.05 / 25.06 |
| eager / three-long-nulls-0 |  parallel | 86.178 | 64.287 | -25.4% | 26.328 / 20.810 | 32.74 / 32.72 |
| eager / three-long-nulls-0 |  serial | 63.161 | 33.828 | -46.4% | 63.218 / 33.901 | 32.53 / 32.59 |
| eager / three-long-nulls-50 |  parallel | 53.350 | 39.522 | -25.9% | 17.321 / 13.735 | 25.17 / 25.15 |
| eager / three-long-nulls-50 |  serial | 38.666 | 24.278 | -37.2% | 38.702 / 24.333 | 24.98 / 25.02 |
