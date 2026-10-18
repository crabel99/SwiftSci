# CPU and memory costs of four merged optimizations

Measured October 18, 2026 after the [27-PR resource audit](../2026-10-18-pr-resource-audit/README.md). This first matched study covers PRs #39, #45, #70, and #82. It uses 19 cases and 342 fresh worker processes, with complete expected-value checks. Five paired timing rounds and three independent memory rounds preserve all samples.

## Result

The measured changes generally reduce CPU consumption as well as elapsed time. The largest memory improvements come from removing temporary materialization. Parallel execution did not automatically make these operations more expensive: in the tested CSV and gather workloads, total process CPU time fell.

This qualifies the listed operations and inputs. It does not establish a single efficiency score for SwiftSci, sustained capacity under a fixed memory budget, or GPU/Neural Engine resource use. Other PRs in the audit remain covered by their historical evidence. These are controlled before/after source comparisons for individual PRs, not an aggregate comparison of an old release with current main.

| Operation | Total CPU ms, before → after | Paired CPU reduction | Process peak MiB, before → after |
| --- | ---: | ---: | ---: |
| CSV inference, 1M rows × 4 | 293.766 → 56.163 | 81.0% | 548.28 → 162.36 |
| Quoted CSV inference, 1M × 4 | 276.910 → 52.805 | 80.9% | 555.89 → 244.17 |
| Target extraction, 1M rows | 36.948 → 0.557 | 98.5% | 190.02 → 136.36 |
| Compact selection plus matrix, 16,384 × 128 source | 4.945 → 1.624 | 66.5% | 73.12 → 74.83 |
| Compact selection plus matrix, 512 × 2,048 source | 4.294 → 0.867 | 79.7% | 50.84 → 50.84 |
| MLP prediction, 4,096 × 32 | 2.305 → 0.402 | 82.6% | 9.34 → 9.25 |
| MLP prediction, 4,096 × 128 | 5.493 → 1.747 | 68.2% | 14.30 → 14.23 |

CPU totals sum process user and system time across threads. Timings include the API call and result release, with validation outside the clock. Reported CPU reductions use medians of paired ratios, so they need not equal a ratio of the displayed medians. Peak RSS includes input preparation and runtime/allocator history. It is not a measure of exclusively owned output memory.

The unchanged flat-matrix controls remain near parity. The one-row MLP case has a median CPU ratio of one and an observed range from 1.000 to 1.375. Its roughly nine-microsecond duration is too small for an efficiency conclusion with these counters. No threshold was changed to hide it.

All cases, wall times, held-output heap deltas, and paired CPU ranges are in [the complete results](RESULTS.md). [Machine-readable summaries](summary.json) include raw-record hashes.

## What the memory measurements mean

For unquoted million-row CSV, the final retained heap delta is about 61.3 MiB both before and after. The process peak drops by about 386 MiB. The saving comes from constructing that output with fewer temporary allocations, rather than returning a smaller logical result. CPU time also drops by about 81%, so the measured workflow improves on both resources.

Target extraction returns the same 7.64 MiB vector on both sides. Before #45, the implementation constructs a nested one-column matrix and then extracts the vector. Removing that intermediate lowers process peak by about 53.7 MiB at one million rows and removes about 98.5% of measured CPU time. The eight-column source itself still occupies about 122 MiB of live malloc storage. That common source limits the apparent percentage reduction in whole-process peak.

Two tradeoffs remain visible:

- Quoted CSV retains about 70.54 MiB of additional heap after the call, compared with 61.30 MiB before. A separate [capacity inspection](quoted-csv-capacities.json) found one returned column with capacity 1,605,630 for 1,000,000 values; the other columns and baseline use capacity 1,000,446. The extra 605,184 optional-Double slots at 16 bytes each account for about 9.23 MiB. Releasing the output returns live heap near the same runtime baseline. This is retained spare capacity, not evidence of an owner leak. Peak process memory is still about 56% lower and CPU time about 81% lower.
- Compact selection plus packing at 16,384 × 128 uses about 66.5% less CPU time but raises process peak about 1.7 MiB. Held-result heap is unchanged at about 10.67 MiB. The measurements do not isolate the extra process residency as live scratch, allocator retention, or thread/runtime state. The wide 512-row case does not activate the new gather threshold and still saves about 80% CPU time, supporting a benefit from reduced copying/packing work as well as parallel execution.

The three ordinary dataframe gathers use about 14–22% less CPU time with nearly unchanged held output and process peak. Their result storage is determined by the same selected rows and schema on both sides. Their improvement is mainly execution cost, within this measurement scope.

## Measurement contract

The [plan](PLAN.md) was written before measurement. [Revision identities](revisions.json) identify exact first-parent/merge source pairs. Every changed production module was rebuilt with the installed Swift 6.4 compiler, `-O`, whole-module optimization, and an arm64 macOS 14 deployment target. Both sides use identical dependency objects within each pair. Those fixed objects need not match the historical package resolver state. The study isolates the changed source under a common dependency/compiler environment; it does not recreate the historical release build.

The host is an Apple M4 Max on AC power. Native CPU scheduling is retained. Thread-count overrides are removed. This does not pin work to performance or efficiency cores and does not measure energy. All eight binaries were checked for the listed LLVM coverage, AddressSanitizer, and ThreadSanitizer runtime symbols; none was present. No build or other benchmark overlapped these runs.

Each timing process performs two warmups and seven measured operations. Five before/after pairs rotate order. Each memory process performs one operation without a warmup; three pairs run separately. CPU counters are taken around the call and around output release. Every expected output value and shape is checked outside those intervals. Both CSV versions infer the schema from the same file bytes, including quotes; filesystem cache is warm. No engine receives a supplied-schema advantage.

Gathering selects and reverses the two-thirds of rows not divisible by three. Compact cases include selecting those rows and materializing the final row-major matrix. Source dimensions are shown in the tables. Numeric values are exactly representable Doubles. No missing-value or mutation-performance claim follows from this fixture family.

MLP comparisons use the existing row-input CPU prediction API, with two ReLU hidden layers of widths P and P/2. Both versions train the same eight rows for one iteration using seed 42, outside prediction timing. Trained-weight and scalar-oracle fingerprints match between every paired process. Every output meets the predeclared `1e-10 * max(1, abs(reference))` bound against an independent scalar forward calculation. This does not measure preprocessing, training, recurrent models, arbitrary activation choices, or accelerator execution.

Live heap comes from `malloc_zone_statistics` and excludes allocations outside malloc. It is sampled before the operation, while the output is held, and after release. It is not a complete allocation/copy trace. Process peak is captured before output validation, but includes earlier source preparation. Original raw records preserve call and release costs separately. Observed ranges are not confidence intervals.

## Consequences for the design

Preserve these measured reductions. In this study, the earlier concern that parallelism might merely exchange more CPU work for lower latency is not supported for the CSV, gather, or batched-prediction cases. Fewer intermediate objects, better packing, and fewer numerical calls can reduce both CPU and memory even when more threads participate.

The immediate memory follow-up is quoted-CSV capacity growth. Profile the builder's reservation and type-promotion behavior before proposing a trim, because trimming itself copies data and can increase peak memory. The compact gather's small peak increase also needs allocation-level attribution before changing its worker policy.

Next resource qualification should cover repeated and churned prediction caches, source retention for tiny selections, and fixed-rate concurrent callers. Those address the optional speed/storage tradeoff in #83 and the saturated-tail observation in #82. GPU and Neural Engine comparisons need device-aware work accounting; host CPU alone is insufficient. Do not combine this study's PR ratios or multiply them into a library-wide speedup.

## Evidence and reproduction

The [evidence archive](evidence.tar.gz) preserves all 342 worker records, build commands and fingerprints, source signatures, host settings, and the separate capacity diagnostic. [Archive integrity](integrity.json) records hashes. The source bodies are recoverable from the pinned Git revisions. Generated CSV fixtures are recoverable from `prepare.py`; their byte hashes are recorded in `cases.json`.

The scripts are retained on the engineering-notes branch. `prepare.py` copies them to a new study directory and extracts the exact sources from a local SwiftSci Git repository. `build.py` and `build-mlp.py` use the existing Release dependency products and package headers identified in their configuration. Matching those object hashes is required to reproduce this exact binary environment; a rebuilt dependency environment creates a new qualification run.

```sh
python3 prepare.py --repo /path/to/SwiftSci --output /path/to/new-study
python3 /path/to/new-study/build.py pr39-before pr39-after pr45-before pr45-after pr82-before pr82-after
python3 /path/to/new-study/build-mlp.py pr70-before pr70-after
python3 /path/to/new-study/run.py
python3 /path/to/new-study/summarize.py
```

No production source, thresholds, or public PR descriptions changed. These measurements remain private engineering evidence until a contribution needs their bounded claims.

## Verification

All 342 worker records passed expected-value checks. Each MLP pair has identical trained-weight and scalar-oracle fingerprints. Every compiled production source file matches its pinned Git blob, and dependency object hashes match within each pair. The evidence archive verifies all 373 members. Replaying fixture preparation reproduces all three CSV byte hashes. Python scripts parse successfully, document links resolve, and the notes pass the Git whitespace check. No full library test-suite claim is made for this supplemental benchmark.
