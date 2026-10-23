# Ordered and disordered sort controls

Eight fresh processes per label. CPU covers public sorting and index release with the input frame retained. CSV construction and exact validation are excluded. Original always has optional storage; prior, current and twin honor the requested choice.

| Shape / count / storage | CPU prior / current, ms | Held heap prior / current, MiB | Peak RSS prior / current, MiB |
|---|---:|---:|---:|
| ascending-1000000 / optional | 4.503 / 5.318 | 23.011 / 23.011 | 45.781 / 45.766 |
| ascending-1000000 / compact | 4.120 / 4.944 | 15.386 / 15.386 | 38.156 / 38.141 |
| ascending-32768 / optional | 0.146 / 0.164 | 0.886 / 0.886 | 8.469 / 8.453 |
| ascending-32768 / compact | 0.138 / 0.161 | 0.636 / 0.636 | 8.250 / 8.234 |
| descending-1000000 / optional | 76.924 / 77.014 | 23.011 / 23.011 | 45.797 / 45.750 |
| descending-1000000 / compact | 69.386 / 71.165 | 15.386 / 15.386 | 38.141 / 38.125 |
| descending-32768 / optional | 1.581 / 1.613 | 0.886 / 0.886 | 8.469 / 8.453 |
| descending-32768 / compact | 1.298 / 1.360 | 0.636 / 0.636 | 8.219 / 8.203 |
| nearby-swaps-1000000 / optional | 12.216 / 13.002 | 23.011 / 23.011 | 45.781 / 45.766 |
| nearby-swaps-1000000 / compact | 9.957 / 10.794 | 15.386 / 15.386 | 38.172 / 38.141 |
| nearby-swaps-32768 / optional | 0.248 / 0.273 | 0.886 / 0.886 | 8.469 / 8.453 |
| nearby-swaps-32768 / compact | 0.213 / 0.243 | 0.636 / 0.636 | 8.219 / 8.203 |
| random-1000000 / optional | 14.098 / 14.065 | 23.011 / 23.011 | 45.859 / 45.844 |
| random-1000000 / compact | 14.589 / 13.977 | 15.386 / 15.385 | 38.250 / 38.227 |
| random-32768 / optional | 0.290 / 0.288 | 0.886 / 0.886 | 8.516 / 8.484 |
| random-32768 / compact | 0.331 / 0.310 | 0.635 / 0.635 | 8.281 / 8.250 |

Quality flags: []. Flagged cases remain unqualified. Process peak RSS can include the earlier CSV construction peak.
