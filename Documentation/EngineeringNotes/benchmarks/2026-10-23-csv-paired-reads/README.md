# Paired CSV reads and native hash-table controls

The remaining small-read CPU warning does not reproduce when the readers share the same immutable native null-token Set. Across three paired experiments, candidate CPU differs from cleanup by at most 0.6% on the targeted cases. Separate native tables produce large differences even in same-source controls. That is evidence against treating the earlier unpaired warning as a demonstrated source regression.

Production remains unchanged at `5d1f89a961106104757f2d8d0b8faba79487d100`. The baseline is cleanup commit `f9a99ce54c77909bdd6f95fadd5fa3b5d15490f2`, after removal of unused matcher preparation and before the prefix-decoder selection. These comparisons do not measure the complete branch against its earlier parent.

## Why this comparison is different

The [previous calibration](../2026-10-22-csv-fallback-isolation/README.md) retains candidate CPU warnings and an identical-binary control warning. Those observations remain intact. They justify checking the measurement method before changing the reader again.

Each new worker constructs one immutable Set and passes value copies into both readers' options. Reader plans and decoders retain those values without mutation. This shares the original copy-on-write storage rather than reconstructing equal sets. [The installed standard-library declarations](stdlib-storage-evidence.json) record the value containers and their reference storage. No private Swift storage API is called by the benchmark. Native String hash fingerprints differ across all 900 workers. Hashing is never fixed, and scheduling remains native.

The independent-table mode changes that one setup choice. Each reader builds its own Set from the same ordered token array before warmup. Token contents and semantics remain identical. Shared options have matching iteration orders in every checked worker; separate options never match in this sample. Iteration order is a consistency check, not a public storage-identity API.

## Controls include both module identities

The first binary reuses the actual candidate object and compiles cleanup under another module name. It also compiles candidate source under another name. Its controls compare one implementation with itself and the same source across module names.

The second binary adds interleaved shared-table and independent-table modes. The reciprocal binary then keeps cleanup's actual production module and object, and uses the candidate alias. All source snapshots, optimized commands, and hashes are retained. Dependencies match the actual head's prior build.

The three cases are streamed reads with 64 long ASCII null tokens, no null-valued cells, and two String columns. They cover 3,392 rows under both policies and 3,456 rows under parallel conversion. Both row counts reject candidate prefix preparation. Matching bytes, schema, options, chunk size, types, values, null positions, and order are checked.

## What the paired reads show

| Shared-table experiment | 3,392 rows parallel | 3,392 rows serial | 3,456 rows parallel |
|---|---:|---:|---:|
| Initial candidate object | +0.25% | +0.11% | +0.12% |
| Table-control binary | -0.43% | +0.12% | -0.56% |
| Reciprocal cleanup object | +0.42% | +0.54% | +0.36% |

Values are candidate CPU relative to cleanup, normalized in the reciprocal comparison. Every shared-table same-implementation and same-source module control passes the unchanged two-sided 10% CPU threshold. Small module effects remain measurable, so these numbers are not claims of instruction-level identity.

Independent tables produce two same-source control warnings in the forward experiment and one in the reciprocal experiment. The largest control difference is -14.47%. For the 3,456-row parallel case, the forward same-source ratio's middle half ranges from 0.863 to 1.352 with separate tables, versus 0.986 to 1.001 with a shared table. Separately prepared tables can therefore dominate a small-read comparison even when the source is the same.

This does not establish an exact bucket, allocator, scheduler, cache, or silicon mechanism. Independent tables vary native hash-table setup and allocation layout together. It also does not prove that table variation explains every earlier standalone observation.

## Validation and limits

The 900 independent workers complete 86,400 timed streams, 21,600 warmup streams, and 5,400 full native-output validation streams. Each comparison uses two warmup blocks followed by eight balanced ABBA or BAAB blocks. A timed read includes complete stream consumption and output release, and checks row count. Full native value hashes, types, nulls, and order are checked outside timing before and after each worker's comparisons.

CPU is process user-plus-system time. Each worker contributes one paired ratio based on 16 reads per label. Elapsed time is reported separately. No observations are trimmed. Power is AC. Our builds finish before timing. Unrelated host activity remains uncontrolled.

[The independent audit](audit.json) recomputes every CPU ratio and flag from raw observations, checks balanced order, and verifies native hash fingerprints. Its strict quality command exits 1 on the deliberately independent-table controls. A diagnostic collection command may finish successfully while retaining a failed quality verdict.

Single-process high-water RSS cannot isolate each implementation's peak memory. The binary also contains multiple reader modules, so it differs from a standalone production executable. These experiments diagnose CPU comparisons; they do not qualify independent memory use or erase prior review flags. No full test suite was rerun because production source and its previously tested compiled object are unchanged.

## Decision

Do not redesign the fallback reader or tune admission thresholds to fit the original unpaired warning. The shared-table and reciprocal controls establish a more useful diagnosis method. Extend it across admitted boundaries and real reference inputs, alongside independent memory checks, before promotion. The branch remains local and experimental, and nothing was pushed.

- [All paired results and intervals](results.md)
- [Decision and remaining limits](decision.json)
- [Prospective hypotheses](plan.json), [table-control plan](table-plan.json), and [reciprocal plan](reverse-plan.json)
- [Original paired measurements](paired/summary.json), [table controls](table-control/summary.json), and [reciprocal controls](reverse-control/summary.json)
- [Worker counts and uncompressed hashes](worker-index.json)
- [Build receipt](build.json), [reciprocal build receipt](reverse-build.json), and [dependency proof](dependency-proof.json)
- [Reproduction scripts, probes, input contracts, source snapshots, and logs](experiments.tar.gz)
- [Artifact hashes](artifact-sha256.json)

The archive preserves recorded paths. Reproduction requires the same Swift toolchain and pinned dependency objects from the build receipts. Extract the source snapshots and inputs, then redirect the declared scratch and dependency paths before building. Raw worker JSONL files are exact gzip streams, with uncompressed hashes recorded separately. No production binaries or build caches are committed.
