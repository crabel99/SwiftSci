# Arrow PR validation and submission

Date: 2026-10-06. [Draft PR #61](https://github.com/Nodibell/SwiftSci/pull/61) head: `c8e4629018f1cebcecfc018cd715701400c8ebdf`. Prerequisite [PR #60](https://github.com/Nodibell/SwiftSci/pull/60) head: `409e6ee545b88c22b83520845660c27ec584125d`.

## State

The isolated Arrow branch was pushed and PR #61 opened against upstream main. It contains two Arrow commits above PR #60. The Arrow-only diff changes three files: ArrowTableBridge.swift and the chunk/date32 regression files. Until #60 merges, the main-based PR diff also includes the prerequisite's six files. Merge #60 first, then reconcile the Arrow branch with the resulting main commit before final advancement.

PR #60's actual head passed benchmark conformance policy, Debug and Release builds, safe-mode unit tests, documentation checks, both CodeQL analyses and patch coverage. Pages deployment was skipped as expected. Its description was refreshed and it was marked ready for review. No PR was merged. PR #61 remains draft while its own hosted checks run.

## Exact-head validation

The full Release suite passed on the Arrow PR head: 1,156 test definitions passed, zero failed, two skipped. The two skips require the optional pinned tokenizer fixture; passing tests do not establish external-dataset coverage. Validation used a tracked-file snapshot, the pinned Swift/core fork, one test runner, two build jobs and precise Metal settings. The host was Apple M4 Max, macOS 27, Xcode 27 and Swift 6.4, with a macOS 14 deployment target.

The standards review found no violations of CONTRIBUTING.md or substantive code smells. The separate behavior review found no missing requirements, scope creep, or implementation faults against the accepted owned-import and signed-date32 specifications. Neither review substituted for the executable suite.

The working memory branch remains at `6e10f5833961d6813cc65b0491fe622c83c55a5d`, with no tracked changes. Memory experiments and engineering documents are absent from the PR diff.

## Benchmark attribution

The PR includes the earlier 42-worker comparison, with all outputs checked against a deterministic oracle. That comparison measured owned Arrow import, selection, gather and Double-matrix construction. It used official MLX Swift 0.32.3 on both sides. Only ArrowTableBridge.swift differed in production code. The current bridge matches the measured implementation byte for byte.

The original benchmark fingerprints remain unchanged: base `0d0de4bea8e892dc1abc32be7878160d7f777109`, patched head `cd6b8218b1adcebd0a43d0382270623e902a125e`, bridge SHA-256 `af067255f6eb8ca9a39b244306465e579babc1c20ba44106f95bbfdc7944eac4`. The current full-suite run is not a fresh performance measurement. The observed 3.78x one-million-row single-chunk and 17.04x 32-chunk speedups do not imply reduced owned-import allocation or whole-library speedups.

Local evidence: `/Users/crabel/local-ai/spl/swiftsci/arrow-pr-ready-20261006`. The earlier performance evidence remains in `/Users/crabel/local-ai/spl/swiftsci/arrow-import-mlx0323-final-20261006`.
