# Retained Arrow column trial

Date: 2026-10-06. Trial branch: `codex/arrow-retention-trial`. Commit: `c57fb6db02ea45b4f28852d812dcd076bf9a8b95`. Parent: `299221aab3865c57f8220bc8f2f03854708c6c65` on `codex/memory-library-reuse`. This remains a local experiment. No production API or source changed, and nothing was pushed.

## Decision

Reuse Arrow's existing buffers, null bitmap accessors, and owner objects. SwiftSci does not need another allocator or garbage collector for these inputs. A small adapter can retain a column holder, slice its logical range, stream values, and pack selected rows into an owned matrix. The adapter is 105 lines including its error helpers.

Keep two explicit storage choices. The current owned dataframe representation suits mutation, concurrency transfer, and repeated access. A retained view suits a short read-only path from Arrow input to a selected numerical result. Do not replace the current `DataFrame(arrowTable:)` semantics with a borrowed view silently.

The safest production sequence is to improve chunk traversal in the existing copying import first, then add a separate retained-view API once the producer immutability and imported-owner contracts are settled. The benchmark supports both choices; it does not support making all dataframe storage borrowed by default.

## Comparison

Median milliseconds over three fresh processes per variant and workload. All paths use the same four-column input and return the same checked row-major Double matrix. The four columns are two Double columns and two Int64 columns. One integer column includes values above 2^53; the expected result follows the existing Double conversion rather than claiming exact integer preservation in the matrix. Missing values vary between columns.

| Workload | Existing copying import | Streaming-copy trial | Retained-view trial |
| --- | ---: | ---: | ---: |
| 1k rows, one chunk | 0.223 | 0.139 | 0.046 |
| 100k rows, no missing values | 20.009 | 12.793 | 4.476 |
| 1M rows, one chunk | 198.034 | 135.353 | 42.138 |
| 1M rows, 32 chunks | 903.925 | 133.038 | 42.425 |
| 1M rows, 32 chunks, sparse selection | 887.155 | 131.657 | 11.180 |
| 100k rows, 8 chunks, five extractions | 37.025 | 13.780 | 6.208 |
| 1M rows, one chunk, ten extractions | 239.971 | 186.504 | 305.948 |

Timing includes import, selection, and matrix extraction. It excludes Arrow fixture construction and output validation. The repeated cases select rows once and repeatedly construct an owned matrix from that selection. They measure amortization, not a recommendation to rebuild an unchanged matrix. Applications that can reuse an already prepared matrix should do so.

For one million rows in a single chunk, the retained workflow takes about 42 ms versus 198 ms for the current path and 135 ms for streaming-copy. For ten extractions, streaming-copy takes about 187 ms while retained views take 306 ms. Owned arrays have a higher import cost but faster subsequent selection and matrix reads.

The 32-chunk case exposes a separate traversal cost. The current bridge indexes `ChunkedArray` for each row, and the pinned dependency searches its chunks linearly. Streaming each chunk once reduces this workload from about 904 ms to 133 ms while retaining owned `TypedColumn` results. Retained views reduce it further to about 42 ms. The sparse case also avoids reading values that will be discarded. Its large ratio is specific to this input and implementation, not a general dataframe or Arrow speedup.

The first version of the trial traversed all values even for a sparse selection and retained every column in a selected batch. The refined version merges sorted selection indices with chunk boundaries and retains only each selected column's holder. Initial and refined measurements are preserved separately so these improvements remain attributable.

## Memory and ownership

The current and streaming-copy imports add about 64,029,856 malloc bytes for the one-million-row, four-column input. Retained metadata adds 576 bytes for one chunk and 10,432 bytes for 32 chunks in these measurements. This is incremental allocation after the Arrow input exists. It excludes the input's own buffers and the eventual dense output. It is not a claim that the whole process uses only a few hundred bytes.

Slicing preserves the original buffer allocation. A one-value view of a 100,000-value column still retains an 800,000-byte value payload plus validity and allocation overhead. With 16 chunks, the slice retains only its 6,250-value chunk, a 50,000-byte value payload. Unrelated columns and chunks release. Materializing the one-value slice and dropping the view releases the original column. Physical footprint can remain high after malloc objects release because the allocator retains pages; that is distinct from a leaked owner.

The adapter retains `ArrowArrayHolder`, including `ImportArrayHolder`, rather than just an `ArrowArray`. For imported C data, the holder owns the release callback. The pinned Arrow importer also borrows the C array struct address. Whoever creates that import must preserve the struct's address for the holder's lifetime. The C fixture observes that requirement and verifies one release after the last retained slice disappears.

Arrow exposes mutable buffer pointers. The view sees subsequent producer writes. Materialization isolates those writes and yields existing `TypedColumn` value semantics. Producer immutability is therefore a contract of the experimental view, not something enforced by Arrow's type system. The adapter has no `Sendable` or unchecked concurrency conformance. No concurrent producer mutation is supported or tested.

Dense row-major matrix output still allocates and performs the existing numeric conversion. This trial does not provide GPU or MLX transfer, asynchronous device ownership, memory-budget integration, or a general `AnyColumn` replacement. Existing typed dataframe APIs remain unchanged.

## Validation

- Release correctness checks pass for Int32, Int64, Float, and Double; all tested slice ranges and nested slices; empty chunks; all-missing data; valid NaN versus null; infinities and signed zero; invalid types and bounds; and selected matrix packing.
- Native buffers remain alive after source objects are dropped and release after the final view. Imported C buffers invoke their release callback exactly once after the last nonempty slice. Unrelated columns and chunks release independently.
- Materialized values remain isolated from later producer and local array mutations.
- All 63 final benchmark workers verified the complete matrix against an independent deterministic oracle. Comparisons cover seven workloads, three variants, and three rotated repetitions.
- Address Sanitizer passes 1,000 ownership cycles for each of the native and imported-C paths with no diagnostic output. macOS `leaks` reports zero leaks after another 1,000 cycles per path.

The full SwiftSci suite was not rerun for this experimental executable. The production benchmark binary remains unchanged. No GPU, concurrency, whole-application performance, or universal leak-freedom claim follows from these bounded checks.

The original 103-row matrix fixture selected no rows and therefore could not use the existing empty-gather path, which removes columns. The comparison fixture now selects actual rows, and empty selection is checked separately in the trial. This fixture correction did not change production behavior.

## Reproduce

The trial adds the `SwiftSciArrowRetentionTrial` executable target. Build it in Release with the repository's resolved packages. Its `check 1000` mode exercises ownership and correctness. Its benchmark mode is `copy|stream-copy|retained rows chunks nullEvery selectEvery repeats`.

Run the controller from `Benchmarks/ArrowRetentionPrototype/run.py` with `--binary /absolute/path/to/SwiftSciArrowRetentionTrial --output /new/results/directory`. It runs one worker at a time, rotates variant order, checks every output, enforces a deadline, and stops before launching another worker if macOS reports memory pressure. It refuses to overwrite an existing measurement log.

Measured on Apple M4 Max, 128 GiB RAM, macOS 27.0, Xcode 27.0, Apple Swift 6.4, Release arm64. Arrow Swift is 21.0.0 at `fb3f3d91be5acd511b7289c7820becc1a68e455d`. The minimum deployment target remains macOS 14; this study does not demonstrate runtime compatibility on an actual macOS 14 installation.

Release worker SHA-256: `007191b829159b32c2024dd14d5d025350c0bec98da3c8e6049a54aad4e2942e`. ASan worker SHA-256: `0ed9a0bdb1d9bc86aca546f0864646adb3a707fca1726e618233f5d23b8b3add`. The controller added the ten-pass case after the worker build; its exact content is fingerprinted separately in the final summary. All Swift worker sources and the manifest match both build snapshots.

Only tracked source files and the explicit trial files entered the isolated builds. Cloud-sync duplicates and unrelated untracked files remained untouched. The evidence archive contains final measurements, prior experiment summaries, lifetime checks, toolchain identity, and file fingerprints. Raw local logs and build snapshots are retained separately. Engineering decisions and reports remain on `codex/engineering-notes` and must not be merged into implementation PRs.
