# Foundation specification review

Reviewed `da03a63015...5cc699a7efe3f1d6a2697172eb62b94a35bc3a26` against `PLAN.md`, `data-audit.md`, and `ownership-audit.md`. Read-only review. No builds, tests, or benchmarks.

No blocking specification findings.

The patch addresses the closeout gaps without changing public APIs:

- `DataFrame+SIMDJoin.swift:36-69` now assembles typed columns even for zero matches. Key existence and dtype checks still precede index computation. The left-empty path at lines 81-84 and existing right-empty handling preserve join-kind row semantics. New tests cover disjoint and empty combinations, suffixes, missing/type validation, compact representation, and zero-row matrix preparation.
- `GroupedDataFrame.swift:309-315,530-547` reads columns by index rather than requesting optional-array exports. The reduction loop at lines 552-619 retains row order, compensation, first/last direction, all-null behavior, and IEEE propagation. Compact tests cover signed-zero grouping, normalized NaNs, null groups, first appearance, a second key, and cancellation-sensitive sum parity.
- Join hashing retains its original optional-array specialization. The final delta dispatches only compact Double combinations through the existing owning `CompactColumnValues` view and a generic indexed collection kernel. Both concrete collection types begin at index zero and use the dataframe row counts; optional elements and hash equality remain unchanged. New compact/optional combinations check signed-zero matches, NaN nonmatches, missing nonmatches, and payload correspondence. The view owns its value-semantic column, and result gathering remains unchanged, so it introduces no borrowed-pointer or snapshot lifetime.
- `CoreMLBatchPipelineWindow.swift:14-23` now charges actual retained provenance capacity. Identity provenance remains implicit; selected indices remain charged. Tests verify both cases and rejection of a selected source against an insufficient allowance. Existing shutdown and failure tests remain the evidence for reservation release.
- `Documentation/FoundationContract.md` distinguishes native and compatibility paths, Double-to-Float behavior, model-declared conversion checks, snapshots, caller synchronization, estimated admission, framework ownership, and device-placement limits. It does not claim universal zero-copy, an RSS cap, certified speed, or full numerical conformance.

The optional second identity-provenance copy remains deferred. Its allowance covers both transient arrays.

Plan completion still needs evidence. Final-head Debug/Release tests, numerical policy, controller checks, documentation/type-size validation, preserved resource-study controls, hosted delivery evidence, and tracker reconciliation still require the parent's completion evidence. No scope creep identified.

Final delta review covers `5cc699a7ef`. The collection view changes visibility only within SwiftDataFrame. No new public type, dtype conversion, reduction, or compact representation is introduced. The join contract still accurately promises direct compact-key reads and compact-preserving gathered output. No new blocking finding. Any test results from before this final delta are not final-head validation.
