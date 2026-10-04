# MLX 0.32.3 upgrade qualification

## Decision

Prototype commit: `a8401be9d8a6ed3e9b810f565a625ad457a5bfdf` on `codex/unified-memory-prototype`.

Keep the MLX 0.32.3 upgrade on the local unified-memory prototype branch. The Swift managed-buffer initializer passes ownership qualification and replaces the direct C adapter in this experiment. Broader adoption is blocked by three reproducible SwiftLLM test failures introduced by the dependency upgrade. No production algorithm or numerical tolerance changed.

The [finalizer fix](https://github.com/ml-explore/mlx-swift/pull/448) first shipped in [0.32.2](https://github.com/ml-explore/mlx-swift/releases/tag/0.32.2). This experiment pins [0.32.3](https://github.com/ml-explore/mlx-swift/releases/tag/0.32.3), revision `19601207e9a0de51e03ee6ec0c3c5f3784275075`. No other resolved dependency changed.

## Ownership and device results

The original managed-import reproducer now passes. Its callback runs exactly once, the captured lease becomes nil, live owner bytes reach zero, and allocation and release counts balance.

- 401 CPU ownership, selection, arithmetic and workflow scenarios passed.
- 151 mutation scenarios passed.
- Nine device scenarios passed, including abandoned lazy graphs, rejected null imports, alignment rejection and the copying fallback.
- The independent finalizer regression passed.
- All 90 measured device processes passed. Five rounds cover three import modes, three sizes, and submitted reads with and without a concurrent host edit.

The managed modes now use `MLXArray(rawPointer:_:dtype:finalizer:)`. The finalizer retains the lease until MLX releases the imported data. Checks require input pointer identity, output sharing with Metal, snapshot isolation, correct Float32 results and final owner release. The earlier direct C adapter and its measurements remain available in the previous commit and archived experiment. New mode names distinguish the Swift wrapper from those historical measurements.

These checks qualify the restricted prototype ownership path. They do not establish an application performance improvement or qualify independent concurrent writers and cancellation of running GPU work.

## Full-library compatibility

The full Release suite reported 1,025 passing test definitions, three failures and two skips, out of 1,030. Dynamic parameter cases have separate execution counts in the Xcode result. This is a failed suite.

| Test | Result with 0.32.3 |
| --- | --- |
| `GenerationResultTests.invalidRequests(api:)` | A negative context limit reaches an embedding allocation. MLX traps with `[bits] Negative dimensions not allowed` before SwiftSci returns its intended request error. |
| `LlamaRotaryScalingTests.transitionFrequencies(gpu:)` | The GPU result for frequency 15 is `774.8639`, compared with reference `774.86475`. Absolute error is `0.0008544922`; the existing one-ULP allowance is `0.00006103515625`. |
| `LlamaRotaryScalingTests.rotationOracle(dimensions:gpu:)` | GPU rotations exceed the existing error budget. One case at dimension 64 and offset 131069 reports an error-to-budget ratio of `1.5823296156926971`. |

A focused rerun of these two suites reproduced all three failures. The same 20 test definitions passed with MLX 0.31.6, with 38 test-case executions when parameterized cases are counted. The comparison snapshots differ only in `Package.swift` and `Package.resolved`. Both builds use the same Release configuration, host, test sources and numerical tolerances. The failing GPU checks pass on the CPU in the upgraded build.

The negative-dimension crash has an identified construction path. The underlying cause of the GPU numerical differences remains unresolved; the comparison establishes a dependency-related regression, not which internal arithmetic change caused it. Tests were not disabled and tolerances were not relaxed.

## Reproduction and evidence

The local archive is `~/local-ai/spl/swiftsci/mlx-0323-upgrade-20261004/`.

- `device/` contains source and binary fingerprints, the finalizer result, device checks, 90 raw measurements and summaries.
- `cpu-checks.json` records the rebuilt worker hash and the two check commands.
- `release-suite/` contains the full build/test log, source provenance and Xcode summary.
- `focused-new/` and `focused-old/` contain the controlled comparison logs, commands and summaries.
- `candidate.patch` preserves the tested change before commit.
- The local test scripts retain the build and focused-run commands. Their paths describe this machine's experiment and are not portable public tooling.

Builds use tracked-source snapshots outside cloud sync. Validation ran on Apple silicon with a macOS 14 deployment target, macOS 27 host and Xcode's macOS 27 SDK. The Metal build flags were `MTL_FAST_MATH=NO`, `MTL_MATH_MODE=SAFE`, and `MTL_MATH_FP32_FUNCTIONS=PRECISE`. These flags alone do not prove the settings of every runtime-compiled dependency kernel. Older host operating systems were not exercised.

## Follow-up boundary

Before adopting this dependency for the library, preserve typed invalid-context errors without creating invalid MLX arrays, isolate the GPU rotary-frequency arithmetic change, and rerun the unchanged full suite. Any production correction should have its own regression test and commit. The successful buffer-release result remains valid independently of that unfinished compatibility work.
