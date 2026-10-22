# Fresh and steady edge controls

Steady workers run two warmups and five recorded complete reads. Worker medians are combined only within the same mode and conversion policy. [Study record](README.md).

| Input | Policy | Mode | Implementation | Workers | Recorded reads | CPU ms | Elapsed ms | Peak RSS MiB |
|---|---|---|---|---:|---:|---:|---:|---:|
| all-string-default-nulls-90 | parallel | fresh | production | 32 | 32 | 3.281 | 2.266 | 9.06 |
| all-string-default-nulls-90 | parallel | timing | production | 32 | 160 | 3.009 | 2.060 | 9.88 |
| all-string-default-nulls-90 | serial | fresh | production | 32 | 32 | 3.249 | 3.256 | 9.00 |
| all-string-default-nulls-90 | serial | timing | production | 32 | 160 | 3.005 | 3.026 | 9.77 |
| all-string-default-nulls-90 | parallel | fresh | ascii-prefix | 32 | 32 | 2.490 | 2.054 | 9.08 |
| all-string-default-nulls-90 | parallel | timing | ascii-prefix | 32 | 160 | 2.213 | 1.796 | 9.83 |
| all-string-default-nulls-90 | serial | fresh | ascii-prefix | 32 | 32 | 2.459 | 2.460 | 9.03 |
| all-string-default-nulls-90 | serial | timing | ascii-prefix | 32 | 160 | 2.203 | 2.222 | 9.75 |
| all-string-none-nulls-0 | parallel | fresh | production | 32 | 32 | 1.990 | 1.555 | 9.08 |
| all-string-none-nulls-0 | parallel | timing | production | 32 | 160 | 1.708 | 1.303 | 10.02 |
| all-string-none-nulls-0 | serial | fresh | production | 32 | 32 | 1.923 | 1.926 | 9.03 |
| all-string-none-nulls-0 | serial | timing | production | 32 | 160 | 1.681 | 1.698 | 9.80 |
| all-string-none-nulls-0 | parallel | fresh | ascii-prefix | 32 | 32 | 2.052 | 1.584 | 9.06 |
| all-string-none-nulls-0 | parallel | timing | ascii-prefix | 32 | 160 | 1.772 | 1.332 | 9.91 |
| all-string-none-nulls-0 | serial | fresh | ascii-prefix | 32 | 32 | 1.994 | 1.991 | 9.00 |
| all-string-none-nulls-0 | serial | timing | ascii-prefix | 32 | 160 | 1.762 | 1.773 | 9.74 |
