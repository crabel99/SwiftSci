# Serial gather resource results

All values include the API call and result release. CPU change is the median of five paired ratios. Ranges are observed paired ratios, not confidence intervals. RSS includes process setup and input construction. Heap delta measures live malloc storage while the output is held.

| Operation and source | CPU ms before → after | CPU change | CPU ratio range | Elapsed ms before → after | Peak RSS MiB before → after | Held heap MiB before → after |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| sort, 4,096 × 4, numeric, random, asc | 0.079 → 0.078 | -1.3% | 0.939–1.013 | 0.078 → 0.077 | 7.33 → 7.33 | 0.31 → 0.31 |
| sort, 1,000,000 × 4, numeric, random, asc | 34.006 → 34.685 | +1.1% | 0.998–1.066 | 22.141 → 22.317 | 155.67 → 155.67 | 61.06 → 61.06 |
| sort, 250,003 × 3, mixed, ties, asc | 23.399 → 8.806 | -61.8% | 0.362–0.421 | 17.516 → 8.276 | 49.23 → 49.28 | 7.91 → 7.91 |
| sort, 250,003 × 8, mixed, ties, asc | 89.533 → 40.746 | -54.5% | 0.454–0.468 | 38.494 → 21.787 | 117.03 → 117.06 | 23.47 → 23.47 |
| sort, 1,000,000 × 4, mixed, random, asc | 147.009 → 76.378 | -48.0% | 0.469–0.534 | 118.385 → 68.713 | 199.98 → 200.02 | 46.77 → 46.77 |
| sort, 250,003 × 4, mixed, nulls, desc | 23.159 → 10.650 | -53.3% | 0.432–0.495 | 16.952 → 9.562 | 56.77 → 56.80 | 11.74 → 11.74 |
| gather, 250,003 × 3, mixed, ties, asc | 16.530 → 5.381 | -66.6% | 0.309–0.353 | 11.001 → 4.839 | 43.36 → 43.38 | 7.91 → 7.91 |
| gather, 250,003 × 8, mixed, ties, asc | 82.434 → 37.520 | -54.6% | 0.446–0.501 | 34.024 → 18.912 | 110.94 → 110.97 | 23.47 → 23.47 |
| gather, 1,000,000 × 4, mixed, random, asc | 127.065 → 58.208 | -54.4% | 0.454–0.473 | 99.193 → 50.955 | 184.61 → 184.64 | 46.77 → 46.77 |
| sort, 250,003 × 4, dates, nulls, asc | 10.417 → 10.452 | +0.3% | 0.896–1.020 | 5.682 → 5.705 | 45.30 → 45.31 | 15.31 → 15.31 |
| gather, 250,003 × 4, dates, random, asc | 7.145 → 7.178 | +0.5% | 0.981–1.145 | 2.296 → 2.312 | 40.28 → 40.28 | 15.31 → 15.31 |
| sort, 4,096 × 4, mixed, random, asc | 0.277 → 0.117 | -58.1% | 0.416–0.432 | 0.277 → 0.117 | 7.50 → 7.52 | 0.24 → 0.24 |
| sort, 131,071 × 3, dates, random, desc | 4.205 → 4.201 | -0.4% | 0.991–1.002 | 3.019 → 3.007 | 23.00 → 23.00 | 6.05 → 6.05 |
| gather, 512,003 × 8, dates, nulls, asc | 53.567 → 53.497 | +0.3% | 0.974–1.023 | 8.089 → 8.247 | 138.12 → 138.14 | 62.63 → 62.63 |
