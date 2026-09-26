## Summary

With Swift 6.4, `TypedColumn.sortedIndices(ascending: false)` returns ascending order for columns containing missing values in an optimized build. Debug mode returns the expected descending order, with missing values last. `DataFrame.sortBy(..., ascending: false)` is also affected.

Observed at upstream commit [`03270a1adb938bc7fd89080cdd07dd31ce0afd96`](https://github.com/Nodibell/SwiftSci/commit/03270a1adb938bc7fd89080cdd07dd31ce0afd96).

Existing upstream tests also catch this:

- "Primitive fast sorting operates correctly on Double, Float, Int64, and Int32" in `Tests/SwiftDataFrameTests/DataFrameSIMDFilterTests.swift`.
- "TypedColumn sortedIndices" in `Tests/SwiftDataFrameTests/TypedColumnCoverageTests.swift`.

These produce five failed assertions across two tests in Release mode; both pass in Debug.

## Environment and behavior

`DescendingNullSort.swift` preserves the original optional-value sorting helper in a standalone program. It does not import SwiftSci or any third-party package. It intentionally retains the compiler trigger after the library workaround.

On Apple Swift 6.4, swiftlang-6.4.0.34.1, targeting arm64 macOS with Xcode 27.0:

| Compilation | Ascending result | Descending result | Exit |
|---|---|---|---|
| `-Onone` | `[2, 0, 1]` | `[0, 2, 1]` | 0 |
| `-O` | `[2, 0, 1]` | `[2, 0, 1]` | 1 |

The input is `[2, nil, 1]`. Both directions should keep the missing value last. Descending order must put 2 before 1.

## Run

Save the reproducer below as `DescendingNullSort.swift`, then run:

```sh
swiftc -swift-version 6 -Onone DescendingNullSort.swift -o /tmp/swiftsci-sort-debug
/tmp/swiftsci-sort-debug
swiftc -swift-version 6 -O DescendingNullSort.swift -o /tmp/swiftsci-sort-release
/tmp/swiftsci-sort-release
```

The optimized program exits 1 on the affected toolchain. It prints actual and expected indices rather than crashing. Other compiler versions may behave differently.

## Isolation

The original upstream tests and a new three-element regression fail in Release and pass in Debug. The standalone program reproduces the failure without the package, its dependencies, XCTest, or Swift Testing. A standalone variant with one comparison closure passes with optimization enabled.

Together these observations point to a compiler optimization defect triggered by separate generic comparison closures. They do not identify the particular compiler pass or establish which other Swift versions are affected. No compiler issue has been filed as part of this investigation.

## Proposed workaround and validation

The proposed fix in my fork sorts with one closure and chooses `<` or `>` inside its non-missing comparison case. Missing-value ordering remains independent of direction. The workaround preserves optimization and the existing API.

`Tests/SwiftDataFrameTests/DescendingNullSortTests.swift` checks the numeric reproduction, String and Bool callers, and dataframe row association. All three tests were run and failed before the production change. All three pass with the workaround in Release mode. The original upstream assertions remain unchanged.

The fix and three regression tests are on [`crabel99:fix/descending-null-sort`](https://github.com/crabel99/SwiftSci/tree/fix/descending-null-sort). The [branch diff](https://github.com/crabel99/SwiftSci/compare/03270a1adb938bc7fd89080cdd07dd31ce0afd96...fix/descending-null-sort) contains only the production change and regression tests. The standalone proof is included in this issue rather than the patch.

After the workaround, all 249 scoped SwiftDataFrame, SwiftStats, and SwiftForecast tests pass in both Release and Debug. Ten additional independent checks pass in Release, including the original sorting reproduction. These results do not cover the rest of the SwiftSci modules.

## Standalone reproducer

```swift
// Compiler reproduction of the original helper, independent of SwiftSci.
import Darwin
func sortedIndices<T: Comparable>(_ values: [T?], ascending: Bool) -> [Int] {
    var indices = Array(values.indices)
    sortIndices(&indices, ascending: ascending) { values[$0] }
    return indices
}
private func sortIndices<C: Comparable>(_ indices: inout [Int], ascending: Bool, key: (Int) -> C?) {
    if ascending {
        indices.sort { i, j in
            switch (key(i), key(j)) {
            case (nil, nil): return false
            case (nil, _):   return false
            case (_, nil):   return true
            case let (l?, r?): return l < r
            }
        }
    } else {
        indices.sort { i, j in
            switch (key(i), key(j)) {
            case (nil, nil): return false
            case (nil, _):   return false
            case (_, nil):   return true
            case let (l?, r?): return l > r
            }
        }
    }
}

let values: [Double?] = [2, nil, 1]
var failures = 0
for ascending in [true, false] {
    let actual = sortedIndices(values, ascending: ascending)
    let expected = ascending ? [2, 0, 1] : [0, 2, 1]
    print("ascending=\(ascending), indices=\(actual), expected=\(expected)")
    if actual != expected { failures += 1 }
}
exit(failures == 0 ? 0 : 1)
```
