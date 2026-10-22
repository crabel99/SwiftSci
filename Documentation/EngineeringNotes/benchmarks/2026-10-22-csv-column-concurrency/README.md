# CSV column conversion: CPU time versus elapsed time

Commit `9c067c6c5116d78c0849073acea7fb150404efab` adds an explicit serial column-conversion mode on `codex/csv-column-concurrency`. The parallel default remains unchanged. Eager and streaming reads share the scheduling decision. Both execute the same conversion code and preserve their existing row-batch bounds.

The change gives callers a resource choice. Serial conversion used less process CPU time on the tested multi-column reference data, but took longer to finish. These measurements do not establish energy use or instruction counts.

## Why this investigation changed direction

The earlier supplemental wider-file comparison exceeded the 10% CPU review threshold. A new 24-round paired reproduction measured a smaller gap of 5.3%. Both observations remain in the evidence. The gap is variable, so this work does not claim that a repeatable 10% regression was fixed.

The Aotizhongxin reference file has 18 columns and 140,130 quote bytes. The original retained-index reader therefore falls back to its compact serial parser. Its unquoted parallel-index path does not explain this comparison.

Instrumented current-source stages measured median CPU times of 0.481 ms for the extra row-count pass, 2.429 ms for field framing, and 8.981 ms for conversion together with joined worker coordination. Instrumentation changes execution and is excluded from acceptance timings. These stage measurements identify where to experiment. They do not isolate the exact cost of the system scheduler, allocations, cache behavior, or CPU frequency.

## Alternatives tested

1. A SIMD quote-parity row counter passed 153,645 count-versus-index checks. It increased CPU time in the full reads, including large energy inputs, so it was rejected.
2. Pairing adjacent columns reduced process CPU time on several inputs, but increased elapsed time on the energy file.
3. Pairing separated columns and grouping four columns also reduced CPU time on some inputs. The useful grouping depends on width and column costs. These trials remain experiments.
4. Serial conversion removed worker dispatch from column conversion. It produced the lowest CPU time on most tested multi-column inputs, with a clear elapsed-time cost.

Generated fixtures cover 1, 2, 4, 8, 18, and 64 columns, with 257 and 32,769 rows. They mix native integers, doubles, strings, nulls, quoted fields, and embedded line endings. Real reference inputs include bike sharing, two Beijing air-quality stations, and household power consumption. Late Boolean and text fallback cases remain in the comparison.

No grouping heuristic or larger batch became the default. Coordinate-capacity reuse was not independently tested in this segment and remains an open hypothesis.

## The public choice

```swift
var options = CSVReadOptions()
options.columnConversionMode = .serial
let frame = try await DataFrame(csv: url, options: options)
```

The same option works with `DataFrame.readCSVStream`. Omit it or select `.parallel` to retain native system parallelism for column conversion. Serial applies to conversion within each read. It does not pin the process to a core, constrain unrelated work, change type inference, or retain more field coordinates.

`CSVColumnConversionMode.forEachColumn` owns the scheduling decision. The eager initial batch, later batches, fallback retries, and streamed column construction use it. The enum has two cases with defined behavior. Experimental group sizes are not exposed as tuning parameters.

## Final reference comparison

Each row compares the same source bytes, row selection, schema mode, native output types, null positions, values, and order. Each process validates output against independent per-column hashes. Full-file timings include output release. Streaming timings use immediate consumption and a separate full-output validation repeat.

| Read, input, schema | Original CPU ms | Parent CPU ms | Parallel CPU ms | Serial CPU ms | Serial CPU vs parallel | Elapsed ms, parallel → serial | Peak RSS MiB, parallel → serial |
|---|---:|---:|---:|---:|---:|---:|---:|
| eager bike-day known | 0.780 | 0.690 | 0.720 | 0.397 | -44.9% | 0.423 → 0.435 | 7.73 → 7.53 |
| eager bike-hour known | 7.448 | 5.303 | 5.235 | 3.591 | -31.4% | 2.048 → 3.631 | 15.78 → 15.52 |
| eager unique-shuffled known | 7.264 | 5.817 | 5.976 | 5.836 | -2.3% | 5.352 → 5.918 | 12.33 → 12.30 |
| eager Aotizhongxin known | 11.887 | 12.695 | 12.610 | 9.070 | -28.1% | 4.996 → 9.125 | 23.08 → 22.78 |
| eager Wanliu known | 12.012 | 12.591 | 12.539 | 9.003 | -28.2% | 4.978 → 9.060 | 22.89 → 22.61 |
| eager energy known | 444.339 | 354.695 | 351.313 | 305.579 | -13.0% | 172.693 → 305.659 | 420.86 → 420.52 |
| eager energy infer | 447.083 | 353.878 | 355.643 | 308.264 | -13.3% | 174.673 → 308.330 | 422.30 → 420.53 |
| eager energy-date-full known | 464.916 | 368.055 | 368.505 | 322.291 | -12.5% | 167.991 → 322.384 | 420.85 → 420.53 |
| eager late-bool infer | 6.731 | 6.598 | 6.829 | 6.665 | -2.4% | 6.889 → 6.712 | 9.67 → 9.67 |
| eager late-text infer | 14.197 | 8.633 | 8.729 | 8.632 | -1.1% | 8.793 → 8.703 | 16.88 → 16.88 |
| stream date-100000-1 known | 4.466 | 4.556 | 4.369 | 4.374 | +0.1% | 4.437 → 4.450 | 8.58 → 8.58 |
| stream bike-hour known | 5.245 | 5.254 | 5.179 | 3.475 | -32.9% | 2.006 → 3.526 | 12.89 → 12.59 |
| stream unique-shuffled known | 5.587 | 5.530 | 5.504 | 5.357 | -2.7% | 4.888 → 5.406 | 9.44 → 9.41 |
| stream Aotizhongxin known | 12.321 | 12.075 | 12.189 | 8.236 | -32.4% | 4.543 → 8.279 | 15.82 → 14.37 |
| stream energy known | 332.460 | 322.219 | 326.214 | 270.152 | -17.2% | 150.576 → 270.226 | 138.09 → 136.43 |
| stream energy-date-full known | 346.076 | 338.891 | 339.049 | 281.436 | -17.0% | 144.800 → 281.561 | 138.34 → 136.50 |

Process CPU time is user time plus system time. Peak resident memory includes mapped pages and runtime overhead. It is not an allocation count. Reported values are medians without outlier removal.

The original column reports the retained-index reader at `dba26e1562503e1594194250d914327830d8f58d`. The parent is `c8c56d1eb25f51afa27c452c6f656cb79dec73a6`. Parallel and serial use the same final module and differ only in the public selector. Keep historical benchmark fingerprints attached to those heads.

## Default compatibility and independent controls

The final reference matrix contains 512 workers across eager and streaming reads. The width and null-density controls contain 544 workers. They compare the new serial option with the earlier direct-loop serial prototype, and the new parallel default with its frozen parent.

No parallel-default CPU increases exceeded the 10% review threshold in either final matrix. No reference-case peak-RSS increase exceeded 5% plus8MiB. These are review limits, not proof that smaller regressions are zero. The serial prototype comparison checks that the public selector retains the direct-loop result; it does not prove serial is optimal for every input.

Control results and all per-case medians are retained in [the mode controls](mode-controls/summary.json). Full reference results are in [the reference summary](acceptance/summary.json). Do not combine these cases into one weighted efficiency score or treat a reduced CPU time as an elapsed-time improvement.

## Verification

- 384 DataFrame tests passed in Release, Debug, and Address Sanitizer. There were no failures or skips.
- Both modes run through public eager and streaming feature tests. Extended indexed-versus-batched tests cover mixed values, headers, ragged rows, explicit conversion errors, row limits, and late fallback.
- The unchanged public parser matched 30,720 grammar fixtures with the recorded digest.
- The standard `tabular-smoke` run produced 190 SwiftSci and pandas samples, and its artifact audit passed. This validates that profile, not the full mathematical or MLX-dependent library.
- Final source hashes match the unit-test receipts and benchmark modules. Accepted timing phases ran after this task's builds, tests, and profilers finished, on AC power.
- An initial feature-test compilation caught an argument-order error in the new test. The test was corrected before the final Release, Debug, and sanitizer runs. The initial failure is preserved separately.

## Standards

The independent standards review found no documented-standard violations or actionable code smells. The public declarations have DocC comments. One shared helper owns the scheduling choice. See [the review record](reviews.md).

## Spec

The independent spec review found no actionable issues. The change preserves type inference, original-token fallback, invalid-explicit-value null handling, cancellation, row limits, native optional storage, the deployment floor, and the existing memory bound.

## Evidence and reproduction

Large raw JSON files and logs are compressed with their original bytes preserved. Redundant progress snapshots are omitted after checking that their records match the completed runs.

The [artifact manifest](artifact-sha256.json) records hashes for the saved evidence. The [verification controller](verify.py), [final reference controller](run-acceptance.py), and [width and null controller](run-mode-controls.py) record their commands and frozen inputs. The [build receipts](build-receipts/) pin source, dependency, harness, and executable hashes.

The trial and final harness versions are both retained. Earlier trials used `ResourceProbe-pilot.swift`; the final public-option build uses `ResourceProbe.swift`. Restore the matching pinned harness when rebuilding a historical trial. The private [experiment archive](experiments.tar.gz) contains generated data, input contracts, and source patches relative to the parent. Local paths in receipts identify the machine that ran them.

The source change is saved separately as [a compressed patch](source-change.patch.gz). Engineering decisions and raw benchmark evidence belong on `codex/engineering-notes`. They are excluded from the implementation branch.

## Remaining work

This change exposes a demonstrated CPU-versus-latency choice. It does not complete CSV optimization or establish a new default. Further work should measure coordinate allocation and field parsing independently, preserve the bounded coordinate lifetime, and test changes against these reference data and broader file shapes. No current evidence justifies a larger default batch, a cache claim, or a new automatic grouping threshold.
