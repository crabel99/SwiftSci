# MLX upgrade regressions traced to source

## Findings

The two GPU rotary accuracy failures have one cause in MLX core. Commit [`51bef6fc25934ebe96e17123a6d82781ec580226`](https://github.com/ml-explore/mlx/commit/51bef6fc25934ebe96e17123a6d82781ec580226), from PR #3728, replaced `setFastMathEnabled(false)` in runtime Metal compilation with `set_compile_options`. On the newer operating-system path, safe mode sets `MTL::MathModeSafe` but leaves `mathFloatingPointFunctions` at its fast default. The old API also selected precise functions. The replacement preserved arithmetic rules but changed the elementary function implementation.

The affected code is [`mlx/backend/metal/device.cpp`](https://github.com/ml-explore/mlx/blob/1f8e74e3f12f31365464a6867c6579f0e9b29d85/mlx/backend/metal/device.cpp#L37), in `set_compile_options`. The newer API path starts at macOS 15. Tests here ran on macOS 27 on Apple silicon; older hosts were not tested.

The separate negative-context crash is an integration defect exposed by stricter MLX validation. Commit [`11fa2c839723386361aade3ac33365200c137d28`](https://github.com/ml-explore/mlx/commit/11fa2c839723386361aade3ac33365200c137d28), from PR #4046, adds negative-dimension rejection to `mlx/random.cpp::bits`. That check correctly rejects an invalid array shape. SwiftSci constructs `posEmbedding` with `config.maxSeqLen` at `Sources/SwiftLLM/Core/TransformerDecoder.swift:368` before its generation API validates that context limit. The Swift MLX error handler turns the C error into a fatal error. Restoring acceptance of invalid shapes in MLX would be the wrong correction.

## Controlled evidence

The tested Swift package revisions were 0.31.6, `0bb916c67f4b9e5c682cbe02a42c701c93ab5021`, and 0.32.3, `19601207e9a0de51e03ee6ec0c3c5f3784275075`. Their MLX core revisions were `ce45c52505c8158ea48d2a54e8caae05efd86bfe` and `1f8e74e3f12f31365464a6867c6579f0e9b29d85`.

A diagnostic test containing only MLX operations reproduces the frequency error without SwiftSci. The exponent is identical on both versions and devices. The first different intermediate is GPU `pow(500000, 0.46875)`.

| Configuration | Float32 result | Float32 bits |
| --- | ---: | ---: |
| MLX 0.31.6 GPU | 469.2369384765625 | 1139449428 |
| MLX 0.32.3 GPU | 469.23675537109375 | 1139449422 |
| Both versions, CPU | 469.2369384765625 | 1139449428 |

The power error propagates through the frequency-scaling formula. At frequency index 15, the old result is `774.86474609375`; the upgraded result is `774.8638916015625`, 14 Float32 ULPs away. The unchanged test permits one ULP. Long-position rotations amplify the changed frequency, causing the second test failure.

A second reproducer uses Metal directly, without MLX. It compiles the same power kernel under Metal language versions 3.2, 4.0 and 4.1 with three option sets. All nine configurations completed successfully.

| Compiler options | Observed result in all three language versions |
| --- | --- |
| Legacy `fastMathEnabled = false` | Precise functions, matches the old MLX bits |
| `mathMode = safe` alone | Fast functions, matches the new MLX bits |
| Safe mode plus precise functions | Matches the old MLX bits |

The comparison covers three powers, with exponents 0.46875, 0.5 and 0.53125. It rules out the Metal-language upgrade for this failure. It does not claim exact rounding for every possible power input.

## Diagnostic correction

An isolated copy of MLX 0.32.3 adds one line to the safe-mode case:

```cpp
mtl_options->setMathMode(MTL::MathModeSafe);
mtl_options->setMathFloatingPointFunctions(MTL::MathFloatingPointFunctionsPrecise);
```

All six original `LlamaRotaryScalingTests` passed, with 11 test-case executions when parameters are counted, no skips and no failures. This includes both previously failing GPU tests. Production test sources and numerical tolerances remained unchanged. The correction preserves precise functions for safe mode and leaves the explicit relaxed and fast cases unchanged.

The standalone negative-shape reproducer constructs `MLXRandom.normal([-1, 8])`. Version 0.31.6 returns an unevaluated array with that invalid shape; 0.32.3 fails immediately with `[bits] Negative dimensions not allowed`. This demonstrates the validation timing change without a transformer or tokenizer. The original construction crash still needs a SwiftSci correction.

The ordinary SwiftSci checkout, its dependency pin and the shared package cache were not modified by this investigation. The one-line correction exists only in the diagnostic copy. The prior upgrade commit remains experimental. No full-suite success or production readiness is claimed, and nothing was submitted upstream.

## Evidence and next work

The local evidence archive is `~/local-ai/spl/swiftsci/mlx-regression-20261004/`. It contains the MLX-only reproducer, the standalone Metal program and nine results, old/new test logs, source commit diffs, the diagnostic correction, and the corrected rotary-suite log, summary and build provenance. These local reproduction scripts use the existing machine's build paths.

Next, qualify the MLX correction with an upstream regression test for runtime compilation precision. Separately, make SwiftSci reject invalid context settings before constructing an invalid positional embedding, while preserving its public error contract. Then repeat the full Release suite. Changing numerical tolerances or disabling MLX's shape validation is not part of either correction.
