# Additional setup and builder controls

These diagnostic controls retain complete native-output checks. Launcher control uses the same executable with a different argv[0]. Local-builder controls use a common launcher name for every executable. These are not final production qualifications. See the [study methods](README.md).

## argument-control

| Scope | Input | Policy | Implementation | CPU ms | Elapsed ms | Peak RSS MiB |
|---|---|---|---|---:|---:|---:|
| stream | energy | parallel | parent-default | 273.070 | 116.909 | 139.06 |
| stream | energy | parallel | parent-explicit | 274.812 | 115.999 | 139.03 |
| stream | energy | parallel | candidate-default | 294.620 | 118.915 | 139.40 |
| stream | energy | parallel | candidate-explicit | 294.663 | 119.588 | 139.31 |
| stream | energy | parallel | fixed-default | 294.497 | 118.607 | 139.22 |
| stream | energy | parallel | fixed-explicit | 293.688 | 117.147 | 139.23 |

## launcher-control

| Scope | Input | Policy | Implementation | CPU ms | Elapsed ms | Peak RSS MiB |
|---|---|---|---|---:|---:|---:|
| stream | energy | parallel | short | 292.683 | 117.647 | 139.33 |
| stream | energy | parallel | production-name | 290.801 | 117.561 | 139.48 |
| stream | energy | parallel | screen-name | 275.602 | 114.831 | 139.33 |

## local-builder-screen

| Scope | Input | Policy | Implementation | CPU ms | Elapsed ms | Peak RSS MiB |
|---|---|---|---|---:|---:|---:|
| stream | energy | parallel | parent | 272.928 | 115.628 | 139.18 |
| stream | energy | parallel | candidate | 295.135 | 119.175 | 139.43 |
| stream | energy | parallel | fixed | 276.219 | 115.036 | 139.24 |
| stream | energy | parallel | local-builder | 260.046 | 111.046 | 139.14 |
| stream | energy | parallel | local-builder-inline | 256.540 | 110.379 | 139.34 |
| stream | energy | parallel | local-builder-parent | 272.938 | 116.125 | 139.15 |
| stream | energy | serial | parent | 232.476 | 232.514 | 136.44 |
| stream | energy | serial | candidate | 220.627 | 220.709 | 136.53 |
| stream | energy | serial | fixed | 220.773 | 220.806 | 136.48 |
| stream | energy | serial | local-builder | 220.881 | 220.984 | 136.45 |
| stream | energy | serial | local-builder-inline | 218.202 | 218.247 | 136.49 |
| stream | energy | serial | local-builder-parent | 235.460 | 235.685 | 136.45 |
| eager | energy | parallel | parent | 283.342 | 123.157 | 422.34 |
| eager | energy | parallel | candidate | 274.719 | 120.965 | 422.34 |
| eager | energy | parallel | fixed | 277.956 | 120.832 | 422.29 |
| eager | energy | parallel | local-builder | 280.002 | 120.817 | 422.36 |
| eager | energy | parallel | local-builder-inline | 275.208 | 121.034 | 422.30 |
| eager | energy | parallel | local-builder-parent | 281.885 | 122.758 | 422.33 |
| eager | energy | serial | parent | 247.879 | 248.028 | 420.56 |
| eager | energy | serial | candidate | 238.339 | 238.410 | 420.53 |
| eager | energy | serial | fixed | 244.071 | 244.165 | 420.50 |
| eager | energy | serial | local-builder | 244.154 | 244.245 | 420.55 |
| eager | energy | serial | local-builder-inline | 248.007 | 248.069 | 420.52 |
| eager | energy | serial | local-builder-parent | 250.927 | 250.983 | 420.57 |
| stream | energy-date-full | parallel | parent | 305.083 | 140.050 | 138.40 |
| stream | energy-date-full | parallel | candidate | 294.870 | 141.526 | 138.96 |
| stream | energy-date-full | parallel | fixed | 296.379 | 140.056 | 139.10 |
| stream | energy-date-full | parallel | local-builder | 296.645 | 139.720 | 139.02 |
| stream | energy-date-full | parallel | local-builder-inline | 295.666 | 140.519 | 139.05 |
| stream | energy-date-full | parallel | local-builder-parent | 305.178 | 141.617 | 138.71 |
| stream | energy-date-full | serial | parent | 259.206 | 259.421 | 136.44 |
| stream | energy-date-full | serial | candidate | 250.823 | 250.868 | 136.59 |
| stream | energy-date-full | serial | fixed | 251.900 | 251.943 | 136.45 |
| stream | energy-date-full | serial | local-builder | 253.524 | 253.568 | 136.47 |
| stream | energy-date-full | serial | local-builder-inline | 251.821 | 251.888 | 136.48 |
| stream | energy-date-full | serial | local-builder-parent | 262.291 | 262.333 | 136.57 |

