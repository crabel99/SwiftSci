# Prepared PCA workflow qualification, 2026-10-26

Prepared batches and row-major or column-major matrices now support PCA fit, transform and fitTransform directly. This record belongs on the engineering-notes branch. Production changes are limited to library code, native tests and user documentation.

## Source and scope

Production contribution: https://github.com/Nodibell/SwiftSci/pull/89, commit 2278521eb707b965914ff46b12a6ffecde134109. The PR is a draft; upstream CI was still running at closeout.

The production branch starts at upstream main e19db7dda4567c425b7eb002da82e234e6c7980f. The unchanged baseline was freshly built from 5cc699a7efe3f1d6a2697172eb62b94a35bc3a26. `workflow/baseline-identity.json` confirms all 380 baseline Sources and Package files match the upstream base. An initially located October 13 cached binary was rejected and never used in measured comparisons.

The candidate Release build uses the standardized worker builder's tracked snapshot and safe Metal settings. Build receipts record source, dependency, binary and resource fingerprints. The final adjacent DocC device correction happened after native tests and workflow measurements; it changed Markdown only. Compare the native build and worker source receipts to verify all Swift sources are identical. The final standardized conformance run uses the refreshed documentation receipt.

## Correctness

- Debug: 656 selected SwiftCluster, SwiftDataFrame and SwiftPreprocessing tests passed, zero failures or skips.
- Release: the same 656 tests passed, zero failures or skips.
- Standardized model conformance: six SwiftSci/Python engine runs passed with existing tolerances, including oblique PCA k=1 and k=2. The certificate audit passed.
- Complete workflow: 90 fresh processes, three fixtures, full and randomized solvers, old nested workflow and candidate nested/batch/both matrix layouts, three repetitions each. All 540 field comparisons passed. Maximum old/new absolute difference was zero. Full SVD results also matched independent NumPy SVD with 1e-12 absolute and relative tolerances. Randomized cases are compared against the unchanged deterministic randomized implementation, without claiming exact full-SVD equivalence.
- Source-row provenance, including repeated held-out indices, matched exactly in every process. Fixtures and all exported raw observations are compressed in `workflow/fixtures-and-raw.tar.gz`.
- SwiftCluster symbol extraction and DocC conversion passed without warnings after correcting preexisting stale device references in the touched article.

## Complete-workflow resource observations

Each measurement starts before CSV import and ends after train-only standardization, PCA fitting, held-out projection and flat score materialization. Fitted state and score arrays remain alive at the RSS sample. JSON serialization is outside the timed boundary. Peak RSS is the process lifetime high-water mark; retained RSS is a current process resident-size observation, not an allocator live-byte count. The paths include caller-held source data and have different ownership lifetimes by design.

The table gives medians across three fresh processes, old nested / new prepared batch. Wine is sklearn's bundled 178x13 dataset, k=4. Tall is deterministic Gaussian latent data with noise, 12000x24, k=6. Wide uses the same generator sequence, 160x512, k=8. Exact CSV hashes and generator information are in `workflow/identity.json`.

| Fixture | Solver | Elapsed ms | User + system CPU ms | Peak RSS MiB | Retained RSS MiB |
| --- | --- | --- | --- | --- | --- |
| wine | full | 1.03 / 0.87 | 0.95 / 0.78 | 9.55 / 9.61 | 9.55 / 9.61 |
| wine | randomized | 0.93 / 0.85 | 0.95 / 0.88 | 9.73 / 9.73 | 9.73 / 9.73 |
| tall | full | 32.80 / 32.20 | 32.76 / 32.28 | 21.67 / 19.50 | 21.67 / 18.66 |
| tall | randomized | 35.93 / 32.95 | 35.79 / 32.85 | 26.02 / 19.50 | 26.02 / 18.55 |
| wide | full | 13.41 / 14.22 | 13.45 / 14.28 | 15.36 / 14.08 | 15.36 / 14.08 |
| wide | randomized | 10.36 / 10.40 | 10.34 / 10.42 | 14.75 / 13.27 | 14.75 / 13.27 |

Prepared batches reduced peak RSS on the tall and wide cases. Timings are mixed, including slower wide prepared batch results. Three small cases on one machine do not establish a general throughput improvement. No performance acceptance threshold or universal memory bound is claimed. GPU correctness is covered by native tests; no GPU performance comparison was made.

## Reproduce

`workflow/Workflow.swift` is the same complete-operation driver compiled against baseline or candidate Release objects. `workflow/build.py` accepts the products directory and binary name, enabling PREPARED_PCA for the candidate. Build JSON files contain complete compiler/linker commands and hashes. The script uses the package cache path recorded in the build receipts and can be adjusted to another verified cache.

Build unchanged and candidate snapshots with `Benchmarks/Tools/bench.py build`, then build both workflow executables and run `workflow/compare.py` with the project's standardized Python environment. The comparison script regenerates the datasets and executes every mode. It requires both binaries in its own directory and NumPy/scikit-learn. Benchmark executables and compiler caches are intentionally excluded from this record. Native test commands and results are in the configuration directories. The standardized model-conformance plan, artifacts and certificate are retained for audit.

The standalone driver does not impose process memory admission. No solver defaults, device choices, or numerical tolerances changed to obtain the results. See `design/selected.md` for fitted-state, schema and precision decisions, and `decisions.tsv` for the decision trail. The available independent reviewer uses GPT-5.6; a separate model vendor/family was unavailable. No active workspace transcript file was exposed, so review used task context and saved artifacts.
