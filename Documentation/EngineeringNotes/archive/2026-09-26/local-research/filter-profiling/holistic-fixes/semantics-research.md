# SwiftSci comparison and reduction constraints

The small fixes should preserve typed values through filtering and sorting, move conversion decisions outside row loops, and reuse metadata only when the operation preserves it. The current public optional-column representation can support these changes. A storage redesign is not required.

## Confirmed code defects and direct fixes

- `GroupedDataFrame.aggregateNumeric` dispatches Double, Float, Int64, and Int32 but omits native Int. Its fallback `toDouble` also omits Int. Add the typed dispatch and fallback conversion. This fixes all shared reductions, not just sum.
- `TypedColumn.sortedIndices` omits native Int and reaches Double promotion. Adjacent integers above 2^53 collapse before comparison. Add Int to the existing generic typed sort. Keep ascending/descending inside the same comparator because the repository records a Swift 6.4 Release compiler defect with separated closures.
- `TypedColumn.filteredIndices` specializes only Double, Int64, and String. Float, Int32, and Int incur per-row existential conversion and mask construction. Extend typed loops and classify the scalar threshold once.
- `TypedColumn.renamed` calls the initializer that scans every optional. Pass the existing `_nullCount` to the private initializer. Values are immutable and unchanged. Swift Array value semantics permit sharing their storage. Other operations that remove or replace nulls can also supply a proved count, but do not reuse the original count after arbitrary gathers or filters.
- Single-string grouping uses `"__null__"` for absence. Use a real optional key. Composite grouping joins text with `||` and uses `"null"` for absence. Use structured equality, with null represented separately from present values. Avoid relying on delimiters or hash values alone for identity.

## Filter contract

Null values fail every ordinary comparison, including `notEquals`. Only `isNull` selects null. Keep row order. An empty input produces an empty index array for a supported condition. Returning nil means the condition is unsupported by that fast path and invokes fallback, not that it matched no rows.

For floating-point comparisons, the current Double path already uses Swift's native operators. NaN is unequal to every value including itself; ordered comparisons and equality with NaN are false, while inequality is true. Preserve signed-zero equality and infinity behavior. The generic fallback currently maps NaN to `orderedSame` because both `<` and `>` are false. This is a correctness defect if that fallback remains responsible for numeric comparisons.

Never convert a Double threshold to Float as an unconditional optimization. Widen Float values to Double, which is exact, or take a Float comparison path only when `Float(exactly: threshold)` succeeds. Example: Float values near 1 can be incorrectly accepted by `>=` when a slightly larger Double threshold rounds down to 1. The same issue affects equality and inequalities in opposite directions at other rounding boundaries.

Integer-to-integer comparisons should stay in the integer domain. Native Int, Int32, and Int64 all fit Int64 on supported macOS targets. Widen Int32 values or classify an out-of-range threshold once; do not truncate it into Int32. Sorting and equality must distinguish adjacent integers above 2^53.

There are two defensible scopes for integer columns with floating thresholds:

1. For a small performance-only commit, keep the existing documented Double-promotion behavior for floating RHS and cover it explicitly. This leaves an acknowledged precision defect near 2^53 and NaN fallback bug unless fixed separately.
2. Preferred correctness contract: compare the mathematical integer value with the represented floating-point threshold exactly. Classify the threshold once into NaN, infinity, outside integer range, exact integer, or fractional interior. For fractional interior, compare integers to the truncated integer and use the fraction sign when equal. `Int64(exactly: threshold.rounded(.towardZero))` avoids trapping conversions. Outside-range classification must avoid treating `Double(Int64.max)` as an in-range maximum, because it rounds to 2^63.

Do not silently mix those contracts between Int, Int32, and Int64. The native comparison path must agree across numeric widths, filter, filterFast, and fallback columns for supported equivalent values. A generic comparison helper should represent unordered values explicitly if one is introduced. Three states cannot represent IEEE unordered comparisons.

Unsupported cross-type comparisons are currently treated as equal by generic `compare`. This is separate from adding typed numeric paths. Preserve current unsupported behavior in this scoped commit or change it explicitly with tests and release notes; do not let a failed conversion accidentally select all rows.

## Reduction and grouping compatibility

Native Int should join the existing Double-returning aggregation contract. The checked integer sum API already provides exact Int64 output. Fixing native Int must not silently change ordinary sum output dtype, overflow behavior, or compensated accumulation order.

Preserve first-seen group order and input order within a group. `.count()` counts rows, while `.agg([column: .count])` counts non-null values. Existing tests intentionally distinguish these. First and last mean first/last non-null value. All-null sum and mean return nil. No grouping columns currently produce no groups; missing grouping column names currently collapse rows into one group. These odd cases should not change incidentally in the collision fix.

Changing composite-key identity needs decisions for floating keys. Current interpolation collapses textual NaNs but may distinguish signed zero. A new raw Double Hashable key would change NaN grouping and signed-zero behavior. Either preserve these existing distinctions while fixing delimiter/null collisions, or document and test a deliberate numeric-equality contract. Group-key output currently remains String columns; changing output dtypes is additional API scope.

`DenseGroupingTests.emptyKeySelectionAndLegacyStringNullKey` explicitly asserts the inherited null-sentinel collision. Replace that assertion with distinct groups and preserve its unrelated no-key/missing-key assertions.

## Regression matrix

- Native Int reductions: sum, mean, min, max, first, last, count, transform; mixed null and all-null groups; output remains Double except row count and sumChecked.
- Native Int sort: both directions, Int.min/max, adjacent values around +/-2^53, duplicates for stability, nulls last, empty input; run Debug and Release.
- Typed numeric filters: all six operators across Float/Double/Int32/Int64/Int, matching and mixed scalar types, odd lengths, zero rows, all-null and no-null data; null inequality remains excluded.
- Float comparisons: thresholds between representable Float values, subnormals, signed zero, infinities, NaN in both operands; compare with exact widening oracle.
- Integer thresholds: Int32.max + 1 and Int32.min - 1, Int64 limits, fractional positive and negative thresholds, values adjacent to 2^53, +/-infinity, NaN. Check all six operators with an independent exact oracle if adopting exact mixed comparisons.
- Rename: values, dtype, count, null count, original name and original values unchanged. The performance validation is absence of a scan, not a timing assertion in a unit test.
- Group collisions: nil versus literal `__null__`; nil versus `null`; tuples `("a||b", "c")` versus `("a", "b||c")`; empty strings, Unicode, duplicate tuples, high cardinality, numeric values beyond 2^53. All shared reductions and transforms should consume the same group IDs.

## Documentation cleanup

`DataFrame+FastFilter.swift` still claims SIMD4/vDSP routing and O(N/4). The active optional-array loops are scalar in source. Remove these claims unless generated machine code or measured implementation supports them. SIMD width does not change asymptotic linear complexity.

## Primary references

Swift's BinaryInteger conversion contract distinguishes truncating floating conversion from exact conversion. Its ordinary floating initializer checks range after rounding toward zero, so unchecked casts are not a safe general threshold conversion. [Apple BinaryInteger documentation](https://developer.apple.com/documentation/swift/binaryinteger).

Swift documents NaN as unequal to itself and provides `isNaN` for identification. A ternary comparison that assumes either less, greater, or equal loses this state. [Swift FloatingPoint.nan documentation](https://docs.swift.org/main/documentation/swift/floatingpoint/nan/).

The exact initializer is explicitly designed to reject conversions that lose information. Use it to establish a scalar fast path once, then keep per-row work typed. [Apple BinaryFloatingPoint.init(exactly:) documentation](https://developer.apple.com/documentation/swift/binaryfloatingpoint/init%28exactly%3A%29-9lyid).

These are source-inspection recommendations. I did not edit production code, run tests, or measure performance in this review.
