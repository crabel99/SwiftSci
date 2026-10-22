# Complete resource controls

CPU means process user-plus-system time per correct result. Each policy compares with the same parent policy. See the [study methods](README.md).

## Width and numeric null controls

| Input and schema | Policy | CPU ms, parent to final | CPU change | Elapsed ms, parent to final | Peak RSS MiB, parent to final |
|---|---|---:|---:|---:|---:|
| width-1-rows-257 | parallel | 0.217 to 0.220 | +1.1% | 0.239 to 0.241 | 7.08 to 7.09 |
| width-1-rows-257 | serial | 0.222 to 0.213 | -3.6% | 0.242 to 0.232 | 7.06 to 7.09 |
| width-2-rows-257 | parallel | 0.242 to 0.237 | -2.1% | 0.256 to 0.255 | 7.11 to 7.11 |
| width-2-rows-257 | serial | 0.224 to 0.224 | +0.0% | 0.247 to 0.246 | 7.09 to 7.09 |
| width-4-rows-257 | parallel | 0.298 to 0.303 | +1.7% | 0.290 to 0.296 | 7.19 to 7.20 |
| width-4-rows-257 | serial | 0.238 to 0.244 | +2.3% | 0.260 to 0.265 | 7.14 to 7.16 |
| width-8-rows-257 | parallel | 0.411 to 0.415 | +0.9% | 0.307 to 0.306 | 7.31 to 7.31 |
| width-8-rows-257 | serial | 0.264 to 0.266 | +0.9% | 0.286 to 0.285 | 7.22 to 7.22 |
| width-18-rows-257 | parallel | 0.603 to 0.623 | +3.3% | 0.361 to 0.363 | 7.53 to 7.48 |
| width-18-rows-257 | serial | 0.341 to 0.340 | -0.3% | 0.360 to 0.357 | 7.39 to 7.34 |
| width-64-rows-257 | parallel | 1.167 to 1.141 | -2.1% | 0.639 to 0.644 | 8.28 to 8.23 |
| width-64-rows-257 | serial | 0.599 to 0.578 | -3.4% | 0.615 to 0.604 | 8.05 to 7.99 |
| width-1-rows-32769 | parallel | 0.629 to 0.625 | -0.6% | 0.651 to 0.647 | 8.48 to 8.48 |
| width-1-rows-32769 | serial | 0.631 to 0.618 | -2.1% | 0.651 to 0.637 | 8.47 to 8.48 |
| width-2-rows-32769 | parallel | 1.104 to 1.084 | -1.8% | 0.885 to 0.874 | 9.17 to 9.14 |
| width-2-rows-32769 | serial | 1.020 to 1.004 | -1.5% | 1.040 to 1.024 | 9.12 to 9.12 |
| width-4-rows-32769 | parallel | 2.476 to 2.441 | -1.4% | 1.700 to 1.681 | 11.02 to 11.03 |
| width-4-rows-32769 | serial | 2.305 to 2.256 | -2.1% | 2.326 to 2.279 | 10.94 to 10.95 |
| width-8-rows-32769 | parallel | 5.418 to 5.330 | -1.6% | 2.718 to 2.660 | 14.99 to 14.96 |
| width-8-rows-32769 | serial | 4.383 to 4.276 | -2.5% | 4.439 to 4.323 | 14.83 to 14.81 |
| width-18-rows-32769 | parallel | 15.547 to 15.451 | -0.6% | 5.505 to 5.463 | 25.52 to 25.45 |
| width-18-rows-32769 | serial | 11.097 to 10.788 | -2.8% | 11.130 to 10.850 | 25.20 to 25.16 |
| width-64-rows-32769 | parallel | 68.585 to 68.197 | -0.6% | 18.376 to 18.698 | 77.64 to 73.17 |
| width-64-rows-32769 | serial | 46.078 to 45.330 | -1.6% | 46.142 to 45.374 | 72.89 to 72.86 |
| nullable-0-infer | parallel | 2.573 to 2.539 | -1.3% | 2.106 to 2.088 | 11.77 to 11.80 |
| nullable-0-infer | serial | 2.405 to 2.383 | -0.9% | 2.436 to 2.401 | 11.70 to 11.77 |
| nullable-50-infer | parallel | 3.019 to 2.982 | -1.2% | 2.320 to 2.291 | 11.59 to 11.59 |
| nullable-50-infer | serial | 2.764 to 2.743 | -0.7% | 2.784 to 2.767 | 11.53 to 11.56 |
| nullable-90-infer | parallel | 3.182 to 3.147 | -1.1% | 2.357 to 2.340 | 11.61 to 11.62 |
| nullable-90-infer | serial | 2.964 to 2.924 | -1.4% | 2.982 to 2.941 | 11.55 to 11.58 |
| nullable-50-known | parallel | 2.905 to 2.894 | -0.4% | 2.260 to 2.242 | 11.56 to 11.58 |
| nullable-50-known | serial | 2.763 to 2.705 | -2.1% | 2.813 to 2.758 | 11.52 to 11.53 |
| nullable-90-known | parallel | 3.117 to 3.103 | -0.4% | 2.312 to 2.293 | 11.58 to 11.58 |
| nullable-90-known | serial | 2.905 to 2.914 | +0.3% | 2.924 to 2.933 | 11.53 to 11.55 |

## Text controls

| Input and schema | Policy | CPU ms, parent to final | CPU change | Elapsed ms, parent to final | Peak RSS MiB, parent to final |
|---|---|---:|---:|---:|---:|
| none-nulls-0 | parallel | 1.515 to 1.508 | -0.5% | 1.335 to 1.333 | 9.12 to 9.11 |
| none-nulls-0 | serial | 1.442 to 1.436 | -0.4% | 1.459 to 1.457 | 9.05 to 9.06 |
| one-nulls-0 | parallel | 1.847 to 1.812 | -1.9% | 1.668 to 1.627 | 9.11 to 9.11 |
| one-nulls-0 | serial | 1.768 to 1.726 | -2.4% | 1.787 to 1.741 | 9.05 to 9.08 |
| one-nulls-50 | parallel | 1.799 to 1.764 | -1.9% | 1.618 to 1.583 | 9.12 to 9.12 |
| one-nulls-50 | serial | 1.736 to 1.696 | -2.2% | 1.756 to 1.715 | 9.05 to 9.06 |
| pair-nulls-0 | parallel | 1.897 to 1.845 | -2.7% | 1.717 to 1.668 | 9.12 to 9.14 |
| pair-nulls-0 | serial | 1.835 to 1.767 | -3.7% | 1.849 to 1.787 | 9.05 to 9.08 |
| pair-nulls-50 | parallel | 1.843 to 1.791 | -2.8% | 1.664 to 1.615 | 9.11 to 9.11 |
| pair-nulls-50 | serial | 1.777 to 1.723 | -3.0% | 1.797 to 1.741 | 9.03 to 9.05 |
| four-nulls-0 | parallel | 3.856 to 3.811 | -1.2% | 2.636 to 2.574 | 9.12 to 9.12 |
| four-nulls-0 | serial | 3.744 to 3.780 | +1.0% | 3.772 to 3.802 | 9.06 to 9.08 |
| four-nulls-50 | parallel | 3.760 to 3.666 | -2.5% | 2.460 to 2.395 | 9.09 to 9.11 |
| four-nulls-50 | serial | 3.526 to 3.524 | -0.1% | 3.546 to 3.542 | 9.05 to 9.05 |
| default-nulls-0 | parallel | 2.790 to 2.823 | +1.2% | 2.614 to 2.639 | 9.11 to 9.12 |
| default-nulls-0 | serial | 2.853 to 2.572 | -9.9% | 2.874 to 2.591 | 9.06 to 9.09 |
| default-nulls-50 | parallel | 2.539 to 2.542 | +0.1% | 2.399 to 2.381 | 9.15 to 9.12 |
| default-nulls-50 | serial | 2.522 to 2.465 | -2.3% | 2.550 to 2.499 | 9.09 to 9.09 |
| default-nulls-90 | parallel | 2.079 to 2.075 | -0.2% | 1.931 to 1.924 | 9.11 to 9.14 |
| default-nulls-90 | serial | 1.997 to 2.003 | +0.3% | 2.044 to 2.045 | 9.08 to 9.08 |
| sixteen-nulls-0 | parallel | 3.837 to 3.846 | +0.2% | 2.585 to 2.594 | 9.14 to 9.16 |
| sixteen-nulls-0 | serial | 3.647 to 3.748 | +2.8% | 3.664 to 3.766 | 9.06 to 9.09 |
| sixteen-nulls-50 | parallel | 3.870 to 3.773 | -2.5% | 2.581 to 2.544 | 9.22 to 9.20 |
| sixteen-nulls-50 | serial | 3.652 to 3.715 | +1.7% | 3.672 to 3.737 | 9.14 to 9.16 |
| seventeen-nulls-0 | parallel | 2.985 to 2.824 | -5.4% | 2.505 to 2.346 | 9.14 to 9.14 |
| seventeen-nulls-0 | serial | 2.659 to 2.837 | +6.7% | 2.672 to 2.854 | 9.06 to 9.11 |
| seventeen-nulls-50 | parallel | 2.966 to 2.793 | -5.8% | 2.473 to 2.319 | 9.25 to 9.22 |
| seventeen-nulls-50 | serial | 2.688 to 2.821 | +4.9% | 2.705 to 2.850 | 9.17 to 9.19 |
| large-nulls-0 | parallel | 20.464 to 20.541 | +0.4% | 18.906 to 18.927 | 9.61 to 9.64 |
| large-nulls-0 | serial | 20.941 to 20.305 | -3.0% | 20.999 to 20.344 | 9.56 to 9.61 |
| large-nulls-50 | parallel | 20.480 to 20.637 | +0.8% | 18.974 to 19.114 | 9.75 to 9.78 |
| large-nulls-50 | serial | 20.449 to 20.301 | -0.7% | 20.498 to 20.335 | 9.69 to 9.73 |
| all-string-none-nulls-0 | parallel | 1.881 to 1.877 | -0.2% | 1.473 to 1.463 | 9.11 to 9.09 |
| all-string-none-nulls-0 | serial | 1.796 to 1.808 | +0.7% | 1.812 to 1.827 | 9.03 to 9.05 |
| all-string-one-nulls-0 | parallel | 2.264 to 2.200 | -2.8% | 1.788 to 1.744 | 9.12 to 9.08 |
| all-string-one-nulls-0 | serial | 2.179 to 2.136 | -2.0% | 2.196 to 2.156 | 9.05 to 9.06 |
| all-string-one-nulls-50 | parallel | 2.222 to 2.154 | -3.1% | 1.731 to 1.698 | 9.06 to 9.08 |
| all-string-one-nulls-50 | serial | 2.123 to 2.072 | -2.4% | 2.140 to 2.093 | 9.02 to 9.05 |
| all-string-pair-nulls-0 | parallel | 2.427 to 2.301 | -5.2% | 1.870 to 1.790 | 9.12 to 9.11 |
| all-string-pair-nulls-0 | serial | 2.308 to 2.185 | -5.3% | 2.324 to 2.204 | 9.05 to 9.05 |
| all-string-pair-nulls-50 | parallel | 2.317 to 2.195 | -5.3% | 1.793 to 1.713 | 9.06 to 9.06 |
| all-string-pair-nulls-50 | serial | 2.237 to 2.121 | -5.2% | 2.271 to 2.153 | 8.98 to 9.03 |
| all-string-four-nulls-0 | parallel | 3.928 to 3.749 | -4.5% | 2.807 to 2.667 | 9.14 to 9.09 |
| all-string-four-nulls-0 | serial | 3.805 to 3.642 | -4.3% | 3.818 to 3.663 | 9.06 to 9.05 |
| all-string-four-nulls-50 | parallel | 3.587 to 3.660 | +2.0% | 2.469 to 2.540 | 9.08 to 9.09 |
| all-string-four-nulls-50 | serial | 3.388 to 3.489 | +3.0% | 3.419 to 3.524 | 9.00 to 9.03 |
| all-string-default-nulls-0 | parallel | 3.850 to 3.866 | +0.4% | 2.659 to 2.645 | 9.12 to 9.12 |
| all-string-default-nulls-0 | serial | 4.048 to 4.197 | +3.7% | 4.064 to 4.216 | 9.05 to 9.06 |
| all-string-default-nulls-50 | parallel | 3.665 to 3.667 | +0.1% | 2.524 to 2.503 | 9.08 to 9.11 |
| all-string-default-nulls-50 | serial | 3.623 to 3.644 | +0.6% | 3.636 to 3.665 | 9.03 to 9.08 |
| all-string-default-nulls-90 | parallel | 3.149 to 3.272 | +3.9% | 2.170 to 2.286 | 9.06 to 9.09 |
| all-string-default-nulls-90 | serial | 3.039 to 3.120 | +2.7% | 3.058 to 3.154 | 9.02 to 9.06 |
| all-string-sixteen-nulls-0 | parallel | 3.748 to 3.818 | +1.9% | 2.667 to 2.685 | 9.09 to 9.12 |
| all-string-sixteen-nulls-0 | serial | 3.694 to 3.694 | +0.0% | 3.712 to 3.711 | 9.05 to 9.06 |
| all-string-sixteen-nulls-50 | parallel | 3.737 to 3.767 | +0.8% | 2.640 to 2.635 | 9.16 to 9.17 |
| all-string-sixteen-nulls-50 | serial | 3.568 to 3.655 | +2.4% | 3.588 to 3.676 | 9.09 to 9.14 |
| all-string-seventeen-nulls-0 | parallel | 3.761 to 3.745 | -0.4% | 2.622 to 2.547 | 9.12 to 9.11 |
| all-string-seventeen-nulls-0 | serial | 4.011 to 3.829 | -4.5% | 4.028 to 3.862 | 9.05 to 9.06 |
| all-string-seventeen-nulls-50 | parallel | 3.639 to 3.615 | -0.6% | 2.550 to 2.579 | 9.17 to 9.20 |
| all-string-seventeen-nulls-50 | serial | 3.595 to 3.521 | -2.1% | 3.657 to 3.573 | 9.12 to 9.17 |
| all-string-large-nulls-0 | parallel | 3.906 to 4.114 | +5.3% | 2.740 to 2.895 | 9.49 to 9.53 |
| all-string-large-nulls-0 | serial | 3.844 to 3.845 | +0.0% | 3.860 to 3.867 | 9.42 to 9.47 |
| all-string-large-nulls-50 | parallel | 3.946 to 4.122 | +4.4% | 2.769 to 2.956 | 9.62 to 9.66 |
| all-string-large-nulls-50 | serial | 3.897 to 3.765 | -3.4% | 3.916 to 3.784 | 9.55 to 9.61 |

## Long String keys and values

| Input and schema | Policy | CPU ms, parent to final | CPU change | Elapsed ms, parent to final | Peak RSS MiB, parent to final |
|---|---|---:|---:|---:|---:|
| one-long-nulls-0 | parallel | 71.927 to 65.728 | -8.6% | 22.776 to 21.557 | 32.77 to 32.71 |
| one-long-nulls-0 | serial | 34.401 to 34.131 | -0.8% | 34.452 to 34.184 | 32.58 to 32.59 |
| one-long-nulls-50 | parallel | 40.123 to 41.825 | +4.2% | 13.603 to 14.029 | 25.03 to 25.02 |
| one-long-nulls-50 | serial | 22.131 to 21.912 | -1.0% | 22.171 to 21.964 | 24.92 to 24.92 |
| pair-long-nulls-0 | parallel | 51.324 to 51.301 | -0.0% | 17.530 to 17.556 | 32.78 to 32.83 |
| pair-long-nulls-0 | serial | 35.123 to 35.105 | -0.1% | 35.163 to 35.161 | 32.58 to 32.61 |
| pair-long-nulls-50 | parallel | 34.758 to 34.751 | -0.0% | 12.358 to 12.299 | 25.09 to 25.06 |
| pair-long-nulls-50 | serial | 22.584 to 22.241 | -1.5% | 22.619 to 22.290 | 24.88 to 24.91 |
| pair-unicode-nulls-0 | parallel | 52.179 to 51.828 | -0.7% | 17.717 to 17.570 | 32.82 to 32.75 |
| pair-unicode-nulls-0 | serial | 35.397 to 34.706 | -2.0% | 35.446 to 34.773 | 32.61 to 32.61 |
| pair-unicode-nulls-50 | parallel | 52.931 to 52.952 | +0.0% | 17.389 to 17.466 | 25.36 to 25.28 |
| pair-unicode-nulls-50 | serial | 36.620 to 35.583 | -2.8% | 36.662 to 35.639 | 25.11 to 25.08 |
| three-long-nulls-0 | parallel | 85.442 to 84.998 | -0.5% | 26.363 to 26.147 | 32.81 to 32.79 |
| three-long-nulls-0 | serial | 62.788 to 63.161 | +0.6% | 62.850 to 63.207 | 32.56 to 32.59 |
| three-long-nulls-50 | parallel | 51.811 to 53.124 | +2.5% | 16.873 to 17.151 | 25.26 to 25.23 |
| three-long-nulls-50 | serial | 38.726 to 38.870 | +0.4% | 38.782 to 38.932 | 25.02 to 25.02 |
