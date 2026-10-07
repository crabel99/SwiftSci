# MinMax ownership follow-up comparison

Date: 2026-10-07

## Scope

Completed the old/new comparison requested after the initial timing pass was interrupted. This run used the two saved executables without rebuilding or changing production code. It compares the prior prepared MinMaxScaler implementation at `4c6d91b263bd16cd776eb315f6e1cafd44b6abab` with consuming column reuse at `a075d7f52ef8fb75ba8b623e1ca21235f89764ab`.

The primary evidence is now this completed interleaved run. The initial before-and-after timings and stopped follow-up remain historical observations. They should not be combined with this run to estimate an average speedup.

## Decision

Keep the consuming implementation for continued development. The adjacent pairs reproduce lower resident memory for large and mixed consumed inputs without reproducing the earlier broad slowdown. Median paired throughput changes for consumed inputs are +1.6% for small, -0.7% for medium, +2.6% for large and +3.5% for mixed. Large-input RSS falls 33% to 37%; mixed-input RSS falls 28% to 32% after rounding.

There is no uniform speedup claim. In particular, large-input throughput pairs range from -0.5% to +39.0%, and mixed pairs from -14.0% to +5.5%. The memory reduction is more repeatable than the timing change. These results support retaining storage reuse without adding a new size threshold or holding this local development step for another idle-machine run. A formal performance baseline remains a separate qualification.

## Method and validation

One worker process ran at a time. Within each workload and ownership mode, the baseline and candidate ran next to one another. Case, ownership and executable order reversed for the middle of three rounds. The user continued to have access to the computer; ordinary host activity was allowed. Memory-pressure gates, child deadlines, complete prediction checks and cleanup checks stayed enabled.

All 48 workers completed, covering 608,256 requests. Every prediction matched the complete output hash from the original baseline. The analytic error bound remained `1e-4`. Every worker drained its reservations, returned active MLX memory to the fitted-model baseline, then released its model and cleared cached allocations. No worker was cancelled in this run.

The workload uses the public RegressionPipeline with a nested Pipeline, a training-only MinMaxScaler and a GPU LinearRegression estimator. Copy retains the original input through validation; owned consumes it. Two request slots refill continuously, with conservative 256 MiB request reservations and a 256 MiB MLX cache limit. There is no cache clearing inside the measurement.

Small uses 32,768 requests of 64 rows and 3 columns. Medium uses 16,384 requests of 4,096 rows and 17 columns. Large uses 512 requests of 65,535 rows and 65 columns. Mixed uses 1,024 requests cycling through 8,191, 65,535, 16,383 and 65,536 rows with 65 columns. Timing includes input creation, preprocessing, prediction, validation and hashing. It excludes fitting, warmup and final cleanup.

The existing 865 selected Release test passes, two optional skips and 12 controller test passes remain the code-validation evidence. They were not rerun because this follow-up changes only measured evidence. Source changes would require fresh validation.

## Results

Requests per second and RSS columns are medians of three fresh workers. The paired-change column is the median of each adjacent candidate/baseline ratio; it is not a ratio of the two median rates. Its range shows all three paired observations. RSS is sampled after the continuous window while the model and normal caches remain present. It includes allocator retention and is distinct from peak or post-cleanup memory.

| Workload | Input ownership | Prior requests/s | Candidate requests/s | Median paired throughput change | Paired range | Prior RSS MiB | Candidate RSS MiB |
| --- | --- | ---: | ---: | ---: | --- | ---: | ---: |
| small | copy | 5467.3 | 5394.9 | -1.3% | -10.7% to +3.5% | 33.6 | 35.4 |
| small | owned | 5430.1 | 5610.9 | +1.6% | -3.9% to +3.3% | 33.4 | 34.4 |
| medium | copy | 2785.3 | 2700.0 | +3.0% | -3.8% to +8.1% | 36.3 | 39.5 |
| medium | owned | 2698.4 | 2680.5 | -0.7% | -1.1% to +0.1% | 36.3 | 34.4 |
| large | copy | 87.4 | 89.7 | +1.5% | -0.1% to +2.7% | 324.3 | 312.3 |
| large | owned | 78.1 | 86.5 | +2.6% | -0.5% to +39.0% | 302.0 | 191.0 |
| mixed | copy | 125.5 | 144.3 | +10.2% | -1.5% to +18.1% | 388.2 | 362.8 |
| mixed | owned | 144.2 | 149.2 | +3.5% | -14.0% to +5.5% | 290.7 | 209.8 |

These are whole-pipeline measurements on one host. Three rounds quantify the observed range but do not establish statistical equivalence, a universal crossover or a general speed guarantee. The results should support a scoped engineering decision with the memory benefit and any workload-specific tradeoff visible. They are not a formal performance baseline for every SwiftSci operation.

## Reproduction

The host is Apple M4 Max with 128 GiB unified memory, running macOS 27.0 build 26A428. Both arm64 Release executables target macOS 14, use the same pinned MLX Swift fork and shared resources, and have coverage disabled. The instrumentation check passed before workers ran. Metal math is safe and FP32 functions are precise. No macOS 14 runtime was exercised.

- Baseline SHA-256: `3f06110e47b16d0c6d48259f56075e35629fc23b08a677d141c40df78b9198d1`.
- Candidate SHA-256: `5f113578cb54ee88daee6ca6efc91ba9e160fe38a9e42911dc46bb5ade948e1f`.

Per-worker commands, complete outputs, source fingerprints, load averages and binary fingerprints are archived with this report. Raw worker JSON uses lossless gzip compression. The driver is preserved for repetition without modifying the prior evidence directory.

- [Paired results and validation](../archive/2026-10-07/gpu-consuming-minmax-followup/validation.json)
- [Worker summary](../archive/2026-10-07/gpu-consuming-minmax-followup/summary.json)
- [Source and binary fingerprints](../archive/2026-10-07/gpu-consuming-minmax-followup/provenance.json)
- [Implementation and original test evidence](2026-10-07-consuming-minmax-integration.md)
