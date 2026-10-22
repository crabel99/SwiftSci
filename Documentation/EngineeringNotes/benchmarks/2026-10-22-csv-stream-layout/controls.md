# Complete resource controls

CPU means process user-plus-system time per correct result. Each policy compares with the same parent policy. See the [study methods](README.md).

## Width and numeric null controls

| Input and schema | Policy | CPU ms, parent to final | CPU change | Elapsed ms, parent to final | Peak RSS MiB, parent to final |
|---|---|---:|---:|---:|---:|
| width-1-rows-257 | parallel | 0.239 to 0.237 | -0.8% | 0.241 to 0.244 | 7.11 to 7.06 |
| width-1-rows-257 | serial | 0.238 to 0.230 | -3.6% | 0.240 to 0.233 | 7.06 to 7.03 |
| width-2-rows-257 | parallel | 0.259 to 0.259 | -0.2% | 0.259 to 0.258 | 7.14 to 7.05 |
| width-2-rows-257 | serial | 0.242 to 0.238 | -1.7% | 0.253 to 0.245 | 7.09 to 7.03 |
| width-4-rows-257 | parallel | 0.334 to 0.316 | -5.4% | 0.298 to 0.287 | 7.20 to 7.12 |
| width-4-rows-257 | serial | 0.257 to 0.269 | +4.5% | 0.261 to 0.273 | 7.14 to 7.06 |
| width-8-rows-257 | parallel | 0.434 to 0.436 | +0.5% | 0.317 to 0.322 | 7.31 to 7.24 |
| width-8-rows-257 | serial | 0.298 to 0.295 | -0.8% | 0.303 to 0.294 | 7.22 to 7.13 |
| width-18-rows-257 | parallel | 0.693 to 0.713 | +2.9% | 0.381 to 0.388 | 7.56 to 7.47 |
| width-18-rows-257 | serial | 0.367 to 0.358 | -2.6% | 0.374 to 0.362 | 7.39 to 7.30 |
| width-64-rows-257 | parallel | 1.267 to 1.298 | +2.4% | 0.577 to 0.560 | 8.30 to 8.21 |
| width-64-rows-257 | serial | 0.641 to 0.626 | -2.3% | 0.641 to 0.630 | 8.06 to 7.97 |
| width-1-rows-32769 | parallel | 0.678 to 0.662 | -2.4% | 0.681 to 0.672 | 8.50 to 8.45 |
| width-1-rows-32769 | serial | 0.683 to 0.663 | -3.0% | 0.688 to 0.668 | 8.48 to 8.42 |
| width-2-rows-32769 | parallel | 1.148 to 1.165 | +1.5% | 0.914 to 0.925 | 9.17 to 9.12 |
| width-2-rows-32769 | serial | 1.113 to 1.093 | -1.8% | 1.117 to 1.099 | 9.12 to 9.06 |
| width-4-rows-32769 | parallel | 2.680 to 2.631 | -1.8% | 1.758 to 1.715 | 11.02 to 10.95 |
| width-4-rows-32769 | serial | 2.442 to 2.387 | -2.2% | 2.446 to 2.387 | 10.97 to 10.89 |
| width-8-rows-32769 | parallel | 5.350 to 5.102 | -4.6% | 2.691 to 2.569 | 16.17 to 15.48 |
| width-8-rows-32769 | serial | 4.629 to 4.546 | -1.8% | 4.633 to 4.547 | 14.84 to 14.75 |
| width-18-rows-32769 | parallel | 15.223 to 15.061 | -1.1% | 5.406 to 5.372 | 25.53 to 27.11 |
| width-18-rows-32769 | serial | 11.787 to 11.514 | -2.3% | 11.804 to 11.517 | 25.21 to 25.12 |
| width-64-rows-32769 | parallel | 71.029 to 71.221 | +0.3% | 19.050 to 18.924 | 73.25 to 76.91 |
| width-64-rows-32769 | serial | 50.144 to 49.266 | -1.8% | 50.178 to 49.281 | 72.95 to 72.86 |
| nullable-0-infer | parallel | 2.732 to 2.741 | +0.3% | 2.220 to 2.231 | 11.80 to 11.75 |
| nullable-0-infer | serial | 2.552 to 2.540 | -0.5% | 2.569 to 2.547 | 11.72 to 11.70 |
| nullable-50-infer | parallel | 3.178 to 3.115 | -2.0% | 2.437 to 2.392 | 11.60 to 11.56 |
| nullable-50-infer | serial | 2.987 to 2.944 | -1.4% | 3.008 to 2.948 | 11.53 to 11.50 |
| nullable-90-infer | parallel | 3.341 to 3.273 | -2.0% | 2.492 to 2.430 | 11.64 to 11.56 |
| nullable-90-infer | serial | 3.153 to 3.131 | -0.7% | 3.153 to 3.138 | 11.55 to 11.52 |
| nullable-50-known | parallel | 3.107 to 3.083 | -0.8% | 2.386 to 2.370 | 12.02 to 11.55 |
| nullable-50-known | serial | 2.993 to 2.857 | -4.5% | 2.990 to 2.860 | 11.55 to 11.47 |
| nullable-90-known | parallel | 3.286 to 3.240 | -1.4% | 2.430 to 2.399 | 11.62 to 11.62 |
| nullable-90-known | serial | 3.139 to 3.013 | -4.0% | 3.135 to 3.018 | 11.55 to 11.48 |

## Text controls

| Input and schema | Policy | CPU ms, parent to final | CPU change | Elapsed ms, parent to final | Peak RSS MiB, parent to final |
|---|---|---:|---:|---:|---:|
| none-nulls-0 | parallel | 1.638 to 1.611 | -1.6% | 1.439 to 1.401 | 9.13 to 9.06 |
| none-nulls-0 | serial | 1.558 to 1.540 | -1.2% | 1.562 to 1.539 | 9.05 to 9.00 |
| one-nulls-0 | parallel | 1.942 to 1.911 | -1.5% | 1.741 to 1.700 | 9.12 to 9.07 |
| one-nulls-0 | serial | 1.898 to 1.841 | -3.0% | 1.901 to 1.845 | 9.05 to 9.02 |
| one-nulls-50 | parallel | 1.913 to 1.868 | -2.4% | 1.714 to 1.683 | 9.16 to 9.11 |
| one-nulls-50 | serial | 1.826 to 1.780 | -2.5% | 1.825 to 1.774 | 9.05 to 9.00 |
| pair-nulls-0 | parallel | 2.071 to 1.979 | -4.4% | 1.869 to 1.766 | 9.14 to 9.09 |
| pair-nulls-0 | serial | 1.972 to 1.895 | -3.9% | 1.972 to 1.916 | 9.05 to 9.05 |
| pair-nulls-50 | parallel | 1.950 to 1.888 | -3.2% | 1.757 to 1.690 | 9.14 to 9.08 |
| pair-nulls-50 | serial | 1.927 to 1.846 | -4.2% | 1.928 to 1.848 | 9.03 to 8.97 |
| four-nulls-0 | parallel | 3.955 to 4.104 | +3.8% | 2.699 to 2.795 | 9.14 to 9.09 |
| four-nulls-0 | serial | 3.978 to 3.925 | -1.3% | 3.982 to 3.927 | 9.06 to 9.05 |
| four-nulls-50 | parallel | 3.784 to 3.760 | -0.6% | 2.533 to 2.471 | 9.16 to 9.09 |
| four-nulls-50 | serial | 3.684 to 3.644 | -1.1% | 3.684 to 3.648 | 9.05 to 9.00 |
| default-nulls-0 | parallel | 3.086 to 2.943 | -4.6% | 2.886 to 2.763 | 9.16 to 9.08 |
| default-nulls-0 | serial | 3.033 to 2.844 | -6.2% | 3.034 to 2.847 | 9.06 to 9.02 |
| default-nulls-50 | parallel | 2.878 to 2.656 | -7.7% | 2.679 to 2.464 | 9.16 to 9.08 |
| default-nulls-50 | serial | 2.623 to 2.704 | +3.1% | 2.624 to 2.709 | 9.08 to 9.00 |
| default-nulls-90 | parallel | 2.253 to 2.195 | -2.6% | 2.053 to 2.001 | 9.14 to 9.06 |
| default-nulls-90 | serial | 2.174 to 2.192 | +0.9% | 2.175 to 2.201 | 9.06 to 9.02 |
| sixteen-nulls-0 | parallel | 4.088 to 4.200 | +2.8% | 2.763 to 2.759 | 9.20 to 9.12 |
| sixteen-nulls-0 | serial | 3.990 to 3.886 | -2.6% | 4.000 to 3.887 | 9.08 to 9.02 |
| sixteen-nulls-50 | parallel | 3.967 to 3.975 | +0.2% | 2.651 to 2.652 | 9.22 to 9.14 |
| sixteen-nulls-50 | serial | 3.865 to 3.820 | -1.2% | 3.867 to 3.829 | 9.16 to 9.06 |
| seventeen-nulls-0 | parallel | 3.176 to 3.213 | +1.2% | 2.673 to 2.707 | 9.16 to 9.06 |
| seventeen-nulls-0 | serial | 3.392 to 3.037 | -10.5% | 3.403 to 3.043 | 9.06 to 9.02 |
| seventeen-nulls-50 | parallel | 3.069 to 3.034 | -1.1% | 2.550 to 2.513 | 9.25 to 9.18 |
| seventeen-nulls-50 | serial | 2.977 to 2.909 | -2.3% | 2.982 to 2.906 | 9.17 to 9.12 |
| large-nulls-0 | parallel | 21.585 to 21.436 | -0.7% | 19.594 to 19.522 | 9.68 to 9.59 |
| large-nulls-0 | serial | 21.535 to 21.623 | +0.4% | 21.551 to 21.625 | 9.56 to 9.52 |
| large-nulls-50 | parallel | 21.474 to 21.378 | -0.4% | 19.986 to 19.859 | 9.77 to 9.84 |
| large-nulls-50 | serial | 21.480 to 21.601 | +0.6% | 21.490 to 21.606 | 9.70 to 9.61 |
| all-string-none-nulls-0 | parallel | 1.950 to 1.949 | -0.1% | 1.517 to 1.500 | 9.11 to 9.05 |
| all-string-none-nulls-0 | serial | 1.920 to 1.881 | -2.0% | 1.923 to 1.888 | 9.03 to 9.02 |
| all-string-one-nulls-0 | parallel | 2.384 to 2.285 | -4.1% | 1.870 to 1.824 | 9.12 to 9.03 |
| all-string-one-nulls-0 | serial | 2.288 to 2.224 | -2.8% | 2.300 to 2.229 | 9.05 to 8.98 |
| all-string-one-nulls-50 | parallel | 2.356 to 2.259 | -4.1% | 1.844 to 1.795 | 9.09 to 9.05 |
| all-string-one-nulls-50 | serial | 2.275 to 2.174 | -4.5% | 2.284 to 2.179 | 9.04 to 8.97 |
| all-string-pair-nulls-0 | parallel | 2.480 to 2.357 | -5.0% | 1.932 to 1.853 | 9.12 to 9.03 |
| all-string-pair-nulls-0 | serial | 2.422 to 2.308 | -4.7% | 2.424 to 2.312 | 9.05 to 8.98 |
| all-string-pair-nulls-50 | parallel | 2.349 to 2.232 | -4.9% | 1.825 to 1.774 | 9.03 to 9.02 |
| all-string-pair-nulls-50 | serial | 2.268 to 2.184 | -3.7% | 2.313 to 2.206 | 8.98 to 8.94 |
| all-string-four-nulls-0 | parallel | 3.852 to 3.823 | -0.7% | 2.759 to 2.752 | 9.12 to 9.02 |
| all-string-four-nulls-0 | serial | 3.717 to 3.804 | +2.3% | 3.768 to 3.877 | 9.06 to 9.00 |
| all-string-four-nulls-50 | parallel | 3.682 to 3.557 | -3.4% | 2.581 to 2.513 | 9.05 to 9.00 |
| all-string-four-nulls-50 | serial | 3.455 to 3.523 | +2.0% | 3.504 to 3.566 | 9.00 to 8.95 |
| all-string-default-nulls-0 | parallel | 3.978 to 4.012 | +0.9% | 2.870 to 2.884 | 9.09 to 9.05 |
| all-string-default-nulls-0 | serial | 4.254 to 3.815 | -10.3% | 4.293 to 3.872 | 9.05 to 9.00 |
| all-string-default-nulls-50 | parallel | 3.729 to 3.651 | -2.1% | 2.558 to 2.554 | 9.08 to 9.05 |
| all-string-default-nulls-50 | serial | 3.635 to 3.550 | -2.4% | 3.679 to 3.606 | 9.03 to 8.98 |
| all-string-default-nulls-90 | parallel | 3.174 to 3.134 | -1.2% | 2.224 to 2.184 | 9.06 to 9.02 |
| all-string-default-nulls-90 | serial | 3.095 to 3.112 | +0.6% | 3.150 to 3.153 | 9.02 to 8.97 |
| all-string-sixteen-nulls-0 | parallel | 3.814 to 3.782 | -0.8% | 2.744 to 2.753 | 9.09 to 9.03 |
| all-string-sixteen-nulls-0 | serial | 3.868 to 3.766 | -2.6% | 3.918 to 3.797 | 9.05 to 9.00 |
| all-string-sixteen-nulls-50 | parallel | 3.785 to 3.844 | +1.5% | 2.728 to 2.743 | 9.14 to 9.12 |
| all-string-sixteen-nulls-50 | serial | 3.685 to 3.598 | -2.4% | 3.731 to 3.643 | 9.09 to 9.05 |
| all-string-seventeen-nulls-0 | parallel | 3.860 to 3.700 | -4.2% | 2.735 to 2.575 | 9.12 to 9.03 |
| all-string-seventeen-nulls-0 | serial | 3.719 to 3.817 | +2.7% | 3.756 to 3.908 | 9.05 to 9.00 |
| all-string-seventeen-nulls-50 | parallel | 3.873 to 3.687 | -4.8% | 2.762 to 2.560 | 9.20 to 9.12 |
| all-string-seventeen-nulls-50 | serial | 3.557 to 3.577 | +0.6% | 3.593 to 3.647 | 9.12 to 9.08 |
| all-string-large-nulls-0 | parallel | 3.925 to 4.083 | +4.0% | 2.809 to 2.936 | 9.47 to 9.39 |
| all-string-large-nulls-0 | serial | 4.054 to 3.863 | -4.7% | 4.135 to 3.941 | 9.42 to 9.38 |
| all-string-large-nulls-50 | parallel | 4.006 to 3.994 | -0.3% | 2.891 to 2.874 | 9.59 to 9.53 |
| all-string-large-nulls-50 | serial | 3.909 to 3.837 | -1.8% | 3.977 to 3.888 | 9.55 to 9.48 |

## Long String keys and values

| Input and schema | Policy | CPU ms, parent to final | CPU change | Elapsed ms, parent to final | Peak RSS MiB, parent to final |
|---|---|---:|---:|---:|---:|
| one-long-nulls-0 | parallel | 56.596 to 54.380 | -3.9% | 20.289 to 20.003 | 32.78 to 32.76 |
| one-long-nulls-0 | serial | 35.041 to 35.219 | +0.5% | 35.114 to 35.250 | 32.58 to 32.57 |
| one-long-nulls-50 | parallel | 40.176 to 38.347 | -4.6% | 13.976 to 13.525 | 25.08 to 25.05 |
| one-long-nulls-50 | serial | 22.580 to 22.545 | -0.2% | 22.633 to 22.567 | 24.92 to 24.86 |
| pair-long-nulls-0 | parallel | 49.242 to 50.319 | +2.2% | 17.391 to 17.659 | 32.85 to 32.77 |
| pair-long-nulls-0 | serial | 35.628 to 35.424 | -0.6% | 35.691 to 35.472 | 32.58 to 32.53 |
| pair-long-nulls-50 | parallel | 34.941 to 33.995 | -2.7% | 12.483 to 12.193 | 25.12 to 25.05 |
| pair-long-nulls-50 | serial | 22.978 to 22.879 | -0.4% | 23.029 to 22.934 | 24.88 to 24.83 |
| pair-unicode-nulls-0 | parallel | 52.078 to 49.593 | -4.8% | 17.837 to 17.547 | 32.90 to 32.78 |
| pair-unicode-nulls-0 | serial | 35.669 to 35.344 | -0.9% | 35.729 to 35.410 | 32.61 to 32.52 |
| pair-unicode-nulls-50 | parallel | 51.272 to 52.154 | +1.7% | 17.084 to 17.307 | 25.43 to 25.28 |
| pair-unicode-nulls-50 | serial | 36.674 to 36.400 | -0.7% | 36.740 to 36.461 | 25.11 to 25.03 |
| three-long-nulls-0 | parallel | 85.689 to 83.740 | -2.3% | 26.788 to 26.318 | 32.88 to 32.84 |
| three-long-nulls-0 | serial | 64.179 to 64.278 | +0.2% | 64.238 to 64.372 | 32.56 to 32.55 |
| three-long-nulls-50 | parallel | 51.733 to 51.955 | +0.4% | 16.918 to 17.140 | 25.30 to 25.22 |
| three-long-nulls-50 | serial | 39.236 to 39.562 | +0.8% | 39.301 to 39.616 | 25.02 to 25.00 |
