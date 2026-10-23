# long key controls results

CPU is process user-plus-system time. Peak RSS is a process high-water mark, not allocations. Elapsed time is separate.

| Scope and case | Policy | Parent CPU ms | Metadata CPU ms | CPU change | Elapsed before / after ms | Peak before / after MiB |
|---|---|---:|---:|---:|---:|---:|
| eager one-long-nulls-0 | parallel | 53.896 | 50.429 | -6.4% | 19.378 / 18.046 | 32.80 / 33.02 |
| eager one-long-nulls-0 | serial | 35.786 | 36.020 | +0.7% | 35.797 / 36.043 | 32.56 / 32.66 |
| eager one-long-nulls-50 | parallel | 35.815 | 37.950 | +6.0% | 12.988 / 13.405 | 25.11 / 25.13 |
| eager one-long-nulls-50 | serial | 22.979 | 23.309 | +1.4% | 22.990 / 23.315 | 24.93 / 24.92 |
| eager pair-long-nulls-0 | parallel | 51.925 | 50.446 | -2.8% | 18.554 / 18.101 | 33.42 / 33.28 |
| eager pair-long-nulls-0 | serial | 36.645 | 37.258 | +1.7% | 36.736 / 37.289 | 32.56 / 32.62 |
| eager pair-long-nulls-50 | parallel | 33.403 | 34.495 | +3.3% | 12.649 / 12.744 | 25.10 / 25.21 |
| eager pair-long-nulls-50 | serial | 23.893 | 24.162 | +1.1% | 23.900 / 24.160 | 24.89 / 24.91 |
| eager pair-unicode-nulls-0 | parallel | 51.721 | 52.383 | +1.3% | 18.721 / 18.971 | 33.57 / 32.93 |
| eager pair-unicode-nulls-0 | serial | 37.041 | 37.330 | +0.8% | 37.089 / 37.351 | 32.56 / 32.62 |
| eager pair-unicode-nulls-50 | parallel | 48.209 | 50.276 | +4.3% | 17.212 / 17.861 | 26.07 / 26.05 |
| eager pair-unicode-nulls-50 | serial | 37.709 | 38.237 | +1.4% | 37.714 / 38.267 | 25.45 / 25.18 |
| eager three-long-nulls-0 | parallel | 86.653 | 59.555 | -31.3% | 27.722 / 20.762 | 32.85 / 33.16 |
| eager three-long-nulls-0 | serial | 66.883 | 36.042 | -46.1% | 66.911 / 36.053 | 32.58 / 32.65 |
| eager three-long-nulls-50 | parallel | 51.712 | 38.446 | -25.7% | 17.355 / 14.140 | 25.31 / 25.26 |
| eager three-long-nulls-50 | serial | 41.755 | 25.755 | -38.3% | 41.774 / 25.761 | 25.02 / 25.08 |
