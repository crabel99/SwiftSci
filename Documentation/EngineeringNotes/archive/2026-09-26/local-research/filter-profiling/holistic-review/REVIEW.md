# Optimization branch review

Review of `codex/dataframe-optimizations` at `3387fd4189` against upstream `bd3953fea9`. No repository source changed during this review. The PR remains on hold.

The branch has worthwhile remaining work. Earlier benchmarks emphasized Int64/Double columns and a single integer grouping key. Broader type and key coverage exposes substantial costs and inherited correctness defects.

## Standards review

No confirmed CONTRIBUTING.md violation in the additions. Public additions have documentation and tests. The helper types retain value semantics. Three practical cleanup opportunities remain: reuse cached null counts, complete concrete-type dispatch, and avoid creating numeric sort indices before returning through specialized paths. The last allocation may already be optimized away; measure before claiming a gain.

## Behavior review

Four confirmed inherited correctness failures need explicit regression coverage:

- Native Int ordinary grouped sums return nil for every group in the probe. `GroupedDataFrame.aggregateNumeric` lacks native Int dispatch, and its fallback `toDouble` does not accept Int. All 100 expected totals were missing. The existing checked-sum API handles Int separately.
- Native Int sorting compares through Double. Ascending sorting of `[9007199254740993, 9007199254740992]` returns indices `[0, 1]` instead of `[1, 0]`.
- String keys `[nil, "__null__"]` produce one group instead of two.
- Composite string keys `("x||y", "z")` and `("x", "y||z")` produce one group instead of two because grouping concatenates components with an unescaped delimiter.

The responsible fallback and key encoding also exist upstream. These are not established regressions introduced by this branch. The current tests deliberately preserve the string sentinel collision, so correcting it requires a documented behavior change.

## Measured opportunities

One million rows, 100 groups, Release on this Mac, two warmups and five samples. These are exploratory medians from a fixed-order process, not controlled before/after speedups. Data construction is outside timing. Full selected values, row order and grouped totals were checked after timing. Only native Int grouped totals failed.

| Operation | Median |
|---|---:|
| Filter Double | 2.93 ms |
| Filter Int64 | 3.13 ms |
| Filter Float | 157.66 ms |
| Filter Int32 | 197.73 ms |
| Filter native Int | 209.41 ms |
| Sum Int64 values | 3.42 ms |
| Sum native Int values, incorrect nil results | 101.99 ms |
| Group one Int64 key | 3.60 ms |
| Group one String key | 18.01 ms |
| Group two Int64 keys, second key constant | 417.10 ms |
| Rename Int64 column | 17.32 ms |
| Rename Double column | 18.23 ms |

The Float/Int32/Int filters fall back to per-row erased-value comparisons. Composite grouping formats keys on every row. Renaming calls the scanning initializer despite already knowing the null count.

## Recommended sequence

1. Add failing tests and complete native Int sorting and ordinary aggregation. Check all-null count behavior explicitly when adding typed dispatch.
2. Extend typed filtering across Int32, native Int and Float. Preserve mixed-type threshold comparisons, missing values and NaN semantics; do not truncate floating thresholds into integers.
3. Reuse null counts in rename and gather-related construction. Check nonnumeric types and ownership, and measure full operations as well as inner loops.
4. Treat collision-free composite grouping as a separate commit with documented semantics and representative key benchmarks. Typed structured keys may address both correctness and allocation costs.

Reusable group IDs across reductions and alternatives to comparison sorting are later candidates. Neither has a new measured implementation here. Compact storage, ownership changes and model adapters remain on the other branch.

`main.swift`, `Package.swift`, raw results and metadata preserve this review probe. To rerun, place main.swift at Sources/ReviewProbe/main.swift in the package directory. Its package dependency points to the local SwiftSci checkout.
