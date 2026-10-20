# Quoted CSV spare capacity comes from parser-buffer reuse

October 20, 2026. The current reader requests the correct output capacity. A freed parser allocation supplies more space than requested, and the resulting Swift Array retains that spare capacity. A measured exact-count prepass removes the surplus but increases CPU cost. Keep the current production implementation unchanged while investigating a single-pass way to reduce parser allocation growth.

## What the trace proves

The historical PR #39 reader reproduces the excess in three of three fresh processes; its predecessor does not. The current local source at `546510bb7df19fc87a664bded5947c738011ee1d` reproduces it too. A 250,000-row quoted input is sufficient. The tested single-column and unquoted controls do not show the large surplus.

The parser stores field coordinates in a growing contiguous array. Its elements and `Double?` output elements both occupy 16 bytes in these builds. The instrumented current reader produces this sequence:

1. The field array grows past capacity 401,406 and releases its previous block.
2. A numeric column builder requests capacity 250,000.
3. Its array receives the same data address as the released field block, with capacity 401,406.
4. The builder finishes with count 250,000 and capacity 401,406. It does not grow during construction.

See the [pointer trace](trace.log), [column output](trace-columns.json), and [audit](audit.json). Instrumentation can change which concurrent column receives the block, so column identity is not part of the conclusion. Instrumented builds are excluded from timing.

The [standalone reproducer](AllocatorReproducer.swift) triggers the same address reuse without SwiftSci. Its [output](allocator-reproduction.log) confirms that a parser-shaped temporary array is enough. This distinguishes allocator block reuse from an erroneous row estimate or a retained parser owner. It does not identify Apple's exact internal free-list policy, and capacity is not a portable performance contract across allocators or OS versions.

The 60% capacity surplus on one column is real live storage in these measurements. For one million rows, replacing capacity 1,605,630 with 1,000,446 removes 9,682,944 bytes, about 9.23 MiB. That is not a 60% increase in total dataframe memory. Peak RSS, live malloc bytes and logical payload are separate measurements.

## Measured alternative and decision

The throwaway [preallocation patch](presized.patch) counts fields and rows before allocating parser buffers. Its quote-state scan includes escaped quotes and embedded newlines. The prototype changes the serial fallback, including small unquoted inputs. Only a large unquoted fast-path control is timed here; small unquoted performance remains unqualified. Both readers still infer their schemas from the same files. The extra scan is inside the timed API call; no fixture row count or supplied schema is given to the reader.

| Million-row quoted input, four columns | Current reader | Preallocation trial |
| --- | ---: | ---: |
| Total CPU time | 47.26 ms | 60.55 ms |
| Elapsed time, including result release | 26.69 ms | 41.16 ms |
| Peak process RSS | 242.88 MiB | 166.97 MiB |
| Live heap increase with output held | 70.31 MiB | 61.08 MiB |

The median paired CPU increase is 27.7%. Displayed CPU times are medians of worker medians, so their quotient need not equal the median paired ratio. The trial saves about 76 MiB of peak RSS and 9.23 MiB of held heap in this case. Across the four quoted workloads, CPU increases 25.5–33.5%; every paired range remains above parity. The unquoted control is near parity. See [all results](RESULTS.md).

This is a useful memory-versus-computation tradeoff, not an unconditional efficiency improvement. A memory-constrained application might prefer it. The evidence does not justify silently making that choice for every caller or adding a public policy solely for this prototype. No production patch, commit or PR was made for the prepass.

The next target is the parser's growing temporary index. Evaluate an approach that limits discarded allocations while preserving sequential scanning and cheap field lookup. Include any later compaction, materialization or lookup cost. Do not trim finished output arrays by copying them, purge process-wide allocator caches, or increase reservation estimates without measuring the resulting CPU and memory costs. The current capped reservation also protects long-record inputs; a replacement must preserve that boundary.

## Scope and verification

The [plan](PLAN.md) was written before timing. Five cases have five alternating timing pairs and three separate memory pairs, for 80 workers. Timing workers use two warmups and five measured samples; memory workers use one operation without warmup. All 250 timed outputs and 30 memory outputs pass complete independent value checks. The seven additional explicit string fixtures pass on both builds, covering quoting, escaped quotes, embedded newlines, CRLF, commas, nulls and multiple rows.

Both variants use the same dependency objects and compiler configuration: Release optimization, Apple silicon, a macOS 14 deployment target, and no coverage or sanitizers. The machine runs macOS 27.0.1, build 26A434, on AC power. CPU uses process user plus system time across native threads. CPU and elapsed measurements include the public CSV read and result release. Input files are cached, schema inference is enabled on both sides, and output validation is outside timing. These measurements do not include downstream application work or establish energy savings.

Memory workers capture process peak RSS before output validation. Their high-water marks include process setup and file reading. Live heap means malloc bytes in use, not all possible memory owners or physical footprint. The [audit](audit.json) verifies source blobs, the single-file experimental patch, matching dependency objects, absence of debug logging in measured sources, the traced pointer match and independently recomputed medians.

The earlier historical PR comparison remains unchanged. This report explains its quoted-CSV capacity finding using the current source. The scalar-gather work from October 19 remains at `546510bb7d` with no new changes.

## Reproduction and retained evidence

The [evidence archive](evidence.tar.gz) contains raw worker records, build receipts, minimization results and comparison metadata. [Checksums](evidence-sha256.json) cover the archive and every member. The [summary](summary.json) and [semantic checks](checks.json) are readable separately.

`reproduce.py` reruns the historical diagnostic binaries. `minimize.py` creates deterministic numeric fixtures and checks reduced cases. `AllocatorReproducer.swift` can be compiled with `xcrun swiftc -O` and run with argument `250000`. `prepare-trial.py` exports the pinned source and creates the experimental snapshot; `build.py`, `compare.py`, `check.py` and `summarize.py` build and summarize the comparison. `audit.py` also requires the original instrumentation artifacts from the archive and verifies the complete diagnosis. The scripts name their existing local source and dependency-cache prerequisites. Use a fresh scratch directory for another run; the runner refuses to overwrite measurements.

The diagnostic snapshots stay outside production worktrees. The [instrumentation patch](instrumented.patch) records the two temporary trace locations. These artifacts belong only to `codex/engineering-notes` and must not enter an implementation PR.
