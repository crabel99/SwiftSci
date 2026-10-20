# Single-pass CSV index storage trial

The active-block prototype reduces quoted CSV memory without the second scan used in the [earlier capacity experiment](../2026-10-20-csv-capacity/README.md). It does not establish a universal resource improvement. Keep it as an experiment until we resolve the remaining CPU costs or define a caller constraint that justifies them.

All variants start from `546510bb7df19fc87a664bded5947c738011ee1d`. The production checkout remains unchanged. This directory belongs to the engineering-notes branch and must stay out of a production PR.

## Question and alternatives

The earlier trace proved that a growing parser array releases large temporary buffers. A later column allocation can reuse one of those buffers and retain more capacity than requested. A counting prepass removed that excess but increased CPU work by about 26–34% in the tested quoted cases.

This trial replaces that growth pattern with blocks of 16,384 packed fields, about 256 KiB of element storage each. This block size is an experimental allocation bound, not a measured Apple cache-size optimum. The first block reserves at most the input byte count divided by eight. Subsequent blocks reserve one block. Allocator rounding can exceed the requested capacity. Row-start storage retains its existing growth policy.

We compared three implementations, each against a freshly run, unchanged baseline:

1. **Nested block append.** Append directly into the last array in the block list. Keep blocks during column construction.
2. **Active block.** Append into one mutable array. Publish it into the block list when full. Keep blocks during column construction.
3. **Final contiguous copy.** Use the active builder, then combine its blocks into an exactly requested contiguous index before column construction. Keep the existing field-lookup representation.

The first two require a storage choice and a block lookup for each field. The third removes that lookup cost but copies the entire index and temporarily holds both representations. No variant adds a public API, changes the input schema policy, or scans CSV syntax twice. All preserve the unquoted fast parser; the first two still change the common index lookup used after that parser.

## Results and decision

Results below use each variant's own matched baseline. CPU percentages are medians of five paired ratios. They are not ratios calculated from the displayed medians, and they are not energy measurements.

| Quoted input | Alternative | Paired CPU change | Peak RSS MiB, baseline → trial | Held heap MiB, baseline → trial |
| --- | --- | ---: | ---: | ---: |
| 1,000,000 rows × 4 columns | Nested append | +15.3% | 241.34 → 180.66 | 70.31 → 61.08 |
| 1,000,000 rows × 4 columns | Active block | −0.1% | 241.31 → 180.64 | 70.31 → 61.08 |
| 1,000,000 rows × 4 columns | Final copy | +0.3% | 241.34 → 241.72 | 70.31 → 61.08 |
| 1,000,000 rows × 2 columns | Nested append | +21.5% | 116.16 → 102.45 | 39.78 → 30.55 |
| 1,000,000 rows × 2 columns | Active block | +5.6% | 116.16 → 102.44 | 39.78 → 30.55 |
| 1,000,000 rows × 2 columns | Final copy | +0.4% | 116.12 → 132.95 | 39.78 → 30.55 |

The active block is the candidate to investigate further. At one million rows and four columns it saved about 61 MiB of peak RSS and 9.23 MiB of held heap, with paired CPU ratios spanning 0.986–1.016. Its two-column CPU ratios all exceeded one, spanning 1.015–1.117. The final copy kept CPU near parity on that case but increased peak RSS. It does not replace the active-block candidate for a peak-memory-constrained workload.

Five held-out shapes tested the active block. A 131,071-row, seven-column input used 1.4% less CPU and reduced peak RSS from 63.95 to 44.34 MiB. A 75,001-row, thirteen-column input had a +1.5% median CPU ratio with pairs on both sides of one, and reduced peak RSS from 66.94 to 46.08 MiB. Small unquoted input used about 5.1% more CPU, 0.32 to 0.33 ms. Small quoted input was near parity. The 100,000-row primary case had a wide CPU ratio range, 1.005–1.508; we retained that variation rather than discarding a pair.

These results support a memory benefit on the tested large quoted inputs. They do not yet support replacing the default for every input shape. The next experiment should isolate and reduce the repeated field-traversal cost while retaining bounded index storage. Do not promote the final copy based only on its CPU result or the active block based only on the four-column case.

Full measurements:

- [Nested block append](RESULTS.md)
- [Active block](active-RESULTS.md)
- [Active block held-out inputs](heldout-RESULTS.md)
- [Final contiguous copy](flattened-RESULTS.md)

## Validation and measurement boundaries

The study ran 320 fresh worker processes, producing 1,000 measured timing samples and 120 separate single-operation memory samples. Each comparison used five alternating timing pairs and three memory pairs per input. Timing workers warmed up twice, then measured five API calls. Memory workers did not warm up.

CPU user-plus-system time and elapsed time include the public CSV read, schema inference, index construction, field access, output construction, and result release. The final-copy variant's copying cost is inside those clocks. Full formula-based output checks run outside the timed interval. Memory snapshots occur before validation. Peak RSS includes process setup and read-time temporaries. Held heap is the change in malloc bytes in use while holding the result; it is not a complete physical-memory accounting. Allocation counts, memory bandwidth, isolated lookup time, and energy were not measured.

All variants use the same Release compiler flags, cached dependency object bytes, fixture bytes, and output validation. Native CPU parallelism remains enabled. AC power was recorded at both ends of each run. File-cache conditions are warm. These are same-machine CPU comparisons, with no GPU or NPU claims.

Seven explicit public-reader fixtures passed for every variant, covering escaped quotes, embedded newlines, CRLF, quoted commas, missing final newline, empty quoted values, and multiple rows. A deterministic parser comparison matched all offsets and escape flags across 2,022 cases, including randomized malformed input, block boundaries, unfinished rows, and a two-million-character field. Matching malformed behavior preserves compatibility; it does not certify that behavior as standards-compliant. Every timed numeric output passed its independent shape and value checks. This is focused module validation, not a full SwiftSci test-suite run.

The capacity probe found the oversized 401,406-element column buffer in the baseline at 250,000 rows. Each prototype produced four buffers with capacity 250,878 on this machine. This is an allocator-dependent observation, not a portable exact-capacity guarantee.

## Evidence and replay

- [Audit receipt](audit.json) checks source, binary, fixture and harness hashes, matching dependency objects, worker coverage, semantic records, and recomputed CPU summaries.
- [Raw evidence archive](evidence.tar.gz) contains every worker record, run plan, check record, and build receipt.
- [Archive member hashes](evidence-sha256.json) verify those records.
- [Nested-append patch](blocked.patch), [active-block patch](active.patch), and [final-copy patch](flattened.patch) apply to the pinned baseline.
- [Replay preparation](replay.py) exports the pinned baseline, applies those patches, copies the measured programs, and regenerates fixtures. Pass a Git checkout containing the pinned commit and a new output directory.

The build script requires this machine's SwiftSci dependency object cache and Xcode installation. Run `python3 replay.py REPOSITORY NEW_DIRECTORY`, then follow the command list it prints. Performance replay produces new evidence; it does not reproduce historical timings exactly. The original scratch directory is `/private/tmp/swiftsci-csv-blocks-20261020`.
