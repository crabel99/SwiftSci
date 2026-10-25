# Identical-twin diagnostics

These diagnostics do not change the seven failed controls or qualify the panel. Every twin runs the same binary, schema, jobs, and output contract as its primary condition. Ratios divide the twin median by the primary median across twelve rotations.

| Condition | Charged CPU | Elapsed | Peak RSS | E instructions | E cycles | E cycles per accounted ns |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| swiftsci_optional | 0.9582 | 0.8108 | 1.0002 | 0.9989 | 0.9732 | 1.0586 |
| swiftsci_compact | 0.9461 | 0.7568 | 0.9963 | 0.9985 | 1.0204 | 1.0641 |
| pandas | 1.2210 | 0.9240 | 1.0355 | 0.9986 | 0.9830 | 0.7490 |
| polars | 1.0654 | 0.9850 | 1.0106 | 0.9984 | 0.9890 | 0.9279 |
| duckdb | 1.2867 | 1.1513 | 1.0607 | 0.9985 | 0.9809 | 0.7436 |
| pandas_arrow | 0.9501 | 1.0928 | 0.9239 | 1.0101 | 1.0664 | 1.0698 |

E cycles and instructions include E-user and E-kernel execution in the same recorded core intervals. P-kernel work remains separate. Cycles per accounted ns is a ratio of two process counters. It is not a direct measurement of core frequency, energy, temperature, or cache misses. A ratio change alone does not identify the hardware mechanism.

Equal application core type therefore does not establish equal work rate or equal contention. Instruction and cycle variation may include runtime, allocator, scheduling, and data-access effects. This record does not isolate those causes. No new tolerance, workload, excluded engine, or accepted ranking follows from these diagnostics.
