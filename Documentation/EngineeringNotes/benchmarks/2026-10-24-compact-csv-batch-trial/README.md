# Reject scoped bulk CSV construction

The working implementation remains at `5b9c90297723cf53dcba17299c57778688e282e2` on `codex/csv-compact-construction`. Its [earlier validity-word optimization](../2026-10-24-compact-csv-construction/README.md) is preserved. This trial retains no production-source change, changes no package minimum, and creates no PR. The temporary empty child branch was removed after preserving both candidate sources and their patch here.

## Question and diagnosis

Can a standard-library bulk append reduce the remaining CPU cost of compact CSV construction without sacrificing its memory benefit? A reduced read-only replay still measured 3.2% more charged CPU for compact than optional storage. Its identical-binary controls passed. The replay exited 1 at its recorded 1.02 diagnostic ratio. This is a screening signal, not a CI timing policy.

The ranked explanations were a remaining append call, validity/array ownership work, and a small construction opportunity within parsing-dominated reads. Native sampling weakens the first explanation: the measured compact append is already inside the conversion loop. It shows more ownership checking for compact storage, while byte parsing and record scanning dominate computation. Idle dispatch and run-loop samples are not computation.

## Design and implementation

The architect workflow produced two caller-first sketches. The builder-wide candidate adds a batch protocol requirement; the scoped candidate limits the change to compact Double conversion. Parent review and an independent cross-judge select the scoped design, preserving the measured Double specialization and leaving optional conversion alone. The exact grounding, sketches, rubric, judgment, synthesis, and rejection are in the archive.

The prototype uses Swift's [Array bulk-append API](https://developer.apple.com/documentation/swift/array/append(addingcapacity:initializingwith:)). A builder-owned callback hides OutputSpan, array capacity, and bitmap state from conversion. The conversion loop still owns decode order and first-invalid rejection. Bitmap ownership moves into a local to avoid a copy-on-write clone; validity remains word-based. No decoded staging array or new writer type is added.

The [OutputSpan proposal](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0485-outputspan.md) distinguishes the type from extensions on standard containers. Type availability alone does not establish availability of Array's new operation. The installed Swift 6.4 SDK declares this operation with client-emitted code and macOS 10.14.4 availability. Both small probes typecheck for the package's macOS 14 deployment target. The prototype conservatively guards the new path with compiler>=6.4 and runtime macOS 26; all other builds call the existing scalar path. No older compiler or macOS 14 runtime was tested. A target typecheck is not deployed-runtime proof.

## Resource result

Each screen has eight rotated rounds, parent optional, parent compact, candidate compact, and an identical-binary twin for each condition. A queue contains four complete household CSV reads with one caller and native CPU parallelism. Each screen completes 48 queues and 192 timed reads. CPU includes worker user/system time and measured controller CPU. Memory is sampled worker RSS. Linked dependency hashes match; the two candidate source files and worker hashes are recorded.

| Variant | Parent compact CPU ms/read | Candidate CPU ms/read | CPU change | Parent peak RSS MiB | Candidate peak RSS MiB | Rounds using more CPU |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| scoped | 265.36 | 276.70 | +4.27% | 317.06 | 316.98 | 8/8 |
| scoped-inline | 265.96 | 278.54 | +4.73% | 317.13 | 316.87 | 8/8 |

Both screens pass their recorded repeated-run CPU and RSS controls. The first candidate's median paired-round CPU change is +4.03%; the inline candidate's is +4.23%. Both use more CPU in every paired round. These are repeated finite screens, not independent statistical observations or energy measurements. The second screen compares the inline candidate with the same preserved baseline; it is not a simultaneous head-to-head comparison of both candidates.

Each candidate passes eight independent-reference, full native-bit public-output checks across both storage modes and both reference datasets, including read/sort/matrix workflows. The throughput worker supplies a complete explicit schema for every column in both builds. These timings measure explicit-schema conversion and exclude type inference. The input manifest's `inference_timestamp_policy` field does not describe the worker's effective options.

## What the profile establishes

The scoped candidate reduces sampled ownership-check leaf entries. The parent's compact profile has 213 uniqueness-check stub samples and 113 implementation samples; the scoped candidate has 35 and 13. However, its profile also has 324 samples in the conversion closure and 274 in the append callback's partial-application thunk. Parsing and scanning remain prominent. This is consistent with work moving into callback machinery rather than a useful end-to-end saving. These samples do not assign exact CPU percentages or prove complete causal attribution. Profiled timings are excluded from performance results.

The single-variable follow-up adds `@inline(__always)` to the new batch operation. It still regresses charged CPU. That result does not prove the callback was or was not eliminated, since the inline variant did not receive a new native profile. It establishes that this compiler hint did not recover a resource benefit.

## Decision and limits

Reject both variants. Fewer ownership checks do not establish better code if the complete operation consumes more CPU. The extra API, guards, and metadata handling are not justified by these results. Restore the simpler parent rather than retaining an unproven bulk path. This does not show that OutputSpan or bulk append is generally slow. It shows that this CSV decoding integration loses on the measured workload.

The rejected candidates did not proceed to the null-density panels, full unit suites, mixed queues, reversed-order production panels, or oldest-supported-toolchain checks. Those would be needed before promotion, not to reject candidates that already lose at their target workload. Exact-output preflight is narrower than a full semantic validation. The restored source matches the previously validated parent byte-for-byte; no new full-suite test result is claimed.

AC power was checked at each screen's start. This short screening helper does not record a power check before every queue. RSS sampling can miss short peaks and count shared pages repeatedly. CPU is time, not FLOPs, instructions, normalized P/E-core work, or measured energy. No GPU or Neural Engine result is implied.

[Summary and receipts](summary.json), [artifact hashes](artifact-sha256.json), and [experiment archive](experiment.tar.gz) preserve the rejected sources, exact source fingerprints, build commands, raw queues, output checks, profiles, and design trail. Executables, objects, caches, and raw reference CSVs are excluded. The parent source snapshot is separate from the two rejected file snapshots.

To reproduce, start from the recorded parent, apply `implement.py`, and use `Benchmarks/CPUThroughput/build.py` with a new output directory and the recorded dependencies. The inline variant adds the one attribute recorded in its source snapshot and patch. `measure.py` accepts baseline and trial workers plus a fresh output directory. Absolute paths must exist or be remapped. The archived source hashes must match before interpreting a rerun.

The next useful investigation is the shared number parser and conversion loop, which consume much more sampled computation than bitmap flushes. A new storage abstraction needs evidence beyond reducing a single class of checks.

## Schema-description correction

A source review after this trial found that the original report incorrectly described numeric columns as inferred. `Benchmarks/CPUThroughput/Worker.swift` sets `columnTypeOverrides` for every name and type in the input contract, with parallel conversion. Its measured source SHA256 is `4d9c46bf307e59a68e7998140a5067ad5456044879d1bbf35bb88f867ac21867`. Parent and candidate use that same worker. The comparisons remain matched and the rejection is unchanged, but these results establish no inference-performance claim. Profile symbol names do not establish which conversion branch runs.

The experiment archive and its receipts remain unchanged as a historical record. This correction overrides any inferred-schema interpretation in the archived design notes. Later parser experiments record effective schema options and reject unknown worker implementations before timing. Their proof is a reviewed source fingerprint, not runtime introspection.
