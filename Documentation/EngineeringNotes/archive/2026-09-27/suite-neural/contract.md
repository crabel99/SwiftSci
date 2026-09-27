# Fixed decoder fixture v1

Operation decoder-fixed-f32. Exact input fields: operation, device, position, execution, loading, tokens, weights.
- device cpu|gpu. Swift explicitly scopes MLX device, no auto/fallback. Python comparator is NumPy CPU irrespective of Swift requested device; no timing ratio claim.
- position learned|rope, RoPEbase=10000 Float32, nontraditional split-half layout.
- execution full|cached. cached uses prefix length2 then one token at a time; tokens sequence length4 required. full permits sequence1..4.
- loading direct|public-loader. direct uses public Module.update actual flattened keys. public-loader calls TransformerDecoder.loadWeights with complete HF key mapping then verifies ALL actual parameters exactly match supplied Float32 weights. Do not repair production loader.
- tokens rectangular1..2 batch, each1..4 tokens, JSONinteger tokens in0..<7.
- weights exact mapping of keys to {shape:[Int],values:[Float32exactlyrepresentable finite JSON numbers]}. Each absolute value<=2. Bool not numbers. Shapes exactly declared below. No missing/extra weights.

Fixed config vocab7 hidden8 heads2 intermediate6 layers1 maxSeqLen8 rmsNormEps=0.0009765625 (2^-10).
Parameter keys/shapes:
embedding.weight [7,8]
posEmbedding.weight [8,8] (included/readback even RoPE unused)
finalNorm.weight [8]
lmHead.weight [7,8]
layers.0.norm1.weight [8]
layers.0.norm2.weight [8]
layers.0.attention.query_proj.weight [8,8]
layers.0.attention.key_proj.weight [8,8]
layers.0.attention.value_proj.weight [8,8]
layers.0.attention.out_proj.weight [8,8]
layers.0.ffn.gate.weight [6,8]
layers.0.ffn.up.weight [6,8]
layers.0.ffn.down.weight [8,6]

Forward math: embedding token + learned position if selected; norm1(x)=x/sqrt(mean(x²)+eps)*weight; q/k/v projections x @ W.T; split contiguous heads4; forrope rotate each halfpair at position p: firsthalf*cos(p/base^(2j/4))-secondhalf*sin(...), secondhalf*cos+firsthalf*sin. Causal scaled dot-product attention using scale 1/sqrt4=0.5. Mergeheads and outputprojection then residual. norm2, down(silu(gate(norm2))*up(norm2)) then residual. finalRMSNorm then independent lmHead (untied). No bias/dropout/training.

Output full: [batch,sequence,7] + all logits row-major. cached same followed by [3,2,3,4] (chunkcount and actual layer cache count after each step). Actual tensor shape and Float32 dtype required, reject any nonfinite output. Extract all Float values and convert toDouble only after evaluate/synchronize. Require actual parameter key set and values equal all supplied arrays after either loading path. Recreate model/cache per timed invocation, no hidden state leaks. Decode input outside timing; modelconstruction, materialize all suppliedweights, load/readback, tokenallocation, forward(s), eval, device-stream synchronization and complete output extraction inside timing. Diagnostic end-to-end conformance only.

Independent expected answers: scalar highprecision mpmath80digits using exact binary32 inputs and formula, serializedfloat64; atol2e-5,rtol2e-5 initial justified Float32 small bounded matrices, never adjusted to pass observed discrepancies without separate evidence. NumPy uses float32 arrays, vectorized backend, CPU comparator.

Initial fixture matrix direct bothdevices x bothpositions x bothexecution=8. Public-loader CPU/learned/full and GPU/rope/full additional2 diagnostic cases. Separate core profile8 and loaderprofile2 so known defects remain visible but don't silently disable passing CI coverage. Also zero-projection direct case? Parent decides and records.
