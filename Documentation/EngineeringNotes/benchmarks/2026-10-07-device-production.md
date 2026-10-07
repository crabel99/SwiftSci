# Shared Metal device production qualification

Date: 2026-10-07

## Decision and scope

Keep the shared default-device owner on `codex/retained-memory-accounting-trial`. All 24 paired throughput comparisons favor the candidate across small, medium, large and mixed workloads, and both input ownership modes. Complete predictions and fitted parameters match the preserved baseline. The broader selected Release suite and resource checks pass.

Commit `5fa86f9f7597681561a82b42787525061c1d35f5` follows `98f9a9268aa2fa82beada688b00b7ddb74171e00`. Production changes consist of one internal device owner and two substitutions at allocation sites. Benchmark changes add the baseline/candidate comparison controller, contract tests and usage instructions. Engineering evidence stays on its separate branch. Nothing was pushed, and the primary checkout remains at `6e10f5833961d6813cc65b0491fe622c83c55a5d`.

`MetalDeviceOwner` uses Swift's once-initialized immutable static storage to retain the initially returned default device. If that initial lookup is unavailable, accesses still call the default-device factory. A successful retry in that exceptional path is returned but not cached. Existing allocation failures therefore remain retryable rather than becoming permanent because of a cached nil.

`ScopedGPURead` and `RetainedGPUInputTrial` now use this owner. Every request still receives a fresh Metal buffer. Size validation, maximum-buffer checks, error cases, input import, synchronization and reservation ownership are unchanged. The owner retains a device, not request buffers. No public API, dependency version, packing policy, buffer pool or CPU/GPU dispatch threshold changes.

The LLM quantized engine already retains its own device, command queue and shader pipelines. It is in a separate module and was left intact. Preprocessing does not acquire a dependency on that engine.

## Public-pipeline comparison

The baseline executable was copied beside its runtime resources before rebuilding. Its digest matched the preceding experiment's fingerprint. The candidate and baseline build commands are identical except for test selection and the result-bundle destination. Dependency declarations and resolution fingerprints match, as do every benchmark-worker Swift source file. The only existing production-source differences are the two allocation sites, plus the newly added internal owner.

The comparison uses the unchanged `pipeline-service` worker through the actual public regression pipeline. It has no prediction-phase clocks. Each process fits training-only imputation/minmax and a CPU regression model, transfers fitted weights to the GPU estimator, warms the path, and processes held-out data with missing observations. The two request slots use the existing conservative 256 MiB admission budget.

Three rounds cover four shapes and both retained and consumed inputs. Binary order alternates within pairs and case order reverses between rounds. Each worker runs four request windows without clearing caches between windows. The complete measured window includes admission, fixture/oracle generation, preprocessing, GPU prediction, output validation, raw hashing, window drains and memory samples. It excludes model fitting, warmup, hexadecimal/JSON encoding and final cleanup. This is an in-memory workflow, not disk ingestion or an entire application benchmark.

Small uses 64 rows and 3 columns for 16,384 requests per worker. Medium uses 4,096 rows and 17 columns for 8,192 requests. Large uses 65,535 rows and 65 columns for 128 requests. Mixed cycles through 8,191, 65,535, 16,383 and 65,536 rows with 65 columns for 256 requests.

## Throughput

Each median below summarizes three within-round candidate/baseline throughput ratios. It is not the ratio of independently aggregated request rates. Positive values mean the candidate completes more requests per second. All individual paired changes are retained; no outlier was removed.

| Workload | Input ownership | Median paired change | Changes in rounds 0, 1, 2 |
| --- | --- | ---: | --- |
| small | copy | +119.0% | +120.6%, +119.0%, +110.6% |
| small | owned | +69.8% | +29.3%, +69.8%, +80.5% |
| medium | copy | +38.9% | +28.1%, +38.9%, +46.3% |
| medium | owned | +52.6% | +1.0%, +53.6%, +52.6% |
| large | copy | +6.2% | +6.2%, +6.9%, +2.5% |
| large | owned | +3.2% | +3.2%, +9.2%, +1.5% |
| mixed | copy | +8.0% | +7.3%, +9.1%, +8.0% |
| mixed | owned | +8.2% | +9.8%, +2.1%, +8.2% |

The observed gains are largest for small and medium requests, where fixed setup costs matter most. Some runs vary substantially, particularly consumed medium inputs. These are results from this host and workload, not universal percentage guarantees. Three pairs per configuration are insufficient to establish a precise population effect or statistical noninferiority bound.

The production gains exceed the earlier diagnostic's 27% to 31% latency reductions in some cases. The diagnostic retained a device in both of its control routes, inserted phase clocks, and forced explicit evaluation. This production experiment changes the actual device lifetime and removes repeated lookup without those probes. The studies have different controls; their percentages should not be substituted for one another. This work does not isolate Metal's internal lifetime or lookup mechanisms well enough to attribute the entire difference to one internal operation.

## Memory and ownership

RSS is sampled process memory, not live request ownership. The table gives medians of measured RSS in MiB across three fresh processes per binary and configuration.

| Workload | Input ownership | Baseline RSS, MiB | Candidate RSS, MiB |
| --- | --- | ---: | ---: |
| small | copy | 28.4 | 28.6 |
| small | owned | 28.2 | 28.0 |
| medium | copy | 36.6 | 37.0 |
| medium | owned | 31.3 | 31.6 |
| large | copy | 292.9 | 288.9 |
| large | owned | 209.7 | 187.7 |
| mixed | copy | 316.0 | 333.5 |
| mixed | owned | 214.1 | 211.9 |

Memory does not uniformly decrease. Retained mixed inputs have higher median candidate RSS, while consumed large inputs have lower candidate RSS. Allocation timing, caches and process high-water history can affect these observations. This change is supported as a device-lookup optimization, not as a general memory reduction.

Every lifecycle window returns MLX active allocation to its fitted-model baseline and drains reservations. Final model release, synchronization and cache clearing leave MLX active and cached allocation at zero. All 48 comparison workers exit. The largest candidate measured RSS is approximately 356 MiB, below the unchanged 2 GiB bound. A persistent process-level Metal device reference is intentional; these checks do not claim that every driver cache releases its memory at request completion.

Eight separate source-integrity workers complete 64 requests across all sizes and ownership modes. They perform 32 full retained-source checks and verify consumed-buffer reuse. Eight additional smoke workers cover standard scaling, minmax, and imputation/minmax with small and mixed inputs. Their historical complete output hashes remain unchanged.

## Tests and review

The selected Release suite passes 874 tests with two optional skips and no failures. It covers the dataframe, statistics, preprocessing, machine learning, clustering, optimization, explanation, NLP and benchmark-support targets. This is not a claim that every target in the repository ran. Thirty-two controller tests pass.

The production comparison completes 299,520 requests across 48 workers. Every prediction hash and fitted-parameter hash matches across binaries, input ownership modes and repetitions. The numerical bound remains `1e-4`. No tolerance or validator was relaxed.

Independent behavioral and standards review found no production issue. Review noted that a syntactically valid zero baseline service median would cause division by zero in the new controller. A test reproduced it, then an explicit positive-denominator check replaced that generic exception with a contract failure. This controller-only correction happened after measurement. The exact controller used is archived. Every observed median is positive, and revalidation with the final controller reproduces every recorded paired result exactly. Production source and benchmark-worker source did not change after measurement.

The unavailable-device retry path was reviewed but not exercised on this Metal-capable host. Runtime validation was on macOS 27, not macOS 14. The change introduces no newer Metal API, but this experiment alone is not runtime qualification for every supported OS.

## Evidence

Host: Apple M4 Max, 128 GiB unified memory, macOS 27.0 build 26A428. Release arm64, coverage disabled, pinned dependencies and precise Float settings. The controller owns its child processes, enforces a 180-second worker deadline and checks normal memory pressure before each launch. Ordinary host activity remains allowed; no unrelated application was stopped.

Baseline binary SHA-256: `b0819cc33fe063bfd92d654b98371ab8d68f878f62c5ebd63c675e9cf27b3f06`.

Candidate binary SHA-256: `fa97a6195dd9cd150435938826a3204fc90771faaa6caa9cae7ed5aa22952211`.

- [Paired throughput and memory results](../archive/2026-10-07/device-production/comparison/paired.json)
- [Per-worker summary](../archive/2026-10-07/device-production/comparison/summary.json)
- [Build and source fingerprints](../archive/2026-10-07/device-production/comparison/provenance.json)
- [Validation totals](../archive/2026-10-07/device-production/validation.json)
- [Controller correction and build-command check](../archive/2026-10-07/device-production/provenance-supplement.json)
- [Previous retained-device diagnostic](2026-10-07-device-reuse.md)

Raw worker records and logs are losslessly compressed. Xcode result bundles and the preserved baseline executable remain local.
