# Compensated grouped sums and means

SwiftSci now uses Neumaier compensation for grouped sums and means, including the shared paths used by `agg` and `transform`. Each group keeps a sum and a rounding correction. The bounded integer-key lookup and hashing fallback are unchanged.

## Correctness

The new cancellation tests failed before the production change, with 28 failed assertions across the focused suites. They passed after the change. Cases include interleaved groups, both signs of cancellation, repeated small contributions, Float input, missing values, subnormal values, infinities, NaNs, intermediate overflow, and empty input. One older test expected a lost contribution; its expectation now requires the mathematically correct result.

All 287 scoped checks passed in both Debug and Release: 33 dataframe XCTest cases, 2 statistics XCTest cases, 125 dataframe Swift Testing tests, 61 statistics tests, 56 forecast tests, and 10 independent checks. This is not the full MLX-dependent package suite. Logs are saved alongside this report.

## Matched grouping benchmark

Same Mac, same fixture, two numeric value columns, 100 integer groups, one missing floating value every 101 rows. Each implementation ran three batches of 15 measured iterations, with two warmups per process and rotating execution order. Times exclude input construction and result extraction. The saved before binary matches the hash of the prior benchmark at commit e861980165.

| Rows | SwiftSci before | SwiftSci compensated | pandas | Kiraa |
|---:|---:|---:|---:|---:|
| 100,000 | 0.401 ms | 0.493 ms | 0.673 ms | 0.900 ms |
| 1,000,000 | 3.821 ms | 4.635 ms | 4.739 ms | 8.836 ms |

Compensation costs about 21% at one million rows in this run. SwiftSci and pandas are close enough that this does not establish a reliable speed advantage over pandas.

The benchmark verifies keys and integer-column sums exactly for this fixture. Floating results are compared with Python `math.fsum` over the original floating inputs. All implementations pass the existing tolerance of rtol=1e-10 and atol=1e-8. The compensated SwiftSci result additionally equals the fsum reference for all 100 groups at both sizes. pandas also has zero observed error here. The older SwiftSci and Kiraa sums differ by at most 5.59e-9 at one million rows. These fixture results do not establish correctly rounded summation for every possible input.

`compare.py` and `results.json` retain the commands, executable hashes and all timing samples. The external stage probes now compare against integer-derived reference sums with a 1e-12 relative tolerance instead of requiring identical rounding to ordinary sequential addition.

## Remaining limits

Integer aggregate inputs still convert to Double, and outputs remain Double. Values outside Double's exact integer range can lose information before accumulation. Compensation does not repair that conversion. Intermediate overflow still propagates infinity, and NaNs still propagate. This change intentionally improves rounding behavior; it does not promise bitwise compatibility with prior sums or pandas.

An explicit integer accumulator, output-type and overflow policy remains a separate API decision.

## Algorithm reference

Boost Histogram also uses Neumaier compensation in its floating sum accumulator: https://www.boost.org/latest/libs/histogram/doc/html/doxygen/classboost_1_1histogram_1_1accumulators_1_1sum.html . This implementation was written locally; no library source was copied.
