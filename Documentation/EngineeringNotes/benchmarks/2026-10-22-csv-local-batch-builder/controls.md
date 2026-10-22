# Complete resource controls

CPU means process user-plus-system time per correct result. Each policy compares with the same parent policy. See the [study methods](README.md).

## Width and numeric null controls

| Input and schema | Policy | CPU ms, parent to final | CPU change | Elapsed ms, parent to final | Peak RSS MiB, parent to final |
|---|---|---:|---:|---:|---:|
| width-1-rows-257 | parallel | 0.255 to 0.265 | +4.1% | 0.277 to 0.283 | 7.08 to 7.05 |
| width-1-rows-257 | serial | 0.236 to 0.235 | -0.2% | 0.275 to 0.274 | 7.06 to 7.05 |
| width-2-rows-257 | parallel | 0.273 to 0.263 | -3.7% | 0.283 to 0.286 | 7.11 to 7.08 |
| width-2-rows-257 | serial | 0.252 to 0.241 | -4.0% | 0.267 to 0.268 | 7.09 to 7.06 |
| width-4-rows-257 | parallel | 0.343 to 0.335 | -2.5% | 0.320 to 0.331 | 7.19 to 7.14 |
| width-4-rows-257 | serial | 0.273 to 0.281 | +3.1% | 0.288 to 0.295 | 7.14 to 7.09 |
| width-8-rows-257 | parallel | 0.431 to 0.436 | +1.0% | 0.341 to 0.342 | 7.31 to 7.26 |
| width-8-rows-257 | serial | 0.329 to 0.303 | -7.8% | 0.351 to 0.338 | 7.22 to 7.16 |
| width-18-rows-257 | parallel | 0.681 to 0.638 | -6.3% | 0.442 to 0.434 | 7.55 to 7.52 |
| width-18-rows-257 | serial | 0.406 to 0.408 | +0.5% | 0.423 to 0.435 | 7.39 to 7.36 |
| width-64-rows-257 | parallel | 1.191 to 1.147 | -3.7% | 0.728 to 0.718 | 8.27 to 8.27 |
| width-64-rows-257 | serial | 0.688 to 0.682 | -0.8% | 0.708 to 0.696 | 8.05 to 8.06 |
| width-1-rows-32769 | parallel | 0.685 to 0.698 | +1.8% | 0.707 to 0.730 | 8.48 to 8.44 |
| width-1-rows-32769 | serial | 0.675 to 0.679 | +0.5% | 0.697 to 0.705 | 8.47 to 8.44 |
| width-2-rows-32769 | parallel | 1.165 to 1.153 | -1.0% | 0.945 to 0.938 | 9.14 to 9.11 |
| width-2-rows-32769 | serial | 1.095 to 1.089 | -0.5% | 1.119 to 1.107 | 9.12 to 9.09 |
| width-4-rows-32769 | parallel | 2.865 to 2.714 | -5.3% | 1.995 to 1.884 | 11.02 to 10.98 |
| width-4-rows-32769 | serial | 2.689 to 2.571 | -4.4% | 2.752 to 2.608 | 10.94 to 10.91 |
| width-8-rows-32769 | parallel | 5.843 to 5.782 | -1.1% | 2.978 to 2.926 | 14.98 to 14.97 |
| width-8-rows-32769 | serial | 4.833 to 4.764 | -1.4% | 4.879 to 4.802 | 14.83 to 14.80 |
| width-18-rows-32769 | parallel | 16.758 to 15.431 | -7.9% | 6.167 to 5.702 | 25.53 to 25.48 |
| width-18-rows-32769 | serial | 11.487 to 11.159 | -2.9% | 11.526 to 11.208 | 25.20 to 25.17 |
| width-64-rows-32769 | parallel | 87.384 to 86.224 | -1.3% | 21.717 to 21.944 | 75.46 to 73.25 |
| width-64-rows-32769 | serial | 58.051 to 56.362 | -2.9% | 58.070 to 56.390 | 72.91 to 72.94 |
| nullable-0-infer | parallel | 3.322 to 3.305 | -0.5% | 2.738 to 2.733 | 11.80 to 11.78 |
| nullable-0-infer | serial | 3.135 to 3.180 | +1.5% | 3.148 to 3.187 | 11.70 to 11.70 |
| nullable-50-infer | parallel | 4.130 to 3.940 | -4.6% | 3.150 to 3.023 | 11.66 to 11.61 |
| nullable-50-infer | serial | 3.789 to 3.789 | +0.0% | 3.782 to 3.784 | 11.55 to 11.55 |
| nullable-90-infer | parallel | 4.254 to 4.159 | -2.2% | 3.262 to 3.144 | 11.62 to 11.61 |
| nullable-90-infer | serial | 4.115 to 4.116 | +0.0% | 4.138 to 4.145 | 11.55 to 11.55 |
| nullable-50-known | parallel | 3.697 to 3.569 | -3.5% | 2.824 to 2.729 | 11.58 to 11.53 |
| nullable-50-known | serial | 3.432 to 3.480 | +1.4% | 3.449 to 3.497 | 11.52 to 11.50 |
| nullable-90-known | parallel | 5.184 to 5.096 | -1.7% | 3.803 to 3.746 | 11.67 to 11.85 |
| nullable-90-known | serial | 5.040 to 4.780 | -5.1% | 5.033 to 4.782 | 11.56 to 11.50 |

## Text controls

| Input and schema | Policy | CPU ms, parent to final | CPU change | Elapsed ms, parent to final | Peak RSS MiB, parent to final |
|---|---|---:|---:|---:|---:|
| none-nulls-0 | parallel | 2.373 to 2.296 | -3.3% | 2.100 to 2.041 | 9.11 to 9.06 |
| none-nulls-0 | serial | 2.244 to 2.208 | -1.6% | 2.290 to 2.255 | 9.05 to 9.03 |
| one-nulls-0 | parallel | 2.483 to 2.352 | -5.3% | 2.252 to 2.130 | 9.11 to 9.10 |
| one-nulls-0 | serial | 2.302 to 2.332 | +1.3% | 2.442 to 2.360 | 9.05 to 9.05 |
| one-nulls-50 | parallel | 2.114 to 2.034 | -3.8% | 1.937 to 1.858 | 9.12 to 9.06 |
| one-nulls-50 | serial | 2.051 to 1.944 | -5.2% | 2.095 to 1.969 | 9.05 to 9.02 |
| pair-nulls-0 | parallel | 2.009 to 2.011 | +0.1% | 1.854 to 1.811 | 9.09 to 9.08 |
| pair-nulls-0 | serial | 1.970 to 1.917 | -2.6% | 1.988 to 1.940 | 9.05 to 9.05 |
| pair-nulls-50 | parallel | 2.045 to 1.993 | -2.5% | 1.854 to 1.809 | 9.11 to 9.11 |
| pair-nulls-50 | serial | 1.974 to 1.897 | -3.9% | 1.990 to 1.908 | 9.03 to 9.00 |
| four-nulls-0 | parallel | 4.178 to 4.136 | -1.0% | 2.851 to 2.817 | 9.14 to 9.11 |
| four-nulls-0 | serial | 4.039 to 4.162 | +3.1% | 4.047 to 4.174 | 9.06 to 9.06 |
| four-nulls-50 | parallel | 4.186 to 3.994 | -4.6% | 2.792 to 2.655 | 9.14 to 9.08 |
| four-nulls-50 | serial | 4.175 to 4.066 | -2.6% | 4.205 to 4.073 | 9.05 to 9.00 |
| default-nulls-0 | parallel | 3.602 to 3.646 | +1.2% | 3.412 to 3.457 | 9.14 to 9.11 |
| default-nulls-0 | serial | 3.303 to 3.606 | +9.2% | 3.366 to 3.650 | 9.06 to 9.05 |
| default-nulls-50 | parallel | 3.410 to 3.437 | +0.8% | 3.197 to 3.241 | 9.16 to 9.11 |
| default-nulls-50 | serial | 3.297 to 3.276 | -0.7% | 3.338 to 3.421 | 9.08 to 9.03 |
| default-nulls-90 | parallel | 2.563 to 2.583 | +0.8% | 2.450 to 2.407 | 9.14 to 9.06 |
| default-nulls-90 | serial | 2.450 to 2.551 | +4.1% | 2.483 to 2.620 | 9.06 to 9.02 |
| sixteen-nulls-0 | parallel | 4.199 to 4.199 | -0.0% | 2.844 to 2.881 | 9.14 to 9.11 |
| sixteen-nulls-0 | serial | 4.226 to 4.135 | -2.2% | 4.245 to 4.149 | 9.06 to 9.05 |
| sixteen-nulls-50 | parallel | 4.304 to 4.258 | -1.1% | 2.945 to 2.890 | 9.23 to 9.17 |
| sixteen-nulls-50 | serial | 4.222 to 4.232 | +0.2% | 4.266 to 4.244 | 9.14 to 9.09 |
| seventeen-nulls-0 | parallel | 4.048 to 3.974 | -1.8% | 3.481 to 3.372 | 9.14 to 9.11 |
| seventeen-nulls-0 | serial | 4.322 to 3.583 | -17.1% | 4.350 to 3.595 | 9.06 to 9.06 |
| seventeen-nulls-50 | parallel | 3.999 to 4.188 | +4.7% | 3.364 to 3.547 | 9.23 to 9.19 |
| seventeen-nulls-50 | serial | 4.023 to 4.083 | +1.5% | 4.176 to 4.130 | 9.17 to 9.14 |
| large-nulls-0 | parallel | 30.346 to 32.025 | +5.5% | 27.511 to 29.756 | 9.62 to 9.61 |
| large-nulls-0 | serial | 31.094 to 33.263 | +7.0% | 31.247 to 33.310 | 9.56 to 9.56 |
| large-nulls-50 | parallel | 20.890 to 21.895 | +4.8% | 19.597 to 20.377 | 9.73 to 9.72 |
| large-nulls-50 | serial | 20.747 to 22.346 | +7.7% | 20.760 to 22.387 | 9.69 to 9.67 |
| all-string-none-nulls-0 | parallel | 1.901 to 1.882 | -1.0% | 1.476 to 1.482 | 9.11 to 9.05 |
| all-string-none-nulls-0 | serial | 1.827 to 1.805 | -1.2% | 1.842 to 1.841 | 9.03 to 9.02 |
| all-string-one-nulls-0 | parallel | 2.310 to 2.207 | -4.5% | 1.824 to 1.784 | 9.12 to 9.06 |
| all-string-one-nulls-0 | serial | 2.209 to 2.178 | -1.4% | 2.234 to 2.192 | 9.05 to 9.03 |
| all-string-one-nulls-50 | parallel | 2.235 to 2.155 | -3.6% | 1.755 to 1.729 | 9.09 to 9.08 |
| all-string-one-nulls-50 | serial | 2.170 to 2.137 | -1.5% | 2.193 to 2.160 | 9.02 to 9.02 |
| all-string-pair-nulls-0 | parallel | 2.427 to 2.307 | -4.9% | 1.893 to 1.820 | 9.12 to 9.09 |
| all-string-pair-nulls-0 | serial | 2.341 to 2.196 | -6.2% | 2.358 to 2.218 | 9.05 to 9.03 |
| all-string-pair-nulls-50 | parallel | 2.511 to 2.350 | -6.4% | 1.936 to 1.845 | 9.06 to 9.03 |
| all-string-pair-nulls-50 | serial | 2.413 to 2.249 | -6.8% | 2.415 to 2.301 | 8.98 to 8.98 |
| all-string-four-nulls-0 | parallel | 3.852 to 3.865 | +0.3% | 2.777 to 2.821 | 9.14 to 9.06 |
| all-string-four-nulls-0 | serial | 3.981 to 3.904 | -1.9% | 3.999 to 3.941 | 9.06 to 9.03 |
| all-string-four-nulls-50 | parallel | 3.612 to 3.623 | +0.3% | 2.527 to 2.504 | 9.05 to 9.03 |
| all-string-four-nulls-50 | serial | 3.531 to 3.613 | +2.3% | 3.547 to 3.632 | 9.00 to 8.98 |
| all-string-default-nulls-0 | parallel | 3.892 to 4.351 | +11.8% | 2.771 to 3.225 | 9.11 to 9.05 |
| all-string-default-nulls-0 | serial | 3.905 to 4.031 | +3.2% | 3.919 to 4.049 | 9.05 to 9.02 |
| all-string-default-nulls-50 | parallel | 3.714 to 3.695 | -0.5% | 2.620 to 2.557 | 9.09 to 9.06 |
| all-string-default-nulls-50 | serial | 3.631 to 3.498 | -3.7% | 3.654 to 3.520 | 9.03 to 9.02 |
| all-string-default-nulls-90 | parallel | 3.244 to 3.195 | -1.5% | 2.248 to 2.189 | 9.06 to 9.03 |
| all-string-default-nulls-90 | serial | 3.108 to 3.114 | +0.2% | 3.129 to 3.135 | 9.02 to 9.00 |
| all-string-sixteen-nulls-0 | parallel | 3.842 to 3.863 | +0.5% | 2.725 to 2.748 | 9.11 to 9.05 |
| all-string-sixteen-nulls-0 | serial | 3.751 to 3.758 | +0.2% | 3.769 to 3.772 | 9.05 to 9.02 |
| all-string-sixteen-nulls-50 | parallel | 3.800 to 3.733 | -1.7% | 2.686 to 2.698 | 9.17 to 9.12 |
| all-string-sixteen-nulls-50 | serial | 3.678 to 3.646 | -0.9% | 3.694 to 3.664 | 9.09 to 9.08 |
| all-string-seventeen-nulls-0 | parallel | 3.750 to 4.096 | +9.2% | 2.665 to 2.965 | 9.12 to 9.06 |
| all-string-seventeen-nulls-0 | serial | 3.673 to 3.776 | +2.8% | 3.719 to 3.798 | 9.05 to 9.03 |
| all-string-seventeen-nulls-50 | parallel | 3.652 to 3.618 | -0.9% | 2.491 to 2.476 | 9.19 to 9.16 |
| all-string-seventeen-nulls-50 | serial | 3.533 to 3.529 | -0.1% | 3.554 to 3.545 | 9.12 to 9.12 |
| all-string-large-nulls-0 | parallel | 4.213 to 4.096 | -2.8% | 3.037 to 2.926 | 9.48 to 9.45 |
| all-string-large-nulls-0 | serial | 4.023 to 4.103 | +2.0% | 4.042 to 4.124 | 9.42 to 9.41 |
| all-string-large-nulls-50 | parallel | 4.029 to 4.010 | -0.5% | 2.862 to 2.854 | 9.61 to 9.61 |
| all-string-large-nulls-50 | serial | 3.808 to 3.788 | -0.5% | 3.860 to 3.834 | 9.55 to 9.55 |

## Long String keys and values

| Input and schema | Policy | CPU ms, parent to final | CPU change | Elapsed ms, parent to final | Peak RSS MiB, parent to final |
|---|---|---:|---:|---:|---:|
| one-long-nulls-0 | parallel | 68.901 to 67.146 | -2.5% | 22.206 to 21.575 | 32.75 to 32.69 |
| one-long-nulls-0 | serial | 34.568 to 34.206 | -1.0% | 34.595 to 34.263 | 32.58 to 32.53 |
| one-long-nulls-50 | parallel | 40.589 to 39.846 | -1.8% | 13.793 to 13.640 | 25.08 to 25.00 |
| one-long-nulls-50 | serial | 22.545 to 22.126 | -1.9% | 22.577 to 22.198 | 24.92 to 24.88 |
| pair-long-nulls-0 | parallel | 52.325 to 52.218 | -0.2% | 17.898 to 17.824 | 32.80 to 32.76 |
| pair-long-nulls-0 | serial | 35.432 to 35.029 | -1.1% | 35.474 to 35.093 | 32.58 to 32.53 |
| pair-long-nulls-50 | parallel | 35.103 to 34.796 | -0.9% | 12.435 to 12.416 | 25.09 to 25.02 |
| pair-long-nulls-50 | serial | 22.776 to 22.424 | -1.5% | 22.884 to 22.476 | 24.88 to 24.83 |
| pair-unicode-nulls-0 | parallel | 52.264 to 52.334 | +0.1% | 17.932 to 17.838 | 32.84 to 32.74 |
| pair-unicode-nulls-0 | serial | 35.293 to 34.974 | -0.9% | 35.383 to 35.029 | 32.61 to 32.53 |
| pair-unicode-nulls-50 | parallel | 53.442 to 52.898 | -1.0% | 17.468 to 17.451 | 25.33 to 25.27 |
| pair-unicode-nulls-50 | serial | 36.065 to 36.156 | +0.3% | 36.121 to 36.207 | 25.11 to 25.05 |
| three-long-nulls-0 | parallel | 87.212 to 86.906 | -0.4% | 26.518 to 26.618 | 32.77 to 32.75 |
| three-long-nulls-0 | serial | 63.562 to 63.233 | -0.5% | 63.600 to 63.294 | 32.56 to 32.53 |
| three-long-nulls-50 | parallel | 53.280 to 53.478 | +0.4% | 17.411 to 17.448 | 25.25 to 25.20 |
| three-long-nulls-50 | serial | 39.075 to 38.909 | -0.4% | 39.121 to 38.964 | 25.02 to 24.98 |
