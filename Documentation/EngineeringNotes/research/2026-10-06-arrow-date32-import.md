# Signed Arrow date32 import

Date: 2026-10-06. Implementation commit: `32badeece6728e9b75054b2f997459c377dfb69e` on `codex/arrow-chunk-import`. Parent: `fafa07a3de4b489636c89db42616b8f89c770082`. This fix is separate from the preceding owned-import performance commit.

## Defect and repair

Arrow's date32 builder returns `ArrowArray<Date>`. SwiftSci requested `ChunkedArray<Int32>` through a forced generic cast, so importing a normal date32 column crashed. The new public-API regression reproduced that exact cast failure before production code changed.

The bridge now requests `ChunkedArray<Date>`. It visits each chunk and uses Arrow's existing `FixedArray<Int32>` accessor over that chunk's ArrowData to decode signed days and nulls. It converts days to Double before multiplying by 86,400. The result remains an owned `TypedColumn<Date>`; all three null strategies preserve date nulls, matching the prior intended behavior. No dependency revision, public signature, allocator, or asynchronous ownership contract changes.

The signed accessor avoids a second defect in pinned Arrow 21.0.0. Its Date32Array subscript reads UInt32 and multiplies before conversion, which misrepresents pre-epoch dates and overflows for sufficiently large positive dates. Apache already merged [PR #194](https://github.com/apache/arrow-swift/pull/194) on September 17, 2026. Its correction reads Int32 and converts before multiplying. At the time of this check, [v21.0.0](https://github.com/apache/arrow-swift/releases/tag/v21.0.0) remains the latest release and lacks that correction. Revisit this adapter when a released dependency includes it. No duplicate upstream issue was opened.

The [Arrow schema specification](https://github.com/apache/arrow/blob/main/format/Schema.fbs) defines date32 as signed days since the Unix epoch. The adapter uses the pinned library's existing null and signed-value accessors, rather than adding a raw-buffer decoder.

## Validation

Before the fix, `DataFrameArrowDate32Tests/builderRepresentation()` crashed while casting `Arrow.ChunkedArray<Foundation.Date>` to `Arrow.ChunkedArray<Swift.Int32>`. One test ran and failed.

After the fix, the complete SwiftDataFrame Release target passed 270 test definitions and 363 executions including parameters, with no failures or skips. Four new test definitions cover canonical Arrow builder output, pre-epoch dates, the full Int32 day range, the UInt32 seconds boundary, leading and interior empty chunks, all-empty columns, all-null columns, and each null strategy. The ownership test mutates the producer's buffer after import and releases the source. Imported values remain unchanged, and the original buffer is released.

The tests ran sequentially on Apple M4 Max with macOS 27.0, Xcode 27.0, and Swift 6.4. The package retains its macOS 14 deployment target. Actual execution on macOS 14 was not tested. The full multi-module suite and a new sanitizer run were not performed. This is a correctness fix for date32; the preceding numeric import benchmark remains evidence for its recorded commit and was not rerun here.

## Boundaries

The fix cannot recover information already lost when a producer constructs its Arrow buffers. Arrow 21.0.0's builder also mishandles pre-epoch times within a day; these tests intentionally construct exact midnight dates. PR #194 repairs that builder separately. Date64 import and export round-trip support remain outside this commit.

The build snapshot contained tracked files and the explicit regression file. Unrelated cloud-sync duplicates were left untouched. Test inputs were checked against the committed file hashes. The shared integration benchmark executable was restored to its preserved fingerprint after testing. No branch was pushed and no PR was created.

Engineering decisions and compact evidence are archived only on `codex/engineering-notes`. The implementation branch contains the production correction and regression tests.
