# GPU cached RoPE source diagnosis

Read-only investigation. No adapter, production, or dependency changes. No diagnostic runtime was executed by this reviewer; parent owns repeat and batch-size experiments.

## Evidence

The actual Release dependency checkout is `/Users/crabel/Library/Caches/SwiftSci/xcode-packages/checkouts/mlx-swift`, revision `0bb916c67f4b9e5c682cbe02a42c701c93ab5021` (reported package version 0.31.6). Its working tree is clean.

Source SHA-256:

- `Source/Cmlx/mlx/mlx/backend/metal/rope.cpp`: `c1d6d4952df627eb1a5a5b9faf0c32a4328d3032c4941ea82933d648e2592afd`
- `Source/Cmlx/mlx/mlx/backend/metal/kernels/rope.metal`: `2b35221ebea033ff43100b85eaaddec5c0e34e3cfd52e7c692573764b2b7d0ab`
- `Source/Cmlx/mlx/mlx/fast.cpp`: `fa9c12db58e5aee9cff7ed02c155413be22701bdb3987e25a664f2607ffe318e`

The recorded Release response `Benchmarks/Runs/suite-neural-01/neural-gpu-rope-cached-swiftsci-0.response.json` fails with actual `-0.024063661694526672`, expected `0.0425054856361493`. This review was told other direct decoder cases pass, including CPU cached RoPE and GPU full RoPE.

## Narrow leading hypothesis: batch dimension omitted from GPU single-token RoPE dispatch

`backend/metal/rope.cpp` lines 28–41 computes `B = input.shape(0)` and `N = product(shape[1 .. ndim-2])`. For decoder Q/K `[batch=2, heads=2, sequence=1, headDimension=4]`, this means B=2, N=2.

Line 96 selects the specialized single-token kernel when input is row-contiguous, T=1 and offset is scalar. Singleton sequence/head transpose can retain row-contiguity.

Lines 133–137 launch this path with `grid_dims = (dims/2, N, 1)`. B is absent. The generic branch at lines 147–151 explicitly includes B in its dispatch instead.

`kernels/rope.metal` lines 28–51 index by `pos.y * stride` and write just those positions. With dim0=2, N=2 and stride=4, only eight Float32 elements are written, but the input has sixteen. Batch 2 is not visited. If the output buffer is donated, batch 2 can retain unrotated values; if separately allocated, its values can be stale or uninitialized. This is consistent with a large numerical error rather than Float32 roundoff.

`fast.cpp` lines 519–528 passes original input dimensions directly to the GPU primitive. Reshaping inside its fallback lambda applies only to fallback computation; it does not flatten batch/head for GPU. `MLXFast.swift`'s actual RoPE implementation passes `array.ctx` directly. Its documentation contains an illustrative reshape snippet, but that is not executed. MLXNN.RoPE and SwiftLLM.RoPEEmbedding also forward the four-dimensional input directly.

This source defect is strongly consistent with batch 1 passing and batch 2 failing only on GPU singleton decode. Parent's batch-size and repeat checks are still needed to link the executed path to this source hypothesis. A future isolated direct RoPE fixture `[2,2,1,4]` with distinct finite values and scalar nonzero offset would localize it without the decoder; fixing the dependency is outside this suite branch.

## Adapter sequencing review

The adapter uses a fresh model/cache, token chunks `[0,1]`, `[2]`, `[3]`, offsets 0,2,3, one layer cache, and concatenates outputs on sequence axis. Token creation preserves batch-major ordering. Every chunk is evaluated before the next forward call. The final output is evaluated and its active stream synchronized before host materialization. All parameter arrays were exactly read back before forward. The adapter never rewrites cache tensors in place; the public KVCache replaces them with concatenated arrays while earlier graph references remain owned by MLX.

No obvious adapter ordering, device selection, missing synchronization, or row-order error was found. The same adapter succeeding for CPU cached RoPE and GPU cached learned positions supports the more specific RoPE dispatch hypothesis. This is not a proof that every stream path is flawless; it is a narrower source-supported explanation of this failure.

## Separate issue

The decoder's multi-token continuation mask concern is unrelated to this observed case. The adapter always decodes single tokens after prefill, so it does not invoke the suspected prefix-width mask mismatch.

## Runtime follow-up

The parent ran three fresh requests for each of five variants. Two-batch GPU cached RoPE failed all three. Each individual batch passed all three GPU cached runs; two-batch CPU cached and GPU full-sequence variants also passed all three. The first mismatching output is flattened index 45, batch index 1, token index 2, vocabulary column 0. This is the first singleton decode output in the second batch, consistent with the omitted batch dimension. These results strengthen the source hypothesis without applying a repair.
