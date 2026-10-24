**Depends on #85. Merge #85 first.** This draft targets upstream `main`, so its current aggregate diff includes the ingestion work: 59 commits across 97 files. The [compact-only comparison](https://github.com/crabel99/SwiftSci/compare/codex/csv-ingestion-review...codex/csv-compact-review) is 14 commits across 22 files. After #85 merges, refresh this branch onto the resulting upstream head and rerun the required checks before review readiness or merge. The local validation below covers the actual submitted head and full combined tree.

CSV-to-matrix workflows can retain an optional Double array, then allocate another representation for numerical consumers. This change lets callers opt into dense Double values with validity bits and preserves that representation through the supported selection and numerical preparation paths. Optional storage remains the default because exporting `.values` from compact storage materializes an optional array on every access.

```swift
var options = CSVReadOptions()
options.doubleStorage = .compact
let frame = try await DataFrame(csv: url, options: options)
```

### Behavior and compatibility

The compact path preserves native Double values, nulls, signed-zero bits, and column types. Numeric predicate filters, gathers, nullable joins, stable sorting, and numeric batch preparation consume or retain compact buffers without first expanding the complete optional array. Matrix construction still allocates its required output; this is not a general zero-copy promise.

Double sorting selects its path before allocating comparison caches, reuses prepared keys, handles monotonic inputs without a general sort, and returns identity indices for all-missing keys. NaN cases retain comparison fallback behavior. Tests cover stable ties, null placement, bitmap boundaries, native Int64 identifiers, numeric handoff, and both storage choices.

Existing generic helpers can still materialize optional arrays. Retaining a `.values` export alongside a compact column retains both representations. Callers should choose storage for their actual consumers rather than assume compact storage makes every operation faster.

### Selected reference measurements

The measured baseline is `5d1f89a961106104757f2d8d0b8faba79487d100`, immediately before the compact work. The measured candidate is `a74f5c3b5e0e511bf5bb69886a40cbae48b28d99`. These are historical measurement fingerprints, not the current review head and not a comparison against original upstream `main`. Production Swift, package dependencies, and benchmark worker/support Swift match the corresponding review cuts; the later readiness fixes affect verification and tests.

| Dataset and complete workflow | Baseline CPU, ms | Compact CPU, ms | Baseline peak RSS, MiB | Compact peak RSS, MiB |
|---|---:|---:|---:|---:|
| Air quality, 35,064 rows, read | 11.622 | 11.756 | 23.203 | 21.984 |
| Air quality, read, stable sort, matrix | 17.497 | 16.047 | 33.180 | 27.164 |
| Household energy, 2,075,259 rows, read | 269.661 | 282.887 | 422.414 | 314.164 |
| Household energy, read, stable sort, matrix | 480.973 | 459.632 | 739.148 | 504.250 |

For the household data, compact reading uses 4.9% more CPU and 25.6% less peak memory. The complete read, stable sort, and matrix path uses 4.4% less CPU and 31.8% less peak memory. The small air-quality read also costs slightly more CPU. These tradeoffs justify a selectable representation rather than a changed default.

The household complete-path comparison also records:

| Engine or candidate storage | CPU, ms | Wall, ms | Peak RSS, MiB |
|---|---:|---:|---:|
| SwiftSci optional | 488.280 | 234.872 | 739.164 |
| SwiftSci compact | 459.632 | 238.967 | 504.250 |
| pandas 3.0.6 | 1354.813 | 1355.521 | 941.883 |
| Polars 1.44.2 | 791.054 | 67.728 | 647.859 |
| DuckDB 1.5.6 | 1224.246 | 192.835 | 1125.453 |

This selected workload uses less CPU and peak memory with SwiftSci compact, while Polars finishes much sooner. CPU is process user plus system time, not energy, FLOPs, or utilization. Absolute process RSS includes different runtime baselines. No general cross-library winner follows from this table. A separate sort diagnostic also retains a measured few-microsecond common-input cost alongside its exceptional-case gains.

All engines receive the same bytes, complete schemas, delimiters, and null tokens. Sorts materialize the complete frame and preserve row order for ties with missing keys last. DuckDB's required row-index construction and stable-order tie-break are included. Matrices own contiguous writable row-major Float64 values. Full fingerprints check native columns and matrix bits outside timing. The fixtures do not include separate valid-NaN payloads.

The CPU study uses native parallelism on an M4 Max with 128 GiB, Swift 6.4, Python 3.14.6, and NumPy 2.5.3. It includes 32 exact preflights and 512 fresh timed processes in 16 balanced orders, with identical-binary controls and AC checks. All four selected comparisons qualify under the existing controls; that does not establish statistical significance for small differences. Repeated reads are not controlled cold-disk tests. Explicit imports and DuckDB connection creation occur before timing. Sort-and-matrix cases include pandas before Arrow registration; other initialization within public operations remains included. Input preparation, copying, computation, output allocation, and output release are included.

### Validation and delivery

Local validation at `224c6a2a2cddb40904ce4ad140829a4b63030884`, based on ingestion head `428891dfd1777be592cb04c85eea1a5b433cb32c`:

- Full Release and Debug package builds and tests: 1,631 passed in each configuration, no failures or skips, all 15 declared test targets included.
- Benchmark controllers with Metal opt-in checks: 226 passed without skips.
- Formal CPU regression policy: passed, 202 of 202 SwiftSci cases and 198 of 202 pandas cases. The same four pandas Wampler failures remain failed strict conformance; no new failures or relaxed tolerances.
- Documentation check passed at 2,431 of 2,464 documented declarations, or 98.66%. No long type-check warnings in changed Swift files; largest changed Swift test file 147 lines. Hosted CodeQL and Codecov are pending on this submitted head, and the CI compiler has not yet validated it.

The final tracked tree matches the independently validated integration checkpoint `bc87628ce1fe8722a716a612d4d3db3d0149b7c8` exactly. This second review unit is 14 commits across 22 files relative to the ingestion branch. This draft remains blocked on #85. After ingestion lands, refresh it onto the merged base and update this validation section after checking the refreshed head. Engineering notes and raw experiments remain outside the source diff.
