# Public workflow implementation and acceptance

The local testing commit `76554ed898479ab18a5febed885d41c8b8077c4a` adds the two approved public-API workflows on `codex/standardized-benchmarks`. It is not pushed. Production sources are unchanged. The earlier uncommitted benchmark README edit remains intact.

## Implemented contracts

The scientific profile has four cases. It stages original CSV observations and calibrations, declares Int64 identifiers and Double measurements through public CSV options, filters numeric quality, joins by site, sorts observation/calibration IDs, exports nested and flat matrices, fits CPU OLS, and predicts. Independent exact-rational answers check every identifier, feature, target, coefficient, prediction, residual, and residual sum of squares. Cases cover duplicate and unique join keys, unmatched and excluded rows, missing quality, feature permutations, and shuffled input rows.

The fitted-model profile has six cases. Public `RegressionPipeline`, `StandardScaler`, and CPU `LinearRegression` fit six training observations and predict three disjoint held-out observations. Paired cases perturb held-out features and targets while retaining identical training data. Independent rational and 90-digit Decimal calculations check fitted state and complete numerical outputs. Prediction must not mutate training state.

The fit route isolates preprocessing and prediction. The native route saves the regressor and reloads it in a fresh process before predicting on already transformed held-out inputs. The Core ML route composes existing public exporters for the fitted scaler and regressor, then compiles and predicts from raw held-out features in a fresh CPU-only process. SwiftSci has no native fitted-pipeline save/load API. The worker does not supply a substitute implementation or pretend regressor persistence also persists preprocessing.

Both profiles join CPU acceptance. The suite now assigns 24 canonical profiles to execution tiers. CI also challenges passing workflow workers with corrupted answers and invalid inputs, retaining evidence after failures.

The contribution's [workflow guide](/Users/crabel/Documents/src/SwiftSci/Benchmarks/Fixtures/workflows/README.md) defines output ordering, tolerances, fixture regeneration, retained artifacts, and timing limits.

## Recorded validation

| Check | Result |
| --- | --- |
| Full controller suite | 144 tests passed |
| Release integrated worker | Built successfully without coverage instrumentation |
| Scientific workflow | 8 of 8 engine-case executions passed; certificate audit passed |
| Fitted-model workflow | 8 of 12 engine-case executions passed; 4 retained Swift library failures |
| Evidence inspection | Complete case coverage; zero infrastructure errors in both new profiles |
| Actual-worker sensitivity | 16 unchanged controls passed; 64 corrupted cases rejected |
| Failing baseline eligibility | 4 cases excluded from sensitivity claims, not counted as successful rejection |
| Existing dataframe-to-tensor CPU profile | 8 of 8 engine-case executions passed; certificate audit passed |

The two new profiles comprise 20 engine-case executions, not 20 independent algorithms. Each passing execution validates two samples. The comparison worker uses pandas, NumPy, and SciPy. Its persistence route saves numerical state in NPZ, so it is not an independent implementation of the Swift native JSON or Core ML serialization formats.

All 364 source-file hashes recorded in the final scientific run match commit `76554ed898479ab18a5febed885d41c8b8077c4a`. The source fingerprint is `06fe15359c24e90dd820f61b20832f8865055b661ece5a17e261122c7300c2b8`. Runs occurred before the commit, so their recorded Git HEAD is the prior commit. The file hashes establish the executed working-tree content. The full 24-profile acceptance run was not repeated; the complete controller suite, both new profiles, actual-worker controls, and the existing CPU boundary profile were run.

## Retained failures for the repair branch

1. Native regressor reload fails in both held-out variants with `Model must be fitted before calling predict or transform.` Training and prediction before saving pass. `LinearRegression.load` calls the supplied-weight initializer, matching the previously retained fixed-weight initialization problem. Repair should preserve the fresh-process regression test.
2. Core ML compilation rejects the exported composite pipeline in both variants with `Feature descriptions exceeded 1`. Existing export-file checks did not execute this artifact. The new test does. Diagnose the scalar/vector feature descriptions in the scaler and regressor export before changing the serialization implementation. No exporter repair or alternate hand-built model was added.

These are two failure categories across four cases. The failed persistence certificate stays failed. A successful training case must not be presented as successful deployment persistence.

## Schema lesson from the scientific integration

The initial worker left CSV type inference enabled without declaring column types. The zero/one quality column became Boolean. Applying the numeric `greaterThanOrEqual(1)` predicate kept the zero-valued observation, producing an unexpected row count before the join.

The intended scientific contract declares numeric quality. Both workers now request that schema explicitly through their public CSV APIs. The independent expected answers did not change. All scientific cases pass with that schema, including duplicate-key joins. This was a test setup assumption about inferred types, not evidence of a join multiplicity defect. The permissive Boolean/numeric fallback remains a separate API concern for later triage.

## Evidence limits

These bounded fixtures qualify selected public operations. They do not establish predictive quality, production memory behavior, general numerical stability, or a formal speed baseline. Persistence timing includes child startup and compilation; parent peak RSS excludes child peak memory. Deployment routes therefore have no speedup claim.

Per-sample model files, child requests, child responses, staged CSV files, and complete outputs support diagnosis. The benchmark certificate audits normal protocol evidence, not every supplemental file. This notes archive independently hashes every included file. It contains only synthetic workflow data and the recorded validation artifacts.

The [evidence manifest](../archive/2026-09-27/public-workflows/manifest.json) lists paths, sizes, and SHA-256 digests. The [compressed archive](../archive/2026-09-27/public-workflows/evidence.tar.gz) includes final runs, controls, build metadata, and controller logs. This report and raw evidence remain only on `codex/engineering-notes`.
