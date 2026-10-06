# Speed up owned Arrow imports and repair date32 conversion

Depends on [PR #60](https://github.com/Nodibell/SwiftSci/pull/60) for MLX Swift 0.32.3 and its required managed-buffer finalizer fix.

Arrow import repeatedly searches chunk boundaries for each row, and the pinned Arrow subscript crashes on empty chunks. Date32 import also requests the wrong generic array type. This change traverses chunks directly through Arrow's existing accessors and repairs signed date32 conversion. Public API, owned TypedColumn values, and per-type null policies remain unchanged.

The date adapter uses signed days because Arrow 21.0.0's date accessor reads UInt32 and can overflow. The [upstream correction](https://github.com/apache/arrow-swift/pull/194) is merged; this patch retains the existing Arrow dependency version.

## Validation

- Head `d8c13bb662b967999da4c05b5c7f5bb418295126` has the same source tree as tested commit `cd6b8218b1adcebd0a43d0382270623e902a125e`.
- Full local Release suite: 1152 passed, 3 failed, and 2 skipped. This is not a clean readiness result while failures remain.
- The focused dataframe target passed on the original branch with 270 definitions and 363 parameterized executions. New regressions cover chunk boundaries, null policies, numeric limits, signed dates, independent owned values, and source-buffer release.
- Before the fixes, empty-chunk regressions crashed and canonical date32-builder import failed its forced cast.
- The separate memory branch reproduces both GPU rotary failures before either Arrow commit. This does not replace validation of this branch.
- Hosted CI has not run for this Arrow branch.

## Performance

Apple M4 Max, 128 GiB RAM, macOS 27.0, Swift 6.4. Matched workers use the same required MLX pin. Median of three fresh-process runs per workload, alternating order. Timing covers owned import, selection, gather, and matrix construction, excluding fixture creation and correctness checks. All 42 complete outputs passed validation.

| Workload | Before, ms | After, ms | Speedup |
| --- | ---: | ---: | ---: |
| 1k rows, one chunk | 0.198 | 0.060 | 3.33× |
| 100k rows, no missing values | 17.924 | 4.607 | 3.89× |
| 1M rows, one chunk | 178.749 | 47.254 | 3.78× |
| 1M rows, 32 chunks | 813.501 | 47.737 | 17.04× |
| 1M rows, 32 chunks, sparse selection | 796.604 | 42.053 | 18.94× |
| 100k rows, five extractions | 33.093 | 5.062 | 6.54× |
| 1M rows, ten extractions | 221.200 | 84.545 | 2.62× |

One-million-row import allocation: 64,029,856 bytes before and 64,029,856 bytes after. This improves owned-import speed without introducing retained storage. Date64 support and the broader memory experiment remain outside this change.

## Compatibility failures still requiring attention

- `GenerationResultTests/invalidRequests(api:)`: Crash: xctest at <deduplicated_symbol>
- `LlamaRotaryScalingTests/rotationOracle(dimensions:gpu:)`: Expectation failed: worstRatio <= 1 worstRatio → 1.5823296156926971 1 → 1.0: dim=64, GPU=true, factor=8.0, traditional=false, length=1, offset=131069, error/budget=1.5823296156926971
- `LlamaRotaryScalingTests/transitionFrequencies(gpu:)`: Expectation failed: abs(actual[index] - expected) <= expected.ulp abs(actual[index] - expected) → 0.0008544922 expected.ulp → 6.1035156e-05: GPU=true, frequency=15, actual=774.8639, expected=774.86475
