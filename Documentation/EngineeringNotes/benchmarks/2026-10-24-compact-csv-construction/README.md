# Reduce compact CSV construction CPU

The local branch is `codex/csv-compact-construction`, commit `5b9c90297723cf53dcba17299c57778688e282e2`. It starts at the matched-caller checkpoint `36a93f7dfd54524fc7360fd52930366190db8d01`. The source commit changes the compact CSV builder and adds one boundary test file. Nothing was pushed, and the existing PR branches remain unchanged.

The retained candidate accumulates validity bits in a scalar word and flushes that word at each 64-row boundary or finalization. Two complete reference-workflow panels show 1.3% and 2.5% less charged CPU for compact storage. The large household CSV read uses 2.7% less operation CPU in both panels. Peak RSS is essentially unchanged. This is a modest CPU saving, not a new memory reduction or a demonstrated general latency gain.

The source commit contains no engineering report or raw benchmark evidence. Those remain here on `codex/engineering-notes`.

## Start with the observed cost

The [preceding matched-caller study](../2026-10-24-matched-caller-throughput/README.md) found a memory benefit but no general CPU improvement from compact storage. Its household read used about 6% more operation CPU. A reduced replay removes contention, sorting, and matrix construction while retaining the reference CSV. The original compact worker still uses 4.1% more charged CPU than optional storage across 32 one-caller queues and 128 reads.

`measure.py --worker <parent-worker> --out <new-directory>` exits 1 when its qualified compact CPU ratio exceeds the recorded 1.02 diagnostic threshold. This is a local performance diagnosis, not a CI timing gate or a universal acceptance limit. The original builder is semantically correct, so the added correctness test is not presented as a test that fails before this optimization.

The ranked hypotheses were per-value validity bookkeeping, allocation or copying, and compiler specialization. Native sampling places work in the compact builder's append routine, alongside parsing and record scanning. It does not identify a dominant whole-column copy. Sampled timings are explicitly excluded from performance evidence. Both final binaries retain append symbols, so the gain cannot be attributed solely to removing a function call.

## Compare the rejected construction choices

| Candidate | Observation | Decision |
| --- | --- | --- |
| Move all missing-value handling into a helper | Household read saves 2.6% CPU. Synthetic present and sparse cases improve, but alternating and all-missing cases cost 2.2% and 4.8% more CPU. | Reject as a general construction improvement. |
| Add a word-boundary growth check to that helper variant | About 0.5% less CPU than the helper variant in the household screen. | Insufficient evidence to justify retaining it. This variant did not receive the density panel. |
| Move only bitmap allocation into a helper | Changes stay around -0.6% to +0.1% across null patterns. | No clear gain. |
| Accumulate a validity word in scalar state | Every synthetic null pattern improves; the complete reference panels also reduce compact CPU. | Retain locally with the limits below. |

The archive preserves each source snapshot, build receipt, raw screen, and decision. Rejected candidates are not folded into the source commit.

## Preserve the storage contract

The builder owns the growing Double array, optional bitmap, null count, and pending validity word. It constructs the existing `CompactNumericColumn` at finalization. Missing values still have NaN placeholders and cleared validity bits. Valid NaNs retain their payloads and remain valid. All-present columns retain a nil bitmap.

The bitmap is private during construction, so delaying a word flush changes no observable intermediate state. The first missing word initializes earlier words as valid. Later words grow the bitmap when the capacity estimate is too small. Finalization flushes a partial word and resets all builder state. No full-column scan, dtype narrowing, new public API, compiler override, or default-storage change is added.

## Check varied null patterns

Each synthetic CSV has 1,000,003 Double rows. Nonmissing values are exact binary quarters. Cases contain no missing values, a missing value every 97 rows, alternating missing values, or only missing values. An independent Python decoder checks native-bit hashes and null counts for both storage modes.

Each pattern uses six rotated rounds with parent optional, parent compact, candidate compact, and an identical-binary twin for each. Every queue contains four reads and one caller. All recorded CPU and RSS controls pass.

| Pattern | Candidate versus parent compact CPU | Parent peak RSS MiB | Candidate peak RSS MiB |
| --- | ---: | ---: | ---: |
| present | -2.04% | 24.25 | 24.56 |
| sparse | -1.32% | 24.43 | 24.48 |
| alternating | -4.59% | 22.31 | 22.28 |
| missing | -7.77% | 19.75 | 20.02 |

These synthetic inputs probe validity handling. They do not establish performance for general CSV formats or replace the reference datasets.

## Check complete reference workflows

The forward panel and a separately recorded reversed-order confirmation each complete 64 queues and 8,192 timed jobs. Each queue has four callers and 32 copies of each air read, air read/sort/matrix, household read, and household read/sort/matrix case. Caller count means worker processes, not CPU threads. Both builds use native CPU parallelism.

Both panels compare parent and candidate in optional and compact modes, each with an identical-binary twin. Eight rotated rounds put every label in every order position. The second panel reverses each order. No source or binary changes occur between panels. CPU and elapsed-time drift limits are 10%; RSS drift uses 5% plus 8 MiB per caller. Both panels pass these controls. A passing drift control does not certify a small performance difference.

The source receipts differ only for `CSVColumnBuilder.swift`; linked dependency hashes match. Schemas, input bytes, Float64 and Int64 types, null tokens, stable missing-last sorting, and matrix contracts are identical. Thirty-two full native-bit output checks pass per panel before and after timing. Timed outputs receive the established shape and type checks. Complete-queue timing includes output release, request dispatch, and controller work, but excludes process startup and full hashing.

| Panel | Storage | Parent CPU ms/job | Candidate CPU ms/job | CPU change | Parent peak RSS MiB | Candidate peak RSS MiB | Throughput change |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Forward | optional | 232.67 | 235.58 | +1.25% | 3507.2 | 3507.5 | -2.19% |
| Forward | compact | 231.58 | 228.49 | -1.33% | 2513.2 | 2512.7 | -0.89% |
| Reversed | optional | 209.36 | 209.76 | +0.19% | 3503.8 | 3504.3 | -0.44% |
| Reversed | compact | 210.62 | 205.30 | -2.53% | 2512.4 | 2510.7 | +2.67% |

Compact storage uses less paired-round CPU in 14 of 16 rounds. The median paired-round change is -1.73%. These rounds are not independent observations, and this count is not a confidence interval.

The unchanged optional path's pooled CPU rises 1.25% in the forward panel and 0.19% in the reversed panel. Its paired-round median changes direction, from +0.74% to -0.35%; across all rounds it is +0.22%, with lower CPU in 7 of 16 rounds. These measurements do not establish a stable default-path regression or improvement. They also cannot rule out a small effect. Retaining the candidate does not mean claiming exactly zero cost outside compact storage.

Compact throughput changes by -0.9% and +2.7% across the two panels. The resource result supports retaining a small CPU reduction. It does not justify a general wall-time claim. The large reference read remains slower in compact storage than optional storage in the same panels, so this change reduces rather than eliminates that construction overhead.

## Keep operation CPU separate from complete-queue CPU

| Panel | Compact case | Parent operation CPU ms | Candidate operation CPU ms | Change |
| --- | --- | ---: | ---: | ---: |
| Forward | Aotizhongxin-default/read | 13.857 | 13.292 | -4.07% |
| Forward | Aotizhongxin-default/sort-matrix | 17.990 | 17.400 | -3.28% |
| Forward | energy-common/read | 308.165 | 299.763 | -2.73% |
| Forward | energy-common/sort-matrix | 584.236 | 581.120 | -0.53% |
| Reversed | Aotizhongxin-default/read | 11.390 | 11.464 | +0.65% |
| Reversed | Aotizhongxin-default/sort-matrix | 15.448 | 15.442 | -0.04% |
| Reversed | energy-common/read | 294.983 | 286.991 | -2.71% |
| Reversed | energy-common/sort-matrix | 518.229 | 505.603 | -2.44% |

Operation CPU covers public CSV reading, requested sorting and matrix construction, shape checks, memory bookkeeping, and output release. Complete-queue charged CPU also includes worker request handling and measured controller CPU. The small air cases do not show a consistent improvement across panels.

CPU time is summed user and system time, not FLOPs, instructions, energy, or normalized work across P-cores and E-cores. RSS is sampled live worker residency and may count shared pages repeatedly. Ten-millisecond sampling can miss short peaks. Retained RSS includes allocator caches. Native lifetime-peak sums stay within 4 GiB in every queue; those sums are conservative bounds, not simultaneous observed peaks. No GPU, Neural Engine, hardware-cache, energy, or global-memory-pressure claim follows from this experiment.

## Validate and reproduce

All 437 dataframe tests pass in Debug and Release, with zero failures and zero skips. The new parameterized test covers underestimated capacities, a late first missing value, full and partial words, and valid NaN payloads. Existing tests cover empty columns, special values, builder reuse, saved-column ownership, multiple appends, rejected inference attempts, and downstream operations. There are no new test-file compiler warnings. This is module validation, not a fresh full-package test claim.

Both complete-workflow audits pass provenance, work completeness, CPU accounting, mode selection, and full-output checks. No experiment workers remain. AC power is checked before every queue, and power settings match across each panel. System snapshots remain in the raw evidence; unrelated activity is not attributed to the benchmark.

[Summary and test receipts](summary.json), [artifact hashes](artifact-sha256.json), and the [experiment archive](experiment.tar.gz) preserve the result. The archive contains exact source snapshots, benchmark controllers, candidate build receipts, sampling output, test logs and summaries, input contracts, all raw queues, and independent expected hashes. It excludes raw CSVs, executables, object files, module caches, and xcresult bundles.

`Benchmarks/CPUThroughput/build.py` rebuilds the worker using the recorded dependency paths. `measure.py` reproduces the narrow replay. `screen-density.py word-state` generates independent expected hashes and repeats density screens after `density.py` has generated the inputs. `compare-workflows.py` and `compare-workflows-reversed.py` run the complete panels. `audit-workflows.py [panel-directory-name]` checks their outputs. Each runner requires a fresh output directory. Absolute source, dependency, and reference-data paths must exist or be remapped.

The worker build receipt records the parent head plus exact candidate source hashes because measurements preceded the source commit. Those hashes match commit `5b9c90297723cf53dcba17299c57778688e282e2`. Historical build receipts and benchmark fingerprints remain unchanged.
