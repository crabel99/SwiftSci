# Reuse across repeated GPU request bursts

Date: 2026-10-07

## Decision

The allocator retains substantial capacity between request bursts. Live malloc storage remains small while RSS and allocated capacity grow early in the run. Growth slows in the longer runs, but the final values depend on the process and shape schedule. These observations support reuse after allocator expansion within this workload. They do not justify a fixed process-memory bound or a universal leak-free claim.

Keep request admission separate from RSS and physical-footprint policy. Do not add forced pressure relief or a generic buffer pool based on these results. The next useful experiment is allocation-site attribution for the raw and transformed column storage, followed by a bounded alternative that can be compared with the existing allocator's reuse.

Implementation commit: `3e8784e8d1c30336d0e66d70fe680a6539e75c9b`.
Parent: `64b3be7ba8eb6bf105eeb91bb03319e410f3ef4c`.
Branch: `codex/retained-memory-accounting-trial`.
The implementation contains only benchmark modes, controllers, tests and replay instructions. Production sources and defaults remain unchanged. Nothing was pushed. This report and raw evidence are held separately on `codex/engineering-notes` and must remain outside implementation PRs.

## Question and controls

The preceding heap and VM investigation found approximately 2 MiB of live malloc allocations and about 129 MiB resident in empty malloc regions after a single request burst. Allocator pressure relief released zero bytes. That left an architectural question: would subsequent requests reuse those pages or keep expanding the process?

The experiment considered three predictions. Reusable storage should tend toward a plateau for fixed request sizes. Retention of request objects should increase live allocation counts or bytes as bursts accumulate. Deferred native cleanup should reduce some memory measurements during an idle interval. These explanations can coexist, and no single counter establishes ownership of all process memory.

Each worker fits a scaler and model once. It then keeps that GPU model alive while processing successive bursts. The fixed schedule always uses 65,535 rows. The mixed schedule repeats 8,191, 65,535, 16,383 and 65,536 rows. Every matrix has 65 columns.

Each burst completes eight requests, allowing at most two active request slots under a 256 MiB reservation limit. Request data is generated after admission, transformed, predicted and checked against the analytic result. Only a hash, error value and timings leave the request function. The worker synchronizes the GPU, clears its cache, samples memory and waits one second before sampling again. It emits each record immediately instead of storing a history of request results.

The model's baseline MLX allocation is allowed between bursts. Additional active MLX bytes, outstanding reservations or nonzero cache bytes after clearing fail validation. The worker releases the model after the last burst and verifies that active and cached MLX bytes return to zero. Complete result hashes must match for each repeated shape across bursts, policies and workers.

The controller runs one worker at a time, checks system memory pressure before launch and applies a 180-second timeout. The worker also stops if an idle snapshot reaches 2 GiB RSS, 2 GiB physical footprint or 64 MiB live malloc storage. Those limits guard the diagnostic; they are not production guarantees. No native heap inspector or allocator pressure-relief call runs during this experiment.

## Twelve-burst comparison

Three fresh-process rounds of each schedule and policy completed 1,152 requests across twelve workers. Several workers continued to grow through burst twelve. Fixed-shape workers ended between roughly 202 and 447 MiB RSS, while mixed-shape workers ended between roughly 237 and 436 MiB. Live malloc storage remained near 2 MiB.

A one-second idle interval released some residency, especially on the logical-copy path, but did not restore the pre-burst process size. Since these workers were still changing, the investigation extended the run length instead of treating the twelve-burst result as steady state.

## Thirty-two-burst follow-up

Two fresh-process rounds of each schedule and policy completed another 2,048 requests across eight workers. The table gives the observed range across those two workers, in MiB. Each cycle averages four consecutive post-idle snapshots, so mixed-size cycles contain the same shapes in the same order. Late RSS growth compares the last two complete cycles.

| Schedule | Policy | First-cycle RSS | Last-cycle RSS | Late RSS growth | Last-cycle live malloc | Last-cycle malloc capacity |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| fixed | logical | 284.82 to 337.09 | 448.05 to 449.84 | 0.16 to 0.37 | 1.93 to 1.94 | 500.00 to 500.00 |
| fixed | padded | 313.19 to 315.68 | 447.54 to 450.32 | 0.33 to 0.66 | 1.93 to 1.94 | 500.00 to 504.00 |
| mixed | logical | 233.76 to 274.00 | 471.98 to 475.17 | 1.72 to 2.28 | 1.95 to 1.95 | 504.00 to 504.00 |
| mixed | padded | 222.83 to 278.57 | 476.55 to 476.58 | 0.69 to 1.18 | 1.95 to 1.95 | 504.00 to 508.00 |

The raw cycle series preserve early expansion and late behavior rather than reducing the experiment to a pass/fail plateau threshold. Malloc allocated capacity and current RSS are different measurements. Neither is the configured request reservation. Model and runtime state, allocator storage and other native resources sit outside that reservation.

A process can therefore finish every request, release all recorded owners and still retain several hundred MiB. The small live malloc measurements argue against retained large request arrays in the sampled heap. Capacity growth points toward retained allocator storage, consistent with the previous VM-map evidence. These new runs do not identify the exact allocation sites, allocator region policy or native resources responsible for every resident page.

Physical footprint also varies over time independently of RSS. Its complete per-cycle measurements are archived. The one-second idle interval is a controlled observation, not a guarantee that all asynchronous system cleanup has finished. Treat final-cycle ranges as measured outcomes on this host, not as an allocator capacity promised by macOS.

## Validation and review

The final Swift source passed the nine selected Release integration targets: 842 tests passed, zero failed and two optional tokenizer tests skipped. Xcode records 1,031 successful executions including parameterized cases. An existing MNIST fixture test returns early when its developer-local input is absent and counts as passed. This was not full-library or sanitizer validation.

Eleven controller tests passed. Review identified a reporting defect in four-burst smoke runs: comparing the first and last four samples reused the same single cycle and necessarily reported zero growth. A monotonically growing synthetic trajectory reproduced the failure. The report now returns null growth when fewer than eight bursts are available. Both independent reviews finished without remaining actionable findings.

The twenty measured workers validated 3,200 requests. The initial four-worker smoke test validated another 32 requests, and the original single-burst mode passed four workers and 32 requests after extraction of the shared scheduler and capacity helpers. The original mode continues submitting all requests to its budget; only the new diagnostic adds a two-slot cap. The shared numerical tolerance remained `1e-4`.

The initial twelve-burst comparison used the controller before the single-cycle reporting correction. That correction does not affect comparisons with twelve or thirty-two bursts. The exact earlier controller is archived with its fingerprint. The thirty-two-burst follow-up matches the final controller and source hashes. The four-burst smoke summary's old zero-growth field is invalid and must not be used; its records remain useful for lifecycle and output checks.

## Reproduction and limits

Hardware was Apple M4 Max with 128 GiB unified memory, running macOS 27.0 build 26A428. The arm64 Release worker targets macOS 14; no macOS 14 runtime was tested. MLX Swift remains pinned to `4657976edcdd2c60642424985d474b45ddddb390`. The build disables code coverage and selects safe Metal math with precise FP32 functions.

Binary SHA-256: `00f51c26bcb005c99d420b5fba5ce43c5a22f9f741caca689bea220851a10303`.

The worker uses one small fitted regression model, generated inputs and a fixed two-request cap. Explicit cache clearing, serialized result recording and idle periods make this a cleanup diagnostic. Its burst timings do not establish uninterrupted-service performance. `queueMS` excludes time waiting to enter an active request slot. There was no network I/O, sustained external memory pressure or long-running production traffic.

Replay instructions are in `Benchmarks/RetainedGPUTrial/README.md` on the trial branch. Local logs and the Xcode result bundle remain under `~/local-ai/spl/swiftsci/gpu-memory-reuse-20261007/`.

- [Validation and complete extended cycle series](../archive/2026-10-07/gpu-memory-reuse/validation.json)
- [Twelve-burst summaries](../archive/2026-10-07/gpu-memory-reuse/comparison/summary.json)
- [Thirty-two-burst summaries](../archive/2026-10-07/gpu-memory-reuse/extended/summary.json)
- [Final provenance](../archive/2026-10-07/gpu-memory-reuse/extended/provenance.json)
- [Original-mode regression comparison](../archive/2026-10-07/gpu-memory-reuse/original-mode/summary.json)
