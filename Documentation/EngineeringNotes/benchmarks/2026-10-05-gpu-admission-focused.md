# Focused GPU admission and physical memory

Date: 2026-10-05. Implementation: `332809996a25cc63c85d64fbe3a5b054f9efff8a` on `codex/memory-kernel-trial`.

## Decision

Retain per-workload GPU admission as an option in the experiment. Do not change
production defaults from this small comparison. One GPU slot reduced median batch
time by 3.13% and median peak physical footprint by 2.11 MiB.
This is a modest benefit. Shared admission width and prepared-input reuse remain
stronger candidates for the next memory/performance comparison.

The user identified host memory exhaustion as the cause of the earlier Metal
hang and asked to move on. The stack captures locate execution during that
condition; they do not establish a separate Metal defect. Process cleanup,
deadlines and pressure checks remain useful protections.

## Workload and preservation rules

Fifteen fresh workers ran five repeats of each GPU limit. Every worker used a
shared admission width of four and ran two CPU and two GPU jobs. CPU inputs were
100,000 rows by 32 columns; GPU inputs were 16,384 rows by 32 columns. CPU fitting
used Double OLS and GPU fitting used Float32 gradient descent. Compare admission
policies within this mixed workload, not the speed or precision of the two solvers.

All 60 timed fits and their separate same-device reference checks passed. Six
admission checks covered success, cancellation, errors, queued admission and a
rejected request. Fourteen controller regressions passed, including process-group
cleanup, timeout stack capture and pressure-stop boundaries. The Release build
passed. No production numerical implementation changed; the full production suite
was not rerun for these benchmark-only changes.

## Measurements

Medians across five fresh processes. Batch time includes admission and completion
of the four jobs. Shared preparation is separately recorded in the raw results.
Memory is sampled before the serial numerical reference fits. The kernel's peak
physical footprint includes graphics allocations, initialization and runtime
memory. RSS and MLX live-buffer accounting remain separate measurements.

| GPU slots | Batch time, ms | Peak physical footprint, MiB | Peak RSS, MiB |
| --- | ---: | ---: | ---: |
| Unrestricted | 887.0 | 276.50 | 126.48 |
| 1 | 859.2 | 274.39 | 124.48 |
| 2 | 881.9 | 276.44 | 126.52 |

All before/after worker memory-pressure readings were normal. All post-batch MLX
active counts were zero and all admission grants were released. The controller
checks pressure at worker boundaries and uses a 15-second worker deadline; it
does not continuously enforce the host's total memory consumption.

This is an exploratory synthetic workload on a shared machine. It is not a
formal production baseline or evidence that a single GPU slot benefits every
operation. Unrestricted and two-slot policies can run the same two GPU jobs;
small differences between them provide a useful indication of run variation.

## Evidence

- [Raw observations](../archive/2026-10-05/gpu-admission-focused/samples.json)
- [Summary](../archive/2026-10-05/gpu-admission-focused/summary.json)
- Binary SHA-256: `5d7124feffba52bb7858d6bb6d6e8035954f14fcaf6bc39a22d2b6d4062a23f7`
- Original build-manifest SHA-256: `34694748ac591246f2e35fe9f979b2bcfd06b6c3273fea77a34cdfe83b3a5a41`
- Raw observations SHA-256: `64b44fd28083c0b37f69bb5498269eaf22a1c8ebaa336bc284f5cd6b18ba9fdf`

The original build manifest remains in the local evidence archive. It records
per-file hashes for the changes built from parent `a309f9106bba129f8d4396565c16ef6a0f5db0ea` before
the implementation commit above. The archived numeric observations are unchanged;
this report does not replace historical benchmark fingerprints.
