# Newly exposed failures for the later repair branch

Do not fix these on the testing/certification branch. Keep one commit per error when repairs begin.

## Decoder public weight loading

Both CPU and GPU loader cases fail exact parameter readback at `layers.0.attention.key_proj.weight`. The loader reports no missing inputs. Direct public Module.update accepts and verifies the complete supplied parameter set. Source inspection shows the loader uses Swift property spellings where pinned MLXNN registers explicit projection keys.

Acceptance after repair: both public-loader cases pass complete parameter readback and independent logits; missing or malformed checkpoint inputs remain detectable. Keep direct-parameter cases to distinguish loader regressions from inference arithmetic.

## Batched single-token RoPE on GPU

Two-batch cached RoPE fails against independent logits in three fresh worker repetitions. Each individual batch passes on GPU; two batches pass for CPU cached execution and GPU full-sequence execution. The failure is substantially larger than Float32 roundoff.

The pinned MLX Metal source omits the batch factor from its contiguous single-token dispatch. The exact source evidence is in gpu-rope-source-review.md. This is the leading cause, supported by the runtime controls; no dependency fix or upgrade was attempted.

Acceptance after repair: the existing two-batch GPU cached-RoPE case passes without weakened tolerances, along with both individual batches, full-sequence CPU/GPU and learned-position controls. A direct RoPE kernel test should localize the repair before integration.

## Source-review concern, not reproduced here

The decoder's populated-cache multi-token continuation constructs a sequence-square causal mask while total keys include the prefix. This profile only covers a two-token prefix followed by single-token steps. Add an isolated contract and runtime reproduction before treating the concern as a confirmed error.
