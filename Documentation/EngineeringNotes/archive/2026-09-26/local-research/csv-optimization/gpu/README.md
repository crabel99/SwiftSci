# CSV GPU experiment

This experiment evaluates a narrow Metal acceleration point without changing SwiftSci. The GPU classifies commas, line feeds, quotes, and carriage returns. The CPU turns those masks into the existing `CSVRecordIndex`. Numeric conversion and DataFrame construction are outside these timings.

## Why this boundary

Each Apple GPU SIMD group classifies 32 input bytes and emits four 32-bit masks. There is no cross-thread dependency in classification. Index construction needs variable-length output and ordered row boundaries, so the first prototype leaves it on the CPU. Any quote sends the whole input through the original parser, preserving its quoted-newline and escaped-quote behavior. This is a conservative fallback, not a parallel quoted-CSV algorithm.

The CPU comparison includes native ARM NEON classification with the same mask output, both serial and parallel. This prevents a GPU advantage over a scalar byte loop from being mistaken for an advantage over the hardware's CPU instructions.

## Source and machine

- SwiftSci parser snapshot: `dc31b5f1afc7f92810cfd472f7269f0d05533438`.
- `SystemsCSVParser.swift` SHA-256: `c83a10a395003f0bac99c3460dac0e52c67d0fa2b9f93372023a0ab6b1b9f95e`.
- M4 Max, 16 physical CPU cores, 128 GiB memory.
- macOS 27.0, build 26A428, Swift 6.4, native ARM64 Release.
- Production one-million-row CSV SHA-256: `a72e18ea5a198ba174a2097686ade2472de671fbd10b9f270bf9e25535c44cf9`.
- The four-million-row input repeats the data section four times and retains one header. Values and row lengths match the production fixture distribution.

## Measurement rules

Each method has two warmups and nine timed repetitions. Method order rotates each repetition. File mapping and Metal pipeline creation occur before timing. The full-index GPU methods include buffer creation, an input copy when requested, command submission, synchronization, CPU materialization, and result destruction. The zero-copy method wraps the existing page-aligned mapped file in a shared Metal buffer. It waits for GPU completion before the borrowed pointer scope ends.

Classification-only methods reuse buffers. Those are diagnostic lower bounds, not end-to-end CSV results. Full-index methods create new output arrays each time. They preserve all field offsets, lengths, escaped-quote flags, and row boundaries. Fixtures are validated against the original parser before timing. Small tests also check empty input, CRLF, quoted newlines, escaped quotes, trailing delimiters, missing final newlines, malformed quotes, and 100 randomized byte strings.

All methods operate on a warm filesystem cache. They do not compare disk performance. No result here establishes complete CSV speed without integration into the column conversion pipeline.

## Apple constraints

Apple's [shared storage documentation](https://developer.apple.com/documentation/metal/mtlstoragemode/shared) requires producer completion before the other processor reads the shared resource. Unified memory removes a compulsory discrete-GPU transfer, but command submission and synchronization still exist. The experiment measures them.

Apple's [buffer wrapping API](https://developer.apple.com/documentation/metal/mtldevice/makebuffer(bytesnocopy:length:options:deallocator:)) can avoid an input copy when the memory meets the API's alignment and lifetime requirements. The copied-input variant measures the fallback cost for ordinary allocation.

The installed Metal compiler rejects a shader with a `double` pointer with `'double' is not supported in Metal`. `correctness.txt` records that compiler diagnostic. This blocks a straightforward Float64 conversion kernel. Using Float32 would change scientific CSV semantics. A software Float64 converter or integer decimal parser would need its own accuracy proof and benchmark.

## Reproduce

```sh
xcrun clang -O3 -c classify.c -o classify.o
xcrun swiftc -O -whole-module-optimization SystemsCSVParser.swift main.swift classify.o -o csv-gpu
./csv-gpu --check
./csv-gpu /Users/crabel/local-ai/spl/swiftsci/benchmark/data-1000000.csv
./csv-gpu data-4000000.csv
```

## Results

| Method | 1M rows, ms | 4M rows, ms |
| --- | ---: | ---: |

| cpu_neon_classify_only | 1.861 | 7.425 |
| gpu_resident_classify_only | 0.756 | 1.375 |
| cpu_original_index | 21.128 | 84.325 |
| cpu_bitmask_index | 22.762 | 88.272 |
| cpu_neon_index | 7.949 | 31.647 |
| cpu_parallel_neon_index | 6.485 | 25.427 |
| gpu_copy_index | 8.723 | 39.085 |
| gpu_no_copy_index | 7.671 | 30.824 |

GPU no-copy index creation is 18.3% slower than parallel NEON at 1M rows and 21.2% slower at 4M. Do not enable GPU in the production CSV reader on this evidence. The classification kernel is useful research, but complete index construction determines this decision. The historical scalar baseline is not the current optimized production parser.

A production integration needs two improvements before another attempt: generate compact offsets directly on the GPU or eliminate CPU output materialization, and retain buffers across calls with a demonstrated workload. Neither is implemented here. Numeric Float64 conversion remains on CPU.

The reproducible candidate is in `SwiftSci/Benchmarks/CSVAcceleration`. It loads the historical parser with `git show` during build rather than maintaining a duplicate. Raw JSON and correctness output remain beside this report.
