# Int64 gather result

The candidate remains on local branch `codex/optimize-filter-null-count`. It is uncommitted and has not been published.

A private concrete Int64 gather helper now complements the existing Double helper. It uses SwiftSci storage and Swift array mapping, preserves Int64 precision and nulls, and changes no public API. No code was copied from pandas or Kiraa.

The standalone phase probe improved full filtering from 32.55 to 4.49 ms and one integer-column gather from 15.09 to 1.10 ms. The complete matched comparison subsequently measured 4.00 ms for the one-million-row SwiftSci filter, versus 32.40 ms for the prior candidate and 165.99 ms before the optimization work.

Million-row medians in the repeated comparison:

| Operation | SwiftSci ms | Kiraa ms | Python ms |
|---|---:|---:|---:|
| csv | 113.456 | 9.402 | 70.292 |
| filter | 3.999 | 2.972 | 2.300 |
| sort | 211.705 | 61.266 | 33.041 |
| group | 254.395 | 9.421 | 5.494 |
| stats | 0.596 | 0.595 | 0.623 |

Every value comparison passed at both 100,000 and 1,000,000 rows. The Python comparison retains the earlier explicit copy for continuity; the separate stage profile measured its cost at about 0.2 ms. Performance remains workload-specific.

All 264 scoped tests passed in Debug and Release: 135 dataframe, 63 statistics, 56 forecasting and 10 independent checks. New Int64 tests verify limits, values beyond 2^53, duplicate and reordered indices, null counts, source preservation, zero/all/partial selections and the parallel gather path in four-column frames. Correctness tests pass before and after; the performance improvement is established by external benchmarks rather than fragile timing assertions in unit tests.

- [Complete comparison](/Users/LOCAL_USER/local-ai/spl/swiftpandas/benchmark/results/20260925T221745Z/REPORT.md)
- [Feature-integration assessment](/Users/LOCAL_USER/local-ai/spl/swiftsci/filter-profiling/FEATURE-INTEGRATION.md)
- [Candidate patch](/Users/LOCAL_USER/local-ai/spl/swiftsci/filter-profiling/int64-candidate.patch)
- [Release validation](/Users/LOCAL_USER/local-ai/spl/swiftsci/filter-profiling/int64-tests-release.log)
- [Debug validation](/Users/LOCAL_USER/local-ai/spl/swiftsci/filter-profiling/int64-tests-debug.log)

The next changes should be independent, measured patches. The feature assessment identifies existing capabilities, genuine gaps, compatibility decisions and acceptance checks. It does not add a new storage engine or importer in this candidate.
