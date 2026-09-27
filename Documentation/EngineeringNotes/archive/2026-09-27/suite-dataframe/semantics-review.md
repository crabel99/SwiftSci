# Dataframe suite semantics review

Reviewed canonical source and test files in `/Users/crabel/Documents/src/SwiftSci`. No production files changed. This is a source and existing-test review, not a new runtime verification. Ignore the untracked files ending in ` 2` and ` 3`; the canonical files carry the reviewed contracts.

## Public calls for the suite

```swift
TypedColumn<Double>(name: "x", values: [Double?])
TypedColumn<Int64>(name: "x", values: [Int64?])
TypedColumn<String>(name: "key", values: [String?])
try DataFrame(columns: [any AnyColumn])
column.filteredIndices(matching: FilterCondition) -> [Int]?
column.sortedIndices(ascending: Bool) -> [Int]
try frame.filter(column: "x", where: condition)
try frame.filterFast(column: "x", where: condition)
try frame.sortBy("x", ascending: true)
frame.groupBy("k1", "k2").sum()
frame.groupBy("k1", "k2").mean()
frame.groupBy("k1", "k2").count()
frame.groupBy("k1", "k2").agg(["x": .count])
try frame.groupBy("k1", "k2").sumChecked()
frame.groupBy("k1", "k2").transform(["x": .sum])
result[column: "x", as: Double.self]?.values
```

`FilterCondition` has equals, notEquals, greaterThan, lessThan, greaterThanOrEqual, lessThanOrEqual, isNull, isNotNull and contains. Thresholds accept `any Sendable`; use explicit Int64 or Double thresholds. The `filterFast(column:op:threshold:)` overload accepts only Double and cannot express an exact odd Int64 above 2^53. Use the condition overload for those cases.

Source references below are relative to `Sources/SwiftDataFrame`. Test references are under `Tests/SwiftDataFrameTests`. All references use canonical files.

## Filtering contract

`Columns/TypedColumn.swift:155` dispatches built-in numeric types. Float64 comparison is at lines 576-614; exact integer comparison is at lines 640-687. `Core/DataFrame.swift:407` and `Core/DataFrame+FastFilter.swift:19` both use this dispatch.

- Every result preserves original row order and gathers every column with the selected row IDs.
- Nil fails every ordinary comparison, including notEquals. isNull selects only nil. isNotNull includes NaN and infinities.
- NaN equality and ordered comparisons are false; notEquals is true for present values. Signed zeros compare equal.
- Integer thresholds and values preserve exact Int64 identity. Mixed integer/Double comparisons use the represented mathematical values without converting the integer to Double first.
- Direct TypedColumn filtering returns `[]` for an empty selection. DataFrame filtering then calls `gathered`, which returns `DataFrame.empty` and loses all columns at `Core/DataFrame.swift:648`.

The documentation explicitly states these rules in `SwiftDataFrame.docc/NumericFiltering.md`. `Tests/SwiftDataFrameTests/NumericFilterDispatchTests.swift` covers precision boundaries, fractional and nonfinite thresholds, mixed comparison directions, and empty/all-null inputs. Its result helper skips schema assertions when expected IDs are empty. That leaves the schema loss untested there.

Use this Float64 fixture with explicit row IDs 0 through 8:

```text
x = [nil, NaN, -Infinity, -0.0, +0.0, 2.0, 2.0, +Infinity, nil]
```

Independent expected IDs:

| Predicate | IDs |
| --- | --- |
| equals 0.0 | 3,4 |
| notEquals 0.0 | 1,2,5,6,7 |
| lessThan 0.0 | 2 |
| lessThanOrEqual 0.0 | 2,3,4 |
| greaterThan 0.0 | 5,6,7 |
| greaterThanOrEqual 0.0 | 3,4,5,6,7 |
| isNull | 0,8 |
| isNotNull | 1,2,3,4,5,6,7 |
| equals NaN | empty |
| notEquals NaN | 1,2,3,4,5,6,7 |
| any ordered comparison with NaN | empty |

Use this Int64 fixture:

```text
p = 9007199254740992
x = [p+1, nil, p, p+2, p+1, -p-1, Int64.min, Int64.max]
```

`equals Int64(p+1)` gives IDs `[0,4]`; `greaterThan Double(p)` gives `[0,3,4,7]`; `equals Double(p)` gives `[2]`; `lessThan Double(-p)` gives `[5,6]`. Parse integer fixture tokens as Int64 directly. Passing them through a Double JSON number can invalidate the fixture before Swift sees it.

Reverse mixed comparison fixture:

```text
x: Float64 = [9007199254740992, 9007199254740994, nil, NaN]
threshold: Int64 = 9007199254740993
```

Expected equals `[]`, notEquals `[0,1,3]`, lessThan and lessThanOrEqual `[0]`, greaterThan and greaterThanOrEqual `[1]`.

## Sort contract and bounds

`Columns/TypedColumn.swift:217` promises a stable permutation and nulls last. The Int64 comparator uses exact values. Both ascending and descending preserve input order among equal keys and place null rows last in input order. Signed zeros are equal sort keys. Infinities have the ordinary ordering. `Core/DataFrame.swift:546` gathers all columns using the permutation.

Safe Float64 fixture with IDs 0 through 9:

```text
x = [2, nil, -0.0, +0.0, -Infinity, 2, +Infinity, -1, nil, 2]
ascending  = [4,7,2,3,0,5,9,6,1,8]
descending = [6,0,5,9,2,3,7,4,1,8]
```

Safe Int64 fixture uses the filtering values above:

```text
ascending  = [6,5,2,0,4,3,7,1]
descending = [7,3,0,4,2,5,6,1]
```

`NumericSortTests.swift` tests stable ties, integer extremes, signed zeros, infinities and nulls. `AdaptiveDoubleSortingTests.swift` exercises larger inputs. The production Double algorithm changes at 1,024 present values, may choose radix sorting when runs are short, and treats very sparse inputs separately at `TypedColumn.swift:332-420`. Include fixture expansions around 1,023/1,024/1,025 and a shuffled long input with duplicate keys; keep expected IDs derived from a separate stable comparison over finite keys.

NaN sort placement has no portable contract. At lines 352-355 and 431-435 the implementation falls back to comparing with `<` or `>`. NaN is incomparable with every finite number, so these comparisons do not define a strict weak ordering. `NumericSortTests.swift:49` constructs its expected result using that same Swift sorting comparator; it proves preservation of the old path, not an independent ordering policy.

Keep NaN sort inputs as a diagnostic case. Require only permutation/payload preservation until a NaN placement policy is approved. Do not adopt pandas' NaN-last order as a Swift contract. Do not mark an arbitrary observed Swift NaN ordering as mathematically correct.

## Group identity and result representation

`Core/GroupedDataFrame.swift:238-249` builds groups in first-appearance order. Key components refine groups independently at lines 257-320. Floating keys canonicalize signed zeros and all NaN payloads at lines 323-330. Integer keys stay native throughout grouping, including beyond 2^53. Null is distinct from literal strings and NaN.

Group result key columns are always `TypedColumn<String>`, including originally numeric keys. Lines 455-464 format the first row's key value. A null key remains nil. Group output order is first appearance, not lexical key order. A first negative zero yields `"-0.0"` even if later positive zeros belong to the group. Canonicalize output rows only after checking group identity and count, and never use joined displayed keys as unique identifiers.

`SwiftDataFrame.docc/GroupKeySemantics.md` and `StructuredGroupingTests.swift` explicitly cover sentinel strings, separators, full-width integers, signed zeros, NaN payloads, and nulls. Existing tests use independent row-equality enumeration for generated Int64/String tuples.

Suggested independent separator fixture:

| ID | k1 | k2 | x Float64 |
| --- | --- | --- | --- |
| 0 | a\|\|b | c | 1 |
| 1 | a | b\|\|c | 2 |
| 2 | null value | x | 3 |
| 3 | literal `null` | x | 4 |
| 4 | a\|\|b | c | 5 |
| 5 | a | b\|\|c | null value |
| 6 | literal `__null__` | empty string | 7 |
| 7 | empty string | literal `__null__` | 8 |
| 8 | null value | x | null value |

Group representatives `[0,1,2,3,6,7]`; group row counts `[2,2,2,1,1,1]`; sums `[6,2,3,4,7,8]`; means `[3,2,3,4,7,8]`; present counts `[2,1,1,1,1,1]`; transformed sums `[6,2,3,4,6,2,7,8,3]`. Swapping k1 and k2 must preserve these group membership sets and first-appearance order.

Suggested Float64/Int64/String tuple fixture:

```text
kFloat = [-0.0, +0.0, NaN_payload_1, NaN_payload_2, nil, nil, NaN, NaN]
kInt   = [p+1,  p+1,  p,             p,             p,   p,   p+1, p]
kText  = ["x",  "x",  "a||b",        "a||b",        "x", "x", "a||b", "null"]
x      = [1,    2,    3,              4,             5,   6,   7,     8]
```

Representatives `[0,2,4,6,7]`; row groups `[0,0,1,1,2,2,3,4]`; counts `[2,2,2,1,1]`; sums `[3,7,11,7,8]`; transformed sums `[3,3,7,7,11,11,7,8]`. Use exact payload bits `0x7ff8000000000001` and `0xfff8000000000002` to check sign/payload independence. Retain the first zero's sign in the output key label assertion. Keep actual null and text `"null"` separately encoded.

## Aggregations and likely mismatch cases

`GroupedDataFrame.swift:98-117` documents Double sum/mean semantics, nil skipping, all-null results and exact sumChecked. Numeric aggregation is at lines 552-619.

- `sum` and `mean` skip nil, propagate NaN, and use compensated Double summation. All-null groups produce nil, not zero. NaN counts as present in the mean denominator.
- Ordinary Int64 sums return Double and can lose integer precision during conversion. Fixture `[9007199254740993, -9007199254740992]` in one group has mathematical sum 1 but ordinary `.sum()` computes 0. This is a documented limitation. Keep it as a precision case; use `.sumChecked()` for the exact contract. Do not silently cast the expected integer sum to Double and call that the intended ordinary-sum behavior.
- `.sumChecked()` preserves Int64 totals, allows temporary overflow if the final total fits, and throws `SwiftMLError.integerOverflow(column:group:)` for final overflow. `[Int64.max,1,-1]` must yield Int64.max. `[Int64.max,1]` must throw. `CheckedIntegerSumTests.swift` provides direct tests.
- `.count()` counts rows including null values, returns Int64 columns under the original numeric value-column names, and omits a synthetic count column when numeric value columns exist. With no numeric values it emits `count`. See lines 503-529.
- `.agg(["x": .count])` counts non-null x values, includes NaN, and returns a Double `x_count`. This differs from `.count()` deliberately. `.first` and `.last` mean first/last present value, skipping nil.
- `.agg` iterates a Dictionary, so order of multiple aggregate output columns should not be treated as a portable contract. Compare named columns unless an explicit suite schema canonicalizes the order.
- Min/max with NaN is input-order dependent. `[NaN,1]` yields NaN; `[1,NaN]` yields 1 because the first present value initializes the result and later comparisons with NaN are false. See lines 586-595. No documented NaN reduction policy was found. Keep this diagnostic outside finite-value min/max certification until the policy is chosen.
- Missing group key names are ignored; if all requested names are absent, nonempty rows form one group. Calling groupBy with no keys produces zero groups. Both historical behaviors are documented. Validate benchmark workload columns before execution rather than silently testing a different operation.
- Empty DataFrame sort/filter result schema loss is a concrete current behavior, not a cross-language default. Retain an explicit case with expected target schema and report the mismatch if schema preservation is required. Do not conceal it by checking only row count.

Independent aggregate fixture:

```text
key = ["finite", "finite", "finite", "empty", "empty", "nan", "nan", "cancel", "cancel", "cancel"]
x   = [1, nil, 3, nil, nil, NaN, 1, 1e16, 1, -1e16]
```

First-seen keys `finite,empty,nan,cancel`; row counts `[3,2,2,3]`; present counts `[2,0,2,3]`; sums `[4,nil,NaN,1]`; means `[2,nil,NaN,1/3]`. Check NaN with a class marker rather than equality. Use a tolerance for nonexact mean 1/3 and assert the class separately before numeric tolerance.

## Fixture format and reference bounds

Use explicit type declarations and separate null/special-value encoding. Int64 decimal strings avoid JSON consumer rounding. Float64 bit-pattern hex or tagged `nan`, `positive_infinity`, `negative_infinity`, and signed-zero tokens avoid treating NaN as null. Every row needs a stable integer ID. Preserve input and output row IDs to prove row alignment across columns.

Write expected results from the small tables above, then extend coverage with a simple independent reference over raw values. For grouping, compare typed tuple components and explicitly canonicalize NaN/zero identity. For sorting, use finite/Infinity keys with null-last and the row ID as an explicit tie key. For sums, exact rational or decimal arithmetic can certify bounded finite cases; a separate classification handles NaN/infinities. Do not copy Swift's compensated accumulation loop into the reference.

Pandas/NumPy are useful comparison implementations only after explicit adapters. Their missing-value representation, group null handling, group ordering, reduction null rules and count interpretation must match each workload contract. A nullable float container may collapse NaN into missing, so a separate validity bitmap is needed to represent both Swift nil and present NaN. Current standardized benchmark specs export finite Float64 only and cannot encode these richer cases without a separate result schema.

The safe first suite includes finite nullable Float64 and exact nullable Int64 filtering; stable finite/Infinity sorting with ties and nulls; grouping by typed multi-key tuples including null, NaN, strings with separators and exact Int64; bounded finite sums plus separately classified nonfinite sums; and sumChecked precision/overflow. Keep NaN sorting and NaN min/max as explicit unresolved-policy diagnostics. Keep schema loss and ordinary integer-sum precision loss visible. No production fixes belong in this suite-first pass.
