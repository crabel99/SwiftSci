# Fixed neural inference conformance checkpoint

Local contribution commit `f8cec1f93ba075892338aef063a7b8d2a101f63d` adds a bounded fixed-weight decoder suite on `codex/standardized-benchmarks`. The contribution branch remains unpushed. No production implementation changed.

The suite covers explicit CPU and GPU execution, learned and rotary positions, full and incremental cached logits, an analytic zero-projection control, exact parameter readback and single-batch controls. Fourteen original MIT fixture packs use a separately implemented 80-digit scalar oracle. Source locks bind the generator, oracle and requirements. All logits are compared, with fixed Float32 tolerances. See the public fixture contract at `Benchmarks/Fixtures/neural/README.md`.

## Verified results

- All 105 controller tests passed and the Release worker built successfully.
- Direct neural profile: 23 of 24 engine cases passed, with 46 validated samples. Swift GPU batched cached RoPE failed against the independent answer.
- Public-loader diagnostic: both NumPy cases passed; both Swift cases failed exact parameter readback before inference.
- CPU CI profile: all 10 engine cases and 20 samples passed, including the certificate audit. The workflow now runs this profile.
- Existing smoke profile: all 28 engine cases passed, including the certificate audit.
- Actual worker rejection tests: eight unchanged controls and eight causal future-token variants passed. All 56 intentionally incorrect inputs or expected outputs were rejected.
- All 346 build-record source hashes match the committed source. The tested binary SHA-256 is `91368edf6493f6c385781d153245c6f86aa028ba8d70bf2a5acabacf86e25274`. Its source tree fingerprint is `b1d6e48e772464374cc81657986402c6f5861828ce188cc60e24c20e0937b884`.

The failed profiles have hash-valid failed certificates. The strict audit rejects them because it only accepts passing certificates. This is expected and does not imply a valid passing neural certificate.

## Production repair queue

The public loader uses parameter destinations that differ from the pinned MLX attention module's actual names. Readback consistently finds `layers.0.attention.key_proj.weight` unchanged. The direct complete parameter-update path passes readback.

The GPU cached RoPE failure occurs with two batches. Each batch separately, CPU cached execution and GPU full execution pass three repeated isolation runs. In the pinned Release dependency `mlx-swift` revision `0bb916c67f4b9e5c682cbe02a42c701c93ab5021`, the specialized Metal single-token dispatch appears to omit the batch factor. This is the leading source-level explanation, not a tested repair. Source hashes and exact locations are retained in the archive.

Keep these as separate repair units after the testing suite is built. A possible populated-cache multi-token mask concern is only a source observation; this increment neither exercises nor confirms it.

## Evidence corrections and limits

The first final orchestration attempt, `suite-neural-02`, stopped because newly added single-batch fixtures had not been prepared. Its exit status alone was insufficient evidence. It produced no run directory and is excluded from all result counts. Preparing the complete profile and running `suite-neural-03` resolved the setup omission. `summarize.py` verifies exact event sets, raw failure responses, successful sample counts, certificate checksums and audit outcomes.

The new source-tamper controller test initially encountered macOS temporary-directory symlink spelling. Resolving the temporary path corrected the test setup; the final controller log records all 105 tests passing.

This is small fixed inference coverage, not pretrained-model quality, training correctness, long-context certification or a performance baseline. NumPy remains a CPU mathematical comparator even for cases requesting Swift GPU execution. Hosted CI has been configured but not executed here. Broader integration and remaining AI operations still need contracts and fixtures before the repair phase and formal performance baseline.

Independent review found and resolved missing CPU CI wiring and incomplete oracle provenance. The reviewer inspected artifacts, not the complete session transcript. Reviewed by GPT-6. The decision trail, review and raw evidence remain solely on `codex/engineering-notes`.
