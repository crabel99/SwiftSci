# Memory residency after GPU request cleanup

Date: 2026-10-07

## Decision

Keep process residency separate from request ownership and reservation accounting. The inspected workers had about 2 MiB of live malloc allocations after cleanup, while VM maps showed about 129 MiB resident in empty malloc regions. That explains a substantial part of the remaining RSS. It does not account for every page in physical footprint or prove that all library workloads are leak-free.

The tested pressure-relief call released zero bytes and produced no immediate change in RSS or physical footprint. There is no evidence here to add it to production cleanup. Before changing allocation strategy, measure repeated bursts in one process to determine whether later work reuses the resident storage or continues growing it.

Implementation commit: `64b3be7ba8eb6bf105eeb91bb03319e410f3ef4c`.
Parent: `18353ffd0645ebde2b7015fcab40a063fb2f198f`.
Branch: `codex/retained-memory-accounting-trial`.
The commit changes benchmark diagnostics, controller tests and replay instructions. It changes no production source or default. Nothing was pushed. This report and its evidence belong to `codex/engineering-notes` and must remain separate from implementation PRs.

## Reproduction and competing explanations

Three runs of the unchanged worker each completed sixteen requests at 65,535 rows, 65 columns and a 256 MiB reservation limit. Logical import left RSS 292.0, 292.6 and 295.5 MiB above the respective pre-burst values. MLX active and cache counters were zero after cleanup. A delta greater than 128 MiB detected the observed symptom in all three runs. That threshold was an investigation trigger, not a requirement that process RSS return below a particular value.

The initial hypotheses were retained request objects, allocator storage surviving deallocation, and native or GPU resources outside MLX's counters. Request-accounting counters alone cannot distinguish them. The profiler therefore records malloc statistics and physical footprint within the worker, and optionally inspects the stopped process with Apple's `heap`, `vmmap` and `leaks` tools. Native inspection omits allocation contents and malloc stack logging.

The final experiment ran four fresh workers, one for each combination of logical or padded import and native inspection or no inspection. Each completed sixteen requests with matching output hashes. Only one worker ran at a time. The controller checked system memory pressure before launch and bounded all waits.

Each worker stops before the request burst, after synchronization and MLX cache clearing, and after a pressure-relief experiment. A controller resumes it between stages. Stopping and inspecting a process perturbs its schedule and can alter memory observations. These diagnostic runs are not throughput benchmarks, and their lower RSS compared with the original reproduction is not a demonstrated optimization.

## Memory after cleanup

All values below are MiB. These are the worker's `after-cache-clear` snapshots, taken before the inspectors for that checkpoint. Allocated malloc capacity is not the same metric as resident bytes or bytes still in use.

| Profile | RSS | Physical footprint | Malloc in use | Malloc allocated capacity |
| --- | ---: | ---: | ---: | ---: |
| logical-native | 180.86 | 325.92 | 1.97 | 176.00 |
| logical-none | 181.17 | 325.81 | 1.97 | 180.00 |
| padded-native | 162.97 | 324.19 | 1.98 | 172.00 |
| padded-none | 171.34 | 332.13 | 2.05 | 196.00 |

In the subsequent native VM snapshots, the logical worker had 129.9 MiB resident in regions labeled `Malloc Small (empty)`. The padded worker had 128.7 MiB there. Their default malloc zones had 144.4 and 142.6 MiB resident, respectively, with roughly 2 MiB allocated to live blocks. Both zone summaries reported 99% fragmentation. The worker's internal snapshot and the later VM snapshot are separate observations; their values need not match exactly.

Each of the six native leak scans, across three stages and two workers, reported zero leaks and zero leaked bytes. All eighteen native inspector invocations returned zero. This supports the conclusion that the large request arrays were no longer live in the sampled malloc heap. A clean leak scan cannot exclude reachable retention, all GPU ownership defects, or failures in untested workloads.

The remaining physical-footprint accounting is not fully attributed. Before the burst, footprint was already about 170 MiB while RSS was about 25 MiB. Following cleanup, footprint was about 324 to 332 MiB. After the native inspection interval, it fell to about 147 to 149 MiB before pressure relief ran. The no-inspection controls retained the larger footprint. Elapsed time, deferred native cleanup and inspection effects are possible explanations for that difference; this experiment does not separate them.

RSS, live heap bytes and physical footprint answer different questions. Apple's [Metal memory analysis guidance](https://developer.apple.com/documentation/xcode/analyzing-the-memory-usage-of-your-metal-app) discusses using VM information to inspect Metal memory. Its [memory diagnosis session](https://developer.apple.com/videos/play/wwdc2021/10180/) explains why dirty and compressed pages matter to footprint and why freed allocations can leave fragmented pages behind. Neither reference makes our reservation estimate an operating-system memory cap.

## Pressure relief

Apple documents `malloc_zone_pressure_relief` as a best-effort release request. Passing a null zone addresses all zones, and a zero goal asks for maximal relief; its return value is the reported number of bytes released. See the [malloc API contract](https://github.com/apple-oss-distributions/libmalloc/blob/main/include/malloc/malloc.h).

The profiler takes an immediate snapshot before calling it and another immediately afterward. This pair avoids crediting earlier changes during the pause to the call itself. Values below are MiB except the final column.

| Profile | RSS before | RSS after | Footprint before | Footprint after | Reported bytes released |
| --- | ---: | ---: | ---: | ---: | ---: |
| logical-native | 164.88 | 164.88 | 149.13 | 149.13 | 0 |
| logical-none | 181.17 | 181.17 | 325.81 | 325.81 | 0 |
| padded-native | 163.17 | 163.17 | 147.34 | 147.34 | 0 |
| padded-none | 171.36 | 171.36 | 332.14 | 332.14 | 0 |

All four immediate RSS pairs and all four footprint pairs were identical at byte precision. The call reported zero bytes released in every case. The diagnostic still creates small bookkeeping allocations around its snapshots, so changes in malloc bytes in use are not an independent measure of relief. No relief call runs during an ordinary benchmark or from production code.

## Controller cleanup and validation

Review found that SIGTERM could terminate the first controller implementation while its worker remained stopped. A real-process regression reproduced this with the child still in state `Ts`. The revised controller owns the child process group, converts SIGTERM into cleanup, kills and reaps unfinished workers, and restores the previous signal handler. The same regression then passed. Force-killing the controller or a machine failure remains outside this cleanup guarantee.

Seven controller tests passed, comprising the four existing budget-validation tests and three profiling tests. The profiling cases cover early exit, a mismatched checkpoint PID, checkpoint timeout, inspector timeout and real SIGTERM cleanup. Both independent reviewers confirmed that their findings were resolved. They reviewed code; their reviews are not additional test executions.

The final Release run passed 842 tests across the nine selected integration targets, with zero failures and two optional tokenizer skips. Xcode also records 1,031 successful executions when parameterized cases are counted. An existing MNIST fixture test returns early without its developer-local file and is counted as passed. This was not a full-library or sanitizer run.

The four final profiles validated 64 requests. The admission validator checked the configured limit, complete outputs, numerical error bounds, matching hashes, zero remaining reservations and zero MLX active/cache counters after cleanup. Diagnostic timings are excluded from performance claims.

## Reproduction and evidence

The machine was an Apple M4 Max with 128 GiB unified memory, running macOS 27.0 build 26A428. The Release arm64 worker targets macOS 14, but no macOS 14 runtime was tested. MLX Swift remains pinned to `4657976edcdd2c60642424985d474b45ddddb390`. The build selected safe Metal math and precise FP32 functions. The controller rejected coverage-instrumented workers.

Final worker SHA-256: `608fe5ac5e1eba9b33de5017dd06a4e0a79110ade55f8988831e4ad4281b8921`.

Each final profile includes the binary hash and hashes of production sources, trial Swift files, the controller and package manifests. They match the committed source. The initial unchanged-worker reproduction predates this profiler's fingerprint collection, so it does not have the same independently captured provenance record. Its raw output remains archived.

Replay instructions are in `Benchmarks/RetainedGPUTrial/README.md` on the implementation branch. Full local logs and the Xcode result bundle remain under `~/local-ai/spl/swiftsci/gpu-residency-profile-20261007/`. Archived native text logs have trailing whitespace normalized; the original local files remain unchanged.

- [Validation summary](../archive/2026-10-07/gpu-residency-profile/validation.json)
- [Logical profile provenance](../archive/2026-10-07/gpu-residency-profile/logical-native-verified/provenance.json)
- [Logical VM map after cleanup](../archive/2026-10-07/gpu-residency-profile/logical-native-verified/after-cache-clear-vmmap.txt)
- [Padded VM map after cleanup](../archive/2026-10-07/gpu-residency-profile/padded-native-verified/after-cache-clear-vmmap.txt)
- [Failing cleanup regression](../archive/2026-10-07/gpu-residency-profile/profile-controller-red.log)
- [Passing controller tests](../archive/2026-10-07/gpu-residency-profile/profile-controller-green.log)

## Next experiment

Run several bounded bursts within one worker, preserving the fitted model but releasing every request's arrays. Record live heap bytes, allocator capacity, RSS and footprint after each burst and after a fixed idle interval. Include mixed request sizes to test reuse across allocation classes. Keep peak admission fixed while comparing logical and padded import.

A plateau would support reuse of retained storage. Continuing growth would require ownership or allocation-site attribution. Only then compare a targeted allocation change, if warranted. This avoids adding a pool before showing that the allocator's existing reuse is inadequate.
