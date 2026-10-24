# Preserve CSV parser trials without changing the default

Keep the existing parser on `codex/csv-compact-construction` at `5b9c90297723cf53dcba17299c57778688e282e2`. The earlier [validity-word construction improvement](../2026-10-24-compact-csv-construction/README.md) remains intact. Both digit-pair candidates are correct, but their CPU savings depend on numeric representation. Each has a confirmed workload that uses more CPU. Neither becomes a production-default change from this experiment.

The local `codex/csv-number-parser-trial` branch preserves two commits. `2518888f13ba6cabbc7248c4e350cd1c78884f83` contains pair accumulation with nested branches. `5e15435685de63f29a07300047900734f326ba21` replaces it with a pair loop and one scalar tail. Both commit messages identify the resource limitation. Nothing was pushed and no PR was opened. Engineering evidence stays on `codex/engineering-notes`.

## What changed

After rejecting the [bulk construction trial](../2026-10-24-compact-csv-batch-trial/README.md), native sampling still placed number parsing and record scanning above bitmap work. The first candidate replaces two duplicated digit loops with a common helper that accumulates two digits at a time. The second simplifies that helper's control flow. Both preserve the existing short-decimal cutoff, integer accumulation, final division, sign handling, and standard-library fallback.

Neither changes public APIs, storage defaults, schema rules, or package minima. The candidates introduce no parsing allocation or new operating-system API. The experiment tests complete CSV operations rather than treating a shorter dependency chain as proof of resource savings.

## Correctness passed for both candidates

Each candidate passes 439 dataframe tests in Debug and another 439 in Release, with no failures or skips. The new focused test file has 50 lines. Tests cover odd and even runs, formatting, offsets, malformed bytes, rounding, signed zero, and fallback values. The new value tests use Swift's standard conversion, and the malformed-byte tests assert rejection. Neither reproduces the candidate algorithm. The original parser also satisfies this contract, so these are semantic guards rather than a red correctness test for the old implementation.

The standalone native checker emits identical presence and Float64 bit patterns for 417,865 cases in the parent and both candidates. A subset of 155,721 cases also has a direct standard-library conversion or explicit rejection oracle. The corpus includes every two-byte combination in four contexts, varying offsets, short and long decimals, scientific notation, wrappers, invalid syntax, large integers, and extreme exponents. The output SHA256 is `c1b0c406361b1f5548271b665571115ee09c61bda681cb405bdf7f8c4c21456f` for all three builds.

Both candidates also pass eight full native-bit reference-output checks across both storage modes and the read, sort, and matrix workflows. The first candidate's completed mixed panels add 64 preflight and postflight checks. The second candidate's incomplete mixed panel supplies no postflight or qualification claim.

## The first candidate saves CPU on the reference mix

Each completed panel contains 64 queues and 8,192 jobs. Four callers process a fixed queue of 128 jobs, with 32 copies of each dataset/workflow combination. The datasets are the 35,064-row Aotizhongxin observations and the 2,075,259-row household power file. Workflows read the full frame or read, stably sort, and construct the numeric matrix. Parent and candidate use the same contracts, output hashes, linked dependencies, and native CPU parallelism.

Eight rotated rounds include an identical-binary twin for each build/storage condition. A second panel reverses the ordering. Both panels pass their recorded CPU, wall-time, RSS, source, binary, and power checks. All conservative sums of kernel-reported worker peaks remain below 4 GiB.

| Panel | Storage | Parent CPU ms/job | Pair CPU ms/job | CPU change | Parent / pair sampled peak MiB |
| --- | --- | ---: | ---: | ---: | ---: |
| Rotated | optional | 197.48 | 193.93 | -1.80% | 3498.8 / 3503.5 |
| Rotated | compact | 194.56 | 191.31 | -1.67% | 2510.4 / 2510.7 |
| Reversed | optional | 207.82 | 200.67 | -3.44% | 3506.6 / 3503.6 |
| Reversed | compact | 203.55 | 197.12 | -3.16% | 2511.2 / 2511.2 |

Compact storage uses less CPU in all 16 paired rounds. Default optional storage uses less CPU in 15 of 16. The pooled and per-round ratios are separate summaries and need not agree exactly. These are finite repeated experiments, not independent statistical samples or confidence intervals.

The household read's compact operation CPU falls 2.68% and 4.21% in the two panels. Its full sort/matrix path falls 1.36% and 2.69%. Smaller observations are mixed. Their compact sort/matrix path uses 1.00% and 0.59% more operation CPU. Memory remains essentially unchanged. The compact representation's existing memory saving is inherited from earlier work, not produced by digit pairing.

Throughput changes are small and variable. Default optional storage changes +0.47% and +2.10%; compact storage changes -0.29% and +0.87%. These results do not establish a general increase in concurrent system throughput.

## Representation screens expose the tradeoff

The six format screens each use 250,003 rows, explicit Float64 storage, and a missing value every 97 rows. Each has six rotated rounds with twins, one caller, and four complete reads per queue. Full output checks use Python's native float bits outside timing. The following CPU changes compare candidate compact storage with parent compact storage within the same screen.

| Representation | Nested pair CPU change | Pair-loop CPU change |
| --- | ---: | ---: |
| one-digit | -1.30% | +4.10% |
| six-fraction | -4.57% | +0.45% |
| short-limit | -2.84% | -0.34% |
| scientific | -2.25% | -0.89% |
| long-fallback | +1.76% | -1.03% |
| quoted-padded | -2.48% | -0.85% |

A longer confirmation uses 32 reads per queue, eight rounds, and 1,536 reads. The first candidate's long-number case uses 2.12% more CPU overall and more CPU in all eight paired rounds. Its median paired increase is 2.01%. The unchanged source of the fallback does not guarantee unchanged complete-operation cost.

The second candidate's longer fallback replay is essentially unchanged at -0.04% overall. However, its longer one-digit replay uses 3.49% more CPU overall. Six of eight paired rounds use more CPU, with a median paired increase of 1.17%. The short and longer one-digit results agree on the concern, while their exact magnitudes differ. Neither tiny changes nor all-missing differences are evidence of a useful optimization.

Four further screens use 1,000,003 rows with binary-exact quarter values. Their missing patterns are none, every 97th row, alternating rows, and every row. Each completes 144 reads.

| Missing pattern | Nested pair CPU change | Pair-loop CPU change |
| --- | ---: | ---: |
| present | -2.10% | -1.41% |
| sparse | -2.77% | -0.33% |
| alternating | -2.21% | +1.34% |
| missing | -0.56% | +0.30% |

The second candidate's broad run stopped intentionally after 18 mixed queues so the one-digit concern could receive a longer check. Its driver received SIGINT, closed its workers, and returned nonzero to the orchestration script. No trial workers remained. Those partial records are archived and excluded from qualified results. They are not a failing unit suite or a hosted CI failure. The second candidate has no completed full mixed-workload result.

## What the compiler evidence does and does not show

The specialized shared parser has 145 instructions in the parent, 183 in the first candidate, and 188 in the second. The second has simpler Swift control flow but larger generated code. The long fallback itself has the same 131-instruction sequence after branch-address normalization. Register assignment and addresses differ. No extra fallback call was established.

These observations do not prove why the first fallback replay costs more CPU. Code layout, instruction-cache behavior, and branch prediction remain hypotheses. No hardware-counter measurement establishes a cache mechanism. The second candidate's fallback result also prevents treating function size alone as an explanation.

## Effective schema and measurement limits

Every timed worker in this study supplies a complete explicit schema and parallel conversion. No inference-performance claim follows from these timings. The earlier bulk-trial report incorrectly described numeric columns as inferred. Its README now corrects that claim while preserving its raw archive and historical fingerprints.

`schema_contract.py` records effective options for the reviewed worker source and rejects unknown worker fingerprints. Its positive and negative checks pass. The full panels and later screens record those options before timing. This is static source/receipt proof, not runtime option introspection. The input manifest's older inference-related field cannot override what the worker actually sets.

The machine is an Apple M4 Max with 128 GiB, on AC with unchanged recorded power settings. Full panels check AC before every queue. Builds use Swift 6.4 in Swift 6 language mode and an arm64 macOS 14 deployment target. Execution occurs on macOS 27.0.1. No Swift 6.0 compiler or macOS 14 runtime result is claimed.

Charged CPU is worker user/system time plus measured controller CPU, including cleanup. It is neither FLOPs nor measured energy, and it does not normalize performance-core and efficiency-core work. Peak memory is sampled summed worker RSS. Sampling can miss short peaks and shared pages can be counted repeatedly. No GPU, Neural Engine, cold-disk, or inference performance claim follows from this study.

## Decision and next investigation

Preserve both candidates locally and retain the existing parser. The reference mix shows a real opportunity, but the representation checks reveal a resource tradeoff that the reference-only average hides. Adding a public parser strategy is not justified by this experiment's small, workload-dependent differences.

The next useful investigation is the complete scanner/conversion boundary with representative numeric formats retained as separate workloads. Native profiling or hardware counters can test the remaining mechanisms. Changes should remove common work without relying on one favorable representation, and whole-workflow CPU and memory remain the acceptance measures.

## Reproduction record

[Summary](summary.json), [artifact hashes](artifact-sha256.json), and the [experiment archive](experiment.tar.gz) retain both exact source snapshots, compiler receipts, standalone checker, golden bit stream, unit-test receipts, full raw queues, interrupted-run receipt, source inspection, and reproducible fixture generators. Compiled executables, objects, module caches, raw CSVs, and xcresult bundles are excluded. The golden binary file is result data, not an executable.

Measured build receipts retain their original parent head and dirty-source fingerprints. The later local commit IDs map to those exact source hashes; receipts have not been relabeled. `audit-workflows.py` verifies both completed full panels against the frozen first-candidate source. `audit-screens.py` recomputes CPU and RSS summaries for all 960 completed screening queues and 7,872 reads. The archive hash inventory checks every preserved file.

To rerun, restore the recorded candidate snapshot or local trial commit, rebuild with `Benchmarks/CPUThroughput/build.py`, and require matching dependency and worker fingerprints. Restore the source snapshot expected by an audit, or pass it as the second argument after the panel name. Remap archived absolute paths, regenerate synthetic CSVs, and recover reference files with matching manifest hashes. Use a fresh output directory for every run. Historical output files remain immutable.
