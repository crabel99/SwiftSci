# Compact CSV index across broader inputs

The compact index reduces resources for nullable numeric tables as well as dense numeric tables. It provides little benefit when long strings or date conversion dominate the read. An alternate layout intended to restore the unquoted fast path instead adds CPU cost. Keep the existing compact candidate and reject that layout.

This extends the [compact-index experiment](../2026-10-20-csv-compact/README.md). All variants use the same production reference, `546510bb7df19fc87a664bded5947c738011ee1d`. Source experiments remain local copies. No production source, default, dependency, or public API changed. These engineering records belong only to `codex/engineering-notes`.

## Resource results

CPU changes are medians of five paired ratios, including the public CSV read and result release. Memory comes from separate fresh processes. Negative CPU percentages mean less total CPU work.

| Input | Paired CPU change | Peak RSS MiB, reference to compact | Held heap MiB, reference to compact |
| --- | ---: | ---: | ---: |
| Nullable numeric, 250,000 rows × 8 columns, inferred types | −10.5% | 127.41 → 71.80 | 32.94 → 30.64 |
| Same nullable input, supplied schema | −11.4% | 127.42 → 71.78 | 32.94 → 30.64 |
| Dense quoted numeric, 1,000,000 × 4 | −0.2% | 241.39 → 149.84 | 70.31 → 61.08 |
| Dense quoted numeric, 1,000,000 × 2 | +3.3% | 116.17 → 86.77 | 39.78 → 30.55 |
| Unquoted numeric, 1,000,000 × 4 | +2.8% | 159.41 → 159.41 | 61.08 → 61.08 |

Every paired nullable-input comparison uses less CPU. Ratios span 0.893–0.943 for inference and 0.861–0.910 with the schema supplied. Peak RSS falls about 44%; held output heap falls about 7%. The earlier allocation-reuse investigation explains why temporary index layout can affect output capacity. This study does not independently attribute CPU savings to cache behavior.

Mixed integer, floating-point, Boolean, and short-string input shows modest peak-memory savings, about 0.5 MiB at 20,000 rows. Its CPU ratios cross one, with substantial spread in the supplied-schema run. Treat the CPU result as inconclusive. All measurements remain in the evidence.

The 2,048-row long-text workload contains an escaped quote, comma, embedded newline, and over 8 KiB of text per row. Memory is effectively unchanged, and CPU ratio ranges cross one under both schema modes. The 2,048-row date workload is also near parity. Compact metadata cannot remove the cost of materializing large strings or converting dates; those operations are separate possible targets.

The fresh dense-numeric comparison agrees with the earlier conclusion. Four-column quoted input retains a large memory saving at near-parity CPU. Narrow quoted input remains a tradeoff. Unquoted input still uses more CPU without a memory benefit. Do not promote a universal default on this evidence.

Full results:

- [Mixed types, nulls, long text, and dates](packed-diverse/RESULTS.md)
- [Fresh numeric reference comparison](packed-primary/RESULTS.md)
- [Rejected layout against production](direct-primary/RESULTS.md)
- [Rejected layout directly against compact storage](layout-primary/RESULTS.md)

## Rejected layout

The existing candidate stores flat, full-width blocked, and compact blocked fields in one enum. The alternate layout separates the flat array from an optional enum holding only blocked storage. This removes one enum case and leaves the original flat array directly accessible. It does not duplicate the scanner or column-building loops.

The alternate layout uses 7.4% more CPU than production for the million-row unquoted input. A direct comparison with the existing compact candidate shows 3.0% more CPU for that case, with all five paired ratios above one. Quoted four-column cases also use more CPU. Both layouts have the same memory results. Preserve the [patch](direct.patch) as rejected evidence; do not include it in a production change.

This experiment disproves the proposed layout improvement on these workloads. It does not identify the exact compiler or processor mechanism behind the remaining unquoted penalty.

## Workload boundaries and validation

The broader fixtures exercise four input families, each with inferred types and an explicitly supplied schema:

- Mixed types: 20,000 rows, four types, periodic `NA` values, and ragged rows with an absent trailing field.
- Nullable numeric: 250,000 rows, eight Double columns, deterministic values and approximately one null in eleven fields.
- Long text: 2,048 rows, integer identifiers and text containing quoting, delimiters, and embedded newlines.
- Dates: 2,048 rows, integer identifiers and ISO calendar dates checked against a UTC Gregorian calendar.

Within each pair, input bytes, schema policy, output types and values, compiler settings, dependency objects, and measurement program are identical. Supplied-schema results are not compared to inference results as though they perform the same work. Numeric precision is unchanged. Fixture creation and independent output validation occur outside timing.

Validation passed:

- All eight broader workloads on the reference and both candidates, checking every value and its type.
- All eight workloads through the public streaming reader in 257-row chunks, checking 4,176,384 fields per variant against independently validated full reads.
- Seven explicit public-reader fixtures and 2,022 parser parity cases per variant, with identical parser-result hashes.
- For the alternate layout, 505,836 compact/full-width/automatic field comparisons, representation boundary checks, and actual range parsing above 2 GiB and 4 GiB using sparse virtual mappings. These mappings touch only small payloads and are released. They are not multi-gigabyte public-read benchmarks.
- Sixteen existing tests in four CSV suites for the alternate layout. The established compact candidate has byte-identical production sources to the previously tested candidate. This is not a full SwiftSci suite or hosted CI run.

The four comparison sets contain 368 fresh worker processes, 1,150 timing samples, and 138 separate memory samples. Each timing worker warms up twice and records five reads. Each memory worker performs one read without warmup and captures process peak RSS before validation. Native CPU parallelism remains enabled. Each set records AC power at both ends. Normal desktop activity is allowed; pair order alternates, and the spread is reported rather than filtered out.

CPU is summed process user-plus-system time, not energy or FLOPs. Peak RSS is a process high-water measurement. Held heap is the change in malloc bytes in use while the DataFrame is retained, not all physical or GPU memory. Allocation counts, bandwidth, cache misses, and energy were not measured.

## Evidence and replay

The [audit](audit.json) checks source, binary, fixture, and dependency identities; complete pair inventories; validation receipts; and recomputed CPU ratios. The [audit program](audit.py), [raw evidence](evidence.tar.gz), and [archive/member hashes](evidence-sha256.json) preserve the measurements and their provenance. The [packed candidate patch](packed.patch) is unchanged from the prior experiment.

[Replay preparation](replay.py) accepts a checkout containing the reference commit and a new destination directory. It exports the reference, applies each patch, regenerates fixtures, and verifies source and input hashes. It then prints the build, validation, and comparison commands. Builds require the Xcode installation and cached dependency objects recorded by `build.py`. Fresh replay preparation passed all source and fixture hash checks; see the [verification receipt](replay-verification.json). This replay check did not repeat the benchmarks or rebuild the modules. A replay can reproduce inputs and code, not identical timing under a different system load.

## Next decision

The broader-input qualification is complete for these fixtures. The unquoted CPU penalty remains unresolved. Before proposing production integration, isolate storage selection from the unquoted lookup loop without copying the typed column-building implementation. A prior generic traversal experiment did not solve this; any new design needs a distinct, testable reason to expect different generated code. If that does not remove the penalty, preserve the memory candidate behind an explicit resource choice rather than impose the cost on every read.
