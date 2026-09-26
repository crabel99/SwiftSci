# Reproducible benchmark architecture

Status: proposal, 2026-09-26. This document defines a migration target. The command interface and file layout below are not implemented yet.

## Decision

Keep benchmarks as development tooling beside the library. Production modules must not import benchmark support or acquire dataset-download, Python or measurement dependencies. Keep one versioned experiment contract and one run/report format across SwiftSci, pandas, NumPy/SciPy and Kiraa adapters.

Retain the existing `SwiftSciBenchmarks` executable as the initial Swift worker. Extract fixture verification, lifecycle and result encoding into a benchmark-only support target. Do not export it as a public library product. The controller runs engines as separate processes, so it needs no language-specific object bridge. Swift code owns Swift timing; Python code owns Python timing. The controller owns scheduling, provenance, run status and comparisons.

Choose this incremental design over a new nested package or a general benchmark plugin platform. Existing engine runners already provide the necessary integration points. A measurement package can supply lower-level metrics later without changing the experiment contract. ASV demonstrates setup separation, parameterization and process isolation; the Swift benchmark package offers a potential native measurement backend. Neither by itself defines semantic equivalence across our engines. [ASV](https://asv.readthedocs.io/en/stable/writing_benchmarks.html), [Swift benchmark package](https://github.com/ordo-one/benchmark).

## Current gaps that motivate the design

These findings concern the general runners, not every historical benchmark report:

- `Swift/BenchmarkDataLoader.swift` and `Python/benchmarks.py` fall back to locally generated inputs when fixture files are missing. Their generators are not identical. They do not verify the recorded SHA-256 before use. Swift's vector loader accepts arbitrary lengths and the matrix loader accepts surplus bytes.
- `Swift/BenchmarkSuite.swift` reads current resident memory after timing; Python uses lifetime peak resident memory. Both expose `memoryMB`, which hides the difference.
- Swift converts a failed case into a result with zero samples and zero timings. `Python/compare.py` can turn zero Swift median time into an infinite speedup.
- Comparison uses normalized names and substring matching. Shape, data identity and operation semantics are not comparison keys.
- Swift trims about 10% from each tail while Python trims 20% from each tail. Both use a simple normal-approximation interval over in-process samples. Summary arithmetic belongs in one implementation.
- Swift records a broad language-version string and prints Release without proving the build settings. Name filtering happens after a suite runs, so it does not isolate execution.
- `Results/README.md` says results should not be committed, while the repository now intentionally retains optimization evidence. Separate scratch runs from published evidence.

The reports under `Results/APIConsolidation` and `Results/CompactIntegration` already retain raw samples, hashes, source revisions and output validation. Preserve those historical records and promote their shared procedures into the maintained runner.

## Proposed layout

```text
Sources/                           production modules, unchanged
Tests/
  Fixtures/                        small, licensed reference and edge-case inputs
  ...                              correctness and ownership tests
Benchmarks/
  ARCHITECTURE.md                   this proposal
  README.md                        runnable user instructions after implementation
  Specs/
    datasets/                      versioned source, shape and checksum manifests
    workloads/                     operation semantics and expected-answer rules
    profiles/                      smoke, standard and extended experiment lists
    schemas/                       validation rules for manifests and run records
  Tools/                           prepare, orchestrate, validate and report
  Support/                         benchmark-only Swift support target
  Swift/                           Swift worker and benchmark implementations
  Python/                          pandas/NumPy/SciPy worker and pinned environment
  Kiraa/                           Kiraa worker and supported-case declarations
  Data/                            existing ignored data cache
  Runs/                            ignored working run directories
  Results/                         selected immutable published evidence
```

Share tiny fixture definitions with correctness tests rather than copy their answers into each runner. Configure test resources explicitly during implementation. Large public inputs remain outside test bundles. Existing tracked experimental suites and published reports retain their paths until their replacements pass migration checks.

## Four versioned records

| Record | Owns | Required information |
|---|---|---|
| Dataset manifest | Identity and decoding of input | Dataset ID/version; upstream URL/version and terms; SHA-256 and exact size; schema and row count; encoding/layout; generator revision, environment and seed where generated; transformation provenance for derived files |
| Workload specification | Meaning of the operation | Stable workload ID/version; ordered operation definition; columns and parameters; dtype/null/NaN/ordering policy; output schema; validation rule and independent reference source; phase being timed |
| Run plan | Exact experiment | Resolved dataset/workload hashes; engine/build identities; profile expansion; worker/process counts; warmups and samples; reset, cache and ownership policy; thread settings; timeout and memory budget; scheduling seed |
| Run record | What actually happened | Run ID; resolved plan; source/binary/environment fingerprints; per-case status and validation; unmodified samples and units; memory metric definitions; logs and termination reasons; derived summary version |

Separate file-format schema version from workload version and dataset version. Change a workload version when its semantics or measured scope changes. Generated inputs are created once and then loaded by every engine. A common seed does not prove identical data.

A comparison key includes workload version/hash, dataset hash, parameters, output semantics and timing scope. Same-engine regression comparisons additionally require compatible hardware, toolchain, dependency and measurement settings. Source revision and binary identity deliberately differ between baseline and candidate. Cross-engine comparisons declare the different engine and backend identities while matching the common experiment contract.

## Workload identity and capabilities

Use IDs such as `dataframe/groupby-sum/v1`, `preprocessing/standard-to-matrix/v1` and `matrix/gemv/v1`. Shape, key count, null fraction, selectivity and ownership are explicit parameters, never inferred from a display name.

Each engine implements the supported IDs in native code. Manifests describe semantics and parameters; they are not an executable query language or arbitrary command container. Engines declare unsupported operations. A required unsupported case fails plan validation; an explicitly optional case records a skip reason and reduces reported coverage. Do not silently drop it or substitute a different algorithm.

For algorithms with different mathematical objectives or convergence policies, label the comparison accordingly or separate the workloads. Matching operation names is insufficient.

## Execution and validation

The controller resolves and validates a plan, builds or identifies the workers, verifies every input, then starts timing processes serially. Downloads, generation and compilation finish before timing begins. Workers must not discover or regenerate missing input during a reported run.

Each worker implements one internal lifecycle:

1. Prepare native inputs and any state excluded by the workload.
2. Reset to the specified precondition before each measured operation, including ownership and mutable state.
3. Execute the defined operation and force any lazy or asynchronous work to finish inside the timed scope.
4. Stop the clock with the output still alive.
5. Consume and validate the complete output outside timing, then release it according to the plan.

Validation must not permanently alter warm/cold state or copy-on-write ownership. Keep the first verification pass separate from measured worker processes where needed. A retained snapshot is an explicit mutation input, not an accidental consequence of a validation reference. Retain row identities and target alignment checks for complete pipelines.

Require a validation result for each recorded sample. Exact workloads can hash canonical output bytes. Floating-point workloads use declared tolerances, error norms or residuals rather than rounded hashes. Use independent small references, certified answers or a reviewed independent implementation. Agreement between baseline and candidate alone cannot detect an inherited bug. A hash is an identity/integrity check, not mathematical evidence by itself.

Invalid output, exceptions, crashes, timeouts and resource limits produce explicit statuses with no usable speedup. The controller preserves completed records, detects missing worker records and returns a nonzero exit status when required work fails. Failures never become zero-duration successes. Write sample events incrementally and finalize the run manifest atomically.

## Timing scopes

Keep separate workload IDs or explicit versioned scopes for:

- Ingestion: input bytes to a fully materialized frame, with disk/page-cache policy stated.
- Operation: an already prepared frame or matrix to a materialized result.
- First use: conversion, fitting/preparation, operation and final consumer output.
- Reuse: retained prepared inputs and fitted parameters, followed by transformation and consumption.
- Full pipeline: read, select, preprocess, export and run the numerical consumer.

Reset mutable inputs outside timing unless reset/construction is part of the declared task. Release or retain outputs consistently across engines. A fresh process is not proof of a cold filesystem cache. Label warm-cache reads honestly; measure cold I/O only under a documented achievable procedure.

Short operations require calibrated batches or more repetitions, with raw batch time and operation count recorded. Calibration must preserve first-use and mutation semantics. If a meaningful interval cannot be measured, record below-resolution status instead of an infinite ratio.

## Statistics and Apple silicon measurements

Write integer elapsed nanoseconds and metric units into raw records, along with effective clock resolution. Compute summaries in one reporter. Preserve all observations; do not silently discard slow samples. Default to medians, spread and individual process-batch values. Derive uncertainty at the independent process/batch level rather than pretending every inner-loop sample is independent.

Run independent baseline/candidate process batches in balanced order. Capture source commit/tree or dirty patch hash, binary hash, dependency locks, full compiler/build flags, coverage/sanitizer/testability settings, OS build, chip, memory, native versus translated execution, backend versions and thread configuration. Record power/thermal observations where available. Block authoritative timing while builds or other benchmark jobs run. A clean copy of the source outside cloud-synced directories is appropriate for this machine; verify its manifest against the intended revision.

Use distinct metrics:

- `process_peak_rss_bytes`: lifetime high-water mark from a fresh worker process, including setup and runtime.
- `process_rss_after_bytes`: current resident memory at a named observation point.
- `logical_payload_bytes`: data buffer accounting with exclusions documented.
- Allocation count/bytes or CPU counters: optional profiling measurements with collector and scope recorded. Unsupported metrics are null with a reason, never zero.

Do not subtract high-water marks and call the difference exact operation allocation. Separate profiling runs from primary timings when instrumentation changes overhead. An operation must materialize results and synchronize GPU completion before its end timestamp. Report GPU-resident reuse separately from first-use packing, submission and synchronization. Shared physical memory does not imply zero conversion or synchronization cost.

## CI and published evidence

Use correctness gates on ordinary CI. Run performance gates on a named Apple silicon machine with a stable configuration. Gate regressions against the same engine's baseline; cross-library comparisons are reported separately. Establish noise and practical effect thresholds per workload before enabling a gate. Confirm a suspected regression with independent batches.

Profiles select explicit cases without silently changing their parameters:

- Smoke: tiny fixture validation, lifecycle/status checks and numerical correctness. Timing is informational.
- Standard: the supported common dataframe/matrix cases, medium inputs and representative distributions.
- Extended: public suites, larger scales, memory-pressure cases, complete workflows and broader engine coverage.

Each published run contains the plan, environment and source identities, raw samples, validation records, summaries and a README explaining omissions and tradeoffs. Keep ordinary run output under ignored `Runs/`. Preserve selected raw evidence in `Results/` or checksum-addressed CI artifacts with a durable retention policy. Do not overwrite an old run. Historical result schemas remain historical; any importer must mark missing fields as unknown rather than invent provenance.

## Proposed command interface

The following illustrates the intended interface only:

```text
bench prepare --profile standard
bench verify --profile smoke --engine swiftsci
bench compare --baseline <commit> --candidate <commit> --profile standard
bench run --profile standard --engines swiftsci,pandas,kiraa
bench report <run-directory>
```

An offline run uses already verified cached data. `prepare` resolves manifests, downloads or generates inputs and checks hashes; it is the only ordinary command that obtains datasets. Comparing commits builds both revisions with the same recorded benchmark tooling where compatible. Report generation reads existing evidence and never reruns workloads.

## Migration sequence and acceptance

1. Define the four record schemas, typed failure statuses and strict comparison keys. Add tests that reject corrupt inputs, mismatched contracts, missing results and invalid timings.
2. Migrate one existing fixture and CSV/groupby/scaler case through Swift and Python. Verify identical inputs, equivalent outputs and complete records. Remove its fallback generation and fuzzy matching once migrated.
3. Add fresh-process orchestration, shared reporting and the Apple silicon measurement profile. Verify a deliberate failure cannot produce a speedup and a deliberate output error invalidates timing.
4. Migrate the remaining current cases and Kiraa overlap; reconcile the full inventory before retiring older active runners. Keep immutable historical reports and scripts as evidence.
5. Add NIST references, H2O-derived workloads and one pinned real-data workflow using the same contracts. Add further adapters only when supported consumers justify them.

Implement this in a benchmark-infrastructure branch and PR, separate from the compact-storage implementation. Initial cases should use existing public APIs so the tooling can compare upstream and optimized revisions. New compact-only cases declare their required capability and cannot be claimed as same-API baseline comparisons.
