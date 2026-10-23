# acceptance results

CPU is process user-plus-system time. Peak RSS is a process high-water mark, not allocations. Elapsed time is separate.

| Scope and case | Policy | Parent CPU ms | Metadata CPU ms | CPU change | Elapsed before / after ms | Peak before / after MiB |
|---|---|---:|---:|---:|---:|---:|
| eager bike-day | parallel | 0.775 | 0.752 | -3.0% | 0.434 / 0.428 | 7.74 / 7.75 |
| eager bike-day | serial | 0.410 | 0.407 | -0.7% | 0.458 / 0.447 | 7.56 / 7.58 |
| eager bike-hour | parallel | 5.293 | 5.314 | +0.4% | 2.062 / 2.058 | 15.81 / 15.83 |
| eager bike-hour | serial | 3.687 | 3.655 | -0.9% | 3.742 / 3.673 | 15.56 / 15.56 |
| eager unique-shuffled | parallel | 6.146 | 6.340 | +3.1% | 5.458 / 5.678 | 12.33 / 12.36 |
| eager unique-shuffled | serial | 5.984 | 6.298 | +5.2% | 6.025 / 6.337 | 12.31 / 12.34 |
| eager Aotizhongxin | parallel | 11.665 | 11.774 | +0.9% | 4.661 / 4.565 | 23.14 / 23.11 |
| eager Aotizhongxin | serial | 8.307 | 8.350 | +0.5% | 8.348 / 8.391 | 22.86 / 22.84 |
| eager Wanliu | parallel | 11.539 | 11.591 | +0.5% | 4.642 / 4.674 | 22.92 / 22.92 |
| eager Wanliu | serial | 8.367 | 8.322 | -0.5% | 8.397 / 8.367 | 22.67 / 22.66 |
| eager energy | parallel | 279.122 | 278.633 | -0.2% | 122.847 / 121.263 | 422.30 / 422.35 |
| eager energy | serial | 245.887 | 249.576 | +1.5% | 246.016 / 249.695 | 420.52 / 420.55 |
| eager energy | parallel | 280.632 | 282.098 | +0.5% | 125.568 / 124.431 | 422.43 / 422.36 |
| eager energy | serial | 257.382 | 259.627 | +0.9% | 257.610 / 260.483 | 421.97 / 422.00 |
| eager energy-date-full | parallel | 316.401 | 317.163 | +0.2% | 152.766 / 153.013 | 422.33 / 422.30 |
| eager energy-date-full | serial | 282.951 | 281.594 | -0.5% | 283.302 / 281.674 | 421.98 / 421.13 |
| eager late-bool | parallel | 6.629 | 6.686 | +0.9% | 6.679 / 6.726 | 9.73 / 9.73 |
| eager late-bool | serial | 6.723 | 6.822 | +1.5% | 6.777 / 6.879 | 9.73 / 9.73 |
| eager late-text | parallel | 7.729 | 7.718 | -0.1% | 7.822 / 7.768 | 16.89 / 16.89 |
| eager late-text | serial | 7.761 | 7.776 | +0.2% | 7.835 / 7.805 | 16.89 / 16.89 |
| stream date-100000-1 | parallel | 4.750 | 4.652 | -2.1% | 4.797 / 4.712 | 8.61 / 8.59 |
| stream date-100000-1 | serial | 4.604 | 4.561 | -0.9% | 4.657 / 4.619 | 8.61 / 8.59 |
| stream bike-hour | parallel | 5.207 | 5.253 | +0.9% | 2.056 / 2.012 | 12.93 / 12.90 |
| stream bike-hour | serial | 3.482 | 3.461 | -0.6% | 3.536 / 3.489 | 12.62 / 12.56 |
| stream unique-shuffled | parallel | 5.788 | 5.865 | +1.3% | 5.146 / 5.224 | 9.48 / 9.52 |
| stream unique-shuffled | serial | 5.697 | 5.671 | -0.4% | 5.730 / 5.705 | 9.43 / 9.42 |
| stream Aotizhongxin | parallel | 10.900 | 10.924 | +0.2% | 4.170 / 4.160 | 15.38 / 15.45 |
| stream Aotizhongxin | serial | 7.801 | 7.848 | +0.6% | 7.838 / 7.868 | 16.09 / 14.38 |
| stream energy | parallel | 262.605 | 259.145 | -1.3% | 114.335 / 113.684 | 139.27 / 139.34 |
| stream energy | serial | 219.788 | 224.874 | +2.3% | 219.888 / 224.954 | 136.52 / 136.47 |
| stream energy-date-full | parallel | 299.082 | 297.114 | -0.7% | 142.338 / 142.724 | 139.14 / 139.04 |
| stream energy-date-full | serial | 257.701 | 251.930 | -2.2% | 257.848 / 252.074 | 136.50 / 136.52 |
| eager Aotizhongxin-default | parallel | 12.319 | 11.991 | -2.7% | 5.083 / 4.644 | 23.14 / 23.13 |
| eager Aotizhongxin-default | serial | 9.379 | 8.568 | -8.7% | 9.418 / 8.626 | 22.88 / 22.84 |
| eager energy-default | parallel | 482.961 | 435.517 | -9.8% | 198.244 / 152.270 | 422.46 / 422.48 |
| eager energy-default | serial | 336.433 | 260.628 | -22.5% | 336.544 / 260.713 | 420.56 / 420.61 |
| stream energy-default | parallel | 470.997 | 388.417 | -17.5% | 184.198 / 135.588 | 139.07 / 139.50 |
| stream energy-default | serial | 300.202 | 227.497 | -24.2% | 300.757 / 227.624 | 136.52 / 136.76 |
