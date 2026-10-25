# CSV integer conversion traps at signed boundaries

Status: unresolved existing defect. The normalized-empty change does not edit the integer parser or fix these failures.

With an explicit Int64 schema, a CSV containing one numeric cell has these results on both parent and candidate:

| Cell | Expected | Actual |
| --- | --- | --- |
| `9223372036854775807` | `Int64.max` | Pass |
| `-9223372036854775808` | `Int64.min` | SIGTRAP |
| `9223372036854775808` | nil under the documented invalid-value coercion | SIGTRAP |
| `-9223372036854775809` | nil under the documented invalid-value coercion | SIGTRAP |

The reproduction uses a full Int64 override and the null token `?`. It runs each input in its own process, checks the complete native-bit result where execution completes, preserves crash status, and exits nonzero if any case fails. The parent is `31c0f958c843cb60279a74aff2b55427ba39abec`. The candidate has the same integer-parser source hash.

Crash frames identify `VectorizedByteParsers.parseInt(buffer:offset:)`. It accumulates a positive `Int` with checked multiply/add, then applies the sign. A positive accumulator cannot hold the magnitude of `Int64.min`, and out-of-range magnitudes trap before the optional fallback can reject them.

The archived `crash-reproducer/reproduce.py` accepts `--binary` and a fresh `--out` directory. Its parent and candidate records each retain three failures and one passing upper-bound case. The original failed control preflight and original nil expectation are preserved. No tolerance, expectation or production code is changed to waive the fault. The repair should have its own branch, regression tests and commit, including valid signed limits, out-of-range values, signs and surrounding whitespace.
