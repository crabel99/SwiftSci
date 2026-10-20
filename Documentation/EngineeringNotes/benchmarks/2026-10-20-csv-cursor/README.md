# CSV field traversal follow-up

The cursor removes the previous two-column CPU penalty in a direct comparison with production, but it does not establish a general resource improvement. Keep the bounded-block index experiment. Do not promote either new traversal implementation into the production default yet.

This study follows the [single-pass block experiment](../2026-10-20-csv-blocks/README.md). The unchanged production reference is `546510bb7df19fc87a664bded5947c738011ee1d`. All source changes remain scratch prototypes. This report and its evidence belong only to `codex/engineering-notes`.

## What changed

The active-block reference is byte-for-byte identical to the prior experiment. It appends into one mutable block and publishes completed blocks without copying all field entries into a final contiguous array.

Two alternatives tested the cost of reading that index:

- The **cursor** holds the current field block for one column. It advances its row position and only changes blocks at a boundary. Thirteen inference and construction loops use it. It still checks ragged row lengths and resets after inference.
- The **specialized reader** selects flat or blocked storage once per column and calls the existing construction logic through a generic row view. It adds no cursor state. The compiler can specialize the loop for each storage representation.

Neither alternative changes the parser or its block builder relative to the active-block reference. Both retain the same schema inference, null handling, and native column parallelism.

## Direct comparison with production

The cursor's full read includes index construction, inference, conversion, column allocation, and result release. CPU changes are medians of five paired ratios, not ratios of the displayed time medians.

| Input | CPU ms, production → cursor | Paired CPU change | Peak RSS MiB, production → cursor | Held heap MiB, production → cursor |
| --- | ---: | ---: | ---: | ---: |
| Quoted, 250,000 × 4 | 12.11 → 12.47 | +2.6% | 65.08 → 48.53 | 17.63 → 15.33 |
| Quoted, 1,000,000 × 4 | 47.53 → 49.24 | +2.5% | 241.31 → 180.67 | 70.31 → 61.08 |
| Quoted, 1,000,000 × 2 | 23.23 → 23.12 | −0.5% | 116.16 → 102.44 | 39.78 → 30.55 |
| Unquoted, 1,000,000 × 4 | 42.26 → 43.21 | +1.8% | 159.36 → 159.41 | 61.08 → 61.08 |

The two-column CPU ratios span 0.988–1.045. Treat that as near parity, not a demonstrated CPU improvement. Every pair for the 250,000-row case and the large unquoted control used more CPU. The million-row four-column ratios span 0.969–1.044, so its small median CPU increase is less consistent.

Held-out inputs retain the large quoted memory savings, but establish no additional general CPU benefit. The specialized reader also provides no repeatable overall gain against the active-block reference. On the thirteen-column held-out input, every pair used more CPU, with a +2.4% median change.

Full results:

- [Cursor against active blocks](RESULTS.md) and [held-out inputs](heldout-RESULTS.md)
- [Specialized reader against active blocks](specialized-RESULTS.md) and [held-out inputs](heldout-specialized-RESULTS.md)
- [Cursor against production](production-RESULTS.md) and [held-out inputs](heldout-production-RESULTS.md)

## What the isolated probes tell us

A separate Release executable walks already-built indexes and checks a checksum of every returned offset. It excludes file reading, parsing, value conversion, and output construction.

| Million-row input | Production lookup CPU ms | Active-block lookup CPU ms | Cursor lookup CPU ms |
| --- | ---: | ---: | ---: |
| Quoted, 2 columns | 1.501 | 1.831 | 2.180 |
| Quoted, 4 columns | 3.261 | 3.837 | 4.356 |
| Unquoted, 4 columns | 3.257 | 3.563 | 4.564 |

The cursor is slower in this isolated loop even though it improves the full two-column read against the active-block reference. We cannot attribute that full-read improvement simply to cheaper field lookup. Compiler optimization of the surrounding conversion loop, allocation behavior, and scheduling remain possible contributors; this experiment does not isolate them.

Another probe times index construction and release with the input already mapped. Production versus active-block CPU medians are 9.443 versus 9.356 ms for quoted two-column input, 19.330 versus 16.964 ms for quoted four-column input, and 14.077 versus 14.080 ms for unquoted four-column input. The active builder itself does not show a construction penalty in these cases.

These probes compile the actual parser and index sources in a smaller compilation unit. They diagnose behavior but do not exactly partition the public API's measured time. Do not add their medians together and claim an exact accounting of a full read. [Diagnostic summaries](diagnostic-summary.json) preserve the numbers.

## Decision and next experiment

Preserve both prototypes as evidence. Do not add the generic reader to production for these results. The cursor remains a possible memory-versus-CPU choice, but its extra state has not earned a general default.

The next experiment should reduce index bytes before adding more per-field machinery. A packed field currently contains two machine-width integers and occupies 16 bytes. Four million fields therefore require about 61 MiB of element storage, plus row starts and allocation overhead. Test a narrower offset representation only when a checked file-size bound guarantees it can represent every field. Keep a full-width path for larger input. Account for flag bits, long fields, ragged rows, and boundary values. This is a proposed experiment, not an implemented improvement or a claim about cache utilization.

## Verification and limits

The full-API studies ran 480 fresh workers, with 1,500 measured timing samples and 180 separate memory samples. Input bytes, inference rules, output checks, Release settings, and dependency objects match within each comparison. Each case uses five alternating timing pairs and three memory pairs. AC power was recorded at the beginning and end. Ordinary desktop activity remains part of the environment; no samples were discarded for being slow.

Both candidates passed seven explicit reader fixtures and matched the baseline on 2,022 parser cases. The cursor also matched 2,800,581 individual offsets across 19 ragged, empty, wide, and block-boundary inputs, including nonzero starting rows. All timed numeric outputs passed the independent shape and value checks.

Sixteen existing tests in four CSV suites passed for each candidate. These cover column null counts, null matching, numeric conversion, and the numeric null fast path. They ran in separate Release builds with internal test access enabled. The timing binaries were unchanged. This was not a full SwiftSci test-suite run; existing tests tied to the old flat internal storage were not rewritten for these prototypes.

The isolated probes add 75 worker processes and 600 timing samples. Lookup workers check identical checksums across variants. Their evidence does not measure energy, CPU instructions, allocation counts, or cache misses. CPU time is summed user-plus-system time across the process's threads. Peak RSS and held malloc bytes describe different memory boundaries. No GPU or NPU comparison is implied.

## Evidence

[Audit receipt](audit.json), [audit program](audit.py), [raw evidence archive](evidence.tar.gz), and [archive hashes](evidence-sha256.json) preserve source identities, build commands, worker records, test logs, and validation checks. The audit recomputes the paired CPU summaries.

[Active-block patch](active.patch), [cursor patch](cursor.patch), and [specialized-reader patch](specialized.patch) each apply to the pinned production reference. [Replay preparation](replay.py) exports that reference and prepares a fresh experiment directory. It requires a Git checkout containing the commit, this machine's Xcode installation, and the cached SwiftSci dependency objects used by `build.py`. Run `python3 replay.py REPOSITORY NEW_DIRECTORY` and follow its printed commands. New runs produce new evidence rather than reproducing historical timings exactly.
