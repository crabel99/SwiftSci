# DataFrame semantic fixture review

Reviewed `/Users/crabel/Documents/src/SwiftSci` at HEAD `31b3cff29057aab3013c459658af80575b794386`. This is a source review. No production files changed and no tests ran for this note.

## Public API and scope

- `DataFrame` is a struct. Its public subscripts are getters. `withColumn`, `mapColumn`, `select`, and `renameColumn` return new frames. A copy fixture must assign the returned value back to a separate variable. There is no public cell setter. See `Sources/SwiftDataFrame/Core/DataFrame.swift:6`, `:433`, and `:707`.
- `TypedColumn<T>` is a struct with public immutable `values: [T?]`. Its direct subscript returns `T?`. `AnyColumn.gathered(at:)` erases the returned type, so require a successful cast back to `TypedColumn<Int64>` when testing exact integer preservation. See `Sources/SwiftDataFrame/Columns/TypedColumn.swift:5`, `:21`, and `:116`.
- Exact matrix method names are `toFeatureMatrix(_:)`, `toFlatFeatureMatrix(_:)`, and `toTargetVector(_:)`. There is no `toMatrix` or `toFlatMatrix` in the inspected source tree. See `Sources/SwiftDataFrame/Core/DataFrame+Matrix.swift:10`, `:49`, and `:59`.
- Both matrix exports accept concrete `TypedColumn<Double>`, `TypedColumn<Int64>`, and `TypedColumn<Bool>`. Nulls become NaN. Bool values become 1 or 0. Other columns throw `.castFailed(column:targetType:)`; absent names throw `.columnNotFound`. There is no public throw-on-null policy. `TypedColumn<Float>`, `TypedColumn<Int32>`, and `TypedColumn<Int>` currently fail matrix export even though their dtype reports numeric. `Int` and `Int64` share `.int64`, so assert the concrete typed accessor as well as dtype.
- `toFlatFeatureMatrix` explicitly writes `flat[row * cols + requestedColumnIndex]`. Requested order and duplicate requested names are honored. Empty requested columns produce `flat == []`, `rows == source.rowCount`, and `cols == 0`.
- `DataFrame(columns: [])` and `select([])` throw `.emptySchema`. `DataFrame()` and `.empty` are valid schema-less frames. A frame built from named zero-length typed columns has a schema until `gathered(at: [])` returns `.empty` and drops it. Column-level empty gather retains name and concrete type. This behavior is already asserted by `GatherWorkTests.emptySelection`; describe it as the current contract, not a newly discovered failure.
- Public raw column values permit tests of returned arrays and alias isolation. Internal `DataBuffer` and `ArrowDataBuffer` do not provide a public backing-buffer contract. Name this suite "logical matrix export and alias isolation". It cannot establish Arrow layout, physical strides across columns, deep copies, or zero-copy behavior.
- `AnyColumn` is a public `Sendable` protocol and may have custom reference conformers. DataFrame stores those conformers without cloning. Scope copy-isolation claims to built-in `TypedColumn` values. Do not claim deep ownership of every possible custom column or reference-valued `SupportedType`.

## Five finite fixtures

1. Exact Int64 gather and typed column preservation. Construct `id = [Int64.min, 9007199254740993, nil, Int64.max, -9007199254740993]` with a String companion column. Gather `[3, 2, 1, 0, 4, 2, 1]`. Expect the literal Int64 sequence `[Int64.max, nil, 9007199254740993, Int64.min, -9007199254740993, nil, 9007199254740993]`, two nulls, original names/order, `.int64`, and a successful Int64 accessor. Assert that the original is unchanged. Include a direct typed column empty gather. Store expected integers as decimal strings or lossless bytes, never Double.
2. Selection and empty-shape contract. Select `["label", "id"]` from the first fixture and require that exact column order, unchanged Int64 cells, and retained row count. Separately record `.emptySchema` for `select([])`, `.columnNotFound` for a missing name, and `.duplicateColumnName` for `select(["id", "id"])`. Gather no rows and expect the current 0 by 0 result. A directly constructed zero-row two-column frame remains 0 by 2 before gathering. Do not normalize these cases into the same representation.
3. Nullable matrix export and precise rejection. Build Double `[1.25, nil, -2]`, Int64 `[7, nil, -8]`, and Bool `[true, false, nil]`. Request `["flag", "id", "value"]`. Expected rows are `[1, 7, 1.25]`, `[0, NaN, NaN]`, `[NaN, -8, -2]`. Verify both exports and target extraction against this independent literal oracle. Assert source null counts and values separately. A String column should throw `.castFailed`; a missing name should throw `.columnNotFound`. If desired, add Float and Int32 rejection as declared current capability checks. Their failures do not prove rejection of nulls.
4. Row-major export in requested order. Build Double `x = [101, 102, 103]`, Int64 `id = [11, 12, 13]`, and Bool `flag = [true, false, true]`. Request `["id", "flag", "x"]`. Expected flat output is `[11, 1, 101, 12, 0, 102, 13, 1, 103]` with shape 3 by 3. Check a non-square request `["x", "id"]` against `[101, 11, 102, 12, 103, 13]` with shape 3 by 2 so square dimensions cannot hide a transpose. Check duplicate request `["id", "id"]` and empty request `[]` separately. Mutate a local returned flat array and confirm a fresh export and the source frame stay unchanged.
5. Copy and column ownership. Construct a frame from mutable local input arrays, retain the original TypedColumn, copy the DataFrame, select a view-like result, and extract `.values` into a mutable array. Change the original input array and the extracted array. Replace `id` only in the copied frame using `withColumn`, passing a replacement column named `temporary` and target name `id`. Require source frame, retained column, selected result, and untouched companion column to stay unchanged. Require replacement name `id`, original column order, and unchanged row count. Follow with `copy = try copy.mapColumn("id", as: Int64.self) { $0.map { $0 + 1 } }` using small values to avoid overflow. Do not use pointer inequality to infer ownership.

## Adapter excerpt

The existing benchmark response accepts only finite `[Double]`, and rejects NaN. Preserve the semantic result before it reaches `BenchmarkSample`. This excerpt emits an ASCII record as finite byte-valued Doubles. Generate the expected ASCII bytes outside SwiftSci from literal fixture definitions. Use `atol = 0`, `rtol = 0`. The type checks are part of execution and must not be replaced by dtype-only checks.

```swift
import Foundation
import SwiftDataFrame

private enum LayoutFixtureError: Error {
    case missingTypedColumn(String)
    case unsupportedFloat
}

private func exactInts(_ frame: DataFrame, _ name: String) throws -> String {
    guard let column = frame[column: name, as: Int64.self] else {
        throw LayoutFixtureError.missingTypedColumn(name)
    }
    let cells = column.values.map { value in value.map(String.init) ?? "null" }
    return "Int64|\(column.name)|\(column.nullCount)|" + cells.joined(separator: ",")
}

// Fixture numbers below are integral Doubles. This avoids locale-dependent
// formatting and leaves NaN explicit without passing it to BenchmarkSample.
private func finiteMatrixRecord(_ flat: [Double], rows: Int, cols: Int) throws -> String {
    let cells = try flat.map { value -> String in
        if value.isNaN { return "nan" }
        guard let integer = Int64(exactly: value) else {
            throw LayoutFixtureError.unsupportedFloat
        }
        return String(integer)
    }
    return "\(rows)x\(cols)|" + cells.joined(separator: ",")
}

// Route .text(result) through the existing worker's text output branch.
// An independent expected fixture contains the exact ASCII bytes of the record.
func dataframeLayoutRecord() throws -> String {
    var input: [Int64?] = [9_007_199_254_740_993, nil, -7]
    let sourceColumn = TypedColumn<Int64>(name: "id", values: input)
    let original = try DataFrame(columns: [
        sourceColumn,
        TypedColumn<String>(name: "label", values: ["a", "b", "c"]),
    ])
    let selected = try original.select(["label", "id"])
    let gathered = original.gathered(at: [2, 0, 1, 0])
    let empty = original.gathered(at: [])
    var copy = original
    input[0] = 99
    var extracted = sourceColumn.values
    extracted[0] = 42
    copy = try copy.withColumn(
        "id", column: TypedColumn<Int64>(name: "temporary", values: extracted))
    let numeric = try DataFrame(columns: [
        TypedColumn<Double>(name: "x", values: [101, 102, 103]),
        TypedColumn<Int64>(name: "id", values: [11, 12, 13]),
        TypedColumn<Bool>(name: "flag", values: [true, false, true]),
    ])
    let matrix = try numeric.toFlatFeatureMatrix(["id", "flag", "x"])
    let nullable = try DataFrame(columns: [
        TypedColumn<Double>(name: "value", values: [1, nil, -2]),
        TypedColumn<Int64>(name: "id", values: [7, nil, -8]),
        TypedColumn<Bool>(name: "flag", values: [true, false, nil]),
    ])
    let nullMatrix = try nullable.toFlatFeatureMatrix(["flag", "id", "value"])
    return try [
        exactInts(original, "id"),
        selected.columnNames.joined(separator: ","),
        exactInts(selected, "id"),
        exactInts(gathered, "id"),
        "empty=\(empty.shape.rows)x\(empty.shape.columns)",
        exactInts(copy, "id"),
        finiteMatrixRecord(matrix.flat, rows: matrix.rows, cols: matrix.cols),
        finiteMatrixRecord(nullMatrix.flat, rows: nullMatrix.rows, cols: nullMatrix.cols),
    ].joined(separator: "\n")
}
```

This is an adapter sketch, not a compiled test. Split it into independent operation cases for failure attribution. The current worker loads CSV and extracts `x` and `y` before dispatch unless it recognizes a special input kind. A new semantic fixture kind must bypass that route before extraction; registering only a switch case is insufficient. The request validator requires positive input `rows`, so use a positive source fixture while checking empty operation results. If byte encoding is used for general nonintegral floating fixtures, encode IEEE-754 bit patterns or tagged JSON with an explicit numeric policy. The integral-only helper above must not silently round arbitrary values.

## Existing coverage and gaps

- `Tests/SwiftDataFrameTests/Int64GatherTests.swift` already exercises exact integers beyond 2^53, extrema, duplicates, nulls, empty typed gathers, source stability, and filters. A finite external fixture adds an independent serialization/oracle check rather than a new library behavior.
- `Tests/SwiftDataFrameTests/GatherWorkTests.swift:75` already pins schema-less empty frame gathering.
- `Tests/SwiftDataFrameTests/ColumnNullCountTests.swift` covers typed empty gathers and null counts across supported built-in types.
- `Tests/SwiftDataFrameTests/DataFrameSelectionTests.swift` checks requested column names and row count, but does not establish exact large-integer payloads or empty column selection errors.
- `Tests/SwiftDataFrameTests/DataFrameRelease35CoverageTests.swift:106` checks flat row-major values in construction order. Its null tests use `.isNaN`. A permuted non-square export gives better layout discrimination.
- `Tests/SwiftDataFrameTests/DataFrameNullSafetyTests.swift:8` explicitly requires Bool nil to become NaN.
- `Tests/SwiftDataFrameTests/DataFrameAPIExtensionTests.swift:8` checks transformed values. `DataFrameFilterTests.swift:60` checks adding/replacing columns but the shown overwrite case checks only column count. The copy fixture should assert payload isolation on every retained result.

## Hazards and assumptions to keep out of the baseline

- Never canonicalize Int64 through `toDoubles`, matrix export, a JSON floating number, or `Double(Int64)` before comparison. This can collapse neighboring integers above 2^53 and make a broken implementation pass. `toDoubles` also removes nulls.
- `TypedColumn` direct indexing is unchecked at the public API level. Integer gathers use Array subscripts that trap for invalid indices. Double and generic gathers use unsafe pointer indexing without bounds checks. Invalid gather indices can crash or read invalid memory; they are unsuitable for an ordinary in-process semantic fixture. If added later, isolate each in its own process and classify outcomes separately.
- A nil source cell and a present NaN become indistinguishable after matrix export. Check the source null mask separately. NaN is not equal to itself; use `.isNaN` or an explicit tag.
- `schema().nullable` derives from observed `nullCount`, not a declared nullable type. Zero-row columns therefore report false. Avoid expecting declared-nullability preservation from schema metadata.
- `renameColumn(old, to: existingName)` does not visibly guard collisions before updating the dictionary and order. Do not silently use it as a safe generic mutation fixture. This is a source-review concern for a separate defect test and fix branch.
- The adapter's byte encoding is exact only with zero tolerances. A permissive numerical tolerance can turn a character mismatch into a passing comparison.
- Keep correctness cases independent of timing claims. A fixed three-row alias-isolation case establishes value semantics for those operations, not a physical memory layout or performance property.
