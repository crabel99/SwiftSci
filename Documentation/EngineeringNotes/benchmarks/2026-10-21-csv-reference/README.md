# Original reference-file CSV comparison

The compact parser benefit survives original scientific files. Across the twelve Beijing station files, the final scoped candidate reduces paired median CPU time by 23.8 to 31.5%, elapsed time by 6.2 to 9.0%, and process peak RSS by about 35%. The 2.08-million-row unquoted household-energy file is effectively neutral. Held output heap is unchanged for both datasets.

This supports retaining the scoped candidate for production integration review. It does not establish a universal CSV speedup or smaller finished DataFrames. Automatic inference fails on these original files in the reference and both candidates; the failed modes are excluded from performance conclusions.

## Compared implementations

- Reference: production source at `546510bb7df19fc87a664bded5947c738011ee1d`.
- Packed: the earlier bounded compact field-index candidate.
- Scoped: compact metadata plus synchronous borrowed field views selected once per column.

All use the same compiler settings, dependencies, public `DataFrame(csv:options:)` call, input bytes, schema knowledge, and validator. Source hashes, module-object hashes, dependency-object hashes, link commands, and executable fingerprints are preserved in the evidence. The modules are reused from the verified [scoped CSV experiment](../2026-10-21-csv-borrow/README.md). Their source and object fingerprints were rechecked. No production source changed in this experiment.

## Original datasets

| Dataset | Original files | Rows | Shape and parsing path |
|---|---:|---:|---|
| [UCI household electric power consumption](https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption) | 1 | 2,075,259 | 9 columns, semicolon separated, CRLF, no quotes; existing flat unquoted path |
| [UCI Beijing multi-site air quality](https://archive.ics.uci.edu/dataset/501/beijing+multi+site+air+quality+data) | 12 | 35,064 each, 420,768 total | 18 columns, quoted headers/string fields; fallback scan, compact storage in both candidates |

The archives were downloaded on 2026-10-21. Source URLs, archive and extracted-file hashes, encoding, delimiters, observed quotes, null counts, schemas, and sizes are in `provenance.json` and `cases.json`. Thirty-nine diagnostic parser runs confirmed the storage paths and record counts. The original files were not concatenated, requoted, cleaned, resampled, or reordered. Auxiliary JPG and sample CSV files in the air-quality outer archive were inventoried but excluded from the twelve original station-file workload. Dataset bytes are not committed.

Both datasets are CC BY 4.0. Attribution: Hebrail, G. and Berard, A., 2006, [Individual Household Electric Power Consumption](https://doi.org/10.24432/C58K54); Chen, S., 2017, [Beijing Multi-Site Air Quality](https://doi.org/10.24432/C5RK5G).

## Correctness and schema contracts

Python standard-library CSV parsing independently produced SHA-256 hashes for every output column. The representation tags nulls, includes string byte lengths and exact UTF-8 bytes, and encodes numeric values as little-endian IEEE 754 binary64. Every integer in these files is exactly representable in binary64. Swift verifies column order, names, row counts, allowed output types, and every value/null position against these hashes after every read. The final audit also checks explicit per-column null counts. No approximate numeric tolerance is used. Python is the correctness oracle here, not a timed competitor.

Energy measurements use Double; Date and Time remain original strings. Both `?` and empty fields are explicit null tokens, matching the actual source bytes. The numeric-inference mode still supplies the same two timestamp overrides and is labeled separately; it is not full inference. The seven measurement columns each contain 25,979 missing values.

Air-quality supplied schemas use Int64 for row number/year/month/day/hour, Double for measurement columns, and String for wind direction/station. `NA` and empty fields are nulls. Known schemas are identical across all three variants.

### Existing failures retained as failures

- All twelve air-quality files fail full inference in all three variants. Sampling the first 1,000 rows chooses Int64 for particulate columns that contain later fractional values. Those values become null. The total is **398 additional, incorrect nulls** per variant. Wanliu infers PM10 correctly but still loses fractional PM2.5 values. No failed inference timings enter the accepted performance results.
- A public-read diagnostic on the first 25,000 original energy rows fails the documented day/month/year interpretation in all three variants. A separate direct reproducer shows `2/1/2007` becomes February 1 rather than January 2. All variants return identical hashes that disagree with the UCI schema. Follow-up inspection of `Date.parse(from:)` and `DateTimeTests.testAmbiguousDates` established that month-first precedence is intentional. Calling this a parser defect was incorrect. Timestamp conversion is excluded from the accepted performance contract by retaining both fields as text. This is an explicit schema choice, not a claim that date inference is correct.

`failure-inventory.json`, `audit.jsonl`, `date-audit.jsonl`, and `date-example.json` retain the failures, first fractional source rows, extra null counts, and reproducer results. The numeric failures require a repair. The date mismatch requires callers to specify the source convention; the measured default behavior matches its documented contract. They do not originate in the compact index or scoped access changes.

## Measurement method

Apple M4 Max with 128 GiB, macOS 27.0.1, Swift 6.4 and Xcode 27.0. Release optimization with whole-module compilation, arm64 macOS 14 deployment target. AC power was confirmed at the start and end. CPU execution uses native parallelism under normal desktop activity; no equal-worker cap or cooldown requirement was imposed.

For each of fourteen valid file/mode cases, all six permutations of the three variants run once in fresh processes. Each timing process has two warmups and three measured calls. Three separate fresh-process memory rounds rotate execution order and use one read with no warmup. Totals: 378 accepted workers, 756 timing samples, and 126 memory samples. There were also 78 preflight workers, including 36 expected failures, three failed date diagnostics, and 39 successful parser-storage diagnostics.

CPU time is summed user plus system time, not FLOPs or energy. Elapsed and CPU intervals include the public read and output release. Full validation occurs between those intervals and is excluded. Memory is sampled while the output is held, before validation. Process peak RSS is a high-water measurement; held heap is the increase in malloc bytes in use, not a census of every allocator. Source download, decompression, and oracle creation are outside measurements. Files are page-cache warm, so this does not measure cold storage throughput.

Each displayed duration is the median of per-process sample medians. Percentage changes use the median of six within-round candidate/reference ratios, which need not equal the ratio of the displayed overall medians. All valid samples are retained. Full ranges and individual measurements are in the evidence.

## Results against production

All air-quality rows below use supplied schemas. Energy inference means numeric inference with Date and Time fixed as text. Memory values are MiB.

| File/mode | CPU ms, reference → scoped | Paired CPU change | Elapsed ms, reference → scoped | Peak RSS, reference → scoped | Held heap, reference → scoped |
|---|---:|---:|---:|---:|---:|
| energy / known | 404.76 → 400.28 | -1.3% | 96.42 → 97.09 | 720.14 → 720.11 | 285.06 → 285.06 |
| energy / infer | 397.23 → 400.01 | -0.1% | 91.59 → 96.41 | 720.19 → 720.19 | 285.06 → 285.06 |
| Aotizhongxin | 16.64 → 11.92 | -28.7% | 6.19 → 5.70 | 39.70 → 25.73 | 9.86 → 9.86 |
| Changping | 16.48 → 11.52 | -30.2% | 6.03 → 5.66 | 39.48 → 25.61 | 9.86 → 9.86 |
| Dingling | 16.59 → 11.39 | -31.5% | 6.03 → 5.60 | 39.44 → 25.58 | 9.86 → 9.86 |
| Dongsi | 16.08 → 11.48 | -28.9% | 6.11 → 5.65 | 39.42 → 25.58 | 9.86 → 9.86 |
| Guanyuan | 16.29 → 11.46 | -29.4% | 6.02 → 5.59 | 39.42 → 25.56 | 9.86 → 9.86 |
| Gucheng | 15.70 → 11.44 | -26.5% | 6.05 → 5.64 | 39.47 → 25.58 | 9.86 → 9.86 |
| Huairou | 15.92 → 11.44 | -28.1% | 5.89 → 5.43 | 39.34 → 25.52 | 9.86 → 9.86 |
| Nongzhanguan | 16.08 → 12.23 | -23.8% | 6.26 → 5.75 | 39.59 → 25.73 | 9.86 → 9.86 |
| Shunyi | 16.17 → 11.54 | -28.4% | 5.92 → 5.58 | 39.44 → 25.59 | 9.86 → 9.86 |
| Tiantan | 15.80 → 11.33 | -28.7% | 6.02 → 5.59 | 39.42 → 25.62 | 9.86 → 9.86 |
| Wanliu | 16.02 → 11.29 | -29.9% | 6.15 → 5.68 | 39.39 → 25.56 | 9.86 → 9.86 |
| Wanshouxigong | 16.31 → 11.39 | -29.2% | 6.16 → 5.80 | 39.66 → 25.81 | 9.86 → 9.86 |

The energy supplied-schema paired CPU ratio ranges from 0.974 to 1.000, with a median improvement of 1.3%. Numeric-inference CPU is neutral at −0.1%, and elapsed time is 3.0% higher. These small results do not support claiming a useful energy-file speedup. Every air-quality file improves CPU work in every timing round; its paired CPU ratio ranges are recorded below.

## What scoped access adds beyond compact storage

The earlier packed candidate already provides the memory reduction. Scoped access keeps that memory behavior and usually reduces CPU work further. Some incremental pair ranges cross 1.0, so the additional speed difference is not equally well resolved for every file.

| File/mode | CPU ms, packed → scoped | Paired CPU change | Packed-to-scoped CPU ratio range | Production-to-scoped CPU ratio range |
|---|---:|---:|---|---|
| energy / known | 403.79 → 400.28 | -0.8% | 0.973 to 1.004 | 0.974 to 1.000 |
| energy / infer | 406.83 → 400.01 | -1.7% | 0.963 to 0.997 | 0.982 to 1.010 |
| Aotizhongxin | 12.14 → 11.92 | -2.0% | 0.916 to 1.008 | 0.671 to 0.741 |
| Changping | 12.09 → 11.52 | -5.8% | 0.886 to 1.017 | 0.675 to 0.764 |
| Dingling | 12.23 → 11.39 | -6.7% | 0.914 to 0.959 | 0.670 to 0.760 |
| Dongsi | 11.84 → 11.48 | -3.1% | 0.933 to 0.987 | 0.682 to 0.748 |
| Guanyuan | 12.07 → 11.46 | -6.7% | 0.869 to 1.005 | 0.686 to 0.716 |
| Gucheng | 11.85 → 11.44 | -2.7% | 0.873 to 0.999 | 0.704 to 0.757 |
| Huairou | 11.75 → 11.44 | -3.1% | 0.938 to 0.975 | 0.706 to 0.725 |
| Nongzhanguan | 12.12 → 12.23 | -0.4% | 0.912 to 1.055 | 0.676 to 0.803 |
| Shunyi | 12.25 → 11.54 | -6.9% | 0.873 to 0.973 | 0.667 to 0.743 |
| Tiantan | 11.67 → 11.33 | -4.4% | 0.935 to 0.998 | 0.699 to 0.742 |
| Wanliu | 11.83 → 11.29 | -3.9% | 0.917 to 0.976 | 0.684 to 0.747 |
| Wanshouxigong | 11.96 → 11.39 | -4.3% | 0.901 to 0.999 | 0.644 to 0.740 |

## Engineering decision

Retain the scoped candidate for a focused production integration review. The real quoted files improve CPU work, elapsed time, and temporary peak memory together, which meets the resource-efficiency direction without requiring a speed-versus-memory switch for these workloads. The unquoted file keeps its original storage path and remains effectively neutral.

Do not describe the memory savings as smaller retained DataFrames. Held heap is unchanged on every real file. The prior synthetic held-memory reduction depended on allocator reuse after discarded parser allocations and is not universal. These results do not prove energy savings, SRAM/cache behavior, or a larger-than-2-GiB file benefit.

The actual-reference comparison gate is complete for the stated schemas. Production integration still needs a focused code review and its normal validation. Full inference is not cleared. Preserve the numeric defect and the source-date-format mismatch as separate follow-ups. The previously recorded fallback, sanitizer, parser parity, streaming, and scoped-lifetime evidence remains relevant; this run does not replace full SwiftSci tests or hosted CI.

## Integration follow-up

The [production integration record](../2026-10-21-csv-integration/README.md) documents the local branch, review, Debug/Release/sanitizer results, line coverage, standard conformance checks, and a bounded original-data confirmation on the committed implementation. The numeric-inference repair and explicit date-format feature remain separate follow-ups. The measurements above retain their original source fingerprints.

## Evidence and replay

- [Evidence archive](evidence.tar.gz): preparation/build/run/validation scripts, Swift probes, source patches, source/build receipts, original-data provenance, independent oracles, all accepted workers, failed-mode diagnostics, parser-path diagnostics, and summary tables.
- [Archive manifest](evidence-sha256.json): SHA-256 for every archived member and the archive.
- [Validation receipt](verification.json): accepted-worker counts and integrity checks.
- [Previous controlled experiment](../2026-10-21-csv-borrow/README.md): source design, compiler evidence, safety checks, and synthetic controls.

The scripts retain the exact local cache paths used for this measurement. Replay first prepares the three source/module variants from the previous experiment, then runs `download.py`, `oracle.py`, `build.py`, `audit.py`, `date-audit.py`, `path-check.py`, `run.py`, `summarize.py`, and `verify.py` from a fresh experiment directory after adjusting the module-cache root in the scripts. Downloads and module builds must finish before timing. Existing result directories are exclusive so reruns cannot overwrite accepted measurements. This is a reproducible local experiment with recorded toolchain/dependency inputs, not a newly integrated portable benchmark command.

## Date-contract correction

The follow-up [explicit date-format record](../2026-10-21-csv-date-format/README.md) distinguishes the UCI source convention from SwiftSci's documented default. Historical diagnostics, hashes, timings, and archived evidence remain unchanged. A failed comparison against the source convention is still excluded from performance claims.
