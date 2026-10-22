# Complete control results

Lower CPU time means less process user-plus-system time per correct result. Both policies compare with the same parent policy. See [study methods](README.md).

## Width and numeric null controls

| Input and schema | Policy | CPU ms, parent → final | CPU change | Elapsed ms, parent → final | Peak RSS MiB, parent → final |
|---|---|---:|---:|---:|---:|
| width-1-rows-257 | parallel | 0.246 → 0.252 | +2.4% | 0.247 → 0.254 | 7.03 → 7.08 |
| width-1-rows-257 | serial | 0.236 → 0.242 | +2.3% | 0.241 → 0.241 | 7.02 → 7.06 |
| width-2-rows-257 | parallel | 0.286 → 0.269 | -6.1% | 0.281 → 0.263 | 7.05 → 7.11 |
| width-2-rows-257 | serial | 0.251 → 0.261 | +4.2% | 0.252 → 0.263 | 7.02 → 7.11 |
| width-4-rows-257 | parallel | 0.352 → 0.340 | -3.4% | 0.314 → 0.308 | 7.11 → 7.20 |
| width-4-rows-257 | serial | 0.285 → 0.280 | -2.1% | 0.283 → 0.277 | 7.06 → 7.14 |
| width-8-rows-257 | parallel | 0.469 → 0.417 | -11.0% | 0.334 → 0.320 | 7.27 → 7.34 |
| width-8-rows-257 | serial | 0.319 → 0.311 | -2.2% | 0.319 → 0.314 | 7.12 → 7.23 |
| width-18-rows-257 | parallel | 0.781 → 0.688 | -12.0% | 0.416 → 0.397 | 7.51 → 7.56 |
| width-18-rows-257 | serial | 0.396 → 0.368 | -6.8% | 0.395 → 0.372 | 7.30 → 7.39 |
| width-64-rows-257 | parallel | 1.294 → 1.202 | -7.1% | 0.598 → 0.605 | 8.23 → 8.30 |
| width-64-rows-257 | serial | 0.748 → 0.656 | -12.2% | 0.745 → 0.655 | 7.95 → 8.05 |
| width-1-rows-32769 | parallel | 0.692 → 0.704 | +1.7% | 0.690 → 0.704 | 8.45 → 8.52 |
| width-1-rows-32769 | serial | 0.684 → 0.700 | +2.2% | 0.687 → 0.703 | 8.41 → 8.49 |
| width-2-rows-32769 | parallel | 1.218 → 1.228 | +0.9% | 0.971 → 0.975 | 9.14 → 9.22 |
| width-2-rows-32769 | serial | 1.117 → 1.106 | -1.0% | 1.127 → 1.127 | 9.05 → 9.12 |
| width-4-rows-32769 | parallel | 3.228 → 2.795 | -13.4% | 2.319 → 1.845 | 11.70 → 11.08 |
| width-4-rows-32769 | serial | 2.909 → 2.437 | -16.2% | 2.922 → 2.434 | 10.88 → 10.97 |
| width-8-rows-32769 | parallel | 6.358 → 5.296 | -16.7% | 3.134 → 2.674 | 16.08 → 16.16 |
| width-8-rows-32769 | serial | 5.716 → 4.649 | -18.7% | 5.712 → 4.658 | 14.75 → 14.84 |
| width-18-rows-32769 | parallel | 18.257 → 15.677 | -14.1% | 6.082 → 5.485 | 27.05 → 26.45 |
| width-18-rows-32769 | serial | 15.001 → 11.919 | -20.5% | 15.000 → 11.920 | 25.11 → 25.20 |
| width-64-rows-32769 | parallel | 79.820 → 71.379 | -10.6% | 20.017 → 19.015 | 77.53 → 77.61 |
| width-64-rows-32769 | serial | 63.297 → 51.140 | -19.2% | 63.359 → 51.164 | 72.80 → 72.89 |
| nullable-0-infer | parallel | 2.660 → 2.706 | +1.7% | 2.161 → 2.215 | 11.72 → 11.80 |
| nullable-0-infer | serial | 2.501 → 2.523 | +0.9% | 2.502 → 2.519 | 11.66 → 11.73 |
| nullable-50-infer | parallel | 3.136 → 3.107 | -0.9% | 2.423 → 2.391 | 11.58 → 11.62 |
| nullable-50-infer | serial | 2.954 → 2.973 | +0.6% | 2.956 → 2.975 | 11.48 → 11.53 |
| nullable-90-infer | parallel | 3.401 → 3.591 | +5.6% | 2.558 → 2.711 | 11.81 → 12.12 |
| nullable-90-infer | serial | 3.076 → 3.108 | +1.1% | 3.073 → 3.113 | 11.52 → 11.55 |
| nullable-50-known | parallel | 3.031 → 3.057 | +0.9% | 2.294 → 2.324 | 11.55 → 11.59 |
| nullable-50-known | serial | 2.833 → 2.834 | +0.0% | 2.828 → 2.832 | 11.44 → 11.52 |
| nullable-90-known | parallel | 3.243 → 3.265 | +0.7% | 2.380 → 2.418 | 11.55 → 11.61 |
| nullable-90-known | serial | 3.084 → 3.144 | +1.9% | 3.087 → 3.149 | 11.45 → 11.55 |

## Text null-set controls

| Input and schema | Policy | CPU ms, parent → final | CPU change | Elapsed ms, parent → final | Peak RSS MiB, parent → final |
|---|---|---:|---:|---:|---:|
| none-nulls-0 | parallel | 1.578 → 1.593 | +1.0% | 1.390 → 1.394 | 9.06 → 9.12 |
| none-nulls-0 | serial | 1.516 → 1.528 | +0.8% | 1.519 → 1.532 | 8.98 → 9.05 |
| one-nulls-0 | parallel | 2.514 → 1.952 | -22.3% | 2.318 → 1.751 | 9.08 → 9.12 |
| one-nulls-0 | serial | 2.517 → 1.887 | -25.0% | 2.519 → 1.888 | 8.98 → 9.05 |
| one-nulls-50 | parallel | 2.377 → 1.870 | -21.3% | 2.178 → 1.680 | 9.05 → 9.12 |
| one-nulls-50 | serial | 2.303 → 1.830 | -20.5% | 2.307 → 1.827 | 8.98 → 9.05 |
| pair-nulls-0 | parallel | 2.606 → 1.994 | -23.5% | 2.400 → 1.802 | 9.08 → 9.12 |
| pair-nulls-0 | serial | 2.423 → 1.924 | -20.6% | 2.422 → 1.927 | 8.98 → 9.05 |
| pair-nulls-50 | parallel | 2.313 → 1.964 | -15.1% | 2.107 → 1.767 | 9.03 → 9.11 |
| pair-nulls-50 | serial | 2.291 → 1.899 | -17.1% | 2.292 → 1.903 | 8.97 → 9.03 |
| four-nulls-0 | parallel | 4.053 → 4.151 | +2.4% | 2.794 → 2.812 | 9.11 → 9.14 |
| four-nulls-0 | serial | 3.898 → 3.938 | +1.0% | 3.904 → 3.936 | 9.02 → 9.06 |
| four-nulls-50 | parallel | 3.760 → 3.761 | +0.1% | 2.508 → 2.482 | 9.05 → 9.12 |
| four-nulls-50 | serial | 3.638 → 3.905 | +7.3% | 3.635 → 3.909 | 9.00 → 9.06 |
| default-nulls-0 | parallel | 3.071 → 2.707 | -11.9% | 2.875 → 2.500 | 9.11 → 9.14 |
| default-nulls-0 | serial | 3.050 → 3.087 | +1.2% | 3.052 → 3.095 | 9.00 → 9.06 |
| default-nulls-50 | parallel | 2.647 → 2.683 | +1.4% | 2.451 → 2.488 | 9.08 → 9.16 |
| default-nulls-50 | serial | 2.628 → 2.538 | -3.4% | 2.635 → 2.539 | 9.02 → 9.09 |
| default-nulls-90 | parallel | 2.220 → 2.239 | +0.8% | 2.018 → 2.034 | 9.06 → 9.17 |
| default-nulls-90 | serial | 2.185 → 2.183 | -0.1% | 2.202 → 2.189 | 9.00 → 9.08 |
| sixteen-nulls-0 | parallel | 3.982 → 4.004 | +0.6% | 2.697 → 2.682 | 9.12 → 9.14 |
| sixteen-nulls-0 | serial | 3.979 → 3.950 | -0.7% | 3.986 → 3.956 | 9.00 → 9.06 |
| sixteen-nulls-50 | parallel | 3.829 → 4.011 | +4.8% | 2.571 → 2.662 | 9.14 → 9.23 |
| sixteen-nulls-50 | serial | 3.946 → 3.893 | -1.3% | 3.947 → 3.896 | 9.08 → 9.14 |
| seventeen-nulls-0 | parallel | 3.204 → 3.054 | -4.7% | 2.702 → 2.552 | 9.14 → 9.14 |
| seventeen-nulls-0 | serial | 3.237 → 3.111 | -3.9% | 3.248 → 3.127 | 9.02 → 9.09 |
| seventeen-nulls-50 | parallel | 3.036 → 3.077 | +1.4% | 2.519 → 2.569 | 9.59 → 9.55 |
| seventeen-nulls-50 | serial | 3.050 → 3.047 | -0.1% | 3.053 → 3.063 | 9.14 → 9.21 |
| large-nulls-0 | parallel | 21.700 → 21.492 | -1.0% | 19.820 → 19.632 | 9.66 → 9.70 |
| large-nulls-0 | serial | 21.412 → 21.494 | +0.4% | 21.430 → 21.510 | 9.50 → 9.59 |
| large-nulls-50 | parallel | 21.565 → 21.912 | +1.6% | 19.768 → 20.356 | 9.95 → 9.77 |
| large-nulls-50 | serial | 21.657 → 21.977 | +1.5% | 21.678 → 21.988 | 9.65 → 9.69 |
| all-string-none-nulls-0 | parallel | 2.038 → 2.003 | -1.7% | 1.587 → 1.550 | 9.08 → 9.11 |
| all-string-none-nulls-0 | serial | 1.915 → 1.922 | +0.3% | 1.920 → 1.921 | 8.97 → 9.03 |
| all-string-one-nulls-0 | parallel | 3.420 → 2.395 | -30.0% | 2.470 → 1.889 | 9.06 → 9.14 |
| all-string-one-nulls-0 | serial | 3.350 → 2.361 | -29.5% | 3.356 → 2.363 | 8.95 → 9.07 |
| all-string-one-nulls-50 | parallel | 3.265 → 2.362 | -27.7% | 2.318 → 1.845 | 9.05 → 9.09 |
| all-string-one-nulls-50 | serial | 3.221 → 2.305 | -28.4% | 3.221 → 2.302 | 8.94 → 9.02 |
| all-string-pair-nulls-0 | parallel | 3.567 → 2.530 | -29.1% | 2.533 → 1.967 | 9.06 → 9.14 |
| all-string-pair-nulls-0 | serial | 3.526 → 2.470 | -29.9% | 3.526 → 2.469 | 8.95 → 9.05 |
| all-string-pair-nulls-50 | parallel | 3.349 → 2.482 | -25.9% | 2.276 → 1.917 | 9.02 → 9.08 |
| all-string-pair-nulls-50 | serial | 3.268 → 2.391 | -26.8% | 3.272 → 2.390 | 8.91 → 8.98 |
| all-string-four-nulls-0 | parallel | 4.133 → 3.890 | -5.9% | 3.047 → 2.857 | 9.08 → 9.16 |
| all-string-four-nulls-0 | serial | 3.884 → 3.999 | +3.0% | 3.879 → 4.003 | 8.95 → 9.08 |
| all-string-four-nulls-50 | parallel | 3.760 → 3.792 | +0.8% | 2.639 → 2.650 | 9.05 → 9.09 |
| all-string-four-nulls-50 | serial | 3.727 → 3.607 | -3.2% | 3.731 → 3.617 | 8.91 → 9.04 |
| all-string-default-nulls-0 | parallel | 4.139 → 4.053 | -2.1% | 2.979 → 2.825 | 9.06 → 9.14 |
| all-string-default-nulls-0 | serial | 4.008 → 4.261 | +6.3% | 4.013 → 4.262 | 8.95 → 9.05 |
| all-string-default-nulls-50 | parallel | 3.872 → 3.907 | +0.9% | 2.624 → 2.655 | 9.06 → 9.12 |
| all-string-default-nulls-50 | serial | 3.844 → 3.763 | -2.1% | 3.874 → 3.760 | 8.95 → 9.03 |
| all-string-default-nulls-90 | parallel | 3.389 → 3.312 | -2.3% | 2.300 → 2.281 | 9.06 → 9.09 |
| all-string-default-nulls-90 | serial | 3.321 → 3.325 | +0.1% | 3.342 → 3.329 | 8.94 → 9.03 |
| all-string-sixteen-nulls-0 | parallel | 4.126 → 4.003 | -3.0% | 2.940 → 2.867 | 9.06 → 9.12 |
| all-string-sixteen-nulls-0 | serial | 3.911 → 3.993 | +2.1% | 3.916 → 3.992 | 8.95 → 9.05 |
| all-string-sixteen-nulls-50 | parallel | 3.901 → 3.893 | -0.2% | 2.796 → 2.775 | 9.14 → 9.17 |
| all-string-sixteen-nulls-50 | serial | 3.877 → 3.828 | -1.3% | 3.877 → 3.832 | 9.02 → 9.09 |
| all-string-seventeen-nulls-0 | parallel | 3.783 → 3.828 | +1.2% | 2.571 → 2.685 | 9.08 → 9.12 |
| all-string-seventeen-nulls-0 | serial | 3.946 → 3.755 | -4.9% | 3.948 → 3.750 | 8.97 → 9.05 |
| all-string-seventeen-nulls-50 | parallel | 3.797 → 3.831 | +0.9% | 2.639 → 2.655 | 9.20 → 9.20 |
| all-string-seventeen-nulls-50 | serial | 3.800 → 3.785 | -0.4% | 3.801 → 3.796 | 9.06 → 9.12 |
| all-string-large-nulls-0 | parallel | 4.234 → 4.000 | -5.5% | 3.045 → 2.791 | 9.47 → 9.52 |
| all-string-large-nulls-0 | serial | 4.123 → 4.065 | -1.4% | 4.127 → 4.069 | 9.34 → 9.42 |
| all-string-large-nulls-50 | parallel | 4.035 → 4.168 | +3.3% | 2.885 → 2.942 | 9.58 → 9.62 |
| all-string-large-nulls-50 | serial | 4.192 → 4.141 | -1.2% | 4.193 → 4.143 | 9.47 → 9.55 |
