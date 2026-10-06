# Metal memory retention at the synchronous matrix boundary

Date: 2026-10-06. Repository head: `64c7688a3401a2a93ec3e454baef0723d53a6cba`.
Production sources and the implementation branch are unchanged by this experiment.

## Finding

A synchronous autorelease pool around `ScopedGPURead.withMatrix` removes the
repeated Metal allocation growth in the nine-fit GPU workload. Three fresh-process
comparisons per arm reproduce the result. All 54 measured fits pass analytical
held-out checks, repeated-result checks and independent same-device references.
Reference fits run after memory observations and are additional to the 54 count.

This isolates a cleanup-lifetime problem at our Swift-to-Metal matrix boundary.
It is consistent with Objective-C/Metal objects surviving until an outer autorelease
pool drains. It is not evidence of a new MLX finalizer leak. The pinned checkout
contains the balanced finalizer implementation inspected during this investigation.
We have not identified every intermediate autoreleased object in the ownership chain.

| Build | Cycle 1 Metal growth | Cycle 2 | Cycle 3 | Cycle 3 footprint growth |
| --- | ---: | ---: | ---: | ---: |
| Unchanged helper | 5.109 MiB | 10.219 MiB | 15.328 MiB | 16.219 MiB |
| Helper enclosed in autorelease pool | 0 MiB | 0 MiB | 0 MiB | 0.813 MiB |

Values are medians across three workers. A cycle fits 16,384 × 32, 100,000 × 8
and 1,024 × 8 training matrices in sequence, each with 128 held-out predictions.
Both arms clear the MLX cache and request malloc pressure relief after each fit.
Both hold one private stream pair across the sequence and drain CPU/GPU streams
at fit boundaries. The inputs stay alive until after the final job snapshot.

MLX reports zero active and cached bytes at these measurement boundaries in both
arms. Metal's `MTLDevice.currentAllocatedSize` sees the retained allocations that
MLX's counters miss. Its increments closely match the externally allocated feature
buffers. These counters overlap with physical footprint and must not be added.

## Evidence chain

1. The previous study reproduced growth despite cache clearing, allocator relief
   and a reused stream. This investigation starts from that reproducible workload.
2. A successful Game Memory trace of a separately signed worker records Metal
   allocation and deallocation events. The worker passes all nine measured fits
   and reproduces the footprint growth. The trace contains surviving buffers at
   feature-matrix sizes. The stripped Release binary limits application-stack
   symbolication, and the 20-second trace window is not proof of full-process
   resource cleanup. Do not infer a complete allocation balance from that window.
3. A separate `leaks --atExit` run saves a memory graph. Analyzing it reports zero
   unreachable allocations. Its exit snapshot is not a measurement at each fit
   boundary and cannot rule out reachable objects retaining memory during work.
4. A disposable build adds Mach timestamps and Metal's allocation counter to the
   existing snapshots. Without Instruments attached, it reproduces cumulative
   Metal growth of 5.109, 10.219 and 15.328 MiB. Profiling-only counters are identical
   in both comparison arms.
5. A second disposable build changes only `ScopedGPURead.withMatrix`, enclosing
   its synchronous body in `autoreleasepool`. Prepared inputs, arithmetic,
   stream draining, cleanup treatments and validation remain identical.
6. A memory assertion checks that Metal allocation after cycle three does not
   exceed its level after cycle one. It fails in all three original workers and
   passes in all three candidate workers. The candidate also returns to the
   inputs-ready Metal allocation level after every cycle.

The original build was restored after the experiment and its SHA-256 verified.
The repository has no tracked edits. Candidate binaries, debug symbols, traces
and raw memory graphs remain local. The portable candidate patch and numerical
observations are preserved on the engineering-notes branch only.

## Profiling access and limitations

The first Game Memory attempt failed to attach to the Release executable.
A separate ad-hoc-signed copy with `com.apple.security.get-task-allow` produced a
successful trace. macOS developer-tool access remained disabled; no global setting
was changed. A subsequent symbolicated recording also failed to attach, reporting
that the target appeared to have exited while loading the instrumentation library.
That failed recording is excluded from the evidence. Successful untraced runs of
both symbolicated binaries provide the paired quantitative comparison.

The initial trace, its exports and the exit memory graph remain local because
profiling containers may include incidental machine and process metadata.
Only target-specific numerical observations and portable patches are archived here.
The memory-graph run used malloc stack logging, which warned that its own pages
were included in footprint. Its footprint is not compared with the paired runs.

The controller uses fresh processes, alternates arm order, removes thread-count
overrides and applies a 20-second deadline to each paired worker. Host pressure
checks remained normal. A reporting-only Python variable collision interrupted
printing after the first valid observation; the saved observation was retained,
and the controller resumed the five remaining workers. No failed numerical run
or adverse memory observation was discarded.

These are memory-lifetime experiments, not speed benchmarks. Instruments and
malloc stack logging add overhead. This does not establish long-duration stability,
concurrent-call safety or a full-production performance result.

## Candidate and promotion boundary

The candidate pool contains no suspension point. It wraps feature-buffer allocation,
fill and the synchronous operation. Existing `withBuffer` cleanup synchronizes GPU
work before the pool drains. That ordering matters; an autorelease pool must not
be stretched across an `await` that can resume on another thread.

Before promoting the candidate, add regression coverage at this helper's ownership
boundary for successful completion and throwing operations. Verify cancellation
through its asynchronous callers, external-owner retention until GPU completion,
and prepared versus row-array fitting and prediction. Then rerun the bounded
workload, relevant production tests and an unprofiled performance comparison.
The existing no-lazy-result-escape contract must remain explicit.

The candidate is not yet a production fix or an upstream dependency report.
The next implementation change should be a small ownership-boundary patch with
those regressions, rather than a global cache purge or a larger reservation budget.

## Fingerprints and reproducibility

- Unchanged symbolicated worker: `42bdb85eb58aa7c1763a6eb63c02288b361559ab3c5c6fb9ca9a3cbbb090fa51`.
- Pool candidate worker: `7a26d7044f11e408f5923eb2b7f13dd4d83d2affa38496b7bac0e16ea19df7a6`.
- Paired observations: `aa0166b4457c60246ea9a91b7eceffa82c8f59fb68e1425c658225fea3f2b0a1`.
- Base implementation: `64c7688a3401a2a93ec3e454baef0723d53a6cba`.

Portable patches and JSON evidence are in
`../archive/2026-10-06/metal-profile/`. Apply `profiling-counters.patch` to a disposable
snapshot of the recorded head for both arms. Apply `pool-candidate.patch` only to
the candidate. Build the integration prototype in Release with debug symbols and
run `--retained-memory gpu-sizes both 3 sequence` for three fresh processes per arm,
alternating order. The two build manifests were checked to differ in exactly one
source file, `Sources/SwiftPreprocessing/Core/ScopedGPURead.swift`.

Raw build manifests, the successful `gpu-signed.trace`, graph and failed-attempt
logs remain in the local `memory-profile-20261006` archive. A future profiling
controller should preserve the same signing isolation, process deadlines,
source fingerprints and explicit distinction between failed and usable traces.
