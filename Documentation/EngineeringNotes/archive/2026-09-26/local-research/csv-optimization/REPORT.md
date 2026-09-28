# CSV optimization results

Five production optimizations, one decimal-rounding fix, and one optional CPU/Metal experiment are committed locally on `codex/dataframe-pipeline-optimization`. HEAD is `4dc6b533dd`. No push or PR was made. The separate compact-column prototype and pre-existing untracked files remain untouched.

## Matched before and after

Native ARM64 Release on the M4 Max with 128 GiB unified memory. Both versions read the same warm-cache files through the public DataFrame API. Each side has 15 timed repetitions across three alternating process pairs, with two warmups per process.

| Rows | Before ms | After ms | Speedup | Before MiB | After MiB |
|---:|---:|---:|---:|---:|---:|
| 100,000 | 6.029 | 5.310 | 1.14x | 38.3 | 32.0 |
| 1,000,000 | 38.947 | 13.565 | 2.87x | 310.1 | 186.4 |

Memory is whole-process peak RSS sampled by the benchmark, including retained fixture arrays, results and allocator caches. It does not isolate column storage. The numeric comparison allows relative error of 1e-15 because the rounding fix deliberately corrects one-bit differences; dedicated tests check exact binary64 rounding and exact Int64 values above 2^53.

## Full production comparison

[Complete timings, memory, variation and methodology](/Users/LOCAL_USER/local-ai/spl/swiftsci/production-comparison/results/20260926T051154Z/REPORT.md). Raw results are beside that report. All 24 SwiftSci workload/size combinations passed value comparison. Kiraa native integer filtering failed the existing two parity checks and is excluded from rankings.

One-million-row medians from the fresh comparison:

| Operation | SwiftSci ms | pandas / Python ms | Kiraa ms | SwiftSci MiB | pandas / Python MiB | Kiraa MiB |
|---|---:|---:|---:|---:|---:|---:|
| CSV read | 13.484 | 67.621 | 9.080 | 186.5 | 321.7 | 253.3 |
| Float64 filter | 3.241 | 2.107 | 2.837 | 98.1 | 147.1 | 65.0 |
| Native integer filter | 3.753 | 1.833 | INVALID | 113.4 | 158.3 | INVALID |
| Int32 filter | 3.727 | 1.842 | n/a | 98.1 | 155.9 | n/a |
| Float32 filter | 3.775 | 2.261 | n/a | 98.1 | 144.4 | n/a |
| Stable descending sort | 35.706 | 28.405 | 58.511 | 136.6 | 201.6 | 80.3 |
| Single-key group sum | 4.635 | 4.762 | 9.277 | 75.5 | 138.2 | 67.7 |
| Two-key group sum | 11.132 | 10.100 | 36.096 | 99.6 | 199.7 | 77.1 |
| Filter, sort, group | 19.838 | 19.885 | 41.590 | 124.9 | 174.4 | 88.8 |
| Mean and sample variance | 0.587 | 0.614 | 0.588 | 75.3 | 134.5 | 53.4 |
| Correlation | 1.810 | 2.579 | n/a | 82.9 | 149.6 | n/a |
| Exponential smoothing and forecast | 12.557 | 391.630 | n/a | 98.4 | 328.7 | n/a |

The libraries use different physical types for inferred CSV numbers: SwiftSci preserves integer columns; Kiraa infers doubles. Fixture integer values fit exactly in doubles. Performance and memory rankings vary by operation; the table does not establish universal superiority.

## Commit decisions

| Commit | Change | Decision |
|---|---|---|
| `04eec07a0f` | Parallel scan of unquoted CSV | Keep. Large-file speed improves; quoted input falls back to the serial DFA. |
| `d7800e6c3d` | Two-word field metadata | Keep. Field stride falls from 24 to 16 bytes, preserving the public offset type. |
| `4ea0bdd334` | Standalone CPU/Metal indexing benchmark | Keep as an opt-in experiment. No GPU code runs in production CSV reads. |
| `259cc46e8f` | Round complete decimal significands once | Keep for correctness. It is not a measured speed win. |
| `f929f58a1e` | Count fields, then fill exact final arrays | Keep. Removes temporary chunk arrays and merge copies. |
| `0f4c4d1d72` | Count nulls during column construction | Keep. Removes a completed-column pass; timing benefit is small. |
| `4dc6b533dd` | Skip impossible numeric/null matches | Keep. Default null tokens cannot equal a successfully parsed decimal; custom numeric and Unicode tokens retain null-first handling. |

## Independent change measurements

These are separate paired experiments, each against the preceding implementation. Background load varied, so do not add their gains. The matched overall test above measures the combined effect.

| Change | Before ms | After ms | Before MiB | After MiB |
|---|---:|---:|---:|---:|
| Parallel scan | 41.345 | 24.323 | 310.0 | 342.3 |
| Packed metadata | 22.055 | 22.431 | 346.9 | 294.6 |
| Decimal rounding | 21.070 | 21.425 | 292.0 | 290.2 |
| Exact allocation | 21.868 | 21.038 | 286.9 | 186.5 |
| Fused null count | 24.261 | 23.837 | 186.6 | 186.5 |
| Numeric/null shortcut | 20.601 | 13.578 | 186.5 | 186.4 |

The first two decimal candidates were slower. Outlining the long-number fallback reduced the full-read difference to about 1.7%. A focused conversion benchmark still found the new parser slower for this fixture, whose numbers mostly have two fractional digits. We kept correct rounding explicitly rather than labeling it a speed improvement. The constant-switch experiment was rejected.

## CPU and memory design

The parallel path starts at 4 MiB and uses at most eight workers. Those are conservative dispatch choices, not universal optimal thresholds. Chunk boundaries follow line endings. A quote in any chunk discards the counts and invokes the existing serial state machine. LF used as delimiter or quote also takes the serial path.

Each worker first counts its complete records. Prefix sums assign disjoint slices of the final field and row arrays. Workers initialize only their own field slices, and all work joins before the mapped input or borrowed output pointers expire. The final row sentinel is written after the worker phase. No chunk field arrays coexist with a merged copy.

Internal field metadata stores the quote flag in the sign of a complemented nonnegative length. This preserves the entire nonnegative Int length range and keeps each entry to two machine words. Public CSVFieldOffset and TypedColumn APIs are unchanged. Numeric column storage remains optional arrays. Promoting the separate values-plus-validity-bitmap prototype requires migrating downstream consumers together; materializing optional arrays at each compatibility access would lose its benefit.

## GPU result

GPU classification was faster than serial NEON classification, but usable field-index construction was slower than parallel NEON: 7.671 versus 6.485 ms at one million rows, and 30.824 versus 25.427 ms at four million. These are index-only measurements with the historical field layout, separate from the complete CSV comparison.

The GPU experiment includes buffer allocation, command submission, synchronization and CPU index materialization. Mapped input avoids a copy but still loses by 18–21%. The installed Metal compiler rejects double, so scientific Float64 conversion stays on the CPU. No Float32 substitution was made.

[Benchmark source and reproduction instructions](/Users/LOCAL_USER/Documents/src/SwiftSci/Benchmarks/CSVAcceleration/README.md). [Raw GPU evidence](/Users/LOCAL_USER/local-ai/spl/swiftsci/csv-optimization/gpu/README.md). A future GPU design could retain packed indexes in shared GPU buffers and avoid CPU array materialization. That belongs with the separate compact-storage work.

## Validation

- Full Debug suite: 884 tests passed, zero failures, zero skips; MLX included.
- Full Release suite: 884 tests passed, zero failures, zero skips; MLX included.
- Each full suite contains 968 device-level executions after parameter expansion.
- Address and thread sanitizers each passed 764 parser cases over 87,060,376 input bytes. These standalone checks use the current source in an unoptimized instrumented build; they cover pointer bounds and races, not leak detection.
- Parser checks cover ragged records, CRLF, quotes, escaped quotes, quoted newlines, EOF handling, custom delimiters and 400 deterministic randomized byte fixtures.
- Decimal checks compare binary64 bit patterns, a 10,000-number corpus, long decimals, scientific notation, signed zero, overflow/underflow and integer typing above 2^53.
- GPU experiment passed 108 small equivalence cases and every field/row comparison on both full input files.

[Sanitizer sources, scripts and captured results](/Users/LOCAL_USER/local-ai/spl/swiftsci/csv-optimization/sanitizers).

[Debug result](/Users/LOCAL_USER/local-ai/spl/swiftsci/full-suite-validation/debug-20260926T050909Z-MJkgg3/summary.json). [Release result](/Users/LOCAL_USER/local-ai/spl/swiftsci/full-suite-validation/release-20260926T051001Z-xoLATq/summary.json).

## Limits

Other applications were using several CPU cores during these runs. Measurements use serial rotating processes and warmups, but small differences remain sensitive to background load. No unrelated process was stopped.

The main CSV fixture has three numeric columns and no quoted fields. The large speedup should not be assumed for heavily quoted or wide text files; their correctness paths are tested, but equivalent throughput claims have not been measured.

Inherited integer-parser overflow, sampled type inference after the first 1,000 rows, and the existing unfinished trailing-delimiter behavior remain outside these changes. The parser tests preserve existing EOF behavior rather than claiming full RFC compliance.
