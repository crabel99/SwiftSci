# Retained Metal device experiment

Date: 2026-10-07

## Finding

Default-device lookup dominates the device/buffer setup phase in this small-input diagnostic. Repeated `MTLCreateSystemDefaultDevice()` calls take about 51 to 52 microseconds, while a fresh 768-byte Metal buffer takes about 3 microseconds. Selecting the actor's retained device handle takes about 0.03 microseconds. This measures the lookup call's cost; it does not establish which internal Metal operation accounts for that time.

The same diagnostic actor runs both device choices. Retaining the handle reduces paired awaited prediction duration by a median 31.0% with one admitted slot and 27.1% with two. All 24 paired cycles favor the retained handle, with latency reductions between 17.8% and 45.6%. This is evidence for testing a narrow production change, not a claim that production service performance already improved by those percentages.

## Implementation and control

Commit `98f9a9268aa2fa82beada688b00b7ddb74171e00` follows `5e1603eea4a0a66635727e01e6f76e20e883bb06` on `codex/retained-memory-accounting-trial`. It changes four benchmark files. Production source, packing strategy, logical-extent import and dispatch are unchanged. Nothing was pushed, and the primary checkout remains at `6e10f5833961d6813cc65b0491fe622c83c55a5d`.

The diagnostic actor retains one Metal device during setup for the entire experiment, including the per-request lookup control. Both controls therefore have the same actor, weights, bias and retained state. The sole request-path choice is obtaining the default device again or selecting that existing handle. Each route allocates and releases a fresh buffer on every request. This is device-handle reuse, not a storage pool.

The third route is the unchanged public GPU prediction API. All routes consume identical 64-row, 3-column fixtures after training-only imputation and minmax scaling. Complete prediction hashes must match across all routes and the preceding diagnostic's historical records. Independent analytic predictions must agree within the unchanged `1e-4` bound.

Each worker runs six cycles of 1,024 requests per route. The cycles cover all six permutations of public, lookup and retained route order. Two fresh processes run each slot count, reversing slot order in the second round. No cache clearing occurs between measured blocks. Every block drains work before memory sampling and the next route.

Output schema version 2 names each route and cycle, splits lookup and allocation times, and preserves aggregate digest construction. Historical schema version 1 records remain tied to their original controller commit. No historical record was rewritten.

## Timing results

Durations are microseconds. Each value is the median of 12 per-block mean durations. Actor-body and awaited durations contain the other phases; they are not additional work. Completion covers host submission and GPU waiting, not device kernel time. Concurrent request durations overlap and cannot be summed as elapsed wall time.

| Phase | One slot, lookup | One slot, retained | Two slots, lookup | Two slots, retained |
| --- | ---: | ---: | ---: | ---: |
| device_lookup | 51.816 | 0.030 | 50.642 | 0.033 |
| buffer_allocation | 3.053 | 2.861 | 2.985 | 2.713 |
| packing | 0.135 | 0.117 | 0.139 | 0.120 |
| import | 1.886 | 1.689 | 1.930 | 1.786 |
| completion | 136.795 | 123.351 | 120.156 | 119.939 |
| scope_cleanup | 19.042 | 18.518 | 18.665 | 18.073 |
| actor_wait | 0.086 | 0.081 | 197.945 | 142.865 |
| actor_body | 215.606 | 151.543 | 203.209 | 147.475 |
| awaited_prediction | 216.200 | 152.185 | 402.782 | 291.971 |

The table below compares routes within the same cycle and process. It gives the median percentage change followed by the complete observed range. Lower duration is better; higher throughput is better. Throughput covers the whole diagnostic block, including fixture generation, preprocessing, numerical validation and raw hashing. It excludes hexadecimal result encoding after the block clock.

| Slots | Awaited duration change | Diagnostic block throughput change |
| --- | ---: | ---: |
| 1 | -31.0% (-45.6% to -19.9%) | +42.8% (+23.2% to +80.2%) |
| 2 | -27.1% (-36.5% to -17.8%) | +35.7% (+20.7% to +55.3%) |

Removing repeated lookup also shortens the work that another request waits behind at two slots. Buffer allocation, packing and import remain small. Completion timing varies, especially in the one-slot runs, so the total improvement should not be attributed entirely to the direct lookup interval. Ordinary host activity was allowed, and no unrelated applications were stopped.

These clocks instrument a benchmark mirror with explicit evaluation and synchronization, not the production method. Clock calls and diagnostic bookkeeping can affect optimization and scheduling. Public-route durations are recorded as a control, but the causal device comparison is lookup versus retained within the same diagnostic implementation.

## Validation and ownership

Two focused Release public-workflow integration tests pass. Twenty-seven controller tests pass, including schema, all-route coverage, later-cycle ordering, output mismatch, impossible timings and cleanup failures. Independent behavioral and standards reviews found no actionable issue.

Two smoke workers complete 768 requests. Four comparison workers complete 73,728 requests, with full prediction equality across routes, slot counts and the historical diagnostic. The maximum absolute analytic error is `3.5762786865234375e-07`.

Every measured block returns MLX active allocation to the fitted-model baseline and drains admission reservations. Final model and probe release, GPU synchronization and cache clearing leave MLX active and cached allocation at zero. All workers exit; sampled RSS stays below 27 MiB. These bounded checks do not prove that Metal or system framework caches retain no memory, or establish universal leak freedom.

The controller retains normal memory-pressure admission, a 180-second child deadline, explicit child-process ownership, a 256 MiB admission/cache limit and a conservative 16 MiB reservation per request. No buffer pooling or global device owner was introduced in production.

## Next production candidate

`ScopedGPURead` currently looks up the default device for each matrix allocation. The retained-input trial allocator also performs a lookup. The next change should provide one internal device owner for these allocation paths while preserving allocation-error behavior, buffer lifetimes, shape checks and stream synchronization. First inspect other device owners in the remaining modules to avoid introducing a competing owner.

Qualify that change through the actual public pipeline with phase clocks disabled, compare against a preserved baseline binary, and cover small, medium, large and mixed request sizes. Recheck numerical equality, source immutability, admission accounting and final cleanup. Do not use this experiment to select a CPU/GPU crossover or justify buffer pooling.

## Evidence

Host: Apple M4 Max, 128 GiB unified memory, macOS 27.0 build 26A428. Release arm64, coverage disabled, pinned dependencies and precise Float settings. No macOS 14 runtime was exercised.

Binary SHA-256: `b0819cc33fe063bfd92d654b98371ab8d68f878f62c5ebd63c675e9cf27b3f06`.

- [Comparison summary](../archive/2026-10-07/device-reuse/comparison/summary.json)
- [Source and binary fingerprints](../archive/2026-10-07/device-reuse/comparison/provenance.json)
- [Validation and paired results](../archive/2026-10-07/device-reuse/validation.json)
- [Previous prediction-phase experiment](2026-10-07-prediction-phases.md)

Worker records and logs are losslessly compressed in the archive. Xcode result bundles remain local.
