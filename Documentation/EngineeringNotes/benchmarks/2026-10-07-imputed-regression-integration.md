# Missing observations through GPU regression

Date: 2026-10-07

## Decision

The imputer and scaler storage path works through model fitting, held-out GPU prediction and repeated cleanup. Keep this integration coverage on the local trial branch. Large and mixed workloads retain a substantial resident-memory benefit when callers transfer ownership. Timing is workload-dependent. Small requests were slower in the sustained comparison, so this evidence does not justify a universal speedup claim or a new dispatch threshold.

Implementation commit: `f0261a2212d08b74f0444d9f76e510e93cb606d8`, following `8386d2476f32a1f685314134cd0be1b5f291e79d` on `codex/retained-memory-accounting-trial`. This increment changes benchmarks and tests only. Production APIs, arithmetic and validation policy are unchanged. The primary checkout remains untouched. Reports and measurements remain on `codex/engineering-notes`.

## Public workflow and independent checks

Training observations are paired with their negatives. All finite values are binary fractions, and missing entries occur symmetrically, so each nonmissing training mean is exactly zero. A public preprocessing `Pipeline` fits `Imputer` and `MinMaxScaler` on that training set. A CPU `RegressionPipeline` fits a linear model using cleaned columns. A GPU estimator then uses those fitted weights for prediction.

Held-out observations include numeric NaNs, explicit missing flags and a shift beyond the training range. An independent linear formula substitutes zero for missing values and supplies the expected answer. Refitting preprocessing on a held-out request would violate that formula. Every prediction must be finite, have the correct count and agree within `1e-4`. The maximum observed absolute error was `1.9073486328125e-06`. Complete output hashes and fitted parameter hashes match across ownership modes and rounds.

The prepared regression API still rejects nonfinite inputs before running its transformers. Imputation occurs in a separate preprocessing pipeline before this boundary. There is no new bypass or default-policy change.

Retained inputs stay alive through prediction validation. Consumed inputs transfer ownership, and each request verifies that preprocessing reuses every column buffer. Separate integrity workers hash all original values, validity words, validity presence and null counts before preprocessing and after prediction. Verification output is explicitly rejected by the timing controller. This prevents source hashing and its temporary allocations from distorting the ownership comparison.

## Lifecycle and scope

Each timed process runs four request windows, with two continuously refilled slots inside each window. Between windows, it drains requests and samples memory while retaining the model and ordinary caches. All 96 timed windows released every request reservation and returned MLX active allocations to the fitted-model baseline. After the fourth window, model release, GPU synchronization and cache clearing returned active and cached MLX allocations to zero. All workers exited.

The admission and MLX cache limits are each 256 MiB. Admission uses conservative byte estimates and does not impose a process RSS cap. Sampled memory must remain below 2 GiB. The controller checks memory pressure before starting a child, owns its process group and applies a 180-second deadline. No cache clearing or allocator pressure relief occurs between measured windows.

RSS includes allocator-retained pages and GPU caches. The benchmark also keeps request IDs, hashes and timing records until serialization, so CPU metadata grows with completed requests. Live MLX allocations and reservation balances are checked separately from RSS. These checks do not certify the absence of every possible CPU leak. The large and mixed retained-input RSS grows across some windows even though active model allocations and reservations return to baseline.

## Validation and review

The final selected Release suite passed 874 tests with zero failures and two optional skips. It covers SwiftDataFrame, SwiftStats, SwiftPreprocessing, SwiftML, SwiftCluster, SwiftOptimize, SwiftExplain, SwiftNLP and benchmark support. The two new tests check training-only preprocessing, retained/consumed prediction agreement, source preservation, rejection of invalid cleaned inputs, reservation release and successful recovery after rejection. Optional tokenizer assets and the existing MNIST fixture early-return behavior remain limitations of the selected suite.

Sixteen controller tests passed. Eight separate integrity workers completed 64 requests, including 32 complete retained-source checks. The sustained comparison completed 24 workers and 149,760 measured requests. Final smoke checks also exercised the existing StandardScaler and MinMaxScaler modes.

Standards review found no hard violations. Its suggestion to centralize repeated memory checks was implemented, including peak-versus-residency checks for every sample. Behavioral review found that retaining source lifetime alone did not prove source preservation in the GPU worker. The separate integrity mode closes that gap. Both follow-up reviews found no remaining issue in the amendment. No production defect was identified by this increment.

An initial build failed because a new test combined two actor-property reads in an assertion autoclosure. Splitting the assertions corrected the test; it was not a library defect. Final Release evidence supersedes that failed build.

## Sustained comparison

The host is Apple M4 Max with 128 GiB unified memory, running macOS 27.0 build 26A428. The arm64 Release worker has coverage disabled and uses the existing pinned dependencies and Metal build settings. The macOS 14 deployment target was built, but no macOS 14 runtime was exercised.

Small workers process 16,384 requests of 64 rows by 3 columns. Medium workers process 8,192 requests of 4,096 by 17. Large workers process 128 requests of 65,535 by 65. Mixed workers process 256 requests cycling through 8,191, 65,535, 16,383 and 65,536 rows with 65 columns. Three fresh-process rounds reverse case and ownership order in the middle round. Ordinary user activity is allowed.

Timing includes admission, fixture creation, missing marking, preprocessing, GPU prediction, analytic validation, full prediction hashing, window drains and memory samples. It excludes fitting, warmup, JSON serialization and final cleanup. No network, disk ingestion, persistence or reload is measured.

The speed column is the median of the three within-round consumed/retained ratios. Its range includes all three observations. RSS and lifetime peak columns are medians of fresh processes, not paired percentage changes.

| Workload | Paired throughput change | Observed throughput range | Retained RSS MiB | Consumed RSS MiB | Retained peak MiB | Consumed peak MiB |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| small | -14.2% | -18.4% to -7.4% | 30.1 | 29.5 | 30.1 | 29.5 |
| medium | -0.3% | -5.8% to +2.6% | 35.0 | 32.4 | 35.8 | 33.2 |
| large | +0.2% | -3.1% to +2.7% | 323.6 | 183.1 | 356.1 | 215.6 |
| mixed | +5.3% | +0.6% to +8.1% | 346.4 | 211.9 | 378.8 | 243.8 |

Large-input resident-memory reductions were 43.4% to 56.5%; mixed-input reductions were 35.5% to 39.1%. Small-input residency was nearly unchanged. Median paired throughput changes were -14.2% for small, -0.3% for medium, +0.2% for large and +5.3% for mixed. The small-request slowdown is an observed tradeoff that needs isolation; no cause is established here. The next timing investigation should separate preprocessing, actor dispatch and GPU completion costs before changing production dispatch.

The earlier shorter comparison completed 28,800 requests successfully, but some timing windows were subsecond. Its medium slowdown was not reproduced consistently by this sustained run, while the sustained run showed a small-request slowdown. That disagreement reinforces the need for scoped interpretation. The initial results are retained as exploratory evidence and are not pooled with the sustained measurements. Neither run compares against the pre-branch implementation or Python.

## Evidence and reproduction

Worker SHA-256: `249146abd1794e04b774c1870a5dc8a78b1c37e4ef1c344696f5c8385e427a9c`.

The committed README documents the comparison command and the separate `verify-source` worker argument. All timing workers require source verification disabled. The archived integrity driver records its complete commands and binary fingerprint. Raw worker JSON and logs are compressed without loss; Xcode result bundles remain in the local evidence directory.

- [Sustained worker summary](../archive/2026-10-07/imputed-regression/comparison-sustained/summary.json)
- [Source and binary fingerprints](../archive/2026-10-07/imputed-regression/comparison-sustained/provenance.json)
- [Paired changes and validation](../archive/2026-10-07/imputed-regression/validation.json)
- [Integrity verification](../archive/2026-10-07/imputed-regression/source-verification/validation.json)
- [Final selected Release result](../archive/2026-10-07/imputed-regression/final-release-summary.json)
- [Implementation fingerprints](../archive/2026-10-07/imputed-regression/commit.json)
