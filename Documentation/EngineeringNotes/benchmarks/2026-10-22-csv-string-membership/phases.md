# String-field replay costs

Each worker runs each phase eight times per String column. The table gives the median of each worker median, across six workers. Replay preparation is untimed. These costs are not additive fractions of complete-read time. [Study record](README.md).

| Input | Column | Phase | CPU ms | Elapsed ms | Held heap delta MiB | Held RSS delta MiB |
|---|---|---|---:|---:|---:|---:|
| Aotizhongxin-default | station | copy | 0.203 | 0.202 | 0.547 | 0.000 |
| Aotizhongxin-default | station | match | 0.692 | 0.690 | 0.547 | 0.000 |
| Aotizhongxin-default | station | parse | 0.466 | 0.465 | 0.547 | 0.000 |
| Aotizhongxin-default | station | parse-match | 0.856 | 0.854 | 0.547 | 0.000 |
| Aotizhongxin-default | wd | copy | 0.206 | 0.204 | 0.547 | 0.000 |
| Aotizhongxin-default | wd | match | 0.784 | 0.782 | 0.547 | 0.000 |
| Aotizhongxin-default | wd | parse | 0.509 | 0.508 | 0.547 | 0.000 |
| Aotizhongxin-default | wd | parse-match | 1.078 | 1.076 | 0.547 | 0.000 |
| all-string-default-nulls-0 | id | copy | 0.192 | 0.190 | 0.516 | 0.000 |
| all-string-default-nulls-0 | id | match | 0.864 | 0.862 | 0.516 | 0.000 |
| all-string-default-nulls-0 | id | parse | 0.444 | 0.443 | 0.516 | 0.000 |
| all-string-default-nulls-0 | id | parse-match | 1.204 | 1.203 | 0.516 | 0.000 |
| all-string-default-nulls-0 | text | copy | 0.189 | 0.186 | 0.516 | 0.000 |
| all-string-default-nulls-0 | text | match | 1.416 | 1.416 | 0.516 | 0.000 |
| all-string-default-nulls-0 | text | parse | 0.499 | 0.499 | 0.516 | 0.000 |
| all-string-default-nulls-0 | text | parse-match | 1.843 | 1.840 | 0.516 | 0.000 |
| energy-default | Date | copy | 12.200 | 12.269 | 31.672 | 0.000 |
| energy-default | Date | match | 45.008 | 45.024 | 31.672 | 0.000 |
| energy-default | Date | parse | 25.817 | 25.941 | 31.672 | 0.000 |
| energy-default | Date | parse-match | 53.889 | 53.901 | 31.672 | 0.000 |
| energy-default | Time | copy | 12.129 | 12.126 | 31.672 | 0.000 |
| energy-default | Time | match | 58.199 | 58.209 | 31.672 | 0.000 |
| energy-default | Time | parse | 25.428 | 25.537 | 31.672 | 0.000 |
| energy-default | Time | parse-match | 80.200 | 80.332 | 31.672 | 0.000 |
