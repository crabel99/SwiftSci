# Owned Arrow import with chunk traversal

Date: 2026-10-06. Commit: `fafa07a3de4b489636c89db42616b8f89c770082` on local branch `codex/arrow-chunk-import`. Parent: `299221aab3865c57f8220bc8f2f03854708c6c65` on `codex/memory-library-reuse`. The retained-view experiment remains separate on `codex/arrow-retention-trial`.

## Change and scope

The owned import now visits each Arrow chunk once for Int32, Int64, Float, Double, Bool, and String columns. A shared private helper replaces repeated per-type loops, and null replacement is chosen once per column. The production bridge loses 37 lines overall. The public API, returned concrete TypedColumn types, owned values, and null policies remain unchanged.

The previous global-row subscript searched chunks again for each value. With the pinned Arrow 21.0.0 implementation, an empty chunk also makes the unsigned `len - 1` calculation invalid. Chunk traversal avoids both the repeated search and that crash. Strings retain their existing decoder; this patch does not introduce raw-buffer reads or another allocator.

The existing date32 path is unchanged. Its representation mismatch is a separate issue described below. This patch therefore does not claim to repair every Arrow logical type.

## Regression evidence

Before changing production code, the new empty-chunk test and the parameterized mixed-boundary test crashed. The all-empty and owned-snapshot tests passed. The two crashes were recorded by Xcode as `DataFrameArrowChunkTests/emptyChunks()` and `DataFrameArrowChunkTests/nullStrategies(_:)`. Inspection of the dependency identifies the unsigned chunk-length calculation; the optimized crash summary itself has deduplicated symbols rather than a precise source location.

After the patch, the complete SwiftDataFrame test target passed in Release: 266 test definitions and 357 executions including dynamic parameters, with zero failures or skips. This includes existing dataframe, Arrow, Feather, matrix, CSV, JSON, and Parquet coverage in that target. The new checks cover leading, middle, and trailing empty chunks; all-empty columns; differing chunk boundaries; exact integer extremes and values above 2^53; valid NaN versus null; signed zero; infinities; Boolean values; Unicode strings; all three null strategies; and isolation from later producer writes.

The initial library scheme did not support testing, and the first method selector ran zero tests. Neither was treated as validation. The suite selector produced the failing-before evidence, and the target selector produced the successful final run.

The full multi-module SwiftSci test suite was not run. The package build compiled its dependencies, but execution was restricted to the dataframe target. No new public API or documentation build was needed.

## Production comparison

The baseline and patched workers use the same benchmark code from the retained-view trial. The only production source difference is `Sources/SwiftDataFrame/Internal/ArrowTableBridge.swift`. The experimental source and target were added only to the isolated measurement snapshot, not this implementation branch.

Each worker starts fresh, warms its code on a small input, then imports the same four-column Arrow input, selects rows, gathers the selected values, and constructs a checked row-major Double matrix. Timing excludes fixture construction, memory sampling, and correctness validation. Repeated cases select once and repeat matrix extraction. This measures amortization, not a recommendation to rebuild an unchanged matrix.

Median milliseconds over three rounds, with before/after order alternated. All 42 workers passed complete-output checks against the deterministic oracle.

| Workload | Before | After | Speedup |
| --- | ---: | ---: | ---: |
| 1k rows, one chunk | 0.199 | 0.061 | 3.23× |
| 100k rows, no missing values | 18.399 | 5.017 | 3.67× |
| 1M rows, one chunk | 184.873 | 48.634 | 3.80× |
| 1M rows, 32 chunks | 823.544 | 48.830 | 16.87× |
| 1M rows, 32 chunks, sparse selection | 826.658 | 42.559 | 19.42× |
| 100k rows, five extractions | 33.898 | 5.140 | 6.59× |
| 1M rows, ten extractions | 219.484 | 83.150 | 2.64× |

The one-million-row import allocation remains 64,029,856 additional malloc bytes in both versions. The patch accelerates owned import; it does not provide the retained trial's memory savings. Dense matrix output still allocates and keeps the current Int64-to-Double conversion semantics.

The large chunked speedups reflect the removed per-row chunk search. These are in-memory Arrow import and dataframe-to-matrix results, not CSV parsing, Arrow file I/O, arbitrary dataframe workloads, or whole-application speedups. The benchmark uses two Double and two Int64 columns. Float, Boolean, and String compatibility is covered by tests, not a separate performance survey.

## Reuse decision

This compatible change captures much of the earlier trial's benefit using the pinned Arrow library's chunk accessors and existing Swift arrays. It adds no storage class, allocator, unchecked Sendable conformance, or ownership-transfer contract. Keep it independent of any future retained-view API.

A retained view remains an option for callers that can guarantee producer immutability and want to avoid the additional owned copy. That API still needs an explicit imported-C owner contract, slice-retention policy, and concurrency boundary. The current patch does not change those decisions.

## Separate date32 follow-up

Source inspection found that the bridge requests `ChunkedArray<Date32>`, where Arrow defines Date32 as Int32. Arrow 21.0.0's canonical Date32Array instead derives from `ArrowArray<Date>`, and its builder emits that representation. ArrowColumn.data performs a forced generic cast. These declarations do not match.

The dependency's Date32Array accessor also reads UInt32 and multiplies by 86,400 before constructing a Date, while its builder writes signed Int32 days. Negative dates and sufficiently distant positive dates therefore need dedicated validation. These findings were not runtime-reproduced or repaired in this patch. Follow up with a focused date32 regression, including pre-epoch dates, nulls, and range boundaries, before claiming date32 compatibility. Keep that fix as a separate commit and distinguish any dependency defect from SwiftSci's bridge mismatch.

## Evidence and provenance

Baseline worker SHA-256: `007191b829159b32c2024dd14d5d025350c0bec98da3c8e6049a54aad4e2942e`. Patched worker SHA-256: `3c6ada0f609de3cc99c846104d2386bf8e83f77ceb26577ccab75e1aec93f2b3`. The baseline matches the preserved Release trial worker. Test and benchmark snapshots match the committed production source. The benchmark controller and build scripts remain with the local evidence, and compact results are archived on the engineering-notes branch.

The measurement environment is the same Apple M4 Max, 128 GiB RAM, macOS 27.0, Xcode 27.0, Apple Swift 6.4 system used for the retained Arrow trial. Workers ran sequentially with normal memory pressure. The minimum package deployment target remains macOS 14; actual execution on macOS 14 was not validated here.

Build snapshots contained tracked files and the explicit regression file only. Unrelated cloud-sync duplicates remained untouched. The shared integration benchmark executable was restored to its preserved fingerprint after the package test build relinked it. No push or PR was performed. Engineering reports and decisions remain solely on `codex/engineering-notes`.
