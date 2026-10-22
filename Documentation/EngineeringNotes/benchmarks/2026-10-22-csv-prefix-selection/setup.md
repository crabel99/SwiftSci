# setup results

CPU is process user-plus-system time. Peak RSS is a whole-process high-water mark. Elapsed time is separate.

| Scope / case | Policy / candidate | CPU before ms | CPU after ms | Change | Elapsed before / after ms | Peak before / after MiB |
|---|---|---:|---:|---:|---:|---:|
| eager / setup-8-0 | parallel production | 0.222 | 0.230 | +3.4% | 0.226 / 0.226 | 7.03 / 7.05 |
| eager / setup-8-0 | parallel byte-only | 0.222 | 0.231 | +3.8% | 0.226 / 0.234 | 7.03 / 7.03 |
| eager / setup-8-0 | serial production | 0.211 | 0.215 | +1.7% | 0.219 / 0.222 | 7.00 / 7.00 |
| eager / setup-8-0 | serial byte-only | 0.211 | 0.208 | -1.7% | 0.219 / 0.214 | 7.00 / 6.98 |
| eager / setup-8-10 | parallel production | 0.228 | 0.232 | +1.8% | 0.232 / 0.233 | 7.06 / 7.08 |
| eager / setup-8-10 | parallel byte-only | 0.228 | 0.230 | +0.7% | 0.232 / 0.230 | 7.06 / 7.03 |
| eager / setup-8-10 | serial production | 0.208 | 0.205 | -1.4% | 0.215 / 0.213 | 7.00 / 7.03 |
| eager / setup-8-10 | serial byte-only | 0.208 | 0.207 | -0.7% | 0.215 / 0.216 | 7.00 / 7.00 |
| eager / setup-8-2048 | parallel production | 0.234 | 0.225 | -3.9% | 0.233 / 0.224 | 7.34 / 7.33 |
| eager / setup-8-2048 | parallel byte-only | 0.234 | 0.225 | -3.6% | 0.233 / 0.225 | 7.34 / 7.34 |
| eager / setup-8-2048 | serial production | 0.207 | 0.208 | +0.7% | 0.213 / 0.210 | 7.30 / 7.31 |
| eager / setup-8-2048 | serial byte-only | 0.207 | 0.206 | -0.2% | 0.213 / 0.214 | 7.30 / 7.30 |
| eager / setup-8-32768 | parallel production | 0.269 | 0.260 | -3.5% | 0.263 / 0.254 | 10.83 / 10.81 |
| eager / setup-8-32768 | parallel byte-only | 0.269 | 0.255 | -5.2% | 0.263 / 0.253 | 10.83 / 10.81 |
| eager / setup-8-32768 | serial production | 0.242 | 0.242 | +0.2% | 0.245 / 0.248 | 10.81 / 10.81 |
| eager / setup-8-32768 | serial byte-only | 0.242 | 0.241 | -0.2% | 0.245 / 0.242 | 10.81 / 10.78 |
| eager / setup-257-0 | parallel production | 0.273 | 0.260 | -4.6% | 0.270 / 0.261 | 7.09 / 7.09 |
| eager / setup-257-0 | parallel byte-only | 0.273 | 0.259 | -5.1% | 0.270 / 0.256 | 7.09 / 7.09 |
| eager / setup-257-0 | serial production | 0.235 | 0.233 | -1.1% | 0.238 / 0.239 | 7.08 / 7.05 |
| eager / setup-257-0 | serial byte-only | 0.235 | 0.229 | -2.8% | 0.238 / 0.234 | 7.08 / 7.05 |
| eager / setup-257-10 | parallel production | 0.323 | 0.306 | -5.1% | 0.314 / 0.302 | 7.14 / 7.11 |
| eager / setup-257-10 | parallel byte-only | 0.323 | 0.289 | -10.4% | 0.314 / 0.291 | 7.14 / 7.11 |
| eager / setup-257-10 | serial production | 0.280 | 0.254 | -9.3% | 0.286 / 0.259 | 7.09 / 7.08 |
| eager / setup-257-10 | serial byte-only | 0.280 | 0.258 | -7.9% | 0.286 / 0.264 | 7.09 / 7.08 |
| eager / setup-257-2048 | parallel production | 0.311 | 0.306 | -1.8% | 0.304 / 0.302 | 7.42 / 7.41 |
| eager / setup-257-2048 | parallel byte-only | 0.311 | 0.302 | -3.0% | 0.304 / 0.296 | 7.42 / 7.42 |
| eager / setup-257-2048 | serial production | 0.277 | 0.270 | -2.5% | 0.280 / 0.274 | 7.38 / 7.34 |
| eager / setup-257-2048 | serial byte-only | 0.277 | 0.269 | -2.9% | 0.280 / 0.272 | 7.38 / 7.36 |
| eager / setup-257-32768 | parallel production | 0.341 | 0.330 | -3.1% | 0.329 / 0.321 | 10.91 / 10.86 |
| eager / setup-257-32768 | parallel byte-only | 0.341 | 0.327 | -4.0% | 0.329 / 0.317 | 10.91 / 10.89 |
| eager / setup-257-32768 | serial production | 0.321 | 0.347 | +8.1% | 0.331 / 0.349 | 10.85 / 10.83 |
| eager / setup-257-32768 | serial byte-only | 0.321 | 0.323 | +0.6% | 0.331 / 0.321 | 10.85 / 10.86 |
