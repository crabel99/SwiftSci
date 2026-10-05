# Repeated fitting and scratch reuse

## Decision

Commit `a356fd07a739da9f8eca38db7a7b275f880c4e6e` on `codex/memory-kernel-trial` adds reproducible benchmark experiments and public usage guidance. Its baseline is `ddb515a47e2490c6f16c19f1cbc4efba00efd56f`. Production Swift code is unchanged. Keep reusable prepared data under caller ownership. Reuse fitted preprocessing only when the training split and preprocessing configuration stay fixed. Do not add an automatic full-source cache or public scaler-workspace API from these measurements.

This report belongs only to `codex/engineering-notes`. The implementation branch contains runnable experiments and API guidance, not these engineering decisions.

## Repeated model fitting

The benchmark constructs a fresh CPU LinearRegression for each pass and measures one, three or eight passes. Strategies rebuild prepared input, retain prepared input, or retain scaled input with its fitted scaler parameters. The scaled strategy is allowed only for a fixed training split. Changing splits always fit preprocessing again.

Each process retains the original immutable source. Cache setup is charged once. Total time includes input preparation, fitting and prediction, while fixture construction and independent reference replay are separate. This experiment uses a noise-free synthetic linear relation to isolate reuse costs. It does not vary model hyperparameters or measure model-selection quality. It also omits the sorting step from the previous workflow experiment, so its absolute times must not be compared with that earlier table as an additional speedup.

Three interleaved rounds completed 153 fresh processes and 576 measured fits. Every fit matched an independent row-array replay for fitted means, deviations, model parameters and held-out predictions. Analytical target checks also passed. Peak RSS was sampled before reference replay. The table gives medians, including cache setup. RSS uses decimal MB and is a process high-water mark, not live cache size.

| Shape, passes and split | Rebuild ms | Prepared cache ms | Scaled cache ms | Rebuild RSS MB | Prepared RSS MB | Scaled RSS MB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 100,000 × 8, 1 fits, fixed | 57.47 | 59.54 | 58.82 | 44.56 | 44.68 | 44.50 |
| 100,000 × 8, 8 fits, fixed | 372.12 | 350.72 | 319.17 | 59.24 | 54.38 | 44.58 |
| 100,000 × 32, 8 fits, fixed | 1340.94 | 1244.35 | 1138.44 | 168.20 | 151.18 | 122.13 |
| 1,000,000 × 4, 3 fits, fixed | 572.15 | 514.57 | 478.03 | 176.06 | 176.03 | 167.99 |
| 100,000 × 8, 8 fits, changing | 353.34 | 348.92 | Not applicable | 59.18 | 71.30 | Not applicable |
| 100,000 × 32, 8 fits, changing | 1342.83 | 1309.91 | Not applicable | 163.35 | 203.64 | Not applicable |

Across eight fixed-split fits, scaled caching reduced total time about 14–15% for the 100,000-row fixtures. At one million rows and three fits, the reduction was about 16%. Unscaled prepared caching saved less because preprocessing still repeats. For a single fit, the fixed-split strategies were close and caching could lose slightly.

Changing-split prepared caching saved only about 1–2% across eight fits. It retained an additional full prepared representation and raised peak RSS by about 12 MB at width eight and 40 MB at width 32. Preparing each fold directly is the better default for these inputs. These results do not establish a rule for expensive external conversion or other consumers that already need a retained full-source representation.

Logical cached payload was about 7.2 MB for 100,000 × 8, 26.4 MB for 100,000 × 32, and 40 MB for one million × 4. This includes cached targets and fitted scaler arrays where applicable. It excludes row maps, capacity, allocator overhead and model state. The original source remained retained in every strategy. Lower observed high-water RSS with scaled caching does not mean caches have no memory cost.

## Serial scratch experiment

A benchmark-only workspace retains the bounded tile and row buffers. Outputs remain independent. A changed second input must match production scaling and leave an earlier output unchanged. The workspace is restricted to a fixed shape, fixed fitted parameters and serial use. No concurrent or shape-changing workspace contract was introduced.

The experiment completed 99 fresh processes across 11 shapes and three strategies: production, fresh trial workspace and retained trial workspace. Exact comparisons passed before timing. Timings are warmed steady-state costs. Retained workspace initialization is excluded, fresh initialization is charged on every call, and output allocation remains included. This favors the retained case when estimating a finite call sequence, so it must not be presented as setup-inclusive savings.

At 32 × 1, median production/fresh/retained times were 0.76/0.89/0.68 microseconds. At 512 × 8 they were 13.68/14.70/14.62 microseconds. At 8,192 × 32 they were 724.83/733.79/774.81 microseconds. Small cases sometimes save fractions of a microsecond; larger cases are neutral or slower. The trial has ownership overhead of its own, so this is not proof that all scratch-reuse designs are unhelpful. It provides no case for promoting this one. Keep production's existing bounded per-call scratch and avoid adding retained mutable state without a larger measured benefit.

## Validation and provenance

Release compilation succeeded. Both benchmark suites passed their per-process checks. Final smoke checks covered all five legal fit strategies and all three scratch strategies. The runner now preserves partial output when a worker times out; a deterministic injected TimeoutExpired verified the saved command, round, strategy, timeout and byte-output decoding.

The timeout diagnostic and documentation changed after timing. `measured-controller.py` preserves the timed controller, and each suite retains its build manifest. All Swift inputs and Package.swift match the final build; no timing or numerical worker logic changed after measurement. The final build manifest matches the committed source. Full Debug/Release production suites were not rerun because production code did not change. The preceding checkpoint's two known MLX precision failures remain unresolved.

Run `repeated_fits.py --suite fits` and `--suite scratch` as documented in the benchmark README, after rebuilding the integration executable. Runners verify executable and source hashes, use AC power, clear thread overrides and rotate strategies. Local evidence is archived under `~/local-ai/spl/swiftsci/repeated-fits-20261005/`, including raw samples, manifests, summaries and final checks.

## Next step

Measure latency, throughput and peak memory under shared byte-budget admission with concurrent consumers. Include retained cache lifetime in the workload estimate. Do not derive a scheduling policy from isolated single-job timings or treat estimated reservations as a hard process-memory limit.

Both branches remain local. Nothing was pushed or submitted.
