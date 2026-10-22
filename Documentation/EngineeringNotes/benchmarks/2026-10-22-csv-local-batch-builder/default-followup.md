# Default-token resource follow-up

Five inputs have 32 observations per implementation and policy. These 640 additional reads preserve the original final matrix. They review its flagged default-token case and retain real air-quality and mixed-column controls. No outlier is removed. Absolute timings vary across studies. See the [study methods](README.md).

| Input | Policy | Parent CPU ms | Candidate CPU ms | CPU change | Peak RSS MiB, parent to candidate |
|---|---|---:|---:|---:|---:|
| all-string-default-nulls-0 | parallel | 8.164 | 7.873 | -3.6% | 9.16 to 9.11 |
| all-string-default-nulls-0 | serial | 6.403 | 6.869 | +7.3% | 9.07 to 9.05 |
| all-string-default-nulls-50 | parallel | 4.040 | 3.913 | -3.2% | 9.11 to 9.09 |
| all-string-default-nulls-50 | serial | 3.856 | 3.832 | -0.6% | 9.03 to 9.02 |
| all-string-default-nulls-90 | parallel | 3.256 | 3.238 | -0.6% | 9.06 to 9.03 |
| all-string-default-nulls-90 | serial | 3.184 | 3.193 | +0.3% | 9.02 to 9.00 |
| default-nulls-0 | parallel | 2.785 | 3.040 | +9.1% | 9.11 to 9.11 |
| default-nulls-0 | serial | 2.877 | 2.833 | -1.5% | 9.06 to 9.05 |
| Aotizhongxin-default | parallel | 12.293 | 12.232 | -0.5% | 23.09 to 23.16 |
| Aotizhongxin-default | serial | 9.342 | 9.324 | -0.2% | 22.84 to 22.88 |
