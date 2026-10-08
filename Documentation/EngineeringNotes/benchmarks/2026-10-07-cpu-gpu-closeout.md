# CPU/GPU memory optimization closeout

Date: 2026-10-07

## Decision and scope

The local contribution branch `codex/cpu-gpu-optimization-closeout` is at `22c6b8908b18c967295f08a5effa69265c7fa4ef`. Implementation commit `e29002e7d0` contains 20 files, with 1,105 insertions and 126 deletions. It follows prepared-memory PR #62 at `2cd1cbe52a`. The upstream #60 merge was reconciled without changing the tested tree. This branch still depends on the prepared-memory contribution.

Keep the measured trial at `5fa86f9f7597681561a82b42787525061c1d35f5` on `codex/retained-memory-accounting-trial`. The primary checkout is unchanged. No branch was pushed and no PR was opened during this closeout.

The contribution includes consuming standard/min-max scaling, native prepared imputation, native pipeline composition, ownership transfer through regression preprocessing, fixed 16-by-16 GPU packing, and default Metal device reuse. Public documentation explains snapshot preservation, Float32 range loss, copying fallback, estimated admission, and completion versus cancellation.

Retained model/input owner trials, reservation transfer, alternative packing strategies, padded imports and experimental executables remain on the trial branch. Their callers are experiments and tests. In particular, the retained prediction adapter always executes Float32 GPU prediction, including for a CPU-fitted model. It needs an explicit device/precision contract before promotion. This boundary preserves the experiments without exposing them as supported production behavior. Core ML and further cache/working-set experiments remain separate milestones in [fork issue #2](https://github.com/crabel99/SwiftSci/issues/2).

## Validation

- Full Release: 1208 tests passed, no failures, 2 optional skips.
- Full Debug: 1208 tests passed, no failures, 2 optional skips.
- Benchmark controller suite: 160 tests passed in the existing reference environment.
- Numerical regression policy: all 15 profiles completed; 196/196 Swift and 192/196 Python cases passed. Four reviewed Python Wampler accuracy failures remain failed conformance. No tolerance or failure inventory changed.
- Public scientific and persisted-model workflow controls: 100 passed, including rejection of incorrect/truncated answers and malformed inputs.
- Documentation checker passed at 98.61% measured public coverage. This is not a claim of literal 100% coverage despite the checker's generic success banner.
- Independent behavior and standards reviews found no remaining actionable extraction issues.

The initial controller invocation used system Python without the reference packages; the final run uses the existing project environment. The first Debug launch crashed inside Xcode's invalidated-package-object handling. A fresh build-for-testing manifest and test-without-building run passed. Neither event required a production code change.

## Final public-workflow comparison

The reference is the preserved measured trial executable, SHA-256 `fa97a6195dd9cd150435938826a3204fc90771faaa6caa9cae7ed5aa22952211`. The candidate uses the extracted production code and a temporary public-only qualification launcher. The pipeline-service implementation and imputed preparation are copied unchanged from the trial; unrelated trial entry points and helpers are removed. Source, manifest and build commands are archived. The temporary launcher is absent from the contribution.

Both executables are checked for absent coverage instrumentation. A preliminary build failed that preflight; no timings from it were accepted. The final candidate was rebuilt through the coverage-disabled test action.

Three paired rounds cover small, medium, large and mixed request sizes, with retained and consumed input ownership. Binary order alternates, and case order reverses. All 48 workers and 299,520 requests passed the unchanged analytical bound, complete prediction and fitted-parameter comparisons, window ownership checks, reservation drains and final MLX cleanup checks. Memory samples remain subject to the unchanged 2 GiB bound. These are bounded lifecycle observations, not proof that every framework or driver allocation is reclaimed.

Median paired throughput changes relative to the measured trial:

| Workload | Retained input | Consumed input |
| --- | ---: | ---: |
| small | -0.7% | +1.0% |
| medium | -0.6% | -1.4% |
| large | -0.6% | -0.1% |
| mixed | -1.4% | +0.9% |

Median throughput differences ranged from -1.44% to +1.03%. Eight additional integrity workers completed 64 requests, including 32 full retained-source checks and consumed-buffer reuse checks.

The comparison tests whether extraction preserves the measured workflow. It is not a new baseline against Python, an estimate of the entire optimization gain, or a statistical noninferiority certificate. Three pairs do not characterize all host scheduling noise. Historical device-reuse gains remain attached to their original source and executable fingerprints.

The measured request window includes admission, fixture/oracle creation, preprocessing, GPU prediction, output validation, hashing and window drains. It excludes fitting, warmup, JSON formatting and final cleanup. Runtime qualification used the current Apple M4 Max host with a macOS 14 deployment target; macOS 14 runtime and unavailable-device retry behavior remain unverified.

## Delivery boundary

CPU/GPU implementation closeout is ready for contribution review at the recorded head, with the measured variation and qualification limits stated above. Publication and hosted CI are separate steps. Review the intended merge order with PR #62 before publishing. Keep engineering notes out of the implementation diff.

- [Validation summary](../archive/2026-10-07/cpu-gpu-closeout/validation.json)
- [Paired results](../archive/2026-10-07/cpu-gpu-closeout/paired.json)
- [Comparison summary](../archive/2026-10-07/cpu-gpu-closeout/summary.json)
