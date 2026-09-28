# Filter optimization decisions

Work started from SwiftSci commit `4dc6b533dd` on `codex/dataframe-pipeline-optimization`. Publication remains on hold.

## Evaluation rules

Compare independently preserved Release binaries with identical benchmark source. Run timing processes serially and alternate baseline/candidate order. Keep a separate holdout with different seeds, dimensions, selection rates, and payload types. Inspect regressions by type and width rather than relying on an overall average. Small differences are uncertain because an unrelated Energy Park calculation and editor work consume CPU throughout this session.

The production matrix checks exact values, row order, schema, and null counts. Its 96 tuning cases cover four numeric types, small and million-row inputs, narrow and wide tables, selection density, missing values, and match distribution. Another 24 cases are held out. A separate 64-case operator matrix covers all six comparisons and both null predicates, including thresholds that cannot be represented exactly at the column's width.

## Selection and compact storage

Do not replace selected indices globally with bitmaps or blocks. Across the million-row prototype matrix, median elapsed-time ratios were 1.056 and 1.064 relative to indices. Dense contiguous selections can benefit, but shuffled and nullable cases regress. Selection density alone does not predict which representation wins.

Keep compact storage work on its separate branch. Compact numeric input and output approximately halve buffer memory. Converting optional input into compact storage and materializing optional output inside a filter was 4.22 to 4.76 times slower by the median million-row case ratio. The benefit requires consumers to retain compact storage across operations.

These results come from a controlled standalone serial prototype, not the production SwiftSci implementation. See `storage-experiment/REPORT.md` and its raw results for all 1,728 validated cases, memory accounting, and limitations.

## Production candidate outcomes

- Accepted gather scheduling at 512 KiB estimated output, after rejecting the initial 4 MiB threshold.
- Accepted native-width floating comparisons only for null-free columns and exactly representable thresholds.
- Rejected native integer comparison after the operator matrix showed no material gain.
- Accepted cached null predicates for uniform-nullness columns.

Final measurements, commit IDs and validation are in [REPORT.md](/Users/LOCAL_USER/local-ai/spl/swiftsci/filter-optimization/REPORT.md).
