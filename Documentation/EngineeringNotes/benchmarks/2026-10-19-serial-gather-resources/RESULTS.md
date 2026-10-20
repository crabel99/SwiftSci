# Serial gather resource results

All values include the API call and result release. CPU change is the median of five paired ratios. Ranges are observed paired ratios, not confidence intervals. RSS includes process setup and input construction. Heap delta measures live malloc storage while the output is held.

| Operation and source | CPU ms before → after | CPU change | CPU ratio range | Elapsed ms before → after | Peak RSS MiB before → after | Held heap MiB before → after |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| sort, 4,096 × 4, numeric, random, asc | 0.079 → 0.079 | +1.3% | 0.987–1.026 | 0.078 → 0.079 | 7.33 → 7.31 | 0.31 → 0.31 |
| sort, 1,000,000 × 4, numeric, random, asc | 35.218 → 35.092 | +1.9% | 0.975–1.042 | 22.786 → 22.776 | 155.67 → 155.66 | 61.06 → 61.06 |
| sort, 250,003 × 3, mixed, ties, asc | 21.215 → 9.922 | -49.8% | 0.365–0.521 | 15.385 → 9.339 | 49.25 → 49.27 | 7.91 → 7.91 |
| sort, 250,003 × 8, mixed, ties, asc | 90.018 → 39.485 | -56.3% | 0.430–0.489 | 37.603 → 20.966 | 117.05 → 117.09 | 23.47 → 23.47 |
| sort, 1,000,000 × 4, mixed, random, asc | 154.540 → 78.032 | -48.8% | 0.499–0.532 | 124.795 → 70.319 | 200.00 → 200.02 | 46.77 → 46.77 |
| sort, 250,003 × 4, mixed, nulls, desc | 26.272 → 13.184 | -55.2% | 0.434–0.541 | 19.822 → 11.914 | 56.78 → 56.80 | 11.74 → 11.74 |
| gather, 250,003 × 3, mixed, ties, asc | 16.832 → 5.433 | -68.6% | 0.250–0.339 | 11.105 → 4.878 | 43.38 → 43.39 | 7.91 → 7.91 |
| gather, 250,003 × 8, mixed, ties, asc | 81.140 → 38.591 | -52.4% | 0.429–0.496 | 32.974 → 19.457 | 110.95 → 110.95 | 23.47 → 23.47 |
| gather, 1,000,000 × 4, mixed, random, asc | 129.432 → 61.787 | -54.1% | 0.444–0.493 | 101.932 → 54.388 | 184.64 → 184.64 | 46.77 → 46.77 |
| sort, 250,003 × 4, dates, nulls, asc | 11.551 → 13.434 | +23.8% | 1.150–1.275 | 6.141 → 6.704 | 45.30 → 45.31 | 15.31 → 15.31 |
| gather, 250,003 × 4, dates, random, asc | 7.285 → 11.356 | +48.7% | 1.335–1.643 | 2.349 → 3.990 | 40.28 → 40.30 | 15.31 → 15.31 |
| sort, 4,096 × 4, mixed, random, asc | 0.282 → 0.118 | -58.3% | 0.411–0.442 | 0.281 → 0.118 | 7.52 → 7.52 | 0.24 → 0.24 |
