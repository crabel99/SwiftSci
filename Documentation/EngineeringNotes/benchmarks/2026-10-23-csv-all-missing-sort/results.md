# Shared-key sparse admission resource results

Eight fresh processes per label. Total CPU includes CSV construction, the requested operation, consumer preparation and release. Operation CPU excludes CSV construction and release. Output validation is outside timing. Original is checkpoint b982028c59; prior is 940353d441. Every client honors the declared storage choice.

| Case | Total CPU original / prior / current, ms | Operation CPU original / prior / current, ms | Held heap original / prior / current, MiB | Peak RSS original / prior / current, MiB |
|---|---:|---:|---:|---:|
| energy-common/serial/optional/sort-indices | 285.31 / 286.34 / 289.49 | 46.28 / 46.69 / 49.63 | 301.00 / 301.00 / 301.00 | 420.65 / 420.59 / 420.56 |
| energy-common/serial/optional/sort-matrix | 432.81 / 439.70 / 434.15 | 196.01 / 195.45 / 196.61 | 396.00 / 396.00 / 396.00 | 737.52 / 737.52 / 737.46 |
| energy-common/serial/compact/sort-indices | 296.49 / 296.61 / 294.88 | 47.88 / 46.75 / 46.55 | 191.95 / 191.95 / 191.95 | 312.43 / 312.39 / 312.36 |
| energy-common/serial/compact/sort-matrix | 416.73 / 424.86 / 414.67 | 170.52 / 168.78 / 169.12 | 286.95 / 286.95 / 286.95 | 503.75 / 503.24 / 503.33 |

Identical-binary flags: []. Affected comparisons remain unqualified. CPU is user plus system process time. These measurements do not establish energy, FLOP or cache effects.
