# Bounded parallel sorting results

2026-10-18. Engineering evidence on `codex/engineering-notes`. Keep this report out of implementation PRs.

## Decision

Decision update after the user clarified the objective on 2026-10-18: park the parallel radix branch as a latency alternative. Its 28.3% increase in accumulated CPU time does not justify replacing the serial default under the [resource-priority evaluation rules](README.md#decision-order). CPU time is a proxy, and no energy conclusion follows.

The original parallel radix trial passes the registered screening and held-out operation criteria. Reject the current chunk-sort-and-merge dispatcher because it exceeds protected-case slowdown limits. This rejects this implementation and threshold, not comparison sorting as an algorithm family. No production default or public policy changes follow from this trial.

Both candidates start at `d23bf7cac92fe9f9c10bd98046ca8ade354b5a3c`. The scalar gather specialization remains separate, so it cannot explain these results. Existing sparse, small, run-adaptive and NaN fallback paths remain in place. Stable ties, missing rows last, signed-zero payloads, both directions and native column types retain the same contract.

| Candidate | Local branch | Commit |
| --- | --- | --- |
| radix | `codex/dataframe-parallel-radix-trial` | `5a253f13b72004bcc71981d2609b05a81539e125` |
| merge | `codex/dataframe-chunk-merge-trial` | `f583c3be4e158b62543fc774c43b180cba7727ec` |

## Complete million-row sort

The random numeric table has four columns. Each number is a median of fresh-process medians. CPU time sums user and system time across process threads over the operation. It measures work, not energy. RSS is the whole-process high-water mark and includes preparation and validation.

| Implementation | Elapsed ms | Process CPU ms | Peak RSS MiB |
| --- | ---: | ---: | ---: |
| baseline | 21.084 | 33.480 | 186.34 |
| radix | 12.183 | 42.945 | 186.97 |
| merge | 19.363 | 87.737 | 187.97 |

Radix lowers elapsed time by 42.2% while process CPU time rises 28.3%. Similar RSS does not establish equal scratch use. The merge candidate offers a smaller latency gain on this case and consumes much more CPU work.

## Held-out complete sorts

The held-out generator seed, row counts and widths differ from screening. Five process pairs per case use alternating launch order. Every numeric complete-sort pair favors radix. Each numeric median paired saving exceeds its registered 0.25 ms or 1 ms minimum.

| Rows | Columns | Layout | Original ms | Radix ms | Paired saving ms [range] | Paired speedup |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| 250,003 | 3 | numeric, random | 4.400 | 2.734 | 1.672 [1.635, 1.755] | 1.615x |
| 250,003 | 8 | numeric, random | 5.294 | 3.634 | 1.636 [1.586, 1.825] | 1.450x |
| 750,007 | 3 | numeric, random | 15.158 | 8.031 | 7.132 [7.004, 7.259] | 1.889x |
| 750,007 | 8 | numeric, random | 16.955 | 9.234 | 7.655 [7.570, 8.028] | 1.828x |
| 250,003 | 3 | mixed, ties | 12.198 | 13.394 | -0.080 [-2.137, 2.699] | 0.993x |
| 250,003 | 8 | mixed, ties | 21.135 | 20.265 | 0.790 [0.499, 2.942] | 1.039x |

The three-column mixed case does not establish a gain. Its paired median loss is 0.080 ms, within the registered 0.25 ms limit, but paired differences range from a 2.137 ms loss to a 2.699 ms saving. Both implementations have slow process outliers. Subtracting the two unpaired aggregate medians gives a different answer and is not the paired statistic. Retain this variability as an open workflow question. The eight-column mixed case has positive savings in every pair.

## Why the merge candidate stops here

At 131,073 rows the merge candidate loses 2.058 ms at the paired median on random input, exceeding the 0.1 ms limit. The repeated-key case loses 1.597 ms at that size, and the million-row repeated-key case loses 1.169 ms against a 1 ms limit. It passes correctness checks and improves the million-row random case, but that does not qualify its proposed automatic route. No held-out confirmation was run for this rejected candidate. No threshold was retuned against held-out measurements.

## Resource model and limitations

Radix retains the original keys and alternating Int index buffers. It adds private 2,048-bin histogram rows and prefixes by bucket then source-worker order. Each active digit has two synchronous joins around a serial prefix step. The worker cap uses activeProcessorCount and at least 65,536 valid rows per worker; two workers require 131,072 valid rows. Actual runnable cores and cache behavior were not profiled.

For one million valid rows on this 16-logical-processor host, the rule caps radix at 15 workers. Requested array-element capacities are about 22.90 MiB for original radix and 23.12 MiB for parallel radix. The cached-record merge has a source-based peak near 38.15 MiB, excluding allocator rounding, runtime state and run metadata. The installed Swift implementation requests half a chunk of local-sort temporary elements. Those temporaries and the final Int output occur in separate phases. These are logical storage estimates, not measured allocation peaks.

All matched case-median RSS increases remain below the registered 64 MiB review threshold. Source-plus-destination logical payload remains below 1 GiB, and estimated algorithm scratch remains below 256 MiB for the registered requests. This is not a general memory-admission guarantee for arbitrary input sizes. No allocation trace, energy measurement, DRAM traffic or core-affinity measurement was collected.

## Correctness and artifact qualification

Each candidate passes all 333 dataframe tests independently in Debug, Release and Address Sanitizer builds, without failures or skips. Each also passes four focused Thread Sanitizer tests, including parameterized uneven boundaries, stable duplicates, missing rows, exact floating payloads, constant digits and late NaN fallback. The shared regression test file is 68 lines.

The retained radix candidate passes fifteen scientific, persisted-model, streaming CSV and wine controls with complete-output validation. These checks establish integration conformance, not application performance or full SwiftSci numerical certification. Library-source patch coverage and hosted CI are not claimed by this experiment.

The audit checks 280 fresh processes and 1,400 timed samples, identical benchmark source, frozen binary checksums, committed source identities, complete validation receipts and unchanged AC settings. Two warmups precede five measured samples in each process. The CPU backend uses native scheduling on the same Apple M4 Max. Output owners remain alive at timer stop; independent full-output validation follows every sample. No compiling or test process ran alongside a timing campaign.

The build recorder initially omitted new untracked helpers. Those pre-stage binaries and receipts are preserved separately and were not used for timings. Final executables were rebuilt from tracked source. The local build tool now rejects untracked implementation files before freezing provenance. The general benchmark runner still needs that omission handled at its own boundary in a separate tooling change.

## Complete screening results

Positive paired savings favor the candidate. Negative savings remain visible even when within the protected bound.

### Complete materialized sort

| Rows, columns, input | Original ms | radix ms; paired saving [range] | merge ms; paired saving [range] |
| --- | ---: | ---: | ---: |
| 131,073, 4, random, numeric, asc | 2.226 | 1.731; 0.480 [0.417, 0.550] | 4.269; -2.058 [-2.103, -2.040] |
| 131,073, 4, ties, numeric, asc | 1.118 | 0.901; 0.215 [0.211, 0.239] | 2.709; -1.597 [-1.648, -1.567] |
| 131,073, 4, nulls, numeric, asc | 1.964 | 2.005; -0.048 [-0.128, 0.049] | 2.034; -0.017 [-0.070, -0.010] |
| 1,000,000, 4, random, numeric, asc | 21.084 | 12.183; 8.920 [8.862, 9.070] | 19.363; 1.693 [1.600, 1.721] |
| 1,000,000, 4, ties, numeric, asc | 10.917 | 7.742; 2.915 [2.878, 3.291] | 11.977; -1.169 [-1.357, -0.950] |
| 1,000,000, 4, nulls, numeric, asc | 18.908 | 11.096; 7.856 [7.640, 8.089] | 18.199; 0.709 [0.601, 1.217] |
| 4,096, 4, random, numeric, asc | 0.073417 | 0.073458; -0.000208 [-0.000292, 0.001250] | 0.073167; 0.000250 [-0.000166, 0.001333] |
| 1,000,000, 4, identity, numeric, asc | 5.063 | 5.038; 0.025 [0.011, 0.029] | 5.053; 0.000 [-0.038, 0.022] |
| 1,000,000, 4, sparse, numeric, asc | 4.571 | 4.487; 0.075 [0.058, 0.135] | 4.565; 0.030 [-0.069, 0.070] |
| 1,000,000, 4, random, mixed, asc | 106.789 | 90.954; 14.882 [8.797, 27.309] | 102.468; 4.321 [-0.314, 14.137] |
| 1,000,000, 4, nulls, numeric, desc | 19.044 | 11.182; 7.878 [7.863, 8.134] | 18.220; 0.796 [0.746, 1.116] |

### Permutation generation

| Rows, columns, input | Original ms | radix ms; paired saving [range] | merge ms; paired saving [range] |
| --- | ---: | ---: | ---: |
| 131,073, 4, random, numeric, asc | 1.936 | 1.387; 0.446 [0.420, 0.590] | 3.924; -2.004 [-2.091, -1.958] |
| 131,073, 4, ties, numeric, asc | 0.823 | 0.592; 0.220 [0.195, 0.258] | 2.384; -1.555 [-1.570, -1.554] |
| 131,073, 4, nulls, numeric, asc | 1.644 | 1.652; -0.021 [-0.113, 0.013] | 1.660; -0.003 [-0.072, 0.004] |
| 1,000,000, 4, random, numeric, asc | 16.032 | 7.263; 8.768 [8.738, 9.127] | 14.404; 1.606 [1.507, 1.982] |
| 1,000,000, 4, ties, numeric, asc | 6.334 | 3.177; 3.177 [3.055, 3.265] | 6.651; -0.387 [-0.749, -0.158] |
| 1,000,000, 4, nulls, numeric, asc | 14.245 | 6.717; 7.451 [7.398, 8.173] | 13.169; 1.003 [0.946, 1.263] |
| 4,096, 4, random, numeric, asc | 0.045625 | 0.046250; -0.000625 [-0.000793, -0.000375] | 0.045750; 0.000001 [-0.001334, 0.000166] |
| 1,000,000, 4, identity, numeric, asc | 3.187 | 3.219; -0.032 [-0.214, 0.239] | 3.216; 0.041 [-0.174, 0.117] |
| 1,000,000, 4, sparse, numeric, asc | 2.537 | 2.451; 0.071 [-0.003, 0.087] | 2.440; 0.060 [0.008, 0.158] |

### Held-out permutation generation

| Rows, columns, input | Original ms | radix ms; paired saving [range] |
| --- | ---: | ---: |
| 250,003, 3, random, numeric, asc | 3.747 | 2.163; 1.593 [1.490, 1.627] |
| 250,003, 8, random, numeric, asc | 3.820 | 2.169; 1.660 [1.640, 1.685] |
| 750,007, 3, random, numeric, asc | 12.132 | 4.876; 7.407 [7.086, 7.649] |
| 750,007, 8, random, numeric, asc | 12.106 | 4.856; 7.536 [7.167, 7.742] |

## Next decision

Keep the radix and rejected merge commits local and independently reproducible. Next measure accumulated CPU time for the scalar gather specialization and prioritize changes that reduce work, copying or retained storage. Combined workflows remain necessary for any candidate advanced under that objective. Freeze a fresh resource-focused plan with workload latency limits before collecting new data. Do not retune against these held-out cases or infer a new ranking against Polars from this SwiftSci-only trial.

Raw evidence and repeatable procedures: `/Users/crabel/local-ai/spl/swiftsci/csv-sort-throughput-20261017/parallel-sort-trial-20261018`. Build, verify, compare, audit and integration scripts remain with the receipts. Use fresh output destinations for a repeat. Frozen source fingerprints are below.

| Implementation | Source fingerprint |
| --- | --- |
| baseline | `761f848cd50811e62f9e13b4089a25d62675020c8f9599415f94da7fe672f9c8` |
| radix | `62b0ada81e504f8e802c45ca5f25553fd0d1c59142cc4a1d0fc96d64febb961a` |
| merge | `0d6f08e811ac864bf85e9e2f42100d304c4c5186b5c53517264c7afc4c99395e` |

[Preregistered design and evaluation plan](parallel-sort-design/evaluation-plan.md). [Design synthesis](parallel-sort-design/synthesis.md). [Scalar gather confirmation](serial-specialization-results.md). [Experiment register](experiments.tsv).
