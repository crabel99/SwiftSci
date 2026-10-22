# Additional fallback measurements

These native fresh-process observations retain the original final matrix unchanged. The committed column uses row-null in the raw records. Boundary trial uses batch-null. The trial is not production code. Control cases have 42 samples per implementation and policy. The default air-quality reference has six. No outliers are removed. See [study methods](README.md).

| Input | Policy | Samples per implementation | CPU ms, parent → committed → boundary trial | Committed CPU change | Peak RSS MiB, parent → committed |
|---|---|---:|---:|---:|---:|
| all-string-default-nulls-0 | parallel | 42 | 4.021 → 4.096 → 3.944 | +1.9% | 9.06 → 9.12 |
| all-string-default-nulls-0 | serial | 42 | 3.950 → 3.768 → 3.793 | -4.6% | 8.95 → 9.05 |
| all-string-default-nulls-50 | parallel | 42 | 3.652 → 3.737 → 3.675 | +2.3% | 9.06 → 9.11 |
| all-string-default-nulls-50 | serial | 42 | 3.518 → 3.543 → 3.627 | +0.7% | 8.95 → 9.03 |
| all-string-default-nulls-90 | parallel | 42 | 3.176 → 3.186 → 3.168 | +0.3% | 9.02 → 9.06 |
| all-string-default-nulls-90 | serial | 42 | 3.116 → 3.107 → 3.110 | -0.3% | 8.94 → 9.02 |
| default-nulls-0 | parallel | 42 | 2.938 → 3.018 → 2.971 | +2.7% | 9.10 → 9.16 |
| default-nulls-0 | serial | 42 | 2.898 → 2.949 → 2.999 | +1.7% | 9.00 → 9.06 |
| four-nulls-50 | parallel | 42 | 3.749 → 3.744 → 3.751 | -0.1% | 9.03 → 9.12 |
| four-nulls-50 | serial | 42 | 3.756 → 3.732 → 3.684 | -0.7% | 8.97 → 9.05 |
| large-nulls-0 | parallel | 42 | 21.758 → 21.706 → 21.720 | -0.2% | 9.59 → 9.64 |
| large-nulls-0 | serial | 42 | 21.448 → 21.440 → 21.357 | -0.0% | 9.50 → 9.56 |
| all-string-large-nulls-0 | parallel | 42 | 3.971 → 3.964 → 4.007 | -0.2% | 9.45 → 9.50 |
| all-string-large-nulls-0 | serial | 42 | 3.945 → 3.845 → 3.833 | -2.5% | 9.34 → 9.42 |
| all-string-none-nulls-0 | parallel | 42 | 1.851 → 1.875 → 1.867 | +1.3% | 9.02 → 9.08 |
| all-string-none-nulls-0 | serial | 42 | 1.777 → 1.794 → 1.792 | +0.9% | 8.95 → 9.03 |
| Aotizhongxin-default | parallel | 6 | 12.627 → 13.014 → 12.702 | +3.1% | 23.03 → 23.13 |
| Aotizhongxin-default | serial | 6 | 9.164 → 9.030 → 9.077 | -1.5% | 22.77 → 22.87 |
