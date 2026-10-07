# Consuming scaler storage after allocation-site profiling

Date: 2026-10-07

## Decision

Keep the consuming scaler as a benchmark prototype for the next integration review. It reuses uniquely owned input columns, preserves shared snapshots through copy-on-write, and matches the existing transform bit for bit in the checked cases. The matched GPU workload measures whether removing the second set of Double columns reduces the allocator's retained footprint.

Implementation commit: `5ee5ff7649035a2953d5ed53941116e61891be02`.
Parent: `3e8784e8d1c30336d0e66d70fe680a6539e75c9b`.
Branch: `codex/retained-memory-accounting-trial`.
No production source or public API changed. Nothing was pushed. This report and raw evidence belong separately to `codex/engineering-notes` and must remain outside implementation PRs.

## Allocation-site evidence

One eight-request run of the previous worker enabled full malloc stack logging in that child only. The worker paused after cleanup. Apple's `malloc_history -callTree -highWaterMark` reconstructed allocations that were live at the logged allocation high-water mark. This is different from current resident memory and from cumulative allocation traffic. Native tool return codes were zero, and the eight request outputs passed validation.

The allocation high-water report totaled 167.7 MB of tracked heap and anonymous VM allocations. Two sites each accounted for 130 allocations totaling approximately 65 MiB:

- `RetainedRegressionWorkflow.fixture`, which creates the raw Double columns.
- `StandardScaler.transform`, which creates the transformed Double columns.

At two concurrent requests, each site holds 65 columns per request. Each column contains 65,535 Doubles. The 130 MiB combined payload explains most of the live peak tracked by this report. The subsequent VM map still showed 132.8 MiB resident in empty small-allocation regions after cleanup.

This identifies dominant allocation sites and motivates removing one set of columns. It does not map every later resident page back to an allocation site. Stack logging and process inspection perturb execution, so no timing or footprint benefit is claimed from that instrumented run. The raw trace used the earlier worker at the parent commit; its binary hash and command are archived separately.

## Prototype and matched control

`OwnedScalerTrial` consumes a dense, nonempty prepared batch while its fitted scaler remains immutable. It keeps the production transform's row-width vDSP calls and tile traversal. Output writes go through Swift array mutation, allowing unique buffers to be reused and shared buffers to detach through copy-on-write. This experiment does not implement the complete public scaler contract for missing values, empty inputs, concurrent fitting or all error cases.

The verification command covers widths 1, 17, 65 and 513, with row counts 1, 31, 32, 33 and 8,191. Those twenty shapes exercise tiled and fallback traversal. Unique inputs must reuse every column address. Shared inputs must detach every output column and retain their original bits. Both results must match the production scaler bit for bit.

Both explicit workload variants compute an analytic answer before scaling and retain that answer through prediction validation. Copy retains its raw batch as well as transformed columns. Owned consumes the raw batch and reuses its columns. Both keep the same GPU packing/import policy, request generator, numerical oracle and output hashing.

The analytic-answer array has its own `rows * 8` reservation entry in both variants. The original raw-plus-transformed estimate remains in both paths, conservatively overestimating the owned path so admission does not change. Each worker still has two request slots and a 256 MiB reservation limit. Every owned request checks reuse of all 65 input columns. The controller checks complete prediction hashes across storage choices, schedules, import policies and fresh processes.

The historical seven-argument worker computes its oracle later. It remains available as an unchanged benchmark path, but it is not the matched control for this experiment. The comparison uses explicit eight-argument copy and owned controls.

## Memory results

Sixteen workers completed two fresh-process rounds of both schedules, import policies and storage choices. Each worker ran 32 bursts of eight requests, totaling 4,096 measured requests. The second round reversed storage and import-policy order. Each burst synchronized the GPU, cleared its cache and waited one second before the final memory sample.

The fixed schedule uses 65,535 rows. The mixed schedule cycles through 8,191, 65,535, 16,383 and 65,536 rows, with 65 columns throughout. The table reports the range across the two workers for the last four-burst mean RSS, in MiB. Percentage reductions compare copy and owned workers within the same round.

| Schedule | Import | Copy RSS MiB | Owned RSS MiB | Paired RSS reduction |
| --- | --- | ---: | ---: | ---: |
| fixed | logical | 373.51 to 381.10 | 238.41 to 242.23 | 35.1 to 37.4% |
| fixed | padded | 373.86 to 381.08 | 242.52 to 243.83 | 34.8 to 36.4% |
| mixed | logical | 401.51 to 404.83 | 250.58 to 253.91 | 36.8 to 38.1% |
| mixed | padded | 402.04 to 402.97 | 252.54 to 253.37 | 37.0 to 37.3% |

Live malloc storage remains small after each burst. The complete records include allocated malloc capacity, physical footprint and process-lifetime peak RSS as separate measurements. Per-request reservations drain to zero, the shared model is the only remaining measured MLX allocation between bursts, and final model release returns active/cache counters to zero.

These results support reducing repeated allocations when ownership permits it. They do not establish a process-memory cap, remove all allocator retention, or prove leak freedom for other workloads. Two rounds on one machine are limited evidence; keep the individual trajectories instead of treating a single percentage as a universal improvement.

## Timing observations

The following values are ranges across the two workers' median eight-request burst times, in milliseconds. Copy and owned perform the same oracle work in the same order. These timings include generation, scaling, prediction, validation and hashing, but exclude cache clearing, record serialization and idle time between bursts.

| Schedule | Import | Copy burst ms | Owned burst ms |
| --- | --- | ---: | ---: |
| fixed | logical | 123.56 to 130.06 | 117.13 to 126.19 |
| fixed | padded | 125.38 to 128.75 | 121.31 to 125.19 |
| mixed | logical | 80.53 to 86.37 | 80.09 to 82.61 |
| mixed | padded | 77.61 to 82.54 | 76.78 to 77.15 |

This is a memory-cleanup workload, not an uninterrupted serving benchmark. Timing differences are supporting observations. Production performance needs a separate comparison without diagnostic idle periods, including varied model sizes and caller ownership patterns.

## Validation and review

The accounted build passed 842 selected Release tests, zero failures and two optional tokenizer skips. Xcode records 1,031 successful executions including parameterized cases. An existing MNIST fixture test returns early without its developer-local file and counts as passed. This is not full-library or sanitizer certification.

All twenty ownership and bitwise checks passed. Thirteen controller tests passed, including rejection of missing oracle capacity and rejection of explicit copy controls falsely claiming no retained oracle. Historical records remain valid through a separate validation option. The final validator rechecked all 4,096 measured requests and their recorded capacity components. The original single-burst mode also passed four workers and 32 requests after the changes.

Review identified the oracle-accounting omission before final measurement. The superseded run was stopped and its incomplete results are excluded. A second review tightened the explicit-copy validator while the corrected run was underway. The exact controller used to collect that run is archived with its provenance; the final stricter validator subsequently checked every record. Both review findings were resolved.

## Reproduction and next integration boundary

Hardware was Apple M4 Max with 128 GiB unified memory, macOS 27.0 build 26A428. The Release arm64 worker targets macOS 14; no macOS 14 runtime was tested. MLX Swift remains pinned to `4657976edcdd2c60642424985d474b45ddddb390`. Coverage is disabled, with safe Metal math and precise FP32 functions.

Final worker SHA-256: `ce101b897de68272db43d7ed67d4a667dc9440b2c1986e3cf81e71efbd7e5d6c`.

Replay commands are in `Benchmarks/RetainedGPUTrial/README.md`. Local full logs and the Xcode result bundle are under `~/local-ai/spl/swiftsci/gpu-allocation-sites-20261007/`. Compressed allocation-history files preserve the original bytes; extracted site summaries retain line numbers.

Before production adoption, decide how callers express permission to consume their input. Then integrate through the existing prepared-batch implementation, preserve its full metadata and missing-value semantics, test errors and concurrent access rules, and benchmark both unique and aliased callers. The prototype's direct reads of scaler parameters rely on the immutable-fitted-scaler condition and are not a new public synchronization contract.

- [Allocation-site evidence](../archive/2026-10-07/gpu-allocation-sites/allocation-sites.json)
- [Validation and paired measurements](../archive/2026-10-07/gpu-allocation-sites/validation.json)
- [Complete comparison summary](../archive/2026-10-07/gpu-allocation-sites/accounted-comparison/summary.json)
- [Comparison provenance](../archive/2026-10-07/gpu-allocation-sites/accounted-comparison/provenance.json)
- [Ownership and bitwise checks](../archive/2026-10-07/gpu-allocation-sites/owned-check-final.stdout)
