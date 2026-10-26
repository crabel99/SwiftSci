# CSV specification review

Reviewer model: gpt-5.6-sol.

No missing requirement, incorrect behavior, or scope creep was found in `962fd9ff4d155e5116baf6f177abfa3e84fd8754...da03a63015`.

- `Sources/SwiftDataFrame/IO/CSVColumnBuilder.swift:42-70` flushes complete validity words, preserves a partial final word, grows beyond the estimated capacity, keeps valid NaN payloads distinct from nulls, and resets after materialization. `Tests/SwiftDataFrameTests/CSVCompactValidityGrowthTests.swift:6-29` covers late first nulls, word boundaries, underestimated and overestimated capacities, and prior values.
- `Sources/SwiftDataFrame/IO/SystemsCSVParser.swift:423-451` narrows 16 structural byte flags into one bit per four-bit slot. The vector and scalar paths use the same slot layout, and trailing-zero division restores the byte index.
- `Sources/SwiftDataFrame/IO/CSVColumnConversion.swift:286-337` rejects raw zero-length fields before String construction and normalized empty text before numeric conversion. It preserves the missing-versus-invalid inference result and explicit-schema nil fallback. `CSVEmptyNumericTests.swift:7-67` covers raw, quoted, and whitespace empties, both Double storage modes, and late inference rejection.
- `Sources/SwiftDataFrame/IO/VectorizedByteParsers.swift:107-158` accumulates negative magnitude with reporting arithmetic, accepts both signed limits, and returns `nil` for either overflow direction. `CSVIntegerBoundaryTests.swift:7-64` checks parser bounds, malformed tokens, both conversion modes, explicit nil fallback, and inferred limits.

The range changes only the four planned production files and three focused test files. I did not run builds or tests for this read-only review.
