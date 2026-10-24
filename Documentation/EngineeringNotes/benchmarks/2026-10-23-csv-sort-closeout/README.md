# CSV and stable-sort closeout on reference data

The retained source is `a74f5c3b5e0e511bf5bb69886a40cbae48b28d99` on `codex/csv-all-missing-sort`. The source tree remains unchanged. This study investigates common-input costs, confirms selected noisy cases under a separately recorded protocol, and compares complete public workflows with pandas, Polars, and DuckDB. Nothing was pushed or submitted.

The [previous all-missing report](../2026-10-23-csv-all-missing-sort/README.md) remains unchanged. Its five unqualified timing comparisons remain unqualified. The new results are additional observations, not replacements.

## Separate the larger observation from the persistent small cost

The earlier million-row half-plus-one compact control showed about 10% more CPU. Two independently recorded repetitions of the same four-case diagnostic did not consistently repeat that increase. In the second repetition, the paired CPU ratios were 1.0045 for that control, 1.0104 for the optional ascending control, and 1.0051 for the compact random control.

The small 32,768-row optional control remained sensitive. A different previously noisy 32,768-row compact control also showed a modest cost in the higher-replication study below. These results do not establish that the metadata guard is free.

Normalized disassembly preserves opcodes and operands while removing relocation-dependent instruction addresses, internal absolute branch targets, and computed ADRP page-address comments. All 428 matched CSV-related symbol bodies are identical between the direct parent and retained candidate. `sortedDoubleRows`, its comparator stub, and matrix preparation are also identical under that normalization. The generic sorting entry changes.

Three-second statistical profiles place most samples in existing key preparation and stable sorting. They do not isolate the few-microsecond difference. Identical normalized routines do not prove identical cache behavior or linked-code effects. No instruction-count, cache-hit, energy, or FLOP claim follows from this inspection.

## Confirm selected cases with more independent processes

The parent in this section is `940353d441`, and the retained candidate is `a74f5c3b5e`. The precision study declares 32 replicates per label before execution, four blocks, rotating case order, and balanced label orders within each block. Parent and candidate each have an identical-binary control. All 1024 measured outputs match. Every case passes the unchanged 10% CPU and 5% plus 8 MiB peak-RSS control limits.

The workload remains the first public index sort, with input construction excluded, input retained by the caller, and output release included. This study does not replace that call with a warmed batch.

| Case | Parent CPU, ms | Retained CPU, ms | Paired CPU ratio | Pairs with more CPU |
|---|---:|---:|---:|---:|
| Double/1000000 | 2.5500 | 0.7555 | 0.3048 | 0/32 |
| Float/1000000 | 2.3705 | 0.7210 | 0.2988 | 0/32 |
| Date/1000000 | 59.8125 | 0.7095 | 0.0123 | 0/32 |
| Double/8000000 | 19.6215 | 5.6735 | 0.2926 | 0/32 |
| Int64/1000000 | 2.4485 | 0.7755 | 0.3067 | 0/32 |
| String/1000000 | 47.6165 | 0.7570 | 0.0161 | 0/32 |
| valid-2-distributed-32768/serial/compact/sort-indices | 0.0970 | 0.1030 | 1.0436 | 26/32 |
| half-plus-one-1000000/serial/compact/sort-indices | 2.5270 | 2.5345 | 1.0158 | 19/32 |

CPU columns are primary-label medians. The paired ratio pools each source with its identical-binary twin within each round. The first four rows revisit previously unqualified all-missing observations. Int64 and String are additional controls. The distributed 32,768-row compact case uses about 4.4% more paired CPU, a few microseconds. The million-row common control is about 1.6% higher. These costs stay visible beside the exceptional-case savings.

## Reject a refactor that spends memory for some CPU savings

Local branch `codex/csv-sort-algorithm-shortcuts`, commit `4d81b5539e`, moves the all-missing checks from the generic entry to the existing Double, primitive, and fallback algorithms. This tests whether reusing counts at those boundaries removes the common-entry cost. It adds no threshold, public API, worker cap, or compiler directive.

All 431 Release dataframe tests pass. All 128 fresh-process outputs match, and duplicate controls pass. The refactor lowers CPU on some controls, but million-row compact sorts raise process peak by about 7.5 MiB. The random control gains no meaningful CPU reduction. We reject that tradeoff and retain the parent. The profiles and source diff do not establish why the compiled variant changes allocation behavior.

| Control | Retained CPU, ms | Trial CPU, ms | Retained peak, MiB | Trial peak, MiB |
|---|---:|---:|---:|---:|
| ascending-1000000/serial/optional/sort-indices | 1.4450 | 1.4065 | 32.797 | 32.828 |
| half-minus-one-32768/serial/optional/sort-indices | 0.0810 | 0.0825 | 8.406 | 8.453 |
| half-plus-one-1000000/serial/compact/sort-indices | 2.8680 | 2.4285 | 30.922 | 38.383 |
| random-1000000/serial/compact/sort-indices | 13.9130 | 14.0235 | 38.188 | 45.812 |

## Compare equivalent complete workflows

Two independent reference datasets cover 35,064 air-quality observations and 2,075,259 household-energy observations. Each has a read workflow and a read, stable sort, and matrix workflow. These four cases are a selected production-path comparison, not the complete benchmark or numerical certification suite.

The historical SwiftSci baseline is `5d1f89a961106104757f2d8d0b8faba79487d100`, immediately before this compact-storage work. Its 50 source hashes match the recorded commit, and those sources were rebuilt with the same toolchain and optimization flags as the candidate. It is not the original unoptimized project. The candidate object and matching module also pass source and object hash checks.

All engines receive complete schemas, identical delimiter and null tokens, and the same input bytes. Swift explicit overrides return before inference. Numeric columns use native Float64 and Int64. Date-like fixture fields remain String in every engine. Pandas uses its round-trip Float64 parser. The two fixtures contain missing floats but no separate valid-NaN payloads. This is a comparison of their common semantics, not a claim that pandas distinguishes valid NaN from missing values.

Each sort materializes the complete input first and returns the complete frame in stable ascending order with missing keys last. DuckDB receives an explicit original-row index as a secondary key because its sort does not itself supply this stable-order contract. Creating, registering, sorting, and releasing that temporary index is included. No engine fuses the CSV scan with a lazy SQL sort.

The matrix includes all numeric columns in source order and owns writable contiguous row-major Float64 values. Input preparation, copying, computation, allocation, and output release count toward total CPU and wall time. Full output hashing is excluded. Read-only operation CPU is timer bookkeeping, not a second data operation. Every worker verifies all columns and matrix bits, including native Int64 bytes, not an approximate numeric aggregate.

Every comparison runs on the CPU with native parallelism. Swift uses its parallel conversion option. The shared production-default policy clears inherited thread caps and scheduling overrides before imports. Recorded pool sizes are configured limits, not measured active cores. No GPU or Neural Engine result is mixed into these tables.

There are 32 exact preflights and 512 timed fresh processes. Six implementations or storage choices plus two identical-binary controls run in 16 balanced orders. Each label occupies each position twice, and each ordered adjacent pair occurs twice. Dataset order rotates each round. AC power is checked at both ends. Explicit imports and DuckDB connection creation precede timing. For sort-matrix, the DuckDB adapter preimports pandas because Arrow registration otherwise loads it lazily during the operation. Read-only does not load that unused dependency. Other first-use initialization within public operations remains included. Process peak includes the runtime baseline, which is also reported separately.

CPU is process user plus system time. It measures work charged to the process, not energy, FLOPs, or cache traffic. Qualification rejects excessive identical-binary drift. It does not provide statistical confidence for small differences. Lower wall time can coexist with higher CPU when a library uses more parallel workers. No cross-library efficiency winner is inferred from wall time alone. Absolute RSS includes different language runtimes. The peak increment above the pre-call high-water mark is reported as additional context, not as an exact measure of dataframe storage. Within-Swift historical comparisons isolate the storage changes more closely.

Runtime versions are pandas 3.0.6, Polars 1.44.2, DuckDB 1.5.6, NumPy 2.5.3, and Python 3.14.6. The hardware and compiler receipt records the M4 Max, 128 GiB memory, macOS version, and Swift 6.4 build. Inputs are read repeatedly after preflight. Disk-cache residency was not forced or measured, so these are not controlled cold-disk tests.

### Air quality, CSV read

Timing quality: qualified.

| Engine or storage | Total CPU, ms | Wall, ms | Operation CPU, ms | Peak RSS, MiB | Peak above baseline, MiB |
|---|---:|---:|---:|---:|---:|
| baseline | 11.622 | 4.705 | 0.003 | 23.203 | 16.500 |
| optional | 11.732 | 4.689 | 0.003 | 23.156 | 16.516 |
| compact | 11.756 | 4.790 | 0.004 | 21.984 | 15.344 |
| pandas | 37.257 | 37.307 | 0.006 | 115.719 | 17.961 |
| polars | 24.273 | 3.225 | 0.009 | 80.375 | 18.008 |
| duckdb | 44.093 | 22.595 | 0.008 | 95.383 | 20.195 |

Compact versus the historical checkpoint uses 1.2% more total CPU and 5.3% less absolute peak RSS. Compact uses 0.48 times Polars' total CPU in this case. Use the table to distinguish the read cost from the additional operation cost.

### Air quality, CSV read, stable sort, and matrix

Timing quality: qualified.

| Engine or storage | Total CPU, ms | Wall, ms | Operation CPU, ms | Peak RSS, MiB | Peak above baseline, MiB |
|---|---:|---:|---:|---:|---:|
| baseline | 17.497 | 6.796 | 6.082 | 33.180 | 26.477 |
| optional | 17.898 | 6.758 | 5.814 | 33.219 | 26.586 |
| compact | 16.047 | 7.140 | 4.397 | 27.164 | 20.523 |
| pandas | 41.894 | 42.036 | 5.227 | 132.164 | 34.375 |
| polars | 42.802 | 6.450 | 19.009 | 104.859 | 42.664 |
| duckdb | 85.782 | 61.432 | 42.657 | 172.969 | 50.750 |

Compact versus the historical checkpoint uses 8.3% less total CPU and 18.1% less absolute peak RSS. Compact uses 0.37 times Polars' total CPU in this case. Use the table to distinguish the read cost from the additional operation cost.

### Household energy, CSV read

Timing quality: qualified.

| Engine or storage | Total CPU, ms | Wall, ms | Operation CPU, ms | Peak RSS, MiB | Peak above baseline, MiB |
|---|---:|---:|---:|---:|---:|
| baseline | 269.661 | 120.883 | 0.005 | 422.414 | 415.711 |
| optional | 274.709 | 118.802 | 0.005 | 422.414 | 415.773 |
| compact | 282.887 | 121.229 | 0.005 | 314.164 | 307.523 |
| pandas | 1169.494 | 1169.920 | 0.006 | 406.094 | 308.094 |
| polars | 375.469 | 27.496 | 0.011 | 407.359 | 344.906 |
| duckdb | 739.760 | 72.826 | 0.013 | 572.352 | 497.320 |

Compact versus the historical checkpoint uses 4.9% more total CPU and 25.6% less absolute peak RSS. Compact uses 0.75 times Polars' total CPU in this case. Use the table to distinguish the read cost from the additional operation cost.

### Household energy, CSV read, stable sort, and matrix

Timing quality: qualified.

| Engine or storage | Total CPU, ms | Wall, ms | Operation CPU, ms | Peak RSS, MiB | Peak above baseline, MiB |
|---|---:|---:|---:|---:|---:|
| baseline | 480.973 | 231.966 | 210.881 | 739.148 | 732.445 |
| optional | 488.280 | 234.872 | 212.302 | 739.164 | 732.523 |
| compact | 459.632 | 238.967 | 179.346 | 504.250 | 497.609 |
| pandas | 1354.813 | 1355.521 | 205.362 | 941.883 | 844.172 |
| polars | 791.054 | 67.728 | 417.362 | 647.859 | 585.594 |
| duckdb | 1224.246 | 192.835 | 488.495 | 1125.453 | 1003.242 |

Compact versus the historical checkpoint uses 4.4% less total CPU and 31.8% less absolute peak RSS. Compact uses 0.58 times Polars' total CPU in this case. Use the table to distinguish the read cost from the additional operation cost.

## Keep deferred imports out of an algorithm comparison

The original first-use panel also contains 512 measured processes with exact outputs and passing duplicate controls. A follow-up diagnostic found 389 modules loaded during the DuckDB sort-and-matrix operation, including 293 pandas modules. The ordinary Arrow index conversion triggers loading, and a typed-buffer trial merely defers it to DuckDB registration. Changing the index representation does not remove that setup.

The primary tables above come from a separately recorded, full 16-round panel that completes that required import before timing. Output contracts, worker budgets, CPU and memory qualification limits, source heads, and all other adapters are unchanged. This is a scope correction, not a tolerance change. The original first-use observations remain in the archive and a separate audit.

| DuckDB sort-matrix case | First-use operation CPU, ms | Import-initialized operation CPU, ms |
|---|---:|---:|
| Aotizhongxin-default/sort-matrix | 190.648 | 42.657 |
| energy-common/sort-matrix | 640.830 | 488.495 |

The two panels occur at different times, so their entire difference is not assigned numerically to imports. The module trace establishes that the first panel includes deferred runtime loading. Neither panel measures a DuckDB sort kernel in isolation.

## Preserve qualification limits and remaining work

All 512 measured outputs match the exact preflight fingerprints. 4 of the four reference timing cases qualify. The quality report retains every failed control. This result does not overwrite earlier failed comparisons or certify unseen datasets.

The retained source and all test files exactly match the receipts for 431 Release, 431 Debug, and 431 Address Sanitizer test functions, each with zero failures or skips. No source change was retained this session, so those exact-source receipts remain applicable. The rejected child has its own fresh 431-test Release result. These are dataframe-module checks, not a claim that the complete MLX-dependent package passed.

The one-line all-missing shortcut remains an isolated candidate with substantial exceptional-case savings and a measured small common-input cost. Its focused source patch and review text are prepared separately. The reference panel evaluates the accumulated compact-storage and sorting branch, so it must not attribute its entire difference from the historical checkpoint to that one line.

Production promotion remains a review decision. Before submission, synchronize the intended source stack with upstream, run the required full-package and hosted checks, and keep engineering evidence on `codex/engineering-notes`. No source push or PR is part of this study.

## Evidence and reproduction

[Reference results and controls](comparison-audit.json), [precision confirmation](precision-decision.json), [rejected child comparison](boundary-decision.json), [retained source validation](retained-checkpoint-validation.json), [independent audit](independent-audit.json), and [review draft](review-draft.md) provide the compact records.

The [experiment archive](experiments.tar.gz) includes the controllers, Python adapter, Swift clients, contracts, raw measurements, disassembly, profiles, compiler commands, source snapshots, and test receipts. It excludes input CSV bytes, binaries, compiled objects, build caches, and xcresult bundles. Reproduction requires the recorded source checkout, dataset, dependency, and fixture paths. The archive preserves the commands and generators, but it is not a portable standalone benchmark package.

Run the archived `comparison-initialized/run.py preflight`, then `measure`, then `audit` in a fresh output directory. The script intentionally refuses to overwrite existing runs. `focused.py` and `precision.py` preserve the diagnostic and higher-replication protocols. The focused source diff is [archived separately](focused-source.patch.gz). [Artifact hashes](artifact-sha256.json) identify the delivered records.
