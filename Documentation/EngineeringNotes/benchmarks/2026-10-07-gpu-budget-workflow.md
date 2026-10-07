# Request admission and scoped import policy

Date: 2026-10-07

## Decision

Keep the request-budget comparison as a benchmark on the memory trial branch. It demonstrates a use for the padded import candidate: saving one temporary Float32 copy can either reduce per-request memory at fixed concurrency or allow another request under the same reservation limit. Production APIs and defaults remain unchanged.

Implementation commit: `18353ffd0645ebde2b7015fcab40a063fb2f198f`.
Parent: `fbafdb53a694a7eea666aa8969c2dc24c852bb8a`.
Branch: `codex/retained-memory-accounting-trial`. Nothing was pushed. This report and evidence belong to `codex/engineering-notes` and must remain separate from implementation PRs.

The experiment does not establish an operating-system memory cap. Reservations control named estimates; process RSS sometimes exceeds the configured limit and can remain elevated after all tracked work is released. That remaining residency needs attribution before a stronger memory guarantee is offered.

## Workload and ownership

Fit StandardScaler and CPU ordinary least squares once on 512 generated training rows. Share the learned scaler and one GPU regression model among a burst of independent requests. Each request has a distinct deterministic seed and waits for a whole-operation reservation before generating its raw input. It then transforms the held-out data without refitting, predicts, checks every output against the analytic formula and hashes the result.

Raw columns, transformed columns and predictions stay within the request function. Only an ID, hash, maximum error and timings return. The enclosing reservation is released after that function returns. One model actor serializes GPU predictions, while admitted requests can generate, transform and consume results concurrently. The experiment adds no gate to force a particular concurrency and no production scheduler.

Wall time includes admission, source generation, preprocessing, prediction, analytic validation and output hashing. There is no network or storage I/O. The analytic consumer makes this an audited request workload rather than an isolated inference benchmark. Per-request prediction time includes waiting for the shared model actor. Training and warmup are excluded. Warmup arrays are released and the MLX cache cleared before the measured burst; normal caching remains enabled during the burst.

## Capacity assumptions

The request estimate includes:

- Two Double column sets for raw and transformed data.
- A page-rounded Float32 packed allocation.
- A second page-rounded Float32 capacity for the logical-copy path when its logical extent is unaligned.
- Twenty-four bytes per output row for GPU output, Float readback, Double result and hash-copy capacity.
- Sixty-four KiB for scaler scratch and metadata.
- An eight MiB backend allowance.

The fixed allowances are benchmark assumptions, not certified allocator bounds for arbitrary models. The Python controller independently reconstructs and checks every component. The shared fitted model, allocator caches and unrelated process memory are outside request reservations. The estimate conservatively sums some capacities with different lifetimes.

At 65,535 rows and 64 columns, the logical path reserves 105.56 MiB per request and padding reserves 89.56 MiB. At 65 columns, these become 107.06 and 90.81 MiB. At 65,536 rows both shapes are aligned, and both policies use the same lower estimate.

This explains the discrete admission change at 192 MiB. Two padded requests fit; two unaligned logical-copy requests do not. These are thresholds in the chosen estimate and budget, not hardware cache thresholds or universal CPU/GPU routing rules.

## Results

The main comparison ran five fresh-process rounds of both policies at widths 64 and 65, row counts 65,535 and 65,536, and limits of 128, 192 and 256 MiB. Each worker completed eight requests. Policies alternate within each round; workers run serially with memory-pressure checks and a 120-second timeout.

Times below are median elapsed milliseconds for the entire eight-request burst. L means logical-extent import; P means padded import. Admission is the peak number of simultaneous whole-request grants. Every round had the same admission peak within each listed case. RSS is median process-lifetime high-water MiB, including fitting and warmup, not an isolated burst peak. The raw records retain the pre-burst snapshot.

| Columns | Rows | Budget MiB | L admitted | P admitted | L ms | P ms | L RSS MiB | P RSS MiB |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 64 | 65535 | 128 | 1 | 1 | 209.33 | 206.83 | 127.17 | 110.78 |
| 64 | 65535 | 192 | 1 | 2 | 210.13 | 117.41 | 127.05 | 192.17 |
| 64 | 65535 | 256 | 2 | 2 | 117.37 | 115.99 | 208.34 | 192.08 |
| 64 | 65536 | 128 | 1 | 1 | 204.98 | 204.47 | 111.06 | 110.70 |
| 64 | 65536 | 192 | 2 | 2 | 115.29 | 116.77 | 192.42 | 192.11 |
| 64 | 65536 | 256 | 2 | 2 | 118.36 | 117.50 | 230.31 | 192.22 |
| 65 | 65535 | 128 | 1 | 1 | 208.57 | 204.28 | 127.69 | 111.12 |
| 65 | 65535 | 192 | 1 | 2 | 210.57 | 115.64 | 127.75 | 194.80 |
| 65 | 65535 | 256 | 2 | 2 | 124.29 | 119.62 | 294.00 | 209.78 |
| 65 | 65536 | 128 | 1 | 1 | 204.06 | 206.18 | 111.39 | 111.20 |
| 65 | 65536 | 192 | 2 | 2 | 115.22 | 117.78 | 196.59 | 196.31 |
| 65 | 65536 | 256 | 2 | 2 | 116.50 | 114.17 | 194.77 | 194.75 |

For unaligned 64-column input at 192 MiB, padding reduced burst time from 210.13 to 117.41 ms, about 1.79 times faster. Median queue time fell from 94.20 to 47.15 ms. At 65 columns the corresponding burst improvement was 210.57 to 115.64 ms, about 1.82 times faster.

At 128 MiB both policies admitted one request. Their elapsed times were close, while padding saved about 16 MiB of peak RSS. At 256 MiB both admitted two requests and their timing advantage largely disappeared. Aligned inputs already avoided the logical copy and showed no corresponding admission advantage. These controls support interpreting the large 192 MiB gain as greater request overlap rather than a faster numerical kernel.

More admitted work raises total live memory. At 192 MiB and 64 unaligned columns, padded requests used about 192 MiB peak RSS compared with 127 MiB for the logical policy because two requests were active instead of one. Lower memory per request does not imply lower memory for the whole serving process when the saved capacity is spent on concurrency.

## Resident-memory limitation

All workers obeyed reservation limits and returned reservations, waiters and tracked MLX active allocations to zero. Explicit cache clearing also returned MLX cache bytes to zero. Nevertheless, some process RSS values exceeded their request budget. In one 256 MiB case, logical import held at most 214.12 MiB in reservations while individual process peaks ranged roughly from 211 to 327 MiB.

An additional comparison doubled that case to sixteen requests, using five rounds of both policies at 65,535 rows, 65 columns and 256 MiB. All workers still admitted at most two requests. Median elapsed times were 224.06 ms for logical import and 226.20 ms for padding. Median process peaks were 212.88 and 196.31 MiB. Individual logical workers still retained elevated RSS after explicit cache clearing, while all tracked counters were zero.

The longer burst did not show a consistent increase in median RSS, but neither comparison proves the absence of leaks. Released pages can remain resident, and these counters do not identify every live Swift or native allocation. Do not attribute all remaining RSS to allocator caches without profiling. The next investigation should separate live allocation ownership from retained allocator pages and record physical footprint as well as RSS.

## Validation and review

The worker built in Release and the nine selected integration targets passed 842 tests, with zero failures and two optional tokenizer skips. Xcode reports 1,031 successful test executions including parameterized cases. Four new controller tests passed, including deliberately corrupted admission, request, oracle and cleanup records.

The main comparison passed 120 workers and 960 requests. The longer-burst check passed ten workers and 160 requests. Complete output hashes matched across policies, rounds and budget limits for each workload. The fixed analytic bound remained `1e-4`; maximum error across the 1,120 measured requests was `1.9073486328125e-06`. A preliminary two-worker smoke test also passed sixteen requests and is archived separately.

Independent behavior and standards reviews found no actionable changes. Both reviews called out that `ru_maxrss` includes the whole process lifetime; the report and tables preserve that definition. The earlier scoped-import stream check was also completed against the pinned MLX source: `Stream.gpu` resolves the task-local override used by the nondefault-stream test.

The two skipped tests need the optional Llama tokenizer fixture. An existing MNIST fixture test returns early and is recorded as passed when its developer-local file is absent. These gaps do not establish those fixture paths. This was a selected integration run, not a full-library or sanitizer run.

## Reproduction and limits

This is a generated regression-serving workload on one Apple-silicon machine, with one shared model actor and fixed request sizes. It does not emulate a complete production service, mixed models, variable arrivals, actual system memory pressure, or an operating-system memory limit. The host has ample physical memory; the configured request limits are application admission policies.

Hardware was Apple M4 Max with 128 GiB unified memory, macOS 27.0 build 26A428. The Release arm64 binary targets macOS 14; no macOS 14 runtime was tested. MLX Swift remains pinned to `4657976edcdd2c60642424985d474b45ddddb390`. Safe Metal math and precise FP32 functions were selected, and the comparison rejected coverage-instrumented binaries.

Binary SHA-256: `f425654dc1c2ef75b6605975cf02b218f10b0e23b166df335ff97177e3a1d032`.

Replay instructions are in `Benchmarks/RetainedGPUTrial/README.md` on the implementation branch. Local commands, logs and test bundle are under `~/local-ai/spl/swiftsci/gpu-budget-workflow-20261007/`. Archived summaries, samples and provenance retain the evidence independently of this prose.

- [Eight-request comparison](../archive/2026-10-07/gpu-budget-workflow/comparison/summary.json)
- [Sixteen-request follow-up](../archive/2026-10-07/gpu-budget-workflow/longer-burst/summary.json)
- [Validation and limitations](../archive/2026-10-07/gpu-budget-workflow/validation.json)
