# Fixed neural inference API review

Read-only review of the current SwiftSci checkout and pinned MLX sources. No build or model execution was performed. Findings below distinguish source-supported contracts from suspected failures.

## Recommended bounded pack

1. **SwiftLLM SwiGLUFFN**: a `[1, 2, 2]` input, intermediate dimension 3, explicitly supplied gate/up/down matrices, mixed positive and negative inputs, zero row and asymmetric matrices. Public `SwiGLUFFN(config:)`, `callAsFunction`, and inherited `Module.update(parameters:verify:)` suffice. Independent scalar oracle: gate and up are `x @ W.T`, SiLU is `g/(1+exp(-g))`, componentwise multiply by up, then down projection. Check every output, Float32 dtype and dimensions. No model download or training.
2. **SwiftVision CLIPProjector**: visual dimensions 3, text dimensions 2, projection dimensions 2, separate nonidentity weight matrices and temperature 0.5. Include zero projected vector, opposite vectors, and a small vector where additive epsilon matters. Check both projected embeddings, the entire similarity matrix, and every softmax probability. Independent formula uses `sqrt(sum(z*z)+1e-12)`, not a hard maximum norm. These are supplied feature vectors, not images or an image encoder. Do not describe this as end-to-end vision accuracy.
3. **SwiftVision UNetOutConv**: asymmetric NHWC image `[1, 2, 3, 2]`, two output channels, supplied 1x1 kernel and nonzero bias. Independent scalar per-pixel affine map. Provides real public image-tensor API and catches NHWC/channel ordering without adding BatchNorm or large image fixtures. Kernel MLX layout is `[out_channels, kernel_height, kernel_width, in_channels]`; confirm against pinned Conv2d before implementing.
4. **SwiftLLM zero-layer learned-position decoder**: vocabulary 5, hidden 4, max sequence 6, batch 2, explicitly supplied token and position embeddings, nonuniform RMSNorm weight and LM head. Public `TransformerDecoder(config:tokenizer:)`, `loadWeights`, `forward`. Check every logit and an offset case. This covers lookup, positions, normalization and output projection, but must be labeled zero-layer: it does not validate attention or FFN.
5. **One-layer decoder direct parameters**: hidden 4, heads 2, intermediate 3, vocabulary 5, token sequence 3, both learned and RoPE if time permits. Full scalar attention/RMSNorm/SwiGLU oracle. Set every parameter, including unused positional embedding, via verified actual Module parameter keys. Full forward plus incremental single-token decode, checking each prefix against independent expected logits and cache count. Only proceed if complete parameter coverage is enforced. Keep HF-style loadWeights conformance separate because of the mismatch described below.

The first three are enough for a bounded initial increment. The decoder cases are valuable but require a larger independent oracle. Do not use randomized weights or compare two paths of the same implementation as the sole expected answer.

## Public API and execution facts

- Sources/SwiftLLM/Core/TransformerDecoder.swift exposes public submodules on SwiGLUFFN, TransformerBlock and TransformerDecoder. Layers derive from MLXNN.Module and parameters can be updated through its public API.
- `LLMConfig` performs assignment without dimension validation. Fixture boundary must validate positive dimensions, `hiddenDim % numHeads == 0`, even RoPE head dimensions, token bounds, position bounds, layer/cache count and all tensor sizes before entering MLX.
- TransformerDecoder.forward accepts tokens `[seq]` or `[batch, seq]`, returns `[batch, seq, vocab]`; learned positions use `offset..<offset+seqLen`. A minimal BPETokenizer can satisfy construction, but token-ID fixtures need not invoke tokenization.
- Attention projections and SwiGLU have no bias by default. Final norm is RMSNorm with Float epsilon; the model's LM head is separate from its embedding even though its doc comment claims tied-by-default.
- `RoPEEmbedding` delegates to MLXNN.RoPE. Default `traditional=false` pairs first and second half of the head, not interleaved adjacent components. An independent oracle must honor that choice and base/offset.
- Model parameters/input explicitly created from Float yield Float32 computations. Inspect output.dtype and full shape before conversion; converting blindly to Float can hide the wrong dtype. Int token buffers should use an explicit integer type.
- These classes have no SwiftSci `ComputeDevice` argument or `resolvedDevice`. They route through MLX defaults. Pinned MLX exposes synchronous and async `Device.withDefaultDevice(.cpu/.gpu)`. Scope construction, updates, forward, eval and conversion within the chosen device context. Record the requested route accurately rather than claiming a per-array device inspection occurred.
- MLX arrays are lazy. Evaluate and copy outputs with `eval(output)` and `asArray(Float.self)` before ending the measured region. Conformance operation construction/weights/host materialization can remain in the measured workload if explicitly described; these timings are not inference latency baselines.
- `Module.train(false)` recursively selects inference behavior. Use it even for layers without dropout. BatchNorm layers default to training, which otherwise changes statistics and state between samples.
- Recreate models and KV caches for each sample. The caches mutate and retain earlier keys/values.
- Benchmark worker currently depends on SwiftVision but not SwiftLLM; add direct SwiftLLM dependency for decoder/FFN cases. Adding direct MLX and MLXNN dependencies is clearer than relying on transitive import visibility.

## Suspected defects to preserve, not repair

### TransformerDecoder HF weight loader attention names

`TransformerDecoder.loadWeights` maps supplied attention weights to paths such as `layers.0.attention.queryProjection.weight`. Pinned MLXNN.MultiHeadAttention declares `@ModuleInfo(key: "query_proj") public var queryProjection`, with analogous `key_proj`, `value_proj`, `out_proj`. Its actual parameter tree therefore uses these explicit keys. SwiftSci calls the nonthrowing Module.update overload, which uses `verify: .none`.

This suggests attention weights can remain at random initialization despite an empty missing-key report. Verify using public parameter readback after loading a supplied dictionary. A correct suite should fail the loader case if values differ; it must not silently substitute direct parameters and label the loader good. Direct-parameter inference is a separate supported inherited API test.

### Cached multi-token decode mask

TransformerDecoder creates a causal mask of `[newSeqLen, newSeqLen]` whenever a call has more than one new token. Cache accumulation increases key length. The resulting mask does not visibly add the existing-prefix width, so a second multi-token chunk can have incompatible mask/key shapes. Existing tests cover a multi-token initial prefill followed by single-token decode, not this case. Avoid in-process crash risk until isolated request behavior is arranged; keep it on the unresolved coverage list.

### Other limits

- Documentation claims LM-head weight tying, but the constructor creates a separate Linear and does not tie its weight. Do not assert tying in the fixture contract.
- Positional embedding load is optional even for learned-position models. Supply and verify it explicitly.
- Full YOLO/UNet numerical fixtures would need all convolution and BatchNorm state, image padding/resize semantics, prediction decoding, and meaningful expected outputs. Existing tests are mainly shape/property checks; that is not independent numerical certification.
- UNetUp currently repeats pixels for 2x nearest-neighbor expansion despite a comment mentioning bilinear; do not write an oracle against bilinear assumptions.
- CPU and GPU use different kernels. Float32 tolerance should be justified by small bounded arithmetic and cross-device observations, not tuned to a single observed wrong answer. Frozen oracle math should not import SwiftSci or MLX.

## Verification suggestions

- Reject unknown/missing weight names, wrong shapes, nonfinite data, invalid temperatures, invalid token IDs and unsupported devices before loading.
- A wrong transposed matrix, omitted bias, changed token, wrong position offset, removed normalization epsilon and permuted channel should each cause actual-worker conformance failure.
- Use non-square matrices and multiple distinct token/image rows so output order, transposition and broadcasting errors are observable.
- Preserve exact supplied fixture hashes; assert all model parameters equal supplied Float32 values before timed forward, especially loader cases.
- Check every element, not just norm/probability sum/argmax. Add batch shape and dtype to serialized conformance output or assert them at the worker boundary.

## Decoder pack agreed for implementation

Use hidden dimension 8, 2 heads (head dimension 4), intermediate 6, vocabulary 7, one layer, sequence 4, batch 2. Head dimension 4 exercises both RoPE frequencies, unlike dimension 2. Suggested cases: learned positions full forward, learned positions offset, RoPE full forward, RoPE initial prefill then one-token increments, and a separate public HF-style loader readback case. Nonzero asymmetric small rational weights prevent all-zero shortcuts; use nonuniform norm weights and two distinct token rows.

Source-derived direct parameter paths (verify against `model.parameters().flattened()` at runtime; this review did not execute MLX):

| Path | Shape |
|---|---|
| `embedding.weight` | `[7, 8]` |
| `posEmbedding.weight` | `[maxSeqLen, 8]` |
| `layers.0.norm1.weight` | `[8]` |
| `layers.0.attention.query_proj.weight` | `[8, 8]` |
| `layers.0.attention.key_proj.weight` | `[8, 8]` |
| `layers.0.attention.value_proj.weight` | `[8, 8]` |
| `layers.0.attention.out_proj.weight` | `[8, 8]` |
| `layers.0.norm2.weight` | `[8]` |
| `layers.0.ffn.gate.weight` | `[6, 8]` |
| `layers.0.ffn.up.weight` | `[6, 8]` |
| `layers.0.ffn.down.weight` | `[8, 6]` |
| `finalNorm.weight` | `[8]` |
| `lmHead.weight` | `[7, 8]` |

RoPE has configuration but no trainable parameters. Neither attention nor SwiGLU has bias here. `posEmbedding.weight` exists even in RoPE mode and should be explicitly supplied to make exact parameter coverage deterministic. Use throwing `try model.update(parameters: NestedDictionary.unflattened(weights), verify: [.noUnusedKeys, .allModelKeysSet, .shapeMismatch])`. Then independently verify flattened key set, shape, dtype, and exact Float32 readback. The constructor's randomized values must never survive a direct-parameter fixture.

For HF-style loader conformance, construct a fresh decoder, supply all equivalent external keys, call `loadWeights`, and require empty missing list plus exact actual-path readback against the fixture. If it fails, emit a readable failed case before running inference; do not allow uncontrolled random initialization into measured samples. Supplying deterministic sentinel parameter values first can make the failure repeatable while retaining the same loader test, but the sentinel strategy must be explicitly described and distinct from a successful replacement.

### Completion and stream APIs

Pinned MLX `Device.withDefaultDevice(_:_:)` is task-local and supports synchronous bodies. `Stream.withNewDefaultStream(device:_:)` is also public and sets the operation stream within the scope; a default-stream task override can otherwise take precedence over the chosen Device. New worker processes should have no inherited task override. `eval(array)` evaluates the graph; `array.asArray(Float.self)` materializes host values. `Stream.defaultStream(device).synchronize()` is public if using that stream; do not synchronize an unrelated stream and assume completion. Materializing every output within the selected scope is sufficient for the fixture to await its own output before returning.

The one-token incremental case should compare every returned timestep for both batch rows against the independent full-prefix oracle. Prefill length 2 followed by singleton tokens reaches sequence 4. Validate offset equals existing cache length. Add a separate isolated multi-token continuation (prefill 2, then 2) only if process-crash results are preserved as failures: the mask source shape appears wrong after the prefix and may trigger an MLX assertion rather than a Swift error.
