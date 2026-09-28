# CSV ingestion grounding

Inspected SwiftSci `2694d303f8`, Kiraa `fc5d957401f7`, installed pandas 3.0.6 and its matching C/Cython source. Production source is unchanged. The only executable probe compiled the existing CSV scanner with a small driver to inspect layout and EOF behavior. No competing performance benchmark ran.

## Recommendation

Start with one internal flat, ragged field index and keep the existing byte scanner's tokenization rules. Route both file readers through that index, and keep `SystemsCSVParser.parse(buffer:) -> [[CSVFieldOffset]]` as a compatibility wrapper. This removes a measured structural allocation cost without changing numeric inference or public column storage. Keep pointer use inside `Data.withUnsafeBytes` while making that change.

Follow with a byte-based null matcher for numeric columns. Parallel scanning and faster numeric conversion come after those two changes have separate measurements. CSV is already column-parallel in SwiftSci. Merely adding that feature would not address the difference from Kiraa.

## Current SwiftSci path and cost

`DataFrame.init(csv:options:)` calls `CSVReader.read`. It maps the file, scans every byte into nested field-offset arrays, decodes and deduplicates headers, chooses a row limit, then converts columns concurrently. Each typed column initializer scans values again to count nulls. The lazy CSV source also calls this reader. The stream reader builds the entire field index before yielding chunks; it is currently chunked output rather than bounded-memory tokenization.

Evidence: [public entry](/Users/LOCAL_USER/Documents/src/SwiftSci/Sources/SwiftDataFrame/Core/DataFrame.swift:61), [file reader](/Users/LOCAL_USER/Documents/src/SwiftSci/Sources/SwiftDataFrame/IO/CSVReader.swift:27), [column conversion](/Users/LOCAL_USER/Documents/src/SwiftSci/Sources/SwiftDataFrame/IO/CSVReader.swift:225), [stream reader](/Users/LOCAL_USER/Documents/src/SwiftSci/Sources/SwiftDataFrame/IO/CSVReader.swift:472), [column initializer](/Users/LOCAL_USER/Documents/src/SwiftSci/Sources/SwiftDataFrame/Columns/TypedColumn.swift:31).

The scanner allocates a new array for every row and calls `reserveCapacity(16)`. A local arm64 Release probe measured `CSVFieldOffset.stride == 24` and actual capacity 17 for a three-field row. That is 408 bytes of reserved field payload per row, about 408 MB decimal at one million rows, before array bookkeeping, file pages, and output columns. A flat index retaining three fields and one row boundary requires about 80 bytes per row before capacity slack. This is a storage arithmetic estimate, not an RSS prediction. The previous whole-process CSV peak was 584.4 MiB and includes benchmark setup and allocator caches.

Evidence: [scanner allocation](/Users/LOCAL_USER/Documents/src/SwiftSci/Sources/SwiftDataFrame/IO/SystemsCSVParser.swift:48), probe `/private/tmp/swiftsci-csv-grounding/main.swift`, [benchmark report](/Users/LOCAL_USER/local-ai/spl/swiftsci/production-comparison/results/20260926T033814Z/REPORT.md).

Every inferred Int64 and Double cell currently constructs a String and hashes it against `nullValues`, then parses the original bytes again. Most such Strings are short and need not imply a heap allocation, but decoding, String machinery, and hashing remain work. The first 1,000 rows also run inference with String conversion and candidate checks. Explicit numeric overrides still construct Strings. No measured attribution yet separates indexing, inference, conversion, or output destruction.

Evidence: [inference](/Users/LOCAL_USER/Documents/src/SwiftSci/Sources/SwiftDataFrame/IO/CSVReader.swift:337), [integer cells](/Users/LOCAL_USER/Documents/src/SwiftSci/Sources/SwiftDataFrame/IO/CSVReader.swift:395), [float cells](/Users/LOCAL_USER/Documents/src/SwiftSci/Sources/SwiftDataFrame/IO/CSVReader.swift:417).

## What the comparison implementations actually do

Kiraa's URL reader keeps all byte consumption inside `withUnsafeBytes`. Its field grid is flat and rectangular. A serial first-row scan determines width; normal rows then use `row * colCount + col`. Large inputs attempt a parallel field scan with a 4 MiB gate. Chunks start after candidate newlines and report a dirty flag for embedded quoted newlines, unfinished quotes, or overflow rows. Any dirty chunk discards speculative output and invokes the serial scanner. Column conversion has its own workload gate and each worker owns output and numeric-conversion scratch storage.

Its default null matcher compares bytes by length; custom null strings become byte patterns once. It infers all numeric fields as Double, accumulating contiguous values and validity bits. If any non-null field fails, it retries that whole column as strings. These are useful mechanisms, but not identical semantics: SwiftSci distinguishes Bool, Int64, Double and Date, and its configured null set differs. Kiraa's rectangular padding and overflow-row behavior should not be copied into a ragged SwiftSci representation.

Evidence: [mapped lifetime](/Users/LOCAL_USER/Documents/src/kiraa-swift-pandas/Sources/SwiftPandas/IO/CSV/CSVReader.swift:310), [FieldGrid](/Users/LOCAL_USER/Documents/src/kiraa-swift-pandas/Sources/SwiftPandas/IO/CSV/CSVReader.swift:220), [null matching and column conversion](/Users/LOCAL_USER/Documents/src/kiraa-swift-pandas/Sources/SwiftPandas/IO/CSV/CSVReader.swift:407), [parallel scanner](/Users/LOCAL_USER/Documents/src/kiraa-swift-pandas/Sources/SwiftPandas/IO/CSV/CSVReader.swift:969).

Kiraa's numeric parser uses wrapping UInt64 arithmetic with a comment assuming fields are short. That is not a safe scientific-data assumption to import. A short literal beyond UInt64 can already overflow. Its speed cannot justify losing exact integers or changing invalid-value policy. [Numeric conversion](/Users/LOCAL_USER/Documents/src/kiraa-swift-pandas/Sources/SwiftPandas/IO/CSV/CSVReader.swift:545).

Pandas' default C engine uses contiguous token storage, a words array, and line-start/line-field arrays. It copies decoded tokens into its stream rather than retaining a zero-copy mapped field grid. The default low-memory reader converts batches of rows into typed arrays, consumes parser rows, and trims buffers. Cython numeric conversion writes directly into preallocated NumPy arrays while releasing the GIL. NA matching uses a C string hash table. Inference attempts int64, float64, bool, then object, with overflow/fallback handling. This reduces Python-level per-cell work and bounds tokenization intermediates even though final result chunks are retained and concatenated.

Evidence: [installed wrapper](/Users/LOCAL_USER/local-ai/spl/swiftsci/benchmark/.venv/lib/python3.14/site-packages/pandas/io/parsers/c_parser_wrapper.py:237), [pinned Cython parser](https://github.com/pandas-dev/pandas/blob/v3.0.6/pandas/_libs/parsers.pyx#L818), [token buffers](https://github.com/pandas-dev/pandas/blob/v3.0.6/pandas/_libs/src/parser/tokenizer.c#L144), [checked integer conversion](https://github.com/pandas-dev/pandas/blob/v3.0.6/pandas/_libs/src/parser/tokenizer.c#L1854). Downloaded exact source is under `sources/pandas-v3.0.6` next to this note.

## Flat index design and compatibility

Use an internal value with `fields: [CSVFieldOffset]` and `rowStarts: [Int]`, including a terminal offset. Row count is `rowStarts.count - 1`; width is the difference between adjacent starts. The field accessor checks that the requested column lies inside that row before indexing. A missing field stays missing and extra fields stay confined to their original row. No per-row padding or rectangular-width multiplication is needed.

The single scanner should produce this internal form. Public `parse(buffer:)` can materialize row arrays only for callers that request the public legacy result. Production readers consume the internal form directly. This preserves the existing public type and avoids maintaining two scanners with diverging quote rules. Migrate file and stream callers in the same change. No new compact-column dependency is necessary.

Keep all column workers synchronously joined inside the same `Data.withUnsafeBytes` closure. The current reader returns a pointer from that closure and uses it afterward at lines 74 and 526. Apple's documented pointer lifetime ends with the closure. Retaining Data is not a substitute for the API's lifetime guarantee. [Apple documentation](https://developer.apple.com/documentation/foundation/data/withunsafebytes(_:)).

## Byte null matcher contract

Match the existing `parseString` result, not raw bytes blindly. Existing behavior removes paired surrounding quotes first, trims ASCII space/tab/CR/LF next, then unescapes doubled quotes. Therefore a field containing quoted spaces can match a null token. Do not trim again after unescaping, and do not lowercase tokens. Default null matching is case-sensitive with an explicit token set.

A safe fast path normalizes the field slice using the same boundaries, checks ASCII null patterns by length and bytes, and leaves escaped fields or non-ASCII custom tokens on the existing String path. Swift String equality includes Unicode canonical equivalence, so raw UTF-8 matching for arbitrary custom tokens could change behavior. Invalid UTF-8 also differs between escaped and ordinary paths today. Empty content must match only when the configured set contains the empty string; Kiraa's custom matcher treats empty as missing unconditionally, which is not the contract to copy.

Evidence: [String normalization](/Users/LOCAL_USER/Documents/src/SwiftSci/Sources/SwiftDataFrame/IO/VectorizedByteParsers.swift:138), [configured null set](/Users/LOCAL_USER/Documents/src/SwiftSci/Sources/SwiftDataFrame/IO/CSVReadOptions.swift:9).

## Inherited correctness gaps, separate from the optimization

These are source findings, not new failures introduced by the proposed layout:

- `parseInt` accumulates a positive signed Int with checked multiplication/addition, then applies sign. Int.min and excessive magnitudes can trap before the fallback parser can run. Use checked negative accumulation or an unsigned magnitude with explicit bounds in a separate correctness commit.
- The sample fixes the inferred type after 1,000 rows. An incompatible later value can turn into nil silently. A later all-column validation/promotion policy needs explicit design, especially across stream chunks.
- File parsing pads short rows with nil and ignores extra fields. The internal String parser throws on mismatched widths. Preserve the file contract in the optimization rather than silently unifying both policies.
- EOF after a delimiter drops the entire final record: the probe `a,b\n1,` produced only the header, while `a,b\n1,\n` produced both rows. The scanner only emits the tail when `fieldStart < count`. This is a small separate regression fix if included.
- Header deduplication differs between file and stream paths; the stream does not apply the file reader's deduplication. Type overrides for int32/float32 produce Int64/Double today. Non-ASCII delimiters use only their first UTF-8 byte in the file path. These policies require separate decisions.

## Research and Apple Silicon implications

The Microsoft SIGMOD 2019 paper explains why arbitrary CSV chunks cannot safely assume that a newline is a row boundary. It supports speculative parsing with validation and recovery, and a conservative two-pass alternative. It does not justify a newline-only split. Kiraa's clean/dirty scheme is an example of a narrower recoverable approach. [Ge et al., Speculative Distributed CSV Data Parsing](https://www.microsoft.com/en-us/research/uploads/prod/2019/04/chunker-sigmod19.pdf).

Lemire's number-parsing work treats correct binary rounding and uncommon decimal inputs as part of the algorithm. SwiftSci's decimal loop currently performs one floating division per fractional digit; replacing it with an integer mantissa/exponent conversion needs round-trip, overflow, underflow, subnormal and long-mantissa evidence. Importing an established conversion routine may be better than inventing another one. [Number Parsing at a Gigabyte per Second](https://arxiv.org/abs/2101.11408).

SIMD structural scanning is a possible later stage. The simdjson paper separates structural discovery from interpretation and demonstrates why that decomposition helps. CSV doubled quotes require their own grammar treatment. It is not evidence that copying JSON quote-mask logic is correct for CSV. [Parsing Gigabytes of JSON per Second](https://arxiv.org/abs/1902.08318).

On this Apple Silicon target, flat arrays remove allocation bookkeeping and dependent row-buffer loads before any instruction-set change. Shared CPU/GPU memory does not remove UTF-8 interpretation, output allocation or command synchronization. Start with CPU allocation and stage profiles; only add SIMD or scan parallelism after the remaining scan share warrants it. The previous [hardware note](/Users/LOCAL_USER/local-ai/spl/swiftsci/filter-profiling/holistic-fixes/hardware-research.md) links Apple's CPU Counters and Swift specialization guidance.

## Measurement and acceptance

Record scanner time, type inference time, conversion time, destruction time, field capacity, allocation counts if Instruments is available, peak RSS, and total public-read latency. Compare the existing fixture plus widths 1/3/32, quoted multiline text, long strings, custom nulls, empty files, header-only files, row limits, ragged rows and no trailing newline. The flat representation must reconstruct exactly the old field offsets on the compatibility corpus. Include column types, null placement and full values in file/stream comparisons.

Then test byte null matching independently against the old String implementation using default/custom ASCII tokens, quoted and escaped fields, whitespace, Unicode tokens and invalid UTF-8 fallback cases. Run Debug and Release checks before serial paired Release benchmarks. Keep inherited bug fixes in separate commits so timing and semantic changes remain reviewable.
