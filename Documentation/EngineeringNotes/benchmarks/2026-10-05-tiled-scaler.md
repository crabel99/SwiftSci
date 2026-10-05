# Bounded prepared scaling

## Decision

Commit `ddb515a47e2490c6f16c19f1cbc4efba00efd56f` on `codex/memory-kernel-trial` promotes tiled traversal in the prepared StandardScaler transform. The baseline is `5c092885fd20a80f8b321570cb22de356235882d`. Public interfaces, precision policy and storage ownership are unchanged. This report belongs only to `codex/engineering-notes`.

Use tiling when the batch has at least 32 rows and at most 512 columns. The tile holds at most 2,048 Doubles, or 16 KiB. Three width-sized temporary arrays bring total logical scratch to at most 28 KiB. This excludes outputs, fitted state and allocator overhead. Other shapes retain the previous row traversal. There is no global cache or public tuning switch.

## Numerical correction during qualification

The initial candidate wrote division output directly into each tile row. A strict comparison failed at eight rows and one column, although the baseline passed. Using a separate array-backed output row removed the discrepancy while preserving row-width vDSP calls. No tolerance was relaxed. The new regression fits the original eight values and checks both eight-row fallback and 64-row tiled transforms with repeated input.

Tile row alignment was the suspected trigger; the experiment establishes that changing the destination fixes the observed rounding difference. It does not establish a general guarantee about Accelerate's internal alignment handling. Exact comparisons remain part of qualification.

## Dispatch evidence

An initial corrected sweep covered 35 shapes. The expanded sweep covered 53 shapes, including widths through 2,049. At 2,047 and 2,048 columns, the tile held one row and took about 33% longer for 128 and 512 rows. Width 1,024 was roughly neutral. Width 512 gained 11–17% at those row counts. Small batches gained little or lost slightly. The final gate therefore requires at least four rows per tile and 32 rows overall.

The final sweep covered 69 shapes in 414 fresh processes. Workers rotated across three rounds, used native threading and AC power, verified binary fingerprints, and compared exact row-array results before timing. Warmed scaling includes output allocation but excludes fitting. Selected median speed ratios were 1.29× at 32 × 8, 1.67× at 512 × 8, 2.32× at 8,192 × 8 and 3.54× at 8,192 × 32. The unchanged wide fallback at 128 × 2,048 was effectively equal. These are shape-specific results on the Apple M4 Max host, not universal speed guarantees.

## Complete workflow comparison

The broader comparison interleaved 45 fresh processes across five fixtures and three representations. Workflow time includes selection, preparation, fitting and prediction. Construction is separate; the independent oracle runs after timing and peak-RSS sampling. Values below are three-round medians. RSS uses decimal MB.

| Training shape and treatment | Rows ms | Prepared before ms | Prepared after ms | Rows RSS MB | Prepared after RSS MB |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1,000 × 4, ordinary, retain | 11.12 | 10.13 | 10.54 | 15.3 | 15.5 |
| 100,000 × 4, ordinary, retain | 67.32 | 70.77 | 62.00 | 40.8 | 33.0 |
| 100,000 × 8, noisy, materialize | 85.70 | 87.37 | 83.36 | 61.0 | 53.2 |
| 100,000 × 32, ordinary, retain | 191.99 | 206.12 | 186.60 | 137.6 | 123.3 |
| 1,000,000 × 4, ordinary, retain | 674.16 | 592.94 | 589.84 | 275.9 | 195.8 |

The 100,000-row prepared workflows improved about 5–12%. The million-row workflow improved only about 0.5%; its existing compact representation still saved about 80 MB against row arrays. The 1,000-row workflow was about 0.4 ms slower than the prior prepared path. Cold setup and other operations contribute to that total, so the warmed kernel speedup must not be presented as a matching whole-workflow gain. Peak memory changed by only about 0.1–0.2 MB against prior prepared execution in these runs.

## Validation and limits

Full Release and Debug runs each recorded 1,046 passing test definitions, two failures and two skips. Both failures and their numerical diagnostics exactly match the recorded baseline: the MLX GPU rotary transition-frequency and long-position oracle failures. No new failures were introduced; the full suite is not green.

The four new test definitions cover exact bit patterns across shapes and dispatch boundaries, the single-column rounding regression, missing and nonfinite values, snapshot provenance and concurrent transformations. Runtime parameter cases are additional executions, not additional test definitions.

Both compatibility and prepared public regression lanes passed 44 workflow scenarios. They also passed eight and five additional checks respectively and all 32 NIST comparisons per lane. NIST regression is unscaled, so it checks solver integration rather than directly certifying the scaler. Direct scaler tests and scaled workflow checks supply that evidence. The final before/after benchmark fingerprints match the committed source files. Standards and numerical-contract reviews found no remaining actionable issues.

## Reproduction and next work

The benchmark README documents `scaling.py` and `compare_prepared.py`. Preserve each executable with its adjacent `.build.json` manifest before comparing revisions. Local evidence is archived under `~/local-ai/spl/swiftsci/tiled-scaler-20261005/`, including failed-candidate output, all crossover sweeps, both full test bundles, workflow checks, NIST results and broad process samples. The archive includes the scripts used for broader comparison and validation. Historical benchmark fingerprints remain unchanged.

Next compare preparation and workspace reuse over repeated fits, measuring retained memory and total work. Then measure concurrent throughput under the shared admission budget. Keep those decisions separate from this bounded traversal optimization. This commit does not address arbitrary GPU ownership, process-wide memory enforcement or the existing MLX precision failures.

The implementation and notes are committed locally. Nothing was pushed or submitted.
