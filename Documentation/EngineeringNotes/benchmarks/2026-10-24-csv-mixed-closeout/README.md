# Retained CSV stack in complete mixed workloads

The local source head is `58db37c4b3c97b287186c377f76f89abcbbb0b0d` on `codex/csv-integer-overflow`. This experiment compares it directly with the starting checkpoint `36a93f7dfd54524fc7360fd52930366190db8d01`. No production source changed during closeout, and nothing was pushed.

Two qualified panels measure 2.3 to 3.5% less paired-round CPU with optional storage and 4.8 to 5.3% less with compact storage. Current code uses less CPU in 16 of 16 qualified compact comparisons. The original reversed panel fails its elapsed-time control and is excluded from this qualifying result.

Five retained commits change four production files: compact validity-word construction, structural scanning, raw-empty numeric fallback, normalized-empty numeric fallback, and signed-integer overflow handling. The endpoint comparison includes all five changes. The rejected digit-pair candidates remain excluded.

## Retained source commits

| Commit | Change |
| --- | --- |
| `5b9c902977` | perf(dataframe): flush compact CSV validity one word at a time |
| `2a8f123066` | perf(dataframe): pack CSV structural flags with SIMD narrowing |
| `31c0f958c8` | perf(dataframe): skip empty numeric CSV string fallback |
| `575f2f63cb` | perf(dataframe): skip numeric conversion of empty CSV text |
| `58db37c4b3` | fix(dataframe): handle CSV integer overflow without trapping |

The complete source diff contains four production files and three small test files. No benchmark or production source changes are added during this closeout.

## Panel qualification

| Panel | Qualified | Control flags |
| --- | --- | --- |
| forward-workflows | True | None |
| reversed-workflows [unqualified] | False | parent_compact: elapsed_ns ratio 1.1063 |
| confirmation-workflows | True | None |

The original reversed panel remains in every table and in the archive. Its CPU and memory controls pass, but its elapsed control fails. The raw control diagnostic records substantial elapsed variation in several rounds. It does not prove a scheduler, clock, thermal, or cache mechanism. One unchanged confirmation is run under a plan that permits no further attempts. The failed panel remains unqualified.

## Complete queue results

Every queue contains 128 jobs at four concurrent callers with native internal parallelism. Each panel rotates both builds and both storage modes, with an identical-binary twin for every condition. The second panel reverses every ordering. Its failed elapsed-time control triggers one unchanged reversed-order confirmation, frozen in a separate plan before that run. Each panel completes eight rounds, 64 queues, 8,192 timed jobs, and 32 full-output checks.

| Panel | Storage | Before CPU ms/job | Current CPU ms/job | CPU change | Throughput change | Before peak MiB | Current peak MiB |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| forward-workflows | optional | 261.56 | 256.29 | -2.01% | +5.14% | 3507.8 | 3507.8 |
| forward-workflows | compact | 261.21 | 250.65 | -4.04% | +6.86% | 2513.4 | 2514.1 |
| reversed-workflows [unqualified] | optional | 266.21 | 254.66 | -4.34% | +7.01% | 3516.1 | 3517.9 |
| reversed-workflows [unqualified] | compact | 270.41 | 251.42 | -7.03% | +10.87% | 2520.3 | 2523.5 |
| confirmation-workflows | optional | 248.29 | 236.70 | -4.67% | +7.10% | 3512.9 | 3495.1 |
| confirmation-workflows | compact | 243.26 | 233.26 | -4.11% | +7.08% | 2519.5 | 2509.2 |

CPU is summed worker user and system time plus measured controller CPU. It is resource consumption per completed job, not FLOPs, energy, or normalized performance-core and efficiency-core work. The table pools each condition with its twin. [Summary](summary.json) and [paired comparisons](comparisons.json) preserve the calculations.

## Paired-round consistency

| Panel | Comparison | Median paired CPU change | Rounds with less CPU | Median paired peak-RSS change |
| --- | --- | ---: | ---: | ---: |
| forward-workflows | optional stack | -2.25% | 7/8 | -0.20% |
| forward-workflows | compact stack | -5.30% | 8/8 | -0.06% |
| forward-workflows | current compact storage | -1.53% | 6/8 | -28.37% |
| forward-workflows | combined choice | -4.85% | 8/8 | -28.29% |
| reversed-workflows [unqualified] | optional stack | -2.72% | 7/8 | -0.26% |
| reversed-workflows [unqualified] | compact stack | -5.72% | 8/8 | -0.87% |
| reversed-workflows [unqualified] | current compact storage | -1.08% | 4/8 | -28.26% |
| reversed-workflows [unqualified] | combined choice | -5.29% | 8/8 | -28.21% |
| confirmation-workflows | optional stack | -3.50% | 8/8 | -0.52% |
| confirmation-workflows | compact stack | -4.75% | 8/8 | -0.17% |
| confirmation-workflows | current compact storage | -1.39% | 6/8 | -28.15% |
| confirmation-workflows | combined choice | -5.20% | 8/8 | -28.49% |

The stack comparisons hold storage mode and caller count fixed. Current compact storage compares optional and compact modes on the same current binary. Combined choice compares the starting optional mode with the current compact mode. The compact memory saving predates these five changes and must not be credited to them.

Paired ratios compare conditions within each round before taking medians. They can differ from ratios of pooled medians above. Counts describe the observed runs, not independent statistical samples or confidence intervals. A passing 10% twin control does not establish that every small difference is meaningful.

## Current storage choices at matched callers

| Panel | Current storage | Jobs/min | CPU ms/job | Peak MiB | Retained MiB | Resident MiB-seconds |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| forward-workflows | optional | 1713.6 | 256.29 | 3507.8 | 3133.1 | 14051.5 |
| forward-workflows | compact | 1727.0 | 250.65 | 2514.1 | 2138.8 | 9818.4 |
| reversed-workflows [unqualified] | optional | 1603.2 | 254.66 | 3517.9 | 3141.9 | 15044.6 |
| reversed-workflows [unqualified] | compact | 1609.9 | 251.42 | 2523.5 | 2144.4 | 10510.3 |
| confirmation-workflows | optional | 1805.4 | 236.70 | 3495.1 | 3136.3 | 13274.4 |
| confirmation-workflows | compact | 1789.6 | 233.26 | 2509.2 | 2137.4 | 9392.3 |

Retained RSS includes allocator and runtime caches. Resident MiB-seconds estimates memory occupancy integrated over queue time. Neither is a direct allocation count or proof of a leak.

## Operation CPU by reference case

| Panel | Storage | Input and workflow | Before CPU ms/job | Current CPU ms/job | Change |
| --- | --- | --- | ---: | ---: | ---: |
| forward-workflows | optional | Aotizhongxin-default/read | 14.79 | 14.56 | -1.52% |
| forward-workflows | optional | Aotizhongxin-default/sort-matrix | 20.18 | 20.64 | +2.27% |
| forward-workflows | optional | energy-common/read | 342.02 | 331.91 | -2.96% |
| forward-workflows | optional | energy-common/sort-matrix | 666.30 | 655.17 | -1.67% |
| forward-workflows | compact | Aotizhongxin-default/read | 14.82 | 14.33 | -3.27% |
| forward-workflows | compact | Aotizhongxin-default/sort-matrix | 19.83 | 19.35 | -2.46% |
| forward-workflows | compact | energy-common/read | 361.08 | 338.00 | -6.39% |
| forward-workflows | compact | energy-common/sort-matrix | 647.45 | 627.86 | -3.03% |
| reversed-workflows [unqualified] | optional | Aotizhongxin-default/read | 14.22 | 13.54 | -4.84% |
| reversed-workflows [unqualified] | optional | Aotizhongxin-default/sort-matrix | 20.00 | 19.43 | -2.85% |
| reversed-workflows [unqualified] | optional | energy-common/read | 350.73 | 328.65 | -6.30% |
| reversed-workflows [unqualified] | optional | energy-common/sort-matrix | 677.98 | 655.35 | -3.34% |
| reversed-workflows [unqualified] | compact | Aotizhongxin-default/read | 14.40 | 14.01 | -2.74% |
| reversed-workflows [unqualified] | compact | Aotizhongxin-default/sort-matrix | 19.28 | 18.66 | -3.21% |
| reversed-workflows [unqualified] | compact | energy-common/read | 368.83 | 337.57 | -8.48% |
| reversed-workflows [unqualified] | compact | energy-common/sort-matrix | 674.37 | 633.05 | -6.13% |
| confirmation-workflows | optional | Aotizhongxin-default/read | 13.35 | 12.82 | -3.95% |
| confirmation-workflows | optional | Aotizhongxin-default/sort-matrix | 19.19 | 18.78 | -2.12% |
| confirmation-workflows | optional | energy-common/read | 320.19 | 296.26 | -7.48% |
| confirmation-workflows | optional | energy-common/sort-matrix | 636.72 | 616.46 | -3.18% |
| confirmation-workflows | compact | Aotizhongxin-default/read | 13.03 | 13.00 | -0.26% |
| confirmation-workflows | compact | Aotizhongxin-default/sort-matrix | 18.23 | 17.57 | -3.58% |
| confirmation-workflows | compact | energy-common/read | 325.89 | 306.88 | -5.83% |
| confirmation-workflows | compact | energy-common/sort-matrix | 613.71 | 593.01 | -3.37% |

These operation figures exclude controller and request-decoding work. They include the public read, any requested sort and matrix construction, shape checks, memory bookkeeping, and release.

## Correctness and resource controls

The reference inputs contain 35,064 Aotizhongxin air-quality observations and 2,075,259 household-electricity rows. Both endpoints receive identical complete schemas, CSV bytes, null sets, Float64 and Int64 types, stable missing-last sorting, and owned row-major matrix output. Independent expected fingerprints match every native numeric bit, null, column, and matrix before and after timing. Full hashing is outside timing. Timed outputs receive shape and type checks.

All panels retain the unchanged twin controls: 10% CPU and elapsed-time drift, plus 5% and 8 MiB per caller for sampled RSS. The qualification table identifies the original reversed panel as unqualified. Its parent-compact twin elapsed-time ratio is 1.1063, above 1.10. No queue is removed and no threshold changes. The audit recomputes every planned queue and job, CPU accounting, memory summaries, output checks, and binary/source identity. All conservative sums of per-process lifetime peaks stay below the 4 GiB ceiling. Those sums are upper bounds, not simultaneous measured peaks.

Sampled RSS can count shared pages more than once and miss short peaks. Resident byte-seconds and retained RSS remain in the raw records. The declared envelope covers benchmark workers, not all physical memory. Background applications remain active. AC and power-policy checks are recorded before every queue and at panel boundaries.

## Validation already owned by the retained commits

The unchanged current source previously passed 447 Debug and 447 Release dataframe tests with no failures or skips. This closeout reuses those exact-head receipts and does not claim a new native test run. The integer repair also passed its independent 6,796-row corpus in both storage modes. The baseline overflow crash remains a historical failure and is not included in the timed reference queue.

The [integer fix report](../2026-10-24-csv-integer-overflow/README.md) owns those correctness receipts. The [construction report](../2026-10-24-compact-csv-construction/README.md), [scanner report](../2026-10-24-csv-structural-mask/README.md), [raw-empty report](../2026-10-24-csv-empty-numeric-fallback/README.md), and [normalized-empty report](../2026-10-24-csv-normalized-empty/README.md) own their individual trials and limitations. Their historical measurement fingerprints remain unchanged.

The 16 CPU queue controller tests pass during this closeout. The measured controller is unchanged. No full MLX suite, hosted CI, or Codecov result is claimed.

## Reproduction and scope

The [source provenance](provenance.json) matches both named commits across all 51 measured sources. Dependency-object hashes match. Historical build-head fields remain untouched. Source snapshots, immutable build receipts, full plans, contracts, hashes, raw queues, generated summaries, and the independent audit are preserved in the [experiment archive](experiment.tar.gz). Compiled objects, executables, module caches, raw CSVs, and xcresult bundles are excluded.

Rebuild the recorded endpoints with `Benchmarks/CPUThroughput/build.py` and matching dependency hashes. Restore the reference files by their recorded SHA256 identities, then remap local paths in `forward.py`, `reversed.py`, and `confirmation.py`. Run them sequentially in fresh output directories. Run `audit-workflows.py` on each completed panel, then `summarize.py`.

This experiment measures finite bursts of full CSV workflows with repeated fixture reads after preflight. It does not measure cold disk, a sustained arrival process, inference performance, GPU or Neural Engine operation, unique physical memory, or energy. It compares SwiftSci endpoints. Equivalent concurrent queues for external engines remain separate work.
