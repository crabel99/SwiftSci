# Representative weighted ML Program qualification

October 26, 2026. Tested SwiftSci source `a1e234d25677d91ce5914062603c41233fe13c09`. This study adds evidence using existing public APIs; it contains no production source change. Prior full local CI belongs to this exact source and is linked in the preceding [representative Core ML qualification](../2026-10-26-coreml-representative/README.md). It was not rerun as part of this study.

## Results

Frozen WDBC and wine neural networks use the original real-data splits, training-only scaling and 64x64 hidden layers. Conversion reuses the existing model controller. All model parameters, held-out data, references, package files and public-probe objects have recorded hashes. The independent scalar Double forward control agrees with the original reference within 7.6e-15. NumPy emitted arithmetic warnings despite finite matching results; the scalar control avoids NumPy/BLAS. No retraining or tolerance adjustment was used.

- 24 reduced-precision processes produced 864 complete batch predictions through direct, prepared and fused pool routes. Ownership, row identity, same-variant route agreement, rejection recovery and reservation drainage passed. Four callers shared two slots; retained owners and input preparation also worked across pools.
- Both original program variants use Float16 internal computation. Float32 I/O is transport, not a full-precision model. Every reduced-precision process exceeds the unchanged Double tolerance `abs(error) <= 1e-5 + 1e-5 * abs(reference)`; maximum observed absolute error is about 0.06922. WDBC had zero classification disagreements. Application suitability was not assessed.
- A task-local, recorded three-substitution derivation of the existing converter produced full-Float32 computation controls. All 12 processes and 432 complete predictions meet the original tolerance. Maximum error is below 6.74e-6. This narrows the discrepancy to the chosen artifacts/precision, without isolating arithmetic rounding from parameter quantization.
- 52 concurrency/sustained cases completed 13,621,364 requests with bounded output/ownership/recovery checks. The 32 fresh synchronous/asynchronous cases performed 64 queued-cancellation checks. The 20 persistent cases performed zero cancellation checks. Four persistent cases lasted 60 seconds. This is bounded stress evidence, not proof of leak freedom or a new performance baseline.
- Eight two-second profiled recordings contain 215,448 completed requests and positive CPU dispatches. No other target device dispatches were observed, including policies permitting the Neural Engine; global ANE tables contain zero rows. Neural Engine acceleration is not established. Profiling-worker timings are excluded from performance comparisons.

Row identity and same-variant route agreement do not imply bit-identical values across batch orderings. Reduced-precision variants differ from permuted normal outputs by at most 0.015625. Of 129,168 compared values across repeated routes and callers, 1,485 exceed the same tolerance against the permuted normal output, spanning 18 of 24 processes. The full-Float32 wine CPU control differs by at most 9.54e-7 on four reversed positions and remains within reference tolerance. Across all full-Float32 variants, none of 64,584 compared values exceed that cross-variant bound.

The wine model's original held-out RMSE is about 0.9569, worse than the constant baseline's 0.8095; original training reached its iteration limit. Agreement with this model does not demonstrate model usefulness.

## Trace recovery and publication

The first recording driver timed out after the wine16 CPU target exited successfully and saved its trace; its cleanup also raised a permission error. The original controller and scoped failure receipt are retained in `trace-programs-before.py` and `traces/initial-driver-failure.json`. The saved target result, model/output identities, successful TOC export and complete prediction/device events were verified before resuming only the three missing cases. `recordings.json` preserves the recovered status and capture-controller hashes rather than claiming a clean driver exit.

Raw trace bundles and compiled executables remain local. Published TOCs remove device name and UUID, and published metadata replaces the hostname with a redacted marker. Authorized filesystem paths remain; `publication-transforms.json` records original and published hashes. Compressed event exports, original digests in the transform maps, all output vectors, frozen model packages and the original recording ledger are retained. `verify-publication.py` checks the file manifest, every published compressed payload and its decompressed digest, transformed TOCs and replayed device-event summaries. Historical provenance paths refer to the original machine; compression and transformation maps resolve the published bytes.

Run `python3 verify-publication.py` from this directory to verify the retained package without inference or tracing. To reproduce model execution, obtain the exact tested SwiftSci commit, restore paths for the recorded controllers, build the benchmark worker with the recorded Metal settings, and use the pinned converter environment. The scripts deliberately reject mismatched source, worker, models or references. Original worker build metadata and public-probe link proof are included. This evidence is not qualification of later integrated source revisions.

## Attention

Reviewed by gpt-6-astra. No blocking findings. The audit retains the persistent-cancellation and cross-batch-order limitations above. See `audit-interim.md` for scope and independently recomputed results. Source integration, documentation reporting and any later LLM work are separate units.

The publication audit in `publication-audit.md` checked the transformed metadata and scoped driver failure. Its remaining wording request was corrected before publication: the verifier checks published decompressed digests, while original digests remain provenance.
