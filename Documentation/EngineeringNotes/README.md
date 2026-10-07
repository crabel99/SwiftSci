# SwiftSci engineering working record

This branch records the engineering rationale behind contributions from the `crabel99/SwiftSci` fork. It retains constraints, alternatives, rejected approaches, benchmark findings, and unresolved questions so reviewers can follow why an implementation changed.

`codex/engineering-notes` is a documentation and evidence branch. It is not an implementation branch and is not intended to merge into upstream `main`. Individual PRs contain the relevant code, tests, public documentation, and a concise explanation of the verified results. Upstream design decisions remain with the maintainer.

The branch started at upstream commit `fd68e6be058aa9fb10be1627a8b8841b9ee9a7e7`. Entries are dated working records, not a claim that every proposal is accepted or every result applies to the latest code. The current contribution sequence is [testing #41](https://github.com/Nodibell/SwiftSci/pull/41), [repairs #43](https://github.com/Nodibell/SwiftSci/pull/43), [precision #44](https://github.com/Nodibell/SwiftSci/pull/44), and [compact preparation #45](https://github.com/Nodibell/SwiftSci/pull/45).

## Start here

- [Consuming prepared-batch scaler integration](benchmarks/2026-10-07-consuming-scaler-integration.md) moves the ownership experiment into the public scaler API and verifies compatibility and retained memory.

- [Consuming scaler storage after allocation-site profiling](benchmarks/2026-10-07-gpu-owned-scaler.md) identifies duplicate column allocations and compares input reuse with a matched copy control.

- [Reuse across repeated GPU request bursts](benchmarks/2026-10-07-gpu-memory-reuse.md) records early allocator expansion, later reuse and the remaining boundary between request budgets and process residency.

- [Memory residency after GPU request cleanup](benchmarks/2026-10-07-gpu-residency-profile.md) attributes most sampled residual RSS to empty malloc regions, records the ineffective pressure-relief experiment, and preserves cleanup regression evidence.

- [Request admission and scoped import policy](benchmarks/2026-10-07-gpu-budget-workflow.md) records throughput and concurrency under fixed reservation limits, plus the unresolved process-residency boundary.

- [Scoped page-padded import trial](benchmarks/2026-10-07-scoped-padding-trial.md) records the avoided-copy memory benefit, timing uncertainty, ownership checks and unchanged default.

- [Prepared GPU packing default qualification](benchmarks/2026-10-07-gpu-packing-default.md) records tile selection, actual API comparisons, broader integration checks and small-input uncertainty.

- [Shared GPU packing and blocked conversion](benchmarks/2026-10-07-shared-gpu-packing.md) records the shared bulk boundary, 226 passing tests and 760 workflow samples across four feature widths.

- [Retained GPU crossover and compiler investigation](benchmarks/2026-10-07-retained-gpu-crossover.md) records 500 workflow samples, 105 phase samples, verified import decisions and Release compiler findings.

- [Owned schema for retained GPU prediction](benchmarks/2026-10-07-retained-gpu-schema.md) records the typed input adapter, 224 passing tests and 60 workflow samples.

- [Direct packing into retained GPU storage](benchmarks/2026-10-07-direct-gpu-packing.md) records 222 passing tests and 60 workflow samples. Direct packing removes the large-input staging penalty while preserving faster repeated prediction.

- [Retained input regression workflow](benchmarks/2026-10-07-retained-gpu-workflow.md) records 220 passing tests and 40 workflow samples, showing faster repeated prediction with higher setup cost and peak memory.

- [Retained GPU input comparison](benchmarks/2026-10-07-retained-gpu-comparison.md) records 80 verified fresh-process samples, faster large-input reuse, lower offset-input memory, and mixed small-input results.

- [Retained shared GPU input trial](research/2026-10-07-retained-gpu-trial.md) records allocation-scoped ownership, GPU completion on every read exit, seven new tests, and 217 passing focused Release tests.

- [Prepared regression production PR](research/2026-10-06-prepared-memory-pr.md) records draft #62, the compatibility correction, 1,174 passing Release tests, the unchanged CPU regression policy, and uninstrumented memory/performance comparisons.

- [Arrow PR validation and submission](research/2026-10-06-arrow-pr-ready.md) records the clean 1,156-test Release result, independent reviews, draft PR #61, and green prerequisite PR #60 now ready for review.

- [MLX compatibility and memory integration](research/2026-10-06-mlx-compatibility.md) records resolution of all three upgrade failures, passing full Release suites, fresh ownership checks, and the tested working memory head.

- [Pinned MLX Swift backport](research/2026-10-06-mlx-simd-backport.md) records the approved temporary fork, exact upstream patch comparison, passing CPU regressions, and three remaining SwiftSci compatibility failures. Preserve both the finalizer correction and SIMD fix when changing this dependency.

- [Signed Arrow date32 import](research/2026-10-06-arrow-date32-import.md) records the reproduced cast failure, signed-date correction, ownership checks, and existing upstream fix.

- [Owned Arrow import with chunk traversal](research/2026-10-06-arrow-chunk-import.md) records the compatible production optimization, regression evidence, and separate date32 follow-up.

- [Retained Arrow column trial](research/2026-10-06-arrow-retention-trial.md) compares copying and borrowed storage, verifies release, and identifies the production integration boundaries.

- [Legacy memory-ticket deprecation](research/2026-10-06-memory-ticket-deprecation.md) records the first compatibility step in backend reuse and its targeted validation.

- [Reuse existing memory implementations](research/2026-10-06-memory-library-reuse.md) identifies MLX, Arrow, Metal, and Swift container integration opportunities and the contracts that still need local policy.

- [Asynchronous CPU workspace cleanup](benchmarks/2026-10-06-cpu-async-cleanup.md) records close-time admission, cancellation-safe draining, sanitizer checks, and retained model results.

- [Scoped CPU workspace ownership](benchmarks/2026-10-06-cpu-scoped-workspace.md) records explicit per-batch ownership, overlapping reservations, last-borrow cleanup, and the retained memory benefit.

- [Batch-planned CPU workspace and reservation lifetime](benchmarks/2026-10-06-cpu-planned-workspace.md) records the changing-shape memory benefit, complete timing, capacity-error behavior, and cancellation checks.

- [Bounded CPU workspace reuse trial](benchmarks/2026-10-06-cpu-workspace.md) compares ordinary arrays, fixed capacity and query-sized growth, including workload-order effects and the limits of normalized memory measurements.

- [CPU retention and allocator reclamation](benchmarks/2026-10-06-cpu-retention.md) identifies freed resident workspace, isolates the GPU-warmup confound, and records the allocator control and CPU leak scan.

- [Production matrix autorelease cleanup](benchmarks/2026-10-06-matrix-cleanup.md) records the failing-before regression, synchronous cleanup fix, cancellation and owner checks, and unprofiled comparisons.

- [Metal memory retention at the synchronous matrix boundary](benchmarks/2026-10-06-metal-profile.md) records Instruments evidence and a disposable autorelease-pool control that removes the repeated GPU allocation growth.

- [Retained memory across repeated job sizes](benchmarks/2026-10-06-retained-memory.md) separates released input ownership, CPU retention and continued GPU footprint growth, including a stream-lifetime control.

- [Counted GPU slots and unequal workspace estimates](benchmarks/2026-10-06-weighted-admission.md) records slot separation, fixed-budget comparisons and the observed 32 MiB footprint exceedances.

- [Regression workspace calibration and mixed-size FIFO](benchmarks/2026-10-06-memory-calibration.md) separates per-job estimates from shared inputs and runtime memory, with measured coverage and queue-ordering checks.

- [Shared admission across workloads](benchmarks/2026-10-05-shared-admission-workloads.md) compares memory, batch time and job response across three input profiles and three CPU/GPU mixes.

- [Shared admission width with one GPU slot](benchmarks/2026-10-05-shared-admission-focused.md) records memory savings, batch timing and the CPU response-time tradeoff across shared widths.

- [Focused GPU admission and physical memory](benchmarks/2026-10-05-gpu-admission-focused.md) records the bounded comparison, graphics-inclusive memory measurements, pressure guards and host-memory incident resolution.

- [Mixed CPU/GPU admission](benchmarks/2026-10-05-mixed-device-admission.md) records private streams, buffer lifetime checks and device-specific throughput/memory tradeoffs.

- [Concurrent CPU admission](benchmarks/2026-10-05-concurrent-admission.md) records shared-cache ownership, throughput, latency and memory tradeoffs.

- [Repeated fitting and scratch reuse](benchmarks/2026-10-05-repeated-fitting.md) compares caller-owned input caches, changing training splits and bounded scratch reuse.

- [Bounded prepared scaling](benchmarks/2026-10-05-tiled-scaler.md) records the measured dispatch limits, exact-rounding correction and full validation.

- [Memory and performance balance](benchmarks/2026-10-05-memory-balance.md) compares tiled traversal, column access, workspace sizes and the next policy decisions.

- [Production memory integration](benchmarks/2026-10-05-memory-production-integration.md) records prepared regression, estimated admission, ownership checks, full-suite results and the measured memory/time tradeoff.

- [Memory prerequisites before production integration](benchmarks/2026-10-05-memory-prerequisites.md) records byte admission, asynchronous ownership, prepared-column qualification and the measured memory/time tradeoff.

- [Memory foundation fixes and qualification](benchmarks/2026-10-05-memory-foundation-fixes.md) records ownership repairs, shared row maps, allocation accounting, NIST qualification, public workflow timings and remaining production boundaries.

- [Third memory foundation review](benchmarks/2026-10-05-memory-foundation-review.md) records the reproduced MLX donation lifetime requirement, duplicate row maps, production-model qualification gaps, and the proposed snapshot/preparation boundary.

- [Snapshot treatments and direct matrix preparation](benchmarks/2026-10-04-snapshot-treatments.md) records per-snapshot storage choices, ownership checks, setup-inclusive reuse comparisons and the slower lower-scratch packing experiment.

- [Memory kernel trial checkpoint](benchmarks/2026-10-04-memory-kernel-trial.md) records the preserved parent, initialized-owner experiment, verification, clone gains and remaining construction regression.

- [Apple silicon memory design review](benchmarks/2026-10-04-memory-design-review.md) identifies preparation, allocation, ownership and byte-budget gaps, with primary-source evidence and an ordered experiment plan.

- [Fitting access and retained-workflow reuse](benchmarks/2026-10-01-retained-workflow-reuse.md) records scoped fitting reads, changing training folds, cache snapshot behavior, and setup-inclusive speed versus memory results.

- [Bounded gathering and scoped reads](benchmarks/2026-10-01-bounded-gather.md) records the tile-size and buffer-access experiments, exact scratch budgets, and the resulting speed versus memory tradeoff.

- [Sort and gather locality experiment](benchmarks/2026-10-01-unified-memory-locality.md) separates sort-key caching from selected-column gathering, records 360 validated measurements, and preserves the speed versus memory tradeoff.

- [Owned column and selection prototype](benchmarks/2026-10-01-unified-memory-prototype.md) records the local trial, correctness checks, measured memory savings, large-input speed regressions and the next locality experiment.

- [Unified-memory storage design](benchmarks/2026-10-01-unified-memory-design.md) records the current allocation paths, Apple and MLX ownership constraints, local Metal feasibility probe, proposed column/selection/matrix design, and qualification plan. This is a proposal, not an implemented storage replacement.

- [Four-PR implementation sequence](benchmarks/2026-09-28-pr-stack.md) records branch boundaries, compact integration, validation, and remaining review criteria.

- [Upstream integration after Parquet merge](benchmarks/2026-09-28-main-sync.md) records the synchronized PR stack, full unit suite, and CPU acceptance results.

- [Precision branch performance comparison](benchmarks/2026-09-28-performance-comparison.md) compares the branch with its starting point and Python, including accuracy costs and remaining dataframe bottlenecks.

- [Original-decimal ANOVA ingestion](benchmarks/2026-09-28-decimal-ingestion.md) records the SmLs ingestion fix, exact decimal centering, unchanged reference contracts and validation evidence.

- [Dot-product implementation](benchmarks/2026-09-28-dot-implementation.md) records the per-operation policy, BLAS crossover, exact recovery, regression tests and integrated performance costs.

- [Dot-product qualification](benchmarks/2026-09-28-dot-qualification.md) identifies the SmLs ingestion fault, compares reduction accuracy and throughput, and records the range limits that block an unconditional replacement.

- [Precision reduction implementation](benchmarks/2026-09-28-precision-kernels.md) records the centered variance fix, ANOVA speedup, memory measurements and retained numerical failures.

- [Efficient precision on Apple silicon](benchmarks/2026-09-28-apple-precision.md) records crabel99's hardware-focused objective, native Swift FMA/SIMD evidence and the next implementation comparison.

- [Scientific precision practices](benchmarks/2026-09-28-precision-practices.md) compares representation, stable arithmetic and diagnostics, with a reproducible NIST input-conversion experiment.

- [PR 41 repair record](benchmarks/2026-09-27-pr41-repairs.md) explains the nine fault commits, complete validation, and retained acceptance limits.

- [Engineering charter](CHARTER.md) sets the objective and the criteria for planning, implementing and reviewing each step. Read it before proposing new work.
- [September 27 objective](discussions/2026-09-27-objective.md) records crabel99's adoption of this direction.

- [Kiraa reference status](benchmarks/2026-09-26-kiraa-reference-status.md) limits our experimental build to optional, independently validated implementation comparisons.

- [NIST univariate coverage](benchmarks/2026-09-26-nist-univariate.md) records the nine-dataset increment, fixed numerical policy, timing correction and final validation.

- [Benchmark contribution boundary](benchmarks/2026-09-26-standardized.md) retains the current benchmark decisions and local validation evidence.

- [September 26 discussion and decisions](discussions/2026-09-26.md) records our needs, contribution approach, compiler fix, coverage work and branch decision.
- [Decision record format](DECISION-RECORDS.md) describes what to retain when choosing an engineering approach.
- [Retained files](RETAINED-FILES.md) indexes 73 original notes and supporting artifacts captured from the existing SwiftSci research and local verification work.
- [PR #39 snapshot](archive/2026-09-26/pr39.json) preserves the description, public discussion and check results observed when this record was created.

- [Memory prototype sequence](benchmarks/2026-10-01-memory-sequence.md) records snapshot mutation costs, public file workflows, direct device sharing and retained failures.
- [Memory integration proposal](benchmarks/2026-10-01-memory-integration.md) defines compatible integration through prepared selections and matrices, with separate mutation and device qualification.
- [Pinned MLX managed-import failure](benchmarks/2026-10-01-mlx-managed-finalizer.md) records a completed finalizer that retains its captured owner and the passing direct C comparison.

- [MLX 0.32.3 upgrade qualification](benchmarks/2026-10-04-mlx-upgrade.md) records the fixed managed-buffer ownership path and three dependency-related LLM failures that block broader adoption.

- [MLX regression source diagnosis](benchmarks/2026-10-04-mlx-regression-source.md) isolates the missing runtime precision option, verifies the correction, and separates the invalid-context construction defect.

- [Invalid-context generation fix](benchmarks/2026-10-04-context-validation-fix.md) preserves typed errors with stricter MLX validation and records the passing combined Release suite.

- [Retained reservation handoff trial](research/2026-10-06-retained-memory-handoff-trial.md) records atomic admission transfer, storage-owner cleanup, focused sanitizer checks, and the remaining model integration boundary.

- [Retained CPU model ownership trial](research/2026-10-07-retained-model-trial.md) records real model and prediction ownership, transactional refits, cancellation races, and the direct-regression comparison.

## Keeping the record

Commit new discussion summaries, research findings, alternatives and evidence to this branch. Date each entry and identify the relevant source revision. Mark proposals, measured results, source observations and unresolved questions separately. Record why a decision changed instead of rewriting an old experiment as if it had reached the new conclusion.

Archived publication copies have local usernames, hostnames, and device identifiers removed. Paths containing `LOCAL_USER` and values such as `LOCAL_DEVICE_ID` are placeholders. Measurements, numerical outputs, failures, source revisions, and technical limitations are retained. See the [publication review](PUBLICATION-REVIEW.md) for scope and provenance limits.

The initial collection includes the retained Markdown notes under the local SwiftSci research directory, three uncommitted workspace proposals, the storage research's small supporting artifacts, and the compiler verification snippets. Build caches, binaries, generated datasets and a duplicate source checkout are excluded. Large raw outputs remain in their existing locations or committed benchmark evidence. This is not an export of other chats or every local run artifact.

## Relationship to upstream contributions

Keep this branch on our fork. Push its commits to `origin/codex/engineering-notes`; do not open an upstream PR from it. The fork and this branch are public. Review prose and evidence for credentials and unnecessary personal or machine information before every push.

Start implementation branches from the appropriate upstream revision or agreed dependency branch. Keep our internal research, engineering decisions, discussion summaries and local reports on this branch. Contribution branches may contain implementation, tests, fixture attribution and public usage instructions. Do not copy internal records into a PR; summarize the relevant verified facts for reviewers. Avoid merging this archive branch into them. Upstream remains the owner of its API and architectural decisions; our working proposals do not imply maintainer approval.

Bring upstream changes into this branch when useful, preserving the dated records. A newer codebase does not retroactively validate an older result.

## How we explain a contribution

Explain the observed problem, the alternatives, the chosen tradeoff, the behavior that must remain correct, and the evidence supporting the choice. State limitations and the conditions that would justify revisiting it. Invite the maintainer to challenge assumptions.

The PR should contain enough reasoning to review the change. Lasting design decisions belong in maintained documentation. Code comments should explain constraints that a future maintainer cannot readily infer from the code.
