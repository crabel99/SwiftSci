# Followup

CPU is process user-plus-system time. Every worker validates native output. See [the study record](README.md).

| Scope | Input | Policy | Implementation | CPU ms | Elapsed ms | Peak RSS MiB |
|---|---|---|---|---:|---:|---:|
| eager | all-string-default-nulls-0 | parallel | production | 7.954 | 9.473 | 9.58 |
| eager | all-string-default-nulls-0 | parallel | ascii-prefix | 4.522 | 7.504 | 9.61 |
| eager | all-string-default-nulls-0 | serial | production | 4.568 | 6.542 | 9.06 |
| eager | all-string-default-nulls-0 | serial | ascii-prefix | 3.635 | 4.720 | 9.06 |
| eager | all-string-default-nulls-90 | parallel | production | 6.145 | 4.982 | 9.10 |
| eager | all-string-default-nulls-90 | parallel | ascii-prefix | 4.643 | 4.229 | 9.18 |
| eager | all-string-default-nulls-90 | serial | production | 4.881 | 6.894 | 9.03 |
| eager | all-string-default-nulls-90 | serial | ascii-prefix | 5.412 | 6.378 | 9.09 |
| eager | Aotizhongxin-default | parallel | production | 21.296 | 11.828 | 25.45 |
| eager | Aotizhongxin-default | parallel | ascii-prefix | 19.983 | 10.812 | 25.43 |
| eager | Aotizhongxin-default | serial | production | 16.905 | 22.042 | 23.93 |
| eager | Aotizhongxin-default | serial | ascii-prefix | 16.122 | 21.029 | 24.16 |
| eager | all-string-none-nulls-0 | parallel | production | 4.080 | 6.558 | 9.09 |
| eager | all-string-none-nulls-0 | parallel | ascii-prefix | 4.298 | 4.726 | 9.06 |
| eager | all-string-none-nulls-0 | serial | production | 1.976 | 1.993 | 9.05 |
| eager | all-string-none-nulls-0 | serial | ascii-prefix | 2.045 | 2.067 | 9.03 |
| eager | three-unicode-nulls-0 | parallel | production | 88.112 | 28.368 | 33.07 |
| eager | three-unicode-nulls-0 | parallel | ascii-prefix | 68.165 | 22.362 | 33.40 |
| eager | three-unicode-nulls-0 | serial | production | 65.024 | 65.082 | 32.57 |
| eager | three-unicode-nulls-0 | serial | ascii-prefix | 65.737 | 65.775 | 32.59 |
| eager | energy-default | parallel | production | 514.837 | 200.176 | 422.49 |
| eager | energy-default | parallel | ascii-prefix | 415.853 | 148.610 | 422.50 |
| eager | energy-default | serial | production | 335.594 | 335.712 | 421.99 |
| eager | energy-default | serial | ascii-prefix | 256.404 | 256.600 | 422.03 |
| stream | energy-default | parallel | production | 474.822 | 185.165 | 139.03 |
| stream | energy-default | parallel | ascii-prefix | 372.046 | 136.001 | 139.21 |
| stream | energy-default | serial | production | 308.863 | 309.110 | 138.89 |
| stream | energy-default | serial | ascii-prefix | 235.875 | 236.013 | 138.88 |
