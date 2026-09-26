# Checked integer group sums

The new opt-in `GroupedDataFrame.sumChecked()` returns Int64 totals for Int32, Int64 and native Int columns. Existing `sum()`, `agg` and `transform` calls keep their Double results and conversion behavior. Floating columns use the existing compensated sum in either API.

## Overflow policy

Integer inputs accumulate in a signed two-word total. Every array-representable sequence of supported signed integers fits in this accumulator. This avoids requiring the macOS 15-only Int128 type in production code. Final totals outside Int64 throw `SwiftMLError.integerOverflow(column:group:)`; the group index is zero-based in first-appearance order. Temporary overflow of the Int64 range can cancel before the final check. Missing values remain missing when a group has no non-null inputs.

Custom integer columns must expose supported integer values. The checked API rejects other values instead of converting them through Double. This API checks integer overflow only; floating NaNs and infinities retain the existing sum behavior.

## Correctness evidence

Before implementation, the regression returned 0 for 9,007,199,254,740,993 minus 9,007,199,254,740,992. The checked API returns the exact Int64 result 1. The original API remains available with its documented conversion limitation.

Tests cover positive and negative final overflow, temporary overflow that cancels, exact large totals, missing groups, mixed numeric widths, multiple keys, custom integer storage, empty input, and existing result types. On macOS 15 or later an independent native Int128 reference checks 200 generated wide cancellation cases and 200 corresponding prefixes, including final overflow detection. That reference test ran on this Mac; production code requires only macOS 14.

All 295 scoped checks passed in Debug and Release: 33 dataframe XCTest cases, 2 statistics XCTest cases, 133 dataframe Swift Testing tests, 61 statistics tests, 56 forecast tests, and 10 independent checks. The full MLX-dependent suite was not run. The red, green, Debug and Release logs are saved here.

## Performance

Identical 100-group fixture with an Int64 ID column, a nullable Double column, and integer group keys. Each implementation ran three batches of 15 timed repetitions after two warmups per process. Process order rotates between batches. These are medians; data construction and output conversion are outside timing.

| Rows | Saved existing sum | Rebuilt existing sum | Checked sum | pandas | Kiraa |
|---:|---:|---:|---:|---:|---:|
| 100,000 | 0.487 ms | 0.504 ms | 0.439 ms | 0.676 ms | 0.902 ms |
| 1,000,000 | 4.755 ms | 4.704 ms | 4.343 ms | 4.764 ms | 9.383 ms |

The checked API is about 8% faster than the rebuilt existing sum at one million rows in this run. It avoids floating compensation for the integer column while adding integer overflow tracking. The small difference between the saved and rebuilt existing sums does not establish a meaningful regression or improvement.

All keys and integer totals in this fixture match their independent integer reference. SwiftSci's floating sums and pandas match the math.fsum reference for every group at both sizes. Kiraa passes the existing numerical tolerance. Large-integer precision is tested separately without conversion to Double in the regression suite.

`compare.py` and `results.json` retain commands, operation names, executable hashes and 45 timing samples per implementation at each size. The saved baseline hash matches the previous compensated-sums benchmark at commit 9686058937.

The checked API currently covers grouped sums. Integer means, extrema, `agg` and `transform` retain their previous conversion semantics. Those require separate decisions before changing their result contracts.
