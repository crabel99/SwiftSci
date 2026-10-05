# Preserve invalid-context generation errors

Implementation commit: `aa5c71968c080f4188357c4cb628389f89ca00a2`.

SwiftSci now allocates zero positional-embedding rows for a nonpositive context limit. It retains the caller's original limit in `LLMConfig`. The existing generation validator returns `GenerationError.invalidContextLimit` before tokenization and inference.

This preserves the nonthrowing model initializer and the typed error behavior of `generate`, `generateStream` and `generateDetails`. Valid capacities follow the same allocation path as before. The correction does not make an invalid configuration usable for inference. Direct `forward` calls remain outside the throwing generation API's validation contract.

The existing `GenerationResultTests.invalidRequests(api:)` regression reproduced the MLX negative-shape crash before the fix. Its coverage now includes zero, minus one and `Int.min`, verifies the original configuration value, and requires no emitted output before an error. The existing oversized-prompt and negative-output-budget cases remain in the same test.

## Validation

| Configuration | Scope | Result |
| --- | --- | --- |
| Released mlx-swift 0.32.3, before the fix | Structured generation results | 13 test definitions passed; the invalid-request test crashed in MLX. |
| Released mlx-swift 0.32.3, after the fix | All SwiftLLM tests | 64 passed, two known GPU rotary precision failures, no skips. All generation tests passed. |
| Our fix plus the isolated MLX precision correction | Full Release suite | 1,028 passed, zero failures, two skips. Including parameterized cases, Xcode reports 1,247 passing executions. |

The two skipped tests belong to the opt-in pinned Llama tokenizer parity suite. No tests were newly disabled and no numerical tolerances changed.

The full passing result depends on the separate MLX correction identified in [the source diagnosis](2026-10-04-mlx-regression-source.md). The actual dependency pin still refers to the unmodified 0.32.3 release, so its two precision failures remain until that dependency correction is integrated. The diagnostic dependency copy is outside the repository and shared package cache.

The local evidence archive is `~/local-ai/spl/swiftsci/context-validation-fix-20261004/`. It retains before/after/combined logs, Xcode summaries, source hashes, commands and the tested patch. The source hash check confirmed that the committed production and test files match the validated files. This change remains local on `codex/unified-memory-prototype`; it was not pushed or submitted.
