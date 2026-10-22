# mode controls results

CPU is process user-plus-system time. Peak RSS is a whole-process high-water mark. Elapsed time is separate.

| Scope / case | Policy / candidate | CPU before ms | CPU after ms | Change | Elapsed before / after ms | Peak before / after MiB |
|---|---|---:|---:|---:|---:|---:|
| eager / width-1-rows-257 |  parallel | 0.215 | 0.220 | +1.9% | 0.235 / 0.241 | 7.05 / 7.06 |
| eager / width-1-rows-257 |  serial | 0.211 | 0.212 | +0.7% | 0.229 / 0.232 | 7.05 / 7.05 |
| eager / width-2-rows-257 |  parallel | 0.239 | 0.240 | +0.2% | 0.252 / 0.254 | 7.08 / 7.06 |
| eager / width-2-rows-257 |  serial | 0.222 | 0.221 | -0.5% | 0.242 / 0.241 | 7.06 / 7.05 |
| eager / width-4-rows-257 |  parallel | 0.295 | 0.289 | -2.2% | 0.284 / 0.278 | 7.14 / 7.14 |
| eager / width-4-rows-257 |  serial | 0.239 | 0.239 | -0.2% | 0.260 / 0.259 | 7.09 / 7.09 |
| eager / width-8-rows-257 |  parallel | 0.400 | 0.391 | -2.2% | 0.304 / 0.304 | 7.27 / 7.31 |
| eager / width-8-rows-257 |  serial | 0.264 | 0.262 | -0.6% | 0.283 / 0.284 | 7.16 / 7.20 |
| eager / width-18-rows-257 |  parallel | 0.641 | 0.606 | -5.5% | 0.378 / 0.372 | 7.52 / 7.49 |
| eager / width-18-rows-257 |  serial | 0.330 | 0.326 | -1.2% | 0.349 / 0.345 | 7.36 / 7.34 |
| eager / width-64-rows-257 |  parallel | 1.175 | 1.156 | -1.6% | 0.643 / 0.647 | 8.27 / 8.27 |
| eager / width-64-rows-257 |  serial | 0.589 | 0.591 | +0.3% | 0.608 / 0.609 | 8.06 / 8.05 |
| eager / width-1-rows-32769 |  parallel | 0.651 | 0.652 | +0.1% | 0.676 / 0.675 | 8.44 / 8.44 |
| eager / width-1-rows-32769 |  serial | 0.633 | 0.638 | +0.7% | 0.654 / 0.657 | 8.44 / 8.44 |
| eager / width-2-rows-32769 |  parallel | 1.095 | 1.099 | +0.4% | 0.875 / 0.884 | 9.11 / 9.11 |
| eager / width-2-rows-32769 |  serial | 1.028 | 1.024 | -0.5% | 1.049 / 1.037 | 9.09 / 9.08 |
| eager / width-4-rows-32769 |  parallel | 2.458 | 2.448 | -0.4% | 1.643 / 1.646 | 10.98 / 10.98 |
| eager / width-4-rows-32769 |  serial | 2.267 | 2.227 | -1.8% | 2.284 / 2.247 | 10.92 / 10.89 |
| eager / width-8-rows-32769 |  parallel | 5.341 | 5.287 | -1.0% | 2.614 / 2.630 | 14.95 / 14.97 |
| eager / width-8-rows-32769 |  serial | 4.277 | 4.270 | -0.2% | 4.319 / 4.290 | 14.80 / 14.83 |
| eager / width-18-rows-32769 |  parallel | 14.265 | 15.097 | +5.8% | 5.165 / 5.394 | 26.41 / 26.41 |
| eager / width-18-rows-32769 |  serial | 11.082 | 11.081 | -0.0% | 11.134 / 11.162 | 25.17 / 25.19 |
| eager / width-64-rows-32769 |  parallel | 67.849 | 68.585 | +1.1% | 18.159 / 18.202 | 77.59 / 75.41 |
| eager / width-64-rows-32769 |  serial | 44.904 | 44.900 | -0.0% | 44.939 / 44.940 | 72.91 / 72.88 |
| eager / nullable-0-infer |  parallel | 2.583 | 2.604 | +0.9% | 2.102 / 2.117 | 11.75 / 11.75 |
| eager / nullable-0-infer |  serial | 2.397 | 2.416 | +0.8% | 2.421 / 2.446 | 11.70 / 11.70 |
| eager / nullable-50-infer |  parallel | 2.986 | 2.980 | -0.2% | 2.290 / 2.309 | 11.58 / 11.58 |
| eager / nullable-50-infer |  serial | 2.788 | 2.789 | +0.1% | 2.804 / 2.803 | 11.53 / 11.53 |
| eager / nullable-90-infer |  parallel | 3.139 | 3.171 | +1.0% | 2.343 / 2.359 | 11.59 / 11.59 |
| eager / nullable-90-infer |  serial | 2.888 | 2.949 | +2.1% | 2.905 / 2.968 | 11.55 / 11.55 |
| eager / nullable-50-known |  parallel | 2.929 | 2.872 | -1.9% | 2.218 / 2.206 | 11.53 / 11.55 |
| eager / nullable-50-known |  serial | 2.692 | 2.703 | +0.4% | 2.710 / 2.719 | 11.48 / 11.48 |
| eager / nullable-90-known |  parallel | 3.120 | 3.112 | -0.2% | 2.282 / 2.293 | 11.55 / 11.56 |
| eager / nullable-90-known |  serial | 2.867 | 2.880 | +0.4% | 2.883 / 2.896 | 11.50 / 11.50 |
