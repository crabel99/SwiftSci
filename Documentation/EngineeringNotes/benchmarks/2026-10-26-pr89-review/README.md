# PR 89 SVD boundary correction

Source: [`4f33c76f3938e070105c2a5928c712aa5e067a00`](https://github.com/crabel99/SwiftSci/commit/4f33c76f3938e070105c2a5928c712aa5e067a00), following the submitted PCA head `09607a7e9caa2b7166651dcaaa167178f6097b55`.

## Maintainer request and correction

The [maintainer's review](https://github.com/Nodibell/SwiftSci/pull/89#pullrequestreview-5656401705) requests checked dimension conversions, overflow-safe full-SVD workspace sizing, and regression coverage for finite inputs whose intermediate mean accumulation overflows.

`PCAFullSVDLayout` now checks positive LAPACK dimensions with exact Int32 conversion. It checks the U, VT, and integer-workspace element counts and byte sizes before allocation. `fullSVD` uses those checked values. Its existing exact conversion of the actual queried LAPACK workspace remains authoritative. Public signatures, solver choices, and numerical accumulation remain unchanged.

Small rectangular layouts preserve economy-SVD dimensions. Boundary tests reject invalid dimensions and Int32-max-square buffer byte overflow without allocating corresponding matrices. A 24,000-square metadata case remains accepted.

The first local candidate also enforced the documentation's sufficient quadratic workspace bound. Independent spec review found that this bound is not tight. An allocation-free Accelerate query for 24,000 square returns `info=0` and Int32-valid `LWORK=1728168000`. The final correction removes that preflight. The initial finding, actual query, and final review are retained. The superseded candidate's bound tests are not evidence of an original backend failure.

## Mean overflow already rejects safely

The new public-path regression fits a valid prepared batch and then attempts refits with two finite `Double.greatestFiniteMagnitude` values in the same feature. Mean accumulation overflows. The existing centering guard rejects the nonfinite intermediate value.

Both full and randomized solvers reject all four input routes: nested rows, prepared batch, row-major matrix, and column-major matrix. Each attempt preserves fitted means, components, explained variance, resolved device, and the original batch's projection.

A separate CPU control linked against the originally submitted worker also passes this behavior. That control's source fingerprints and linker proof are retained. No production mean calculation was changed.

## Final verification

All 1,667 native tests pass in both Debug and Release, with no failures or skips. The full local main and benchmark workflows and Python CodeQL pass. Swift 6.3.3 passes both builds, compiles all test targets, passes the safe suite, and passes all four new tests in the two regression suites. Its LLVM profile records eight dimension-error throws and one size-overflow throw in the actual production helper.

See `qualification.json` for completed, source-bound results. `verify-qualification.py` checks those outcomes, changed-source fingerprints, actual worker identity, and workflow log hashes.

The main workflow includes both builds, safe tests, coverage export, DocC generation, public documentation coverage, and an additional check that the export contains library source records. The benchmark workflow retains existing controller tests, optional Polars and DuckDB comparisons, checkpoint controls, inventory reconciliation, CPU acceptance policy, public-worker challenges, and three MLX CPU profiles. Tolerances and policy remain unchanged. Four known Python Wampler reference failures remain under that existing policy.

Swift CodeQL is unsupported with the retained Xcode 27 / Swift 6.4 toolchain. Native xccov results are not presented as a library source coverage percentage. Large-shape metadata and native workspace queries do not establish memory availability for allocating those matrices. No performance claim is made.

Standards and Spec final reviews have zero actionable findings. Hosted GitHub checks are separate from these local results.

## Records and reproduction

`production.patch` contains only the changes after the submitted PR head. Scripts preserve the original task's paths and toolchain selection for inspection and adaptation to a fresh isolated directory. Builds use independent caches. The older compiler does not change the selected Xcode.

Logs and coverage text are compressed with gzip; `compression-map.json` records original hashes and paths. `FILES.sha256` binds the published files. Native test summaries retain all test counts; large xcresult bundles and compiled caches remain at the local paths in those records.

The first broad qualification was stopped when review identified the overly restrictive candidate. The final runs use fresh output directories and the corrected commit. One initial Release launch ran inside the restricted sandbox and could not discover the Swift package; the final native run uses the same cache access as the successful Debug run. Those attempts are not reported as final passes.
