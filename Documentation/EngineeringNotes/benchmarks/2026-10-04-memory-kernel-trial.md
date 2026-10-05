# Memory kernel trial, first checkpoint

Date: 2026-10-04. Status: local experiment with mixed performance results. This is not a production promotion or a completed memory-kernel architecture.

## Branch and rollback

The child branch `codex/memory-kernel-trial` starts at `aa5c71968c080f4188357c4cb628389f89ca00a2`. The parent `codex/unified-memory-prototype` remains unchanged at that commit. The first child commit is `5904a0eaebcd0da60400fb593f3fadbe335e675c`. Both branches remain local for this step; no push or PR was performed.

This follows the [memory design review](2026-10-04-memory-design-review.md). The branch isolates architectural experiments while retaining the existing prototype as a comparison control. Engineering rationale stays on `codex/engineering-notes`.

## Implementation

The owner now separates allocation from initialization. A private initialized-prefix count controls destruction if a generated value throws. Successful initialization publishes the complete owner. Generated columns write each payload once, including a zero payload for missing cells, and validity words start at their required all-valid value. Cloning initializes the destination directly from the source rather than filling it with zeros first.

Zero-filled scratch and the mutable dense-buffer callback preserve their existing initialized-storage contract. Numerical operations, matrix layouts, missing-value semantics and public production sources are unchanged. Source changes are limited to the prototype's `Storage.swift`, `Checks.swift` and README.

An initial candidate updated the owner property for every element. It passed correctness checks but made construction slower. The revised candidate tracks the initialized prefix locally and records it when the initializer exits, including thrown exits. This improved the focused comparisons. The first candidate's source, binaries and measurements remain archived as adverse evidence.

The experiment does not yet introduce capacity growth, a general snapshot interface, direct consumer packing, byte admission or asynchronous device scheduling. Those remain separate changes so their effects can be measured independently.

## Verification

The exact parent executable was rebuilt before edits. Its 401 core and 151 mutation scenarios passed. The final candidate passed:

- 473 core scenarios, including 72 added allocation/initialization scenarios.
- 151 mutation scenarios.
- 9 MLX device scenarios and the separate managed-owner finalizer probe.
- The 72 focused initialization scenarios under AddressSanitizer, without reported errors.

The added checks cover empty and invalid extents, arithmetic overflow before allocation, all-missing values across bitmap boundaries, CPU and shared Metal owners, independent clones, throws at several initialized-prefix positions, and the initialized dense-callback contract. Existing tests still require bitwise matrix agreement with the production control, correct numerical results, snapshot isolation and balanced owner release.

The finalizer ran exactly once, released its captured lease, and left zero live owner bytes. An initial attempt to run a copied device binary failed because the adjacent Metal library resources were absent. Running the identical binary hash at its normal build location passed. That launch failure was not an allocation defect; device reproduction must retain its runtime resources.

Builds used the existing Release runner and pinned dependencies. The focused sanitizer build used Apple Swift 6.4 on arm64 macOS 27. The sanitizer does not instrument GPU memory accesses. The full SwiftSci library suite and minimum-host qualification were not rerun. The previously identified MLX numerical regression remains outside this change.

## Measurements

Measurements used AC power, native thread settings, fresh processes and alternating parent/candidate execution order. Each process warmed once before measurement. The full-workflow comparison used the existing `keys-tile-borrowed-fit-4096` path across twelve shapes and key patterns for five rounds, giving 120 independently checked process measurements. The allocation comparison used three modes and three sizes for seven rounds, giving 126 checked process measurements.

The allocation experiment uses an optimized standalone build of the same storage source. Its medians are isolated construction or clone timings, not application speedups.

| Operation | Elements | Parent ms | Trial ms | Trial / parent |
| --- | ---: | ---: | ---: | ---: |
| dense | 1,000,000 | 1.7598 | 1.7162 | 0.975 |
| dense | 8,000,000 | 14.0721 | 13.7828 | 0.979 |
| nullable | 1,000,000 | 0.6952 | 0.5953 | 0.856 |
| nullable | 8,000,000 | 5.6059 | 4.9813 | 0.889 |
| clone | 1,000,000 | 0.1453 | 0.1100 | 0.757 |
| clone | 8,000,000 | 1.4242 | 1.0025 | 0.704 |

Large clones improved about 24-30%, and nullable construction improved about 11-14% in this isolated comparison. Dense construction differed by only about 2-3%; this does not establish a meaningful application improvement.

The complete numerical workflow was essentially unchanged. Construction-inclusive median ratios ranged from 0.979 to 1.020 across the twelve shapes. The generated-fixture construction stage still regressed by about 5-9% in several dense cases. Do not present the clone result as a whole-workflow speedup or ignore this remaining regression. Per-element callback and initialization overhead need further isolation before selecting a production builder.

No new reduction in physical memory footprint is claimed. Logical payload sizes and materialization counts are unchanged; the candidate targets redundant writes. Existing owner counters still omit allocator padding, Swift arrays and MLX caches.

## Decision and next experiments

Retain this commit as an experimental checkpoint. It demonstrates useful clone behavior and safe partial initialization, while preserving the construction tradeoff for review. It is not the default production storage implementation.

Next, define the retained numerical snapshot and preparation interface, keeping values, validity and row identities together. Compare a batched builder with the scalar initialization path, then test preparation directly into the consumer's layout. Preserve the existing arithmetic while changing memory movement. Capacity growth, device-completion ownership and byte budgets should each receive independent commits and comparisons.

The emerging memory kernel is an internal library module with a small interface for ownership, snapshots and preparation. Its implementation can specialize CPU and device storage. It should not require every caller to understand raw pointers, page alignment or foreign finalizers.

## Evidence archive

Raw results, executable fingerprints, comparison scripts, isolated source copies and sanitizer output are retained locally under `~/local-ai/spl/swiftsci/memory-kernel-trial-20261004/`.

- `baseline.build.json`, `candidate.build.json` and `device-candidate.build.json` identify the executables and complete source file hashes.
- `workflow-samples.json` and `workflow-summary.json` retain all full-workflow observations.
- `allocation-samples.json`, `allocation-summary.json` and `allocation-fingerprints.json` retain the isolated comparison.
- `first-candidate/` retains the slower implementation and its evidence.
- `candidate--*.json` and `initialization-asan.log` retain qualification outcomes.

The candidate was built before its Git commit. Its recorded file hashes were checked against the committed worktree before this report was recorded. Historical evidence has not been relabeled as a later implementation.
