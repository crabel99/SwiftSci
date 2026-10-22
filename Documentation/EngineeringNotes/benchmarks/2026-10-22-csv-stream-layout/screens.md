# Compiler-boundary screening

These 400 diagnostic observations select the candidate for final qualification. The earlier 32-process reproduction overlapped a build and contributes no timing evidence. See the [study methods](README.md).

| Scope | Case | Policy | Implementation | CPU ms | Elapsed ms | Peak RSS MiB |
|---|---|---|---|---:|---:|---:|
| eager | energy | parallel | parent | 284.810 | 126.814 | 422.10 |
| eager | energy | parallel | candidate | 271.311 | 122.939 | 422.27 |
| eager | energy | parallel | dispatch-inline | 278.775 | 125.548 | 420.84 |
| eager | energy | parallel | attempt-outline | 276.366 | 123.167 | 420.81 |
| eager | energy | parallel | direct-value | 274.103 | 123.706 | 422.26 |
| eager | energy | serial | parent | 249.401 | 249.480 | 420.58 |
| eager | energy | serial | candidate | 240.224 | 240.352 | 420.53 |
| eager | energy | serial | dispatch-inline | 242.374 | 242.796 | 420.52 |
| eager | energy | serial | attempt-outline | 244.810 | 244.862 | 420.50 |
| eager | energy | serial | direct-value | 246.773 | 246.843 | 420.48 |
| stream | energy | parallel | parent | 276.660 | 116.564 | 138.80 |
| stream | energy | parallel | candidate | 294.715 | 119.440 | 139.33 |
| stream | energy | parallel | dispatch-inline | 264.490 | 113.080 | 138.90 |
| stream | energy | parallel | attempt-outline | 260.592 | 112.744 | 139.01 |
| stream | energy | parallel | direct-value | 263.123 | 114.495 | 139.19 |
| stream | energy | serial | parent | 234.135 | 234.181 | 136.45 |
| stream | energy | serial | candidate | 221.750 | 221.832 | 136.54 |
| stream | energy | serial | dispatch-inline | 226.134 | 226.178 | 136.44 |
| stream | energy | serial | attempt-outline | 221.334 | 221.368 | 136.47 |
| stream | energy | serial | direct-value | 219.195 | 219.271 | 136.44 |
| stream | energy-date-full | parallel | parent | 305.533 | 141.148 | 138.84 |
| stream | energy-date-full | parallel | candidate | 295.716 | 142.481 | 138.44 |
| stream | energy-date-full | parallel | dispatch-inline | 300.459 | 141.881 | 138.77 |
| stream | energy-date-full | parallel | attempt-outline | 298.512 | 141.600 | 138.84 |
| stream | energy-date-full | parallel | direct-value | 298.468 | 139.944 | 139.13 |
| stream | energy-date-full | serial | parent | 265.750 | 265.809 | 137.59 |
| stream | energy-date-full | serial | candidate | 255.565 | 255.653 | 136.66 |
| stream | energy-date-full | serial | dispatch-inline | 256.584 | 256.647 | 136.42 |
| stream | energy-date-full | serial | attempt-outline | 252.816 | 252.895 | 137.60 |
| stream | energy-date-full | serial | direct-value | 258.106 | 258.145 | 136.50 |
| stream | Aotizhongxin | parallel | parent | 11.868 | 4.207 | 15.68 |
| stream | Aotizhongxin | parallel | candidate | 11.552 | 4.131 | 15.80 |
| stream | Aotizhongxin | parallel | dispatch-inline | 11.521 | 4.128 | 15.69 |
| stream | Aotizhongxin | parallel | attempt-outline | 11.979 | 4.151 | 15.69 |
| stream | Aotizhongxin | parallel | direct-value | 11.823 | 4.090 | 15.73 |
| stream | Aotizhongxin | serial | parent | 7.841 | 7.894 | 17.79 |
| stream | Aotizhongxin | serial | candidate | 7.540 | 7.600 | 14.45 |
| stream | Aotizhongxin | serial | dispatch-inline | 7.583 | 7.636 | 14.34 |
| stream | Aotizhongxin | serial | attempt-outline | 7.468 | 7.511 | 14.38 |
| stream | Aotizhongxin | serial | direct-value | 7.495 | 7.551 | 14.39 |
