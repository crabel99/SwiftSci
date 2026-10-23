# Matched CSV resource results

CPU ratios use one immutable shared native null-token Set and correctly matched compiled interfaces and objects. Each worker contributes one paired ratio from its two read medians. CPU is process user plus system time. Elapsed time is separate. Memory is from independent fresh standalone processes and excludes validation from the captured peak.

| Reference and scope | Policy | Cleanup CPU ms | Candidate CPU ms | Paired CPU change | Bootstrap 95% interval | Paired elapsed change | Cleanup / candidate peak MiB |
|---|---|---:|---:|---:|---|---:|---|
| Aotizhongxin-default, eager | parallel | 10.643 | 10.058 | -7.04% | -8.21% to -4.68% | -5.99% | 23.12 / 23.12 |
| Aotizhongxin-default, eager | serial | 9.062 | 8.096 | -9.39% | -12.54% to -6.88% | -9.91% | 22.81 / 22.84 |
| Aotizhongxin-default, stream | parallel | 10.811 | 10.046 | -7.49% | -10.57% to -5.92% | -8.87% | 15.23 / 15.79 |
| Aotizhongxin-default, stream | serial | 8.402 | 7.684 | -8.11% | -9.47% to -7.11% | -7.99% | 15.59 / 16.78 |
| energy-default, eager | parallel | 524.268 | 423.446 | -18.02% | -18.84% to -16.03% | -25.94% | 422.48 / 422.48 |
| energy-default, eager | serial | 332.349 | 244.814 | -24.80% | -26.24% to -22.88% | -24.80% | 421.98 / 422.00 |
| energy-default, stream | parallel | 570.389 | 490.742 | -16.71% | -18.34% to -13.05% | -26.25% | 139.11 / 139.24 |
| energy-default, stream | serial | 321.943 | 244.444 | -23.40% | -26.70% to -22.61% | -23.55% | 138.87 / 137.63 |
| energy, stream | parallel | 269.655 | 268.152 | +0.19% | -0.94% to +0.41% | -0.96% | 139.09 / 139.04 |
| energy, stream | serial | 235.003 | 237.696 | +1.96% | +1.02% to +3.64% | +2.04% | 137.76 / 138.83 |

CPU columns are separate medians of worker medians. Their quotient need not equal the median paired ratio used for review. Each reference combination has eight independent workers and two timed blocks per comparison after one warmup block. Aotizhongxin and household-energy files are full inputs. Default and original two-token null configurations remain distinct.

## Preparation boundaries

Each boundary combination has 24 independent workers and eight timed blocks per comparison after two warmup blocks. Chunk size equals selected rows in streaming boundary cases; reference streams use 10,000 rows. The reader internal bound is unchanged.

| Rows and injected-null percent | Scope | Policy | Paired CPU change | Paired elapsed change | Candidate CPU flag |
|---|---|---|---:|---:|---|
| 3456, 0 | eager | parallel | +1.08% | +0.84% | within threshold |
| 3456, 0 | eager | serial | +0.26% | +0.29% | within threshold |
| 3456, 0 | stream | parallel | +0.12% | +0.19% | within threshold |
| 3456, 0 | stream | serial | +0.32% | +0.01% | within threshold |
| 3456, 90 | eager | parallel | -0.39% | -0.50% | within threshold |
| 3456, 90 | eager | serial | -0.14% | -0.10% | within threshold |
| 3456, 90 | stream | parallel | -0.26% | -0.19% | within threshold |
| 3456, 90 | stream | serial | +0.06% | -0.35% | within threshold |
| 3457, 0 | eager | parallel | -25.13% | -18.48% | within threshold |
| 3457, 0 | eager | serial | -24.30% | -23.07% | within threshold |
| 3457, 0 | stream | parallel | -25.40% | -22.21% | within threshold |
| 3457, 0 | stream | serial | -31.14% | -28.68% | within threshold |
| 3457, 90 | eager | parallel | -0.24% | +0.16% | within threshold |
| 3457, 90 | eager | serial | +0.88% | +0.85% | within threshold |
| 3457, 90 | stream | parallel | -0.04% | -0.08% | within threshold |
| 3457, 90 | stream | serial | +1.31% | +1.10% | within threshold |
| 3458, 0 | eager | parallel | -36.52% | -28.10% | within threshold |
| 3458, 0 | eager | serial | -34.98% | -33.02% | within threshold |
| 3458, 0 | stream | parallel | -26.57% | -22.11% | within threshold |
| 3458, 0 | stream | serial | -28.69% | -27.30% | within threshold |
| 3458, 90 | eager | parallel | +0.09% | +0.39% | within threshold |
| 3458, 90 | eager | serial | +1.38% | +1.06% | within threshold |
| 3458, 90 | stream | parallel | -0.58% | -0.17% | within threshold |
| 3458, 90 | stream | serial | +1.03% | +0.89% | within threshold |
| 3328, 0 | stream | serial | +0.51% | +0.26% | within threshold |
| 3392, 0 | stream | parallel | +0.10% | -0.42% | within threshold |
