# MLX compatibility and memory integration

Date: 2026-10-06. [PR #60](https://github.com/Nodibell/SwiftSci/pull/60) head: `409e6ee545b88c22b83520845660c27ec584125d`. Working memory head: `6e10f5833961d6813cc65b0491fe622c83c55a5d`.

The three compatibility failures reported in the [pinned backport record](2026-10-06-mlx-simd-backport.md) are resolved. The PR keeps the pinned MLX Swift/core fork and adds two separate correction commits. It changes six files and contains no memory-kernel or Arrow implementation changes.

## Corrections and evidence

`7a046416d0259c7c454d96d60eb36c0c8bb223e9` carries forward the existing invalid-context correction. Model construction uses an empty positional embedding for nonpositive context limits, while preserving the original configured limit. All three generation APIs return the typed request error without emitting output, including for Int.min.

`409e6ee545b88c22b83520845660c27ec584125d` computes cached Llama scaling frequencies with the CPU backend. A stage-by-stage probe isolated GPU power rounding. At frequency 15, the CPU power was 469.23694 and the GPU power was 469.23676; the final denominators were 774.86475 and 774.8639. Feeding the CPU power value into the subsequent GPU arithmetic recovered 774.86475. This difference exceeded the existing long-position phase budget. Computing the small constant table on the CPU removes the initialization-device dependence while retaining the checkpoint Float32 arithmetic. MLX rotation and inference stay on the caller's device. No numerical tolerance changed.

The new regression checks bitwise initialization parity over two head dimensions, two bases, and four scaling configurations. It failed before the correction. Existing checkpoint, Double-oracle, dtype, cached-decoding, and standard-RoPE tests pass after the correction. Temporary instrumentation exists only in the recorded diagnostic logs, not in committed source.

| Validation | Result |
| --- | --- |
| Original focused suite | 17 passed, 3 failed |
| Corrected focused suite with new regression | 21 passed, 0 failed, 0 skipped |
| Full Release on the exact PR head | 1,148 passed, 0 failed, 2 skipped |
| Full Release on the integrated memory head | 1,058 passed, 0 failed, 2 skipped |
| Managed-buffer ownership probe on the pinned fork | One finalizer call, one allocation and release, no retained lease, zero live owner bytes |
| Device ownership and donation checks | Passed |
| End-to-end integration | 44 workflows and 8 additional checks passed |
| Prepared-data integration | 44 workflows and 5 additional checks passed |

Test counts are definitions, including parameterized tests. The two skips require the optional pinned tokenizer fixture. These results do not establish external-dataset coverage or broad numerical certification. The suites overlap and their counts must not be added together. The host was Apple M4 Max, macOS 27, Xcode 27 and Swift 6.4, using a macOS 14 deployment target and precise Metal settings.

## Integration state

The working `codex/arrow-chunk-import` branch was fast-forwarded from `32badeece6728e9b75054b2f997459c377dfb69e` to the tested memory head. Its existing memory and Arrow work is preserved. The package manifest retains its prototype targets and now resolves the pinned fork. The separate, unpushed Arrow compatibility branch was restacked above the corrected PR head; its scope remains two Arrow commits and three files. It has no new standalone full-suite claim at that restacked head.

PR #60 was pushed and its description now reports the passing local suite. Hosted Debug and Release builds passed; other hosted checks were still running when this record was written. Hosted safe-mode tests exclude SwiftLLM, so they cannot substitute for the local MLX tests. The PR remains draft pending those checks. No PR was merged and no maintainer comment was sent.

The shared build directory now contains freshly built memory executables for the corrected dependency. Their fingerprints and exact commands are in worker-checks.json. The older named comparison executable remains preserved; do not relabel historical benchmark results with the new head.

Local evidence: `/Users/crabel/local-ai/spl/swiftsci/mlx-compatibility-20261006`. Reports, logs, full result bundles, worker outputs, and branch fingerprints are retained there. Engineering records stay on codex/engineering-notes.
