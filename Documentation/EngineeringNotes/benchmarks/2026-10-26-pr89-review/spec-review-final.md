## Spec

No findings in the corrected diff from `09607a7e9caa2b7166651dcaaa167178f6097b55` to `4f33c76f39`.

The maintainer requested “checked dimension conversions and overflow-safe workspace sizing” and suggested a finite-input mean-overflow regression (`review-request.json:41`). `PCAFullSVDLayout.swift:11–23` now checks exact positive Int32 dimensions and computes U, VT and integer-workspace element counts and storage bytes using checked multiplication (`:26–37`). `PCAComputation.swift:115–123` uses those verified counts before its auxiliary allocations. The existing actual LAPACK workspace query and exact positive Int32 conversion remain unchanged (`:125–132`), preserving backend-selected workspace sizes and valid solver behavior.

The initial review’s P2 is resolved: the non-tight sufficient workspace bound has been removed, and `PCAFullSVDLayoutTests.swift:27–32` accepts the backend-supported 24,000-square metadata without allocating its buffers. Invalid dimensions and the Int32-max-square byte-overflow case are rejected without enormous allocations (`:17–24`).

`PCAMeanOverflowTests.swift:8–31` covers finite intermediate-mean overflow for both CPU solvers through legacy rows, prepared batches, and both prepared matrix layouts, asserting failed-refit state preservation. No production math, public API, or unrelated behavior changes were added.

Spec: 0 findings. This is a source/spec review; complete local CI evidence is the parent task’s separate verification responsibility. The initial report remains preserved in `spec-review.md`.
