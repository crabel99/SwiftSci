# acceptance results

CPU is process user-plus-system time. Peak RSS is a whole-process high-water mark. Elapsed time is separate.

| Scope / case | Policy / candidate | CPU before ms | CPU after ms | Change | Elapsed before / after ms | Peak before / after MiB |
|---|---|---:|---:|---:|---:|---:|
| eager / bike-day | known parallel | 0.973 | 0.949 | -2.5% | 0.453 / 0.435 | 7.80 / 7.77 |
| eager / bike-day | known serial | 0.436 | 0.430 | -1.3% | 0.436 / 0.429 | 7.56 / 7.56 |
| eager / bike-hour | known parallel | 5.449 | 5.436 | -0.2% | 2.098 / 2.093 | 15.81 / 15.80 |
| eager / bike-hour | known serial | 3.866 | 3.818 | -1.2% | 3.868 / 3.827 | 15.55 / 15.53 |
| eager / unique-shuffled | known parallel | 6.466 | 6.737 | +4.2% | 5.747 / 6.023 | 12.36 / 12.36 |
| eager / unique-shuffled | known serial | 6.239 | 6.726 | +7.8% | 6.240 / 6.733 | 12.31 / 12.31 |
| eager / Aotizhongxin | known parallel | 11.741 | 12.055 | +2.7% | 4.615 / 4.669 | 23.15 / 23.08 |
| eager / Aotizhongxin | known serial | 8.800 | 8.644 | -1.8% | 8.806 / 8.648 | 22.86 / 22.81 |
| eager / Wanliu | known parallel | 11.567 | 11.765 | +1.7% | 4.635 / 4.670 | 22.97 / 22.91 |
| eager / Wanliu | known serial | 8.767 | 8.657 | -1.2% | 8.770 / 8.666 | 22.67 / 22.62 |
| eager / energy | known parallel | 272.125 | 274.914 | +1.0% | 123.077 / 125.144 | 422.32 / 422.33 |
| eager / energy | known serial | 254.706 | 252.353 | -0.9% | 254.737 / 252.486 | 420.61 / 421.85 |
| eager / energy | infer parallel | 270.039 | 275.339 | +2.0% | 123.163 / 125.373 | 422.34 / 422.34 |
| eager / energy | infer serial | 257.579 | 257.231 | -0.1% | 257.634 / 257.253 | 421.26 / 420.61 |
| eager / energy-date-full | known parallel | 312.212 | 316.486 | +1.4% | 150.338 / 153.027 | 422.27 / 422.27 |
| eager / energy-date-full | known serial | 275.486 | 281.795 | +2.3% | 275.687 / 281.984 | 420.56 / 421.98 |
| eager / late-bool | infer parallel | 6.740 | 6.730 | -0.1% | 6.790 / 6.771 | 9.73 / 9.73 |
| eager / late-bool | infer serial | 6.755 | 6.692 | -0.9% | 6.795 / 6.767 | 9.73 / 9.73 |
| eager / late-text | infer parallel | 7.744 | 7.826 | +1.1% | 7.796 / 7.877 | 16.89 / 16.88 |
| eager / late-text | infer serial | 7.707 | 7.806 | +1.3% | 7.760 / 7.845 | 16.91 / 16.88 |
| stream / date-100000-1 | known parallel | 4.552 | 4.781 | +5.0% | 4.618 / 4.827 | 8.62 / 8.59 |
| stream / date-100000-1 | known serial | 4.498 | 4.611 | +2.5% | 4.543 / 4.672 | 8.61 / 8.58 |
| stream / bike-hour | known parallel | 5.159 | 5.176 | +0.3% | 2.035 / 2.040 | 12.91 / 12.91 |
| stream / bike-hour | known serial | 3.398 | 3.359 | -1.1% | 3.436 / 3.404 | 12.59 / 12.57 |
| stream / unique-shuffled | known parallel | 5.698 | 5.812 | +2.0% | 5.085 / 5.178 | 9.47 / 9.48 |
| stream / unique-shuffled | known serial | 5.521 | 5.546 | +0.5% | 5.578 / 5.589 | 9.42 / 9.45 |
| stream / Aotizhongxin | known parallel | 11.040 | 11.418 | +3.4% | 4.080 / 4.141 | 15.67 / 15.77 |
| stream / Aotizhongxin | known serial | 7.734 | 7.522 | -2.7% | 7.775 / 7.572 | 16.08 / 14.38 |
| stream / energy | known parallel | 256.733 | 257.894 | +0.5% | 111.090 / 112.189 | 139.07 / 139.28 |
| stream / energy | known serial | 218.913 | 224.160 | +2.4% | 218.996 / 224.224 | 136.50 / 136.46 |
| stream / energy-date-full | known parallel | 290.638 | 296.731 | +2.1% | 141.521 / 140.454 | 138.96 / 138.55 |
| stream / energy-date-full | known serial | 251.724 | 248.716 | -1.2% | 251.801 / 249.361 | 136.48 / 136.50 |
| eager / Aotizhongxin-default | known parallel | 12.393 | 11.701 | -5.6% | 4.928 / 4.648 | 23.15 / 23.11 |
| eager / Aotizhongxin-default | known serial | 9.178 | 8.484 | -7.6% | 9.295 / 8.541 | 22.88 / 22.84 |
| eager / energy-default | known parallel | 509.538 | 426.428 | -16.3% | 192.122 / 144.373 | 422.41 / 422.45 |
| eager / energy-default | known serial | 323.307 | 249.047 | -23.0% | 323.350 / 249.104 | 420.56 / 421.09 |
| stream / energy-default | known parallel | 495.773 | 382.808 | -22.8% | 187.712 / 132.927 | 139.20 / 139.23 |
| stream / energy-default | known serial | 294.892 | 223.925 | -24.1% | 294.946 / 224.541 | 137.67 / 136.50 |
