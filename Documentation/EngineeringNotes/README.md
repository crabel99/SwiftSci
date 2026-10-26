# SwiftSci engineering working record

This branch records the engineering rationale behind contributions from the `crabel99/SwiftSci` fork. It retains constraints, alternatives, rejected approaches, benchmark findings, and unresolved questions so reviewers can follow why an implementation changed.

`codex/engineering-notes` is a documentation and evidence branch. It is not an implementation branch and is not intended to merge into upstream `main`. Individual PRs contain the relevant code, tests, public documentation, and a concise explanation of the verified results. Upstream design decisions remain with the maintainer.

The branch started at upstream commit `fd68e6be058aa9fb10be1627a8b8841b9ee9a7e7`. Entries are dated working records, not a claim that every proposal is accepted or every result applies to the latest code. The initial contribution sequence was [testing #41](https://github.com/Nodibell/SwiftSci/pull/41), [repairs #43](https://github.com/Nodibell/SwiftSci/pull/43), [precision #44](https://github.com/Nodibell/SwiftSci/pull/44), and [compact preparation #45](https://github.com/Nodibell/SwiftSci/pull/45).

## Start here

- [October 26 roadmap and publication closeout](benchmarks/2026-10-26-roadmap-closeout/README.md) records the updated tracker, final decision trail and independent publication audits, with delivery and research still open.

- [Complete public numerical workflow](benchmarks/2026-10-26-numerical-template/README.md) provides a copyable package for training-only preprocessing, prepared PCA and classification, with independent stage checks and an actual remote dependency build/run.

- [Agent completion and cooperative cancellation](benchmarks/2026-10-26-agent-completion-cancellation/README.md) preserves producer completion status before tool execution, fixes consumer cancellation, and records full qualification plus the retained legacy database security finding.

- [Combined scientific and inference qualification](benchmarks/2026-10-26-scientific-ai-integration/README.md) joins the reviewed PCA stack with later inference work and corrects false documentation coverage reporting. It preserves separate historical measurement fingerprints.

- [Representative weighted ML Programs](benchmarks/2026-10-26-mlprogram-representative/README.md) records full output vectors, strict precision failures, successful full-Float32 controls, bounded pool stress and CPU-only device dispatch evidence.

- [PR89 maintainer correction](benchmarks/2026-10-26-pr89-review/README.md) records checked PCA dimensions and LAPACK workspace handling, including the correction that preserves native workspace-query limits.

- [Representative Core ML workflows](benchmarks/2026-10-26-coreml-representative/README.md) records frozen real-data models, complete numerical workflows and the multiclass export correction.

- [Logistic GPU zero-logit correction](benchmarks/2026-10-26-logistic-gpu-gradient/README.md) records the demonstrated gradient defect, regression and qualification.

- [Prepared classification](benchmarks/2026-10-26-prepared-classification/README.md) records prepared logistic fitting and prediction with original row provenance.

- [Prepared PCA](benchmarks/2026-10-26-prepared-pca/README.md) records fitting and projection through prepared matrices. The later PR89 review record carries the maintainer-requested sizing corrections.

- [CSV String lookup cost and prefix trials](benchmarks/2026-10-22-csv-string-membership/README.md) separates parsing from matching, records default-token CPU gains and exhaustive Unicode-scalar coverage, and identifies setup amortization before production qualification.

- [CSV String optional-return trial](benchmarks/2026-10-22-csv-string-value-path/README.md) rules out redundant result conversion with identical generated instructions, retains 1,152 validated observations, and rejects both trials without a source change.

- [CSV worker-local batch builder](benchmarks/2026-10-22-csv-local-batch-builder/README.md) records the streaming CPU improvement, 391-test configurations, 3,048 validated observations, and the remaining mixed default-token costs.

- [CSV streaming layout sensitivity](benchmarks/2026-10-22-csv-stream-layout/README.md) records the failed compiler-only qualification, identical code with different setup timings, and worker-local builder trials.

- [CSV null-decoder dispatch experiment](benchmarks/2026-10-22-csv-null-dispatch/README.md) records the local direct-key trial, eager CPU gains, reproduced parallel-streaming cost, ownership diagnosis, and the decision to defer promotion.

- [Bounded CSV String null lookup](benchmarks/2026-10-22-csv-small-null-lookup/README.md) records the conditional two-token CPU benefit, default-set costs, rejected alternatives, 2,080 validated reads, and 2,052 follow-up observations.

- [CSV vector mask reduction](benchmarks/2026-10-22-csv-vector-mask-reduction/README.md) records exact platform reductions, 1,344 validated reference and control reads, and the measured CPU benefit with unchanged storage policy.

- [CSV ingestion and numerical handoff strategy](research/2026-10-21-csv-ingestion-strategy.md) proposes prepared conversion, scoped record batches, demand-driven streaming and staged numerical handoff. It defines compatibility and CPU/memory gates; no implementation benefit is claimed.

- [CSV reference source comparison](research/2026-10-21-csv-date-source-comparison.md) traces the benchmarked pandas, Polars and DuckDB paths and distinguishes parsing cost, value reuse and output storage.

- [Quoted CSV capacity diagnosis](benchmarks/2026-10-20-csv-capacity/README.md) traces oversized columns to reuse of freed parser buffers. A measured preallocation trial saves memory but costs 25–34% more CPU, so production stays unchanged.

- [Serial gather CPU and memory qualification](benchmarks/2026-10-19-serial-gather-resources/README.md) retains the String/Bool savings, identifies the Date regression, and validates a narrower local candidate. Both studies and raw evidence remain recorded.

- [Matched CPU and memory measurements for four merged PRs](benchmarks/2026-10-18-pr-resource-metrics/README.md) records 19 cases and 342 validated workers. CSV, direct target extraction, compact preparation, and batched prediction save CPU; quoted CSV retains additional spare capacity.

- [Resource-efficiency audit of all 27 authored PRs](benchmarks/2026-10-18-pr-resource-audit/README.md) separates measured costs, explicit caller tradeoffs, correctness requirements, and missing CPU evidence. It prioritizes the CSV and gather defaults for resource qualification.

- [Dataframe evaluation protocol](benchmarks/2026-10-18-dataframe-evaluation/README.md) defines comparable experiments, resource and compatibility gates, complete-workflow checks, and the initial CSV and sorting experiment register. It is a plan, not a claim that the new gates have passed.

- [Shared Metal device production qualification](benchmarks/2026-10-07-device-production.md) records the allocation-path change, 874 Release passes and paired public-pipeline results across four sizes.

- [Retained Metal device experiment](benchmarks/2026-10-07-device-reuse.md) isolates repeated device lookup, compares a retained handle with fresh per-request buffers, and defines the next production qualification.

- [GPU prediction phases](benchmarks/2026-10-07-prediction-phases.md) separates small-input packing from device setup, completion and actor waiting, and records the benchmark hash-formatting correction.

- [Small-request latency diagnosis](benchmarks/2026-10-07-small-imputed-latency.md) separates preprocessing and validation overhead from the awaited prediction call, records variable ownership timing, and leaves production dispatch unchanged.

- [Missing observations through GPU regression](benchmarks/2026-10-07-imputed-regression-integration.md) records training-only preprocessing, source integrity, repeated cleanup, sustained memory savings and the observed small-request throughput tradeoff.

- [Prepared imputer integration](benchmarks/2026-10-07-prepared-imputer-integration.md) records native column reuse, the regression finite-input boundary, 872 selected Release test passes and the CPU comparison.

- [Completed MinMax ownership comparison](benchmarks/2026-10-07-consuming-minmax-followup.md) records 48 interleaved workers, 608,256 checked requests and the observed throughput and resident-memory ranges.

- [Consuming MinMax columns in prepared pipelines](benchmarks/2026-10-07-consuming-minmax-integration.md) records verified storage reuse and lower observed resident memory. Throughput remains unqualified because concurrent host work confounded timing.

- [Consuming prepared pipelines under continuous requests](benchmarks/2026-10-07-consuming-pipeline-integration.md) records native ownership transfer, legacy compatibility fixes and sustained public-API measurements.

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

- [CPU/GPU production closeout](benchmarks/2026-10-07-cpu-gpu-closeout.md) records the production/research boundary, complete validation and final public-workflow comparison.
