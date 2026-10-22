# Setup controls

CPU is process user-plus-system time. Every worker validates native output. See [the study record](README.md).

| Scope | Input | Policy | Implementation | CPU ms | Elapsed ms | Peak RSS MiB |
|---|---|---|---|---:|---:|---:|
| eager | setup-8-0 | parallel | production | 0.252 | 0.272 | 7.05 |
| eager | setup-8-0 | parallel | ascii-prefix | 0.241 | 0.257 | 6.98 |
| eager | setup-8-0 | serial | production | 0.234 | 0.275 | 7.00 |
| eager | setup-8-0 | serial | ascii-prefix | 0.230 | 0.266 | 6.97 |
| eager | setup-8-10 | parallel | production | 0.267 | 0.291 | 7.02 |
| eager | setup-8-10 | parallel | ascii-prefix | 0.244 | 0.289 | 7.05 |
| eager | setup-8-10 | serial | production | 0.221 | 0.249 | 7.00 |
| eager | setup-8-10 | serial | ascii-prefix | 0.234 | 0.266 | 7.03 |
| eager | setup-8-2048 | parallel | production | 0.424 | 0.465 | 7.45 |
| eager | setup-8-2048 | parallel | ascii-prefix | 0.500 | 0.528 | 7.48 |
| eager | setup-8-2048 | serial | production | 0.407 | 0.437 | 7.44 |
| eager | setup-8-2048 | serial | ascii-prefix | 0.476 | 0.504 | 7.47 |
| eager | setup-8-32768 | parallel | production | 3.026 | 3.066 | 12.34 |
| eager | setup-8-32768 | parallel | ascii-prefix | 4.127 | 4.165 | 12.36 |
| eager | setup-8-32768 | serial | production | 3.005 | 3.047 | 12.38 |
| eager | setup-8-32768 | serial | ascii-prefix | 4.105 | 4.210 | 12.38 |
| eager | setup-257-0 | parallel | production | 0.267 | 0.267 | 7.10 |
| eager | setup-257-0 | parallel | ascii-prefix | 0.276 | 0.282 | 7.11 |
| eager | setup-257-0 | serial | production | 0.248 | 0.253 | 7.08 |
| eager | setup-257-0 | serial | ascii-prefix | 0.245 | 0.245 | 7.05 |
| eager | setup-257-10 | parallel | production | 0.331 | 0.318 | 7.16 |
| eager | setup-257-10 | parallel | ascii-prefix | 0.298 | 0.289 | 7.14 |
| eager | setup-257-10 | serial | production | 0.294 | 0.302 | 7.09 |
| eager | setup-257-10 | serial | ascii-prefix | 0.284 | 0.292 | 7.11 |
| eager | setup-257-2048 | parallel | production | 0.523 | 0.520 | 7.55 |
| eager | setup-257-2048 | parallel | ascii-prefix | 0.570 | 0.563 | 7.58 |
| eager | setup-257-2048 | serial | production | 0.478 | 0.486 | 7.50 |
| eager | setup-257-2048 | serial | ascii-prefix | 0.546 | 0.546 | 7.55 |
| eager | setup-257-32768 | parallel | production | 3.271 | 3.253 | 12.45 |
| eager | setup-257-32768 | parallel | ascii-prefix | 4.294 | 4.293 | 12.49 |
| eager | setup-257-32768 | serial | production | 3.225 | 3.229 | 12.42 |
| eager | setup-257-32768 | serial | ascii-prefix | 4.178 | 4.175 | 12.41 |
