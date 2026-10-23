# CSV Double storage choice resource results

Eight fresh processes per label. CPU includes public CSV construction, requested operations and release. Full output validation is outside timing. All outputs match the original reader. Original always uses optional Double arrays. Prior always uses compact Double buffers. Current and twin honor the storage choice in each case. The choice intentionally changes physical representation while preserving the same logical input and output contract.

| Case | CPU original / prior / current, ms | Held heap original / prior / current, MiB | Peak RSS original / prior / current, MiB |
|---|---:|---:|---:|
| energy-common/serial/optional/join-materialize | 711.57 / 495.33 / 717.52 | 316.83 / 429.48 / 316.83 | 642.44 / 550.20 / 642.47 |
| energy-common/serial/optional/batch | 252.59 / 250.04 / 251.83 | 397.81 / 176.11 / 397.81 | 420.61 / 312.41 / 420.64 |
| energy-common/serial/compact/join-materialize | 701.52 / 478.67 / 476.77 | 316.83 / 429.48 / 429.48 | 642.44 / 550.20 / 550.22 |
| energy-common/serial/compact/batch | 265.16 / 258.65 / 254.81 | 397.81 / 176.11 / 176.11 | 422.03 / 313.11 / 312.47 |
| energy-common/parallel/optional/join-materialize | 731.64 / 502.46 / 726.85 | 316.83 / 429.48 / 316.83 | 644.29 / 552.00 / 644.30 |
| energy-common/parallel/optional/batch | 285.82 / 282.09 / 293.55 | 397.81 / 176.11 / 397.81 | 422.47 / 314.24 / 422.49 |
| energy-common/parallel/compact/join-materialize | 720.64 / 504.51 / 505.39 | 316.83 / 429.48 / 429.48 | 644.23 / 551.88 / 552.03 |
| energy-common/parallel/compact/batch | 281.64 / 273.35 / 283.46 | 397.81 / 176.11 / 176.11 | 422.41 / 314.33 / 314.31 |
| Aotizhongxin-default/serial/optional/join-materialize | 22.09 / 16.23 / 22.09 | 10.50 / 13.65 / 10.50 | 29.03 / 22.80 / 29.02 |
| Aotizhongxin-default/serial/optional/batch | 8.72 / 8.52 / 8.77 | 14.51 / 8.49 / 14.51 | 22.89 / 21.78 / 22.92 |
| Aotizhongxin-default/serial/compact/join-materialize | 22.50 / 16.20 / 16.36 | 10.50 / 13.65 / 13.65 | 29.05 / 22.83 / 22.77 |
| Aotizhongxin-default/serial/compact/batch | 8.59 / 8.44 / 8.46 | 14.51 / 8.49 / 8.49 | 22.92 / 21.78 / 21.77 |
| Aotizhongxin-default/parallel/optional/join-materialize | 25.54 / 19.15 / 25.13 | 10.50 / 13.65 / 10.50 | 29.33 / 23.10 / 29.49 |
| Aotizhongxin-default/parallel/optional/batch | 11.83 / 11.48 / 11.79 | 14.51 / 8.49 / 14.51 | 23.20 / 22.08 / 23.38 |
| Aotizhongxin-default/parallel/compact/join-materialize | 25.08 / 19.22 / 19.16 | 10.50 / 13.65 / 13.65 | 29.34 / 23.09 / 23.05 |
| Aotizhongxin-default/parallel/compact/batch | 11.85 / 11.55 / 11.58 | 14.51 / 8.49 / 8.49 | 23.37 / 22.05 / 22.02 |

Identical-binary flags: []. Flagged cases remain unqualified. These are CPU and allocation measurements, not energy, FLOP or cache measurements.
