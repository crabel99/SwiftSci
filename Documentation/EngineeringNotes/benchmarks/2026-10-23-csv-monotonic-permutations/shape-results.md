# Ordered and disordered sort controls

Eight fresh processes per label. CPU covers public sorting and index release with the input frame retained. CSV construction and exact validation are excluded. Original is checkpoint 91c0ff09b7; prior is 42f0633fd5. All labels honor the requested storage choice.

| Shape / count / storage | CPU original / prior / current, ms | Held heap original / prior / current, MiB | Peak RSS original / prior / current, MiB |
|---|---:|---:|---:|
| ascending-1000000 / optional | 4.441 / 5.087 / 1.459 | 23.011 / 23.011 / 23.011 | 45.797 / 45.797 / 32.859 |
| ascending-1000000 / compact | 4.011 / 4.863 / 1.681 | 15.386 / 15.386 / 15.386 | 38.172 / 38.156 / 25.234 |
| ascending-32768 / optional | 0.134 / 0.157 / 0.043 | 0.886 / 0.886 / 0.886 | 8.469 / 8.484 / 8.297 |
| ascending-32768 / compact | 0.119 / 0.147 / 0.051 | 0.636 / 0.636 / 0.635 | 8.219 / 8.234 / 8.062 |
| descending-1000000 / optional | 75.189 / 75.898 / 2.281 | 23.011 / 23.011 / 23.011 | 45.781 / 45.781 / 32.844 |
| descending-1000000 / compact | 65.951 / 66.855 / 2.729 | 15.386 / 15.386 / 15.386 | 38.156 / 38.156 / 25.219 |
| descending-32768 / optional | 1.415 / 1.451 / 0.073 | 0.886 / 0.886 / 0.886 | 8.469 / 8.469 / 8.297 |
| descending-32768 / compact | 1.153 / 1.184 / 0.083 | 0.636 / 0.636 / 0.636 | 8.234 / 8.203 / 8.047 |
| nearby-swaps-1000000 / optional | 11.519 / 12.070 / 12.184 | 23.011 / 23.011 / 23.011 | 45.797 / 45.812 / 45.781 |
| nearby-swaps-1000000 / compact | 9.278 / 10.130 / 10.214 | 15.386 / 15.386 / 15.386 | 38.172 / 38.156 / 38.156 |
| nearby-swaps-32768 / optional | 0.213 / 0.234 / 0.235 | 0.886 / 0.886 / 0.886 | 8.469 / 8.453 / 8.469 |
| nearby-swaps-32768 / compact | 0.181 / 0.211 / 0.213 | 0.636 / 0.636 / 0.636 | 8.219 / 8.219 / 8.219 |
| random-1000000 / optional | 12.505 / 12.400 / 12.462 | 23.011 / 23.011 / 23.011 | 45.875 / 45.859 / 45.859 |
| random-1000000 / compact | 12.681 / 12.444 / 12.419 | 15.386 / 15.385 / 15.385 | 38.250 / 38.234 / 38.234 |
| random-32768 / optional | 0.288 / 0.285 / 0.288 | 0.886 / 0.886 / 0.886 | 8.516 / 8.484 / 8.516 |
| random-32768 / compact | 0.305 / 0.281 / 0.294 | 0.636 / 0.635 / 0.635 | 8.281 / 8.250 / 8.234 |

Quality flags: []. Flagged cases remain unqualified. Process peak RSS can include the earlier CSV construction peak.
