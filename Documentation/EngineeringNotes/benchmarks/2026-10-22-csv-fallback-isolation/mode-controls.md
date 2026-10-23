# mode controls results

CPU is process user-plus-system time. Peak RSS is a process high-water mark, not allocations. Elapsed time is separate.

| Scope and case | Policy | Parent CPU ms | Metadata CPU ms | CPU change | Elapsed before / after ms | Peak before / after MiB |
|---|---|---:|---:|---:|---:|---:|
| eager width-1-rows-257 | parallel | 0.234 | 0.235 | +0.9% | 0.239 / 0.239 | 7.06 / 7.11 |
| eager width-1-rows-257 | serial | 0.229 | 0.234 | +2.0% | 0.231 / 0.236 | 7.05 / 7.09 |
| eager width-2-rows-257 | parallel | 0.253 | 0.246 | -2.6% | 0.251 / 0.250 | 7.09 / 7.12 |
| eager width-2-rows-257 | serial | 0.227 | 0.227 | -0.2% | 0.234 / 0.237 | 7.06 / 7.08 |
| eager width-4-rows-257 | parallel | 0.300 | 0.298 | -0.8% | 0.275 / 0.276 | 7.14 / 7.17 |
| eager width-4-rows-257 | serial | 0.246 | 0.257 | +4.5% | 0.254 / 0.258 | 7.11 / 7.12 |
| eager width-8-rows-257 | parallel | 0.396 | 0.392 | -1.1% | 0.295 / 0.301 | 7.27 / 7.31 |
| eager width-8-rows-257 | serial | 0.276 | 0.283 | +2.7% | 0.282 / 0.294 | 7.17 / 7.22 |
| eager width-18-rows-257 | parallel | 0.705 | 0.674 | -4.4% | 0.363 / 0.374 | 7.55 / 7.55 |
| eager width-18-rows-257 | serial | 0.344 | 0.344 | +0.1% | 0.359 / 0.352 | 7.36 / 7.38 |
| eager width-64-rows-257 | parallel | 1.129 | 1.139 | +0.9% | 0.571 / 0.616 | 8.28 / 8.27 |
| eager width-64-rows-257 | serial | 0.619 | 0.614 | -0.8% | 0.623 / 0.621 | 8.05 / 8.00 |
| eager width-1-rows-32769 | parallel | 0.688 | 0.688 | -0.1% | 0.700 / 0.691 | 8.47 / 8.50 |
| eager width-1-rows-32769 | serial | 0.670 | 0.664 | -0.8% | 0.680 / 0.673 | 8.44 / 8.47 |
| eager width-2-rows-32769 | parallel | 1.151 | 1.151 | -0.1% | 0.906 / 0.917 | 9.14 / 9.19 |
| eager width-2-rows-32769 | serial | 1.088 | 1.085 | -0.2% | 1.094 / 1.092 | 9.11 / 9.11 |
| eager width-4-rows-32769 | parallel | 2.570 | 2.525 | -1.8% | 1.736 / 1.707 | 11.02 / 11.05 |
| eager width-4-rows-32769 | serial | 2.405 | 2.381 | -1.0% | 2.408 / 2.386 | 10.91 / 10.95 |
| eager width-8-rows-32769 | parallel | 5.494 | 5.706 | +3.9% | 2.723 / 2.742 | 14.98 / 14.98 |
| eager width-8-rows-32769 | serial | 4.543 | 4.561 | +0.4% | 4.549 / 4.567 | 14.83 / 14.83 |
| eager width-18-rows-32769 | parallel | 15.370 | 15.175 | -1.3% | 5.774 / 5.683 | 25.51 / 25.55 |
| eager width-18-rows-32769 | serial | 11.743 | 11.652 | -0.8% | 11.764 / 11.716 | 25.17 / 25.19 |
| eager width-64-rows-32769 | parallel | 70.644 | 71.106 | +0.7% | 18.834 / 18.798 | 77.62 / 73.23 |
| eager width-64-rows-32769 | serial | 49.312 | 49.886 | +1.2% | 49.367 / 49.912 | 72.94 / 72.88 |
| eager nullable-0-infer | parallel | 2.600 | 2.632 | +1.2% | 2.111 / 2.147 | 11.75 / 11.77 |
| eager nullable-0-infer | serial | 2.396 | 2.417 | +0.9% | 2.416 / 2.444 | 11.70 / 11.72 |
| eager nullable-50-infer | parallel | 2.990 | 3.005 | +0.5% | 2.308 / 2.348 | 11.58 / 11.58 |
| eager nullable-50-infer | serial | 2.818 | 2.796 | -0.8% | 2.845 / 2.813 | 11.53 / 11.53 |
| eager nullable-90-infer | parallel | 3.201 | 3.153 | -1.5% | 2.379 / 2.370 | 11.59 / 11.61 |
| eager nullable-90-infer | serial | 2.991 | 3.017 | +0.8% | 3.008 / 3.033 | 11.55 / 11.55 |
| eager nullable-50-known | parallel | 2.946 | 2.945 | -0.1% | 2.223 / 2.259 | 11.51 / 11.55 |
| eager nullable-50-known | serial | 2.745 | 2.705 | -1.5% | 2.756 / 2.723 | 11.48 / 11.50 |
| eager nullable-90-known | parallel | 3.221 | 3.137 | -2.6% | 2.365 / 2.318 | 11.58 / 11.56 |
| eager nullable-90-known | serial | 2.954 | 2.935 | -0.7% | 2.976 / 2.953 | 11.50 / 11.52 |
