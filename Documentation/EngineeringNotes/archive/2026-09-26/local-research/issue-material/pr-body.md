Fixes #37.

With Apple Swift 6.4 in Release mode, descending sorting of a column containing missing values can return ascending order. For `[2, nil, 1]`, the original helper returns indices `[2, 0, 1]` instead of `[0, 2, 1]`. This also affects `DataFrame.sortBy`.

Use one comparison closure and select `<` or `>` inside its non-missing case. This avoids the observed optimized-build failure while preserving the API, missing-values-last ordering, and compiler optimization settings. The standalone reproduction in #37 points to a compiler optimization defect; the specific compiler pass and affected version range remain unconfirmed.

The diff contains only the sorting change and three regression tests covering:

- The minimal three-element numeric case.
- String and Bool columns using the same helper.
- Dataframe sorting with row association preserved.

All three new tests were run before the production change and failed for the expected descending-order mismatch. They pass after the workaround. Existing assertions were not changed.

Validation on Apple Silicon, Xcode 27.0, Apple Swift 6.4 `swiftlang-6.4.0.34.1`:

- 249 tests passed in both Release and Debug across SwiftDataFrame, SwiftStats, and SwiftForecast, using a separate validation package to scope the build to those modules.
- 10 additional local independent checks passed in Release, including the original sorting reproduction, CSV/Parquet round trips, joins, statistics, and simple forecasts.
- `git diff --check` passed.

The remaining SwiftSci modules and other compiler versions have not been tested. Reproducer code and diagnostic documentation are in #37 rather than the PR diff.
