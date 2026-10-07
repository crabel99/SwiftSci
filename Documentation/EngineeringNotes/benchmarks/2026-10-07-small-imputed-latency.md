# Small-request latency diagnosis

Date: 2026-10-07

## Finding and decision

The earlier 14.2% small-request throughput loss did not reproduce as a stable ownership penalty. An unchanged-binary rerun produced paired consumed-versus-retained changes of +64.0%, -1.0% and -2.7%. Same-process controls also varied in both directions. Keep explicit consuming ownership and the existing production behavior. These observations do not justify a preprocessing size threshold.

The phase probes localize most request time inside the awaited model prediction call. The combined preprocessing and ownership-check phase is about 0.4 to 1.2 microseconds in the aggregate table, and is lower for consumed inputs in every route and concurrency combination. GPU prediction-call durations are about 366 to 766 microseconds. That call includes actor waits, validation, Float packing/import, GPU execution and readback. This experiment does not identify an internal GPU cause or distinguish scheduling from allocation behavior within that call.

Output validation and hexadecimal hash formatting cost about 28 to 48 microseconds in the aggregate controls. That is benchmark work, and it dwarfs the preprocessing operation for these small inputs. It must remain visible when interpreting complete-workflow throughput.

## Implementation scope

Commit `4230c29fc00cf7b89bde9d8f1ba000415aa8dd7f` follows `f0261a2212d08b74f0444d9f76e510e93cb606d8` on `codex/retained-memory-accounting-trial`. It adds a separate diagnostic worker, controller, contract tests and README instructions. The original throughput worker and all production sources are unchanged. Nothing was pushed; the primary checkout was not switched. Measurements and decisions remain on `codex/engineering-notes`.

The worker exposes three controls. `preprocessing` uses the same fitted preprocessing but checks predictions with a scalar CPU formula using fitted weights. It is not production CPU inference. `direct` calls the public GPU model; `pipeline` calls it through the public regression pipeline. Each control runs one and two admitted request slots.

Each process alternates retained and consumed blocks over six pairs of 2,048 requests per mode, reversing ownership order in alternate pairs. Both members of a pair use identical request IDs and data. A second fresh process repeats each control, with route order reversed. Each request has 64 rows and 3 columns, training-only imputation and scaling, missing entries and shifted held-out observations.

## Measurement interpretation

The diagnostic clocks split fixture generation with oracle construction, preprocessing with ownership checks, prediction, and output validation with hash formatting. The preprocessing phase intentionally measures the original benchmark helper, including address capture and the consumed-only buffer assertion. It bounds their combined cost and cannot isolate public transform cost from check cost.

Prediction timing measures the complete awaited API call. It is not device kernel time. Request durations overlap with two slots, so their sum does not equal elapsed wall time. Diagnostic clocks and paired block drains perturb execution, and these timings must not be pooled with throughput qualification results. No cache clearing occurs between blocks.

The table gives medians of per-block mean durations in microseconds. Each duration cell is retained / consumed. The throughput column is the median of 12 within-process paired ratios, with all observed ratios shown in the range.

| Control | Slots | Preprocessing plus checks, µs | Prediction call, µs | Paired throughput change | Paired range |
| --- | ---: | ---: | ---: | ---: | --- |
| preprocessing | 1 | 0.57 / 0.41 | 0.5 / 0.5 | +0.3% | -2.2% to +7.1% |
| preprocessing | 2 | 0.77 / 0.50 | 0.5 / 0.6 | +0.8% | -3.8% to +13.8% |
| direct | 1 | 0.89 / 0.79 | 366.2 / 384.7 | -1.3% | -35.0% to +23.0% |
| direct | 2 | 0.90 / 0.62 | 607.1 / 558.6 | +2.9% | -27.6% to +27.5% |
| pipeline | 1 | 1.00 / 0.62 | 376.6 / 368.2 | +0.6% | -32.6% to +32.5% |
| pipeline | 2 | 1.15 / 0.80 | 759.5 / 766.3 | +1.8% | -39.5% to +36.3% |

GPU controls still vary when the regression wrapper is bypassed. This rules out treating the wrapper as the sole explanation for the variability; it does not measure a causal wrapper penalty. The submicrosecond preprocessing difference cannot explain the earlier tens-of-microseconds service gap in these observed runs. Direct-model and pipeline paired medians are close to zero compared with their ranges, but no formal equivalence or noninferiority claim is made.

## Validation, resource handling and review

The Release diagnostic built and two focused public-workflow integration tests passed. Twenty controller tests passed, including rejection of missing or mismatched outputs, malformed phase timings, nonfinite errors, undrained reservations and invalid memory samples. The prior 874 selected Release passes belong to the parent commit; the full suite was not rerun for this benchmark-only change.

Six smoke workers exercised every route and slot count. Twelve diagnostic workers completed 294,912 requests. Complete output hashes match across ownership modes; GPU hashes also match between direct and pipeline routes and between concurrency settings. The maximum absolute prediction error was `3.5762786865234375e-07`, below the unchanged `1e-4` bound.

Every paired block released its request reservations and returned MLX active allocations to the fitted-model baseline. Final model release and cache clearing returned active and cached MLX memory to zero. All workers exited. Admission and cache limits remained 256 MiB, request reservations were 16 MiB, and diagnostic memory samples stayed below 512 MiB. These are bounded-run checks, not universal CPU leak certification.

The first smoke attempt stopped at the memory-pressure gate before launching a worker. A read-only follow-up reported normal pressure, and the retry passed under the same gate. Ordinary host activity remained allowed. No process belonging to another application was stopped.

Standards review found no actionable violation. Behavioral review identified that the preprocessing clock includes ownership checks. The README and controller now state that combined scope explicitly; no claim of pure transform timing remains. Review also identified two omitted controller-dependency fingerprints. The final controller records `contracts.py` and `runner.py`. The exact controller used for these measurements is archived, with a supplemental manifest documenting the metadata-only correction. Workload and validation logic did not change after measurement.

## Next experiment

Separate the awaited prediction boundary into dispatch/validation, packing/import, GPU submission/completion and readback before changing a size threshold. Also separate hexadecimal result formatting from measured work while preserving complete output verification. That would remove a known benchmark cost without weakening correctness checks. The current results do not establish which internal prediction phase causes the variance, or where a CPU/GPU crossover belongs.

## Evidence

Host: Apple M4 Max, 128 GiB unified memory, macOS 27.0 build 26A428. Release arm64 diagnostic, coverage disabled, existing pinned dependencies. No macOS 14 runtime was exercised.

Diagnostic binary SHA-256: `211f056e98d667848c61921c5bd3c919c856f89099c1929bb4d0db8b26b9df93`.

Unchanged throughput-recheck binary SHA-256: `249146abd1794e04b774c1870a5dc8a78b1c37e4ef1c344696f5c8385e427a9c`.

- [Diagnostic phase summary](../archive/2026-10-07/small-imputed-latency/phases/summary.json)
- [Measured source fingerprints](../archive/2026-10-07/small-imputed-latency/phases/provenance.json)
- [Unchanged throughput rerun](../archive/2026-10-07/small-imputed-latency/recheck/summary.json)
- [Validation and paired ratios](../archive/2026-10-07/small-imputed-latency/validation.json)
- [Provenance correction](../archive/2026-10-07/small-imputed-latency/provenance-supplement.json)
- [Previous complete workflow](2026-10-07-imputed-regression-integration.md)

Raw worker JSON and logs are losslessly compressed in the archive. Xcode result bundles remain in the local evidence directory.
