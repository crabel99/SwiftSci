# Refined setup

CPU is process user-plus-system time. Every worker validates native output. See [the study record](README.md).

| Scope | Input | Policy | Implementation | CPU ms | Elapsed ms | Peak RSS MiB |
|---|---|---|---|---:|---:|---:|
| eager | setup-8-0 | parallel | production | 0.253 | 0.252 | 7.05 |
| eager | setup-8-0 | parallel | required-prep | 0.262 | 0.258 | 7.05 |
| eager | setup-8-0 | parallel | prefix-required-prep | 0.253 | 0.251 | 7.03 |
| eager | setup-8-0 | serial | production | 0.227 | 0.225 | 7.00 |
| eager | setup-8-0 | serial | required-prep | 0.224 | 0.228 | 7.00 |
| eager | setup-8-0 | serial | prefix-required-prep | 0.227 | 0.234 | 6.98 |
| eager | setup-8-10 | parallel | production | 0.248 | 0.242 | 7.03 |
| eager | setup-8-10 | parallel | required-prep | 0.240 | 0.240 | 7.06 |
| eager | setup-8-10 | parallel | prefix-required-prep | 0.246 | 0.245 | 7.05 |
| eager | setup-8-10 | serial | production | 0.233 | 0.236 | 7.00 |
| eager | setup-8-10 | serial | required-prep | 0.229 | 0.239 | 7.01 |
| eager | setup-8-10 | serial | prefix-required-prep | 0.227 | 0.227 | 7.02 |
| eager | setup-8-2048 | parallel | production | 0.462 | 0.459 | 7.48 |
| eager | setup-8-2048 | parallel | required-prep | 0.262 | 0.261 | 7.34 |
| eager | setup-8-2048 | parallel | prefix-required-prep | 0.368 | 0.353 | 7.36 |
| eager | setup-8-2048 | serial | production | 0.427 | 0.426 | 7.44 |
| eager | setup-8-2048 | serial | required-prep | 0.242 | 0.238 | 7.30 |
| eager | setup-8-2048 | serial | prefix-required-prep | 0.317 | 0.317 | 7.31 |
| eager | setup-8-32768 | parallel | production | 3.152 | 3.161 | 12.38 |
| eager | setup-8-32768 | parallel | required-prep | 0.302 | 0.296 | 10.83 |
| eager | setup-8-32768 | parallel | prefix-required-prep | 1.393 | 1.393 | 10.84 |
| eager | setup-8-32768 | serial | production | 3.132 | 3.144 | 12.36 |
| eager | setup-8-32768 | serial | required-prep | 0.292 | 0.289 | 10.80 |
| eager | setup-8-32768 | serial | prefix-required-prep | 1.365 | 1.369 | 10.82 |
| eager | setup-257-0 | parallel | production | 0.268 | 0.263 | 7.11 |
| eager | setup-257-0 | parallel | required-prep | 0.278 | 0.274 | 7.12 |
| eager | setup-257-0 | parallel | prefix-required-prep | 0.281 | 0.280 | 7.09 |
| eager | setup-257-0 | serial | production | 0.258 | 0.264 | 7.08 |
| eager | setup-257-0 | serial | required-prep | 0.252 | 0.259 | 7.08 |
| eager | setup-257-0 | serial | prefix-required-prep | 0.260 | 0.266 | 7.06 |
| eager | setup-257-10 | parallel | production | 0.367 | 0.360 | 7.18 |
| eager | setup-257-10 | parallel | required-prep | 0.370 | 0.367 | 7.18 |
| eager | setup-257-10 | parallel | prefix-required-prep | 0.329 | 0.323 | 7.12 |
| eager | setup-257-10 | serial | production | 0.317 | 0.324 | 7.12 |
| eager | setup-257-10 | serial | required-prep | 0.296 | 0.303 | 7.09 |
| eager | setup-257-10 | serial | prefix-required-prep | 0.293 | 0.297 | 7.07 |
| eager | setup-257-2048 | parallel | production | 0.529 | 0.515 | 7.56 |
| eager | setup-257-2048 | parallel | required-prep | 0.326 | 0.320 | 7.42 |
| eager | setup-257-2048 | parallel | prefix-required-prep | 0.369 | 0.367 | 7.39 |
| eager | setup-257-2048 | serial | production | 0.483 | 0.486 | 7.50 |
| eager | setup-257-2048 | serial | required-prep | 0.294 | 0.298 | 7.39 |
| eager | setup-257-2048 | serial | prefix-required-prep | 0.342 | 0.343 | 7.38 |
| eager | setup-257-32768 | parallel | production | 3.231 | 3.219 | 12.48 |
| eager | setup-257-32768 | parallel | required-prep | 0.429 | 0.414 | 10.95 |
| eager | setup-257-32768 | parallel | prefix-required-prep | 1.488 | 1.476 | 10.93 |
| eager | setup-257-32768 | serial | production | 3.256 | 3.324 | 12.55 |
| eager | setup-257-32768 | serial | required-prep | 0.418 | 0.422 | 10.93 |
| eager | setup-257-32768 | serial | prefix-required-prep | 1.429 | 1.474 | 10.94 |
