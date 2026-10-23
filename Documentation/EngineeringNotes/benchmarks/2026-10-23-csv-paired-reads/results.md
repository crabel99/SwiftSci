# Paired CPU results

All rows use 60 independent native-hash workers. CPU is process user plus system time. Each worker contributes the ratio of its two implementation medians over 16 reads per label. The table reports the median of those 60 paired ratios. Bootstrap intervals describe that estimator and do not replace the unchanged review threshold.

For `change`, ratios always mean candidate divided by cleanup, including the reversed-module experiment. For controls, ratios mean label A divided by label B. Controls use the same source. Independent table modes deliberately permit different native table layouts. Elapsed time stays separate.

| Stage | Table | Rows | Policy | Comparison | CPU change | Bootstrap 95% interval for CPU change | Elapsed change | CPU review |
|---|---|---:|---|---|---:|---|---:|---|
| paired | shared | 3392 | parallel | same | +0.08% | -0.05% to +0.23% | -0.12% | within threshold |
| paired | shared | 3392 | parallel | namespace | +1.91% | +1.69% to +2.42% | +2.16% | within threshold |
| paired | shared | 3392 | parallel | change | +0.25% | +0.00% to +0.54% | +0.47% | within threshold |
| paired | shared | 3392 | serial | same | +0.08% | -0.13% to +0.32% | +0.13% | within threshold |
| paired | shared | 3392 | serial | namespace | +0.21% | -0.02% to +0.46% | +0.15% | within threshold |
| paired | shared | 3392 | serial | change | +0.11% | -0.08% to +0.38% | +0.20% | within threshold |
| paired | shared | 3456 | parallel | same | -0.07% | -0.15% to +0.07% | -0.04% | within threshold |
| paired | shared | 3456 | parallel | namespace | +2.20% | +1.96% to +2.65% | +1.91% | within threshold |
| paired | shared | 3456 | parallel | change | +0.12% | -0.11% to +0.52% | +0.15% | within threshold |
| table-control | shared | 3392 | parallel | same | -0.06% | -0.32% to +0.20% | -0.03% | within threshold |
| table-control | shared | 3392 | parallel | namespace | -0.56% | -0.79% to -0.09% | -0.45% | within threshold |
| table-control | shared | 3392 | parallel | change | -0.43% | -0.78% to +0.17% | -0.23% | within threshold |
| table-control | independent | 3392 | parallel | same | +0.00% | -0.25% to +0.24% | +0.08% | within threshold |
| table-control | independent | 3392 | parallel | namespace | +1.16% | -11.23% to +14.08% | +0.71% | within threshold |
| table-control | independent | 3392 | parallel | change | -11.94% | -28.09% to +1.70% | -9.12% | within threshold |
| table-control | shared | 3392 | serial | same | -0.24% | -0.30% to -0.05% | -0.11% | within threshold |
| table-control | shared | 3392 | serial | namespace | -0.05% | -0.30% to +0.29% | -0.02% | within threshold |
| table-control | shared | 3392 | serial | change | +0.12% | -0.11% to +0.35% | +0.12% | within threshold |
| table-control | independent | 3392 | serial | same | -0.04% | -0.23% to +0.09% | +0.07% | within threshold |
| table-control | independent | 3392 | serial | namespace | -10.90% | -21.00% to -0.45% | -10.66% | flag |
| table-control | independent | 3392 | serial | change | -1.61% | -12.03% to +4.76% | -1.01% | within threshold |
| table-control | shared | 3456 | parallel | same | -0.04% | -0.25% to +0.18% | -0.19% | within threshold |
| table-control | shared | 3456 | parallel | namespace | -0.85% | -1.09% to -0.51% | -1.08% | within threshold |
| table-control | shared | 3456 | parallel | change | -0.56% | -0.94% to +0.05% | -0.56% | within threshold |
| table-control | independent | 3456 | parallel | same | +0.09% | -0.26% to +0.24% | -0.13% | within threshold |
| table-control | independent | 3456 | parallel | namespace | +13.38% | -0.33% to +23.36% | +11.78% | flag |
| table-control | independent | 3456 | parallel | change | -0.69% | -12.09% to +12.77% | -1.11% | within threshold |
| reverse-control | shared | 3392 | parallel | same | -0.05% | -0.16% to +0.10% | -0.26% | within threshold |
| reverse-control | shared | 3392 | parallel | namespace | -0.01% | -0.89% to +0.41% | -0.33% | within threshold |
| reverse-control | shared | 3392 | parallel | change | +0.42% | +0.04% to +1.05% | +0.50% | within threshold |
| reverse-control | independent | 3392 | parallel | same | -0.03% | -0.36% to +0.23% | -0.18% | within threshold |
| reverse-control | independent | 3392 | parallel | namespace | +4.90% | -1.84% to +23.36% | +3.78% | within threshold |
| reverse-control | independent | 3392 | parallel | change | +0.00% | -18.59% to +9.97% | -0.03% | within threshold |
| reverse-control | shared | 3392 | serial | same | +0.11% | -0.10% to +0.31% | +0.24% | within threshold |
| reverse-control | shared | 3392 | serial | namespace | -0.20% | -0.41% to +0.07% | -0.18% | within threshold |
| reverse-control | shared | 3392 | serial | change | +0.54% | +0.35% to +0.77% | +0.45% | within threshold |
| reverse-control | independent | 3392 | serial | same | +0.13% | -0.06% to +0.47% | +0.23% | within threshold |
| reverse-control | independent | 3392 | serial | namespace | -14.47% | -28.70% to -2.74% | -13.91% | flag |
| reverse-control | independent | 3392 | serial | change | +9.45% | -2.14% to +24.42% | +9.41% | within threshold |
| reverse-control | shared | 3456 | parallel | same | +0.08% | -0.12% to +0.30% | +0.02% | within threshold |
| reverse-control | shared | 3456 | parallel | namespace | -0.39% | -1.19% to +0.15% | -0.31% | within threshold |
| reverse-control | shared | 3456 | parallel | change | +0.36% | -0.04% to +1.07% | +0.06% | within threshold |
| reverse-control | independent | 3456 | parallel | same | +0.10% | +0.00% to +0.23% | +0.14% | within threshold |
| reverse-control | independent | 3456 | parallel | namespace | +4.43% | -4.70% to +21.60% | +3.85% | within threshold |
| reverse-control | independent | 3456 | parallel | change | +2.23% | -18.40% to +20.94% | +1.89% | within threshold |
