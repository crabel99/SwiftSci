# CPU retention and allocator reclamation

Date: 2026-10-06. Production head: `530151b4fa700cdd55cca95dc43d4d5080469d2a` on `codex/memory-kernel-trial`.

## Finding

The large retained CPU workspace is freed memory held by the process allocator.
After fitting three matrix shapes, VM snapshots identify 33.3 MiB in two
`Malloc Large (empty)` regions. Those regions are unchanged between the first
and twelfth three-fit cycles. Returning from the input-owning helper also removes
about 42.46 MiB of live input allocations, but the default allocator retains their
pages. This explains why releasing Swift owners does not immediately lower the
process footprint by the same amount.

A process-local diagnostic control, `MallocLargeCache=0`, removes the empty large
regions and lowers median post-fit footprint growth from 35.16 MiB to
0.77 MiB. The three control observations are
0.766, 0.781, 0.750 MiB. All fits retain their numerical
checks. This attributes the main retained footprint to allocator caching and
deferred reclamation, rather than accumulating live models.

This is not a production setting recommendation. Apple's published xzone source
makes this flag change both the huge-allocation cache and deferred reclamation
for tiny, small and large allocations. It is broader than its name suggests.
The controls therefore do not isolate the performance cost of the large cache
alone. The source is a published revision, not a verified source match for every
internal detail of macOS 27. The observed VM differences establish the result on
this host. See the [pinned allocator initialization](https://github.com/apple-oss-distributions/libmalloc/blob/c49dafa25f1efe8607701ae6014a663ad2ee437f/src/xzone_malloc/xzone_malloc.c#L8489-L8508).

## Repeated-fit measurements

Twelve fresh workers run twelve cycles each, for 432 measured fits. Each profile
has three workers with CPU and GPU warmup and three that skip the GPU warmup fit.
Worker order alternates by round. Inputs remain alive during all fit snapshots.
The table shows medians for the workers that skip GPU warmup, relative to their
inputs-ready observations.

| Profile | Footprint growth after 3 fits | After 36 fits | Live malloc growth after 36 fits |
| --- | ---: | ---: | ---: |
| cpu-same | 25.44 | 26.56 | 94.9 KiB |
| cpu-sizes | 34.53 | 35.16 | 116.0 KiB |

The footprint mostly plateaus. It does not return to zero, nor is it exactly flat.
Across cycles 6 through 12, individual runs add at most 1.04 MiB for the repeated
shape and 0.36 MiB for the shape sequence. Trace dictionaries and small numerical
results remain live during measurement, so the roughly 95 to 116 KiB of live
malloc growth is not evidence that all of it is leaked. This bounded experiment
does not establish an unlimited-duration no-leak guarantee.

The repeated shape is 100,000 by 32. The shape sequence is 100,000 by 32,
8,192 by 128, and 100,000 by 8. Each cycle runs three sequential Double OLS fits.
A single private stream scope surrounds the sequence. Each fit verifies held-out
predictions, result completeness, selected CPU route, repeatability and zero
active MLX bytes. Independent reference fits follow the memory observations.
Small MLX compatibility state and stream synchronization remain in the CPU route;
skipping the GPU warmup fit does not remove all MLX or Metal initialization.

## Warmup confound

All six workers with GPU warmup show a delayed footprint drop of roughly 160 MiB.
None of the six workers that skip that fit shows the same drop. The instrumented
GPU-warmed worker has 160.0 MiB labeled `owned unmapped (graphics)` before the
measured sequence, and that category disappears later. This explains the sign
change in the earlier CPU traces. It is not evidence of improved CPU deallocation.
The exact backend owner of that graphics region was not traced.

VM inspection takes time and shifts the point at which reclamation happens.
The instrumented GPU-warmed run loses that region earlier than the uninstrumented
runs. Instrumented observations are therefore attribution evidence, not timing
samples or substitutes for the repeated uninstrumented measurements.

## Ownership and leak checks

Three VM-profiled workers inspect warmed, inputs-ready, cycle 1, cycle 12,
inputs-dropped and final-cleanup boundaries. Two use the default allocator and
one sets `MallocLargeCache=0`. The default CPU-only-warmup worker has 33.3 MiB of
empty large regions and 66.4 MiB resident in empty small regions after releasing
inputs. With the control, no empty large region remains; empty small regions are
still resident but have zero dirty bytes in the snapshot. Resident size, dirty
bytes, physical footprint and malloc bytes in use are different measurements.
Do not add these categories or substitute one for another.

A separate default-allocator worker runs the same 36 fits under malloc stack
logging and Apple's `leaks --atExit`. The scanner reports zero leaks and zero
leaked bytes. That checks the process-exit graph, not every intermediate boundary.
It complements the live-allocation and VM observations; it does not prove that
all allocations in SwiftSci or its dependencies are leak-free.

The terminal malloc pressure-relief request remains a best-effort diagnostic.
A zero return must not be interpreted as absence of reclaimable resident pages.
No automatic allocator relief or MLX cache clearing was added to production.

## Scope and validation

- The two initial current-head reproductions pass all numerical checks and retain
  26.11 and 34.41 MiB respectively after nine fits.
- The repeated-fit matrix passes 432 measured fits across 12 workers.
- Three cache-disabled controls pass another 108 measured fits.
- Three VM-profiled workers pass 108 measured fits.
- The separate leak-scanned worker passes 36 measured fits and the leak check.
- Total: 21 fresh workers and 702 measured fits, excluding warmups and later
  independent reference fits. Every worker has a 45, 60 or 90 second deadline.
- Builds and measured workers run sequentially. Host-pressure checks remain normal.
- The Release diagnostic snapshot builds successfully. Production code and the
  tracked checkout are unchanged. The previously validated executable is restored
  after the snapshot build. No full production test rerun or CI run was needed
  for these disposable instrumentation changes.

## Design consequence

Keep active-job reservations separate from process-resident headroom. Ending a
reservation proves that the job released its logical ownership; it cannot promise
that macOS immediately returns its cached pages. The earlier strict 32 MiB
footprint-coverage failure remains a policy/accounting issue, not a corrected
production assertion. Do not hide it by raising defaults without validation.

The next useful experiment is a library-owned, bounded CPU workspace reused across
fits and counted once while retained. Compare its throughput, peak footprint and
size-transition behavior against the current allocator-backed arrays under normal
allocator settings. Check whether it avoids duplicate retained capacity before
integrating it. Avoid global allocator switches or per-fit purge calls as a
library policy. This report makes no performance claim for the diagnostic flag.

## Reproduction assets

The archive retains the disposable source patch, controllers, numeric observations,
sanitized VM categories and source fingerprints. Full VM output and the leak log
stay in the local evidence directory because they contain process and address
metadata. The diagnostic executable remains a separate cache copy. No code or
report has been pushed, and no engineering notes enter the implementation branch.
