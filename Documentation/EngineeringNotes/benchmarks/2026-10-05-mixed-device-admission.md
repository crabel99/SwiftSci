# Mixed CPU/GPU admission and ownership

## Decision

Commit `597421a7a38e80e7485aa8c71c63cb08d92cffbe` on `codex/memory-kernel-trial` qualifies mixed CPU/GPU consumers under one estimated-byte budget. The baseline is `4a488b52799cbf3b173b8d3b9b2606588cd2f265`. Production algorithms, memory APIs and default admission policy are unchanged. This report belongs only to `codex/engineering-notes`.

The combined private-stream and reservation pattern passed ownership and numerical checks. More admitted CPU work improved throughput. More admitted GPU fits did not improve the larger workload's throughput and increased memory. Keep device concurrency and memory admission as separate caller decisions. These results do not justify one global concurrency default or a universal CPU/GPU routing rule.

## Workload and contracts

Each fresh process submits four independent public LinearRegression models sharing immutable, training-only scaled input. Small inputs contain 1,024 rows and eight features; large inputs contain 16,384 rows and 32 features. Both have 128 held-out rows and use the existing noise-free synthetic linear fixture. Device mixes are four CPU jobs, four GPU jobs, or two of each. One, two and four equal job estimates vary admitted width.

CPU uses the existing Double OLS solver. GPU uses the existing Float32 gradient-descent implementation with 1,000 epochs. They do not perform the same algorithm or promise the same precision. Compare admission settings within each mix. A difference between CPU and GPU batch time is not a hardware speed comparison.

Every job checks the resolved device. After timing and memory capture, independently constructed row-array pipelines provide serial references on the same device. CPU predictions and fitted parameters must agree exactly. GPU predictions and fitted parameters use the existing bound `5e-6 * max(1, abs(reference))`. Both routes also check analytical held-out predictions, using the existing absolute bounds of `1e-7` for CPU and `0.01` for GPU. Scaler parameters must match training-only reference fitting. No tolerance was relaxed.

## Streams and ownership

The pinned MLX Swift implementation creates private task-local CPU and GPU streams through `Stream.withNewDefaultStream`. Nested `Device.withDefaultDevice` preserves those streams; selecting a device alone does not establish isolation. The reviewed build checkout is revision `19601207e9a0de51e03ee6ec0c3c5f3784275075`. See its [Stream implementation](https://github.com/ml-explore/mlx-swift/blob/19601207e9a0de51e03ee6ec0c3c5f3784275075/Source/MLX/Stream.swift).

Each timed job creates its model within the admitted operation and drains its private streams on success, cancellation and errors. The shared input cache has one reservation before construction. A separate helper owns the cache until all timed jobs and reference checks finish, then returns scalar measurements before the shared reservation ends. Persistent model state does not escape; returned predictions are ordinary value arrays and their retention remains a separate accounting responsibility.

Three deterministic lifetime cases exercise the production ScopedGPURead adapter inside this explicit stream-drain pattern. They submit an aliased shared Metal buffer, then hold the operation open. A weak reference confirms that the actual buffer remains alive, while the budget confirms the full reservation remains held. The cancellation case repeats these checks after cancellation with the gate still closed. Success, cancellation and injected error all finish with the buffer released and zero reserved bytes.

These checks qualify the combined adapter and explicit private-stream drain. They do not isolate the adapter's internal drain, nor prove that GPU instructions are still executing when the gate is inspected. Source review found no remaining actionable issue after adding the post-cancellation assertion and direct owner observation.

## Memory and timing

The shared estimate covers three input payloads plus 64 MiB, including cache-construction overhead. Each job uses the existing conservative estimate of twelve Double feature buffers, four Double row buffers and 64 MiB. Using equal CPU/GPU estimates isolates admitted width from device-specific cost weighting. These are experimental allowances, not calibrated allocator limits. The total limit always accommodates the shared cache plus the allowed number of complete job estimates.

Batch timing includes task-stream creation, fitting, prediction and draining. Shared input construction is reported separately and as setup-plus-batch time. Queue, service and completion durations are preserved per job and device. Process CPU time includes native library threads. Admitted-scope overlap is checked, including both devices in concurrent mixed runs; it does not establish simultaneous kernel execution.

Process peak RSS includes cache construction and the timed batch, sampled before the reference runs. MLX peak active allocation, remaining active allocation and retained cache are distinct fields. They do not measure the same quantities as RSS or the admission estimate. Oracle allocations occur after measurement and are excluded from the comparison.

## Results

Three rotated rounds completed 54 fresh processes and 216 model fits on an Apple M4 Max with 128 GiB unified memory, macOS 27.0 build 26A428, on AC power. Native thread settings were retained with thread-count overrides removed. The following table shows across-round medians for the larger input. Memory uses decimal MB.

| Mix | Admitted jobs | Batch ms | Jobs/s | Peak RSS MB | MLX peak active MB |
| --- | ---: | ---: | ---: | ---: | ---: |
| CPU | 1 | 101.52 | 39.40 | 30.28 | 0.000 |
| CPU | 2 | 68.35 | 58.53 | 34.91 | 0.000 |
| CPU | 4 | 49.05 | 81.55 | 43.61 | 0.000 |
| GPU | 1 | 1336.74 | 2.99 | 33.54 | 2.294 |
| GPU | 2 | 1336.55 | 2.99 | 35.68 | 4.457 |
| GPU | 4 | 1354.57 | 2.95 | 40.80 | 8.783 |
| MIXED | 1 | 743.84 | 5.38 | 37.73 | 2.294 |
| MIXED | 2 | 729.32 | 5.48 | 40.40 | 4.391 |
| MIXED | 4 | 692.73 | 5.77 | 44.92 | 4.457 |

Four admitted CPU jobs produced about 2.07 times the throughput of one, with RSS increasing about 44%. Four GPU jobs produced essentially the same throughput as one, while RSS increased about 22% and MLX peak active allocation rose from about 2.29 MB to 8.78 MB. The mixed batch gained about 7% throughput while RSS rose about 19%. Its two GPU fits dominate elapsed time for this workload.

Small-input gains were modest in absolute time. CPU batch time fell from about 2.58 ms to 2.10 ms; the mixed batch fell from about 460 ms to 451 ms. Small GPU measurements were non-monotonic across admission widths. Three rounds provide initial comparative evidence, not confidence intervals or a demonstrated optimum.

Every measured process returned to zero MLX active bytes after its batch and released all reservations. MLX retained some reusable cache, reaching at most 394,636 bytes across these runs. Neither observation proves a general upper bound for other model types or input sizes. No hardware counters were collected, so the experiment cannot assign the GPU throughput plateau to bandwidth, command submission, synchronization or arithmetic saturation.

## Validation and reproducibility

The final Release build passed. All three ownership cases and all 54 benchmark configurations passed without widening numerical tolerances. A separate existing eight-job CPU benchmark also passed after sharing the controller invocation code. Controller checks cover four-job, eight-job and lifetime-only success records, plus nonzero exits, timeouts with partial byte output, malformed JSON and incomplete records. Both controller entry points work.

The measured executable's binary hash and complete recorded source fingerprint match the committed files. The build manifest records the parent HEAD because the final sources were staged during the build; file hashes establish the exact measured contents. No source changed after the repeated run. The full production Debug/Release suites were not repeated because production Swift code is unchanged. Their two previously recorded MLX rotary precision failures remain unresolved; this experiment is not a claim of full numerical conformance.

Run `python3 Benchmarks/UnifiedMemoryPrototype/mixed_device.py --build --output /tmp/swiftsci-mixed-device`. The controller records the build fingerprint, ownership checks, raw samples, summary and failures. Local evidence is under `~/local-ai/spl/swiftsci/mixed-device-20261005/`, with repeated results in `full/`. Initial smoke samples are separate from the final 54-process dataset.

## Next work

Test a caller-selected GPU concurrency cap while allowing CPU work to use the remaining byte budget. Acquire device-lane permission before reserving shared execution capacity so waiting GPU jobs do not hold memory grants needed by CPU work. Verify cancellation and ordering for that composition before recommending it. Include heavier CPU work and other GPU consumers before treating these small regression batches as representative of training or LLM inference.

Keep precision choice, device choice, reusable-cache ownership and scheduling objective explicit. The current evidence supports the memory kernel's admission and lifetime pattern; it does not call for changing the production solver or silently adding a scheduler.

Implementation and engineering notes remain local. Nothing was pushed or submitted.
