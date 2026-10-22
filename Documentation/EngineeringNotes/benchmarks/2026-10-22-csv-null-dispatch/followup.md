# Streaming resource follow-up

The first final matrix reports a parallel household streaming CPU increase. This follow-up uses 24 balanced orders, with 24 observations per implementation and policy for four cases. The original results remain unchanged. See the [study methods](README.md).

| Input and schema | Policy | CPU ms, parent to final | CPU change | Elapsed ms, parent to final | Peak RSS MiB, parent to final |
|---|---|---:|---:|---:|---:|
| eager energy known | parallel | 282.236 to 277.080 | -1.8% | 123.016 to 120.653 | 422.34 to 422.32 |
| eager energy known | serial | 245.903 to 238.138 | -3.2% | 245.950 to 238.180 | 420.58 to 420.53 |
| stream energy known | parallel | 274.829 to 296.195 | +7.8% | 116.189 to 119.822 | 138.98 to 139.34 |
| stream energy known | serial | 233.248 to 220.405 | -5.5% | 233.341 to 220.447 | 136.45 to 136.53 |
| stream energy-date-full known | parallel | 306.678 to 298.705 | -2.6% | 143.054 to 144.870 | 138.84 to 138.93 |
| stream energy-date-full known | serial | 268.700 to 261.067 | -2.8% | 268.827 to 261.138 | 137.56 to 136.58 |
| stream Aotizhongxin known | parallel | 11.801 to 11.693 | -0.9% | 4.252 to 4.159 | 15.70 to 15.79 |
| stream Aotizhongxin known | serial | 7.814 to 7.588 | -2.9% | 7.867 to 7.633 | 16.06 to 14.48 |
