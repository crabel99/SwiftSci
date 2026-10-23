# Shared keys for adaptive Double sorting

This local candidate replaces separate dense comparison and radix preparation with the same UInt64 keys. Preparation starts after the first direction change. Monotonic inputs keep their direct stable permutations. The purpose is lower CPU work and temporary memory across input arrangements, while preserving exact results.

Source is `b982028c59c89f615688882ee71be19a0eccd8f2` on `codex/csv-lazy-sort-cache`, based on `e1f5f8c30500e1511b0700bcffe10efb7ac8e88b`. Every panel also measures the earlier qualified checkpoint `91c0ff09b7810b57cabdd953f8bc67791b1008f5`. The source, tests, and evidence remain local. No PR or push is included.

## The smallest alternative lost its CPU advantage

A separate trial, `def5a57c59`, sorted row indices by looking up original nullable values. It removed tuple preparation but repeatedly decoded source keys during comparison. Its 64 output preflights matched. One-worker screening showed roughly 11 to 27 ms CPU for a million-row compact nearby-swap case, despite lower peak memory. Those are unqualified screening observations, not accepted benchmark results. The trial was rejected and preserved in the [direct-index evidence archive](rejected-direct-indices.tar.gz).

## One representation serves both sorters

The existing Double probe records direction changes without allocating keys. At the first change, eligible columns prepare one eight-byte key per physical row. Preparation encodes the already-read prefix without recounting its runs, then resumes classification on the unread suffix. It continues NaN checks after the run policy has selected radix.

The encoder is the existing IEEE order transformation. It normalizes both zero signs, encodes valid numeric order, and complements keys for descending order. UInt64.max marks missing rows. Neither ascending nor descending valid non-NaN keys can reach that sentinel, including infinities and subnormals. A valid NaN rejects preparation and uses the exact existing optional-value comparison fallback. Stored column values are unchanged.

A key scan builds one result array with valid rows first and missing rows last, each in source order. Stable comparison sorts only the valid prefix using encoded keys. Radix consumes the same keys through the existing 11-bit passes. This removes the separate missing-row array and tuple-to-result mapping from the prepared path. Buffer borrows avoid mutable ArraySlice copies.

Radix scratch holds only valid rows. If its final permutation occupies scratch, nullable results copy the valid prefix back to preserve the missing suffix. Null-free results can still swap buffers. This copy is a measured cost, not assumed to be free.

The shared-key representation is admitted when its 8*N key bytes fit within the 16*V native tuple bytes they replace, expressed as N-V <= V. This conservative component budget is not an optimal whole-sort density threshold. The shared representation also removes missing-row storage, so total peak memory can favor it below this bound. Sparse comparison locality remains a separate question. Columns below the bound keep the existing tuple comparison path; their radix path still uses the shared encoder and kernel.

The minimum-size and sparse bypasses remain unchanged, as does max(8, validCount / 64) for radix selection. There is no new public option, precision conversion, worker cap, or tuned row-count cutoff. The [design synthesis](architecture.md) records both alternatives and the [independent judgment](architecture-judgment.md).

## Broader controls test the structure

Twenty-four fixtures cover two sizes, 32,768 and 1,000,000 rows. Layouts include ascending, descending, repeated nearby swaps, single early/middle/late swaps, pseudorandom values, and alternating runs that trigger radix near the last row. Nullable fixtures sit just below, at, and above half occupancy. A sparse disordered fixture exercises the forced radix path. Both storage choices produce 48 cases.

Independent Python stable permutations and complete value hashes define expected output. Quoted empty CSV fields preserve missing rows. The existing dispatch boundary informs adversarial tests; no production constant is tuned to them.

The table shows million-row compact cases. Each cell gives earlier-qualified, monotonic-checkpoint, and shared-key medians. CPU covers public sorting and index release with the input retained. CSV creation and full output validation are excluded. Process peak RSS can include the earlier CSV construction peak.

| Million-row storage and layout | CPU earlier / monotonic / shared-key, ms | Peak RSS earlier / monotonic / shared-key, MiB |
|---|---:|---:|
| compact / ascending | 4.000 / 1.597 / 1.570 | 38.172 / 25.234 / 25.203 |
| compact / descending | 66.021 / 2.715 / 2.571 | 38.156 / 25.219 / 25.188 |
| compact / nearby-swaps | 9.286 / 10.238 / 6.811 | 38.172 / 38.164 / 34.188 |
| compact / single-early | 4.024 / 4.885 / 2.846 | 38.172 / 38.164 / 30.547 |
| compact / single-middle | 4.702 / 5.617 / 3.860 | 38.172 / 38.164 / 34.359 |
| compact / single-late | 3.996 / 4.864 / 3.616 | 38.156 / 38.156 / 30.531 |
| compact / late-radix-64 | 15.227 / 13.427 / 12.290 | 45.859 / 38.234 / 38.203 |
| compact / random | 13.162 / 12.565 / 12.294 | 38.234 / 38.234 / 38.203 |
| compact / half-minus-one | 2.638 / 3.538 / 3.542 | 38.719 / 38.672 / 38.656 |
| compact / half | 2.627 / 3.416 / 2.445 | 38.688 / 38.656 / 30.969 |
| compact / half-plus-one | 2.604 / 3.479 / 2.465 | 38.672 / 38.688 / 30.969 |
| compact / sparse | 5.832 / 5.744 / 2.277 | 38.719 / 38.703 / 31.016 |

For compact nearby swaps, CPU falls from 10.238 to 6.812 ms, about 33.5%, while peak RSS falls from 38.164 to 34.188 MiB. Single early, middle, and late disorder also use less CPU. The sparse disordered radix case falls from 5.744 to 2.278 ms, with peak RSS down from 38.703 to 31.016 MiB. These are operation-level results for the recorded fixtures.

The candidate is not an unconditional winner. The optional million-row ascending control rises from 1.367 to 1.437 ms in this panel, about 5%, while its peak memory remains essentially unchanged. Compact monotonic controls retain their earlier gains. Below the conservative admission boundary, nearly ordered comparison still takes the old path. At one valid value below half occupancy, compact CPU remains about 3.54 ms; at half occupancy it falls to 2.45 ms. This discontinuity calls for testing a broader key-admission policy against whole-operation CPU and memory, not treating the component budget as optimal.

[All 48 controls](shape-results.md) include both storage choices and sizes, CPU, held heap, and peak RSS. For eligible prepared cases, logical source reads after a direction change at row k are approximately N+k rather than 2N, but preparation also scans encoded keys and comparison reads those keys. This source-loop analysis does not measure physical traffic, cache activity, or energy. A late first change offers little source-read saving.

## Real observation workflows

The matched reference panel uses 2,075,259 household electricity observations and 35,064 Aotizhongxin air-quality observations. Every label honors the same schema, null tokens, native types, input bytes, storage choice, and output order. Both serial and native parallel CSV conversion run index sorting, sorting followed by matrix preparation, and sorting followed by retained optional exports.

Total CPU includes construction, operations, consumer preparation, and release. Operation CPU excludes construction and release. Complete output hashes run outside timing. These are the serial household cases, shown as monotonic-checkpoint and shared-key medians.

| Storage and workflow | Total CPU prior / current, ms | Operation CPU prior / current, ms | Held heap prior / current, MiB | Peak RSS prior / current, MiB |
|---|---:|---:|---:|---:|
| optional / sort-indices | 279.90 / 281.79 | 47.53 / 46.21 | 301.00 / 301.00 | 420.59 / 420.56 |
| optional / sort-matrix | 431.20 / 430.55 | 197.15 / 192.99 | 396.00 / 396.00 | 737.48 / 737.48 |
| optional / sort-materialize | 409.74 / 412.35 | 179.34 / 177.49 | 285.16 / 285.16 | 626.64 / 626.62 |
| compact / sort-indices | 288.29 / 293.36 | 46.70 / 46.29 | 191.95 / 191.95 | 312.41 / 312.37 |
| compact / sort-matrix | 411.18 / 414.16 | 167.56 / 167.88 | 286.95 / 286.95 | 503.38 / 503.18 |
| compact / sort-materialize | 417.39 / 422.60 | 176.38 / 175.48 | 397.81 / 397.81 | 550.97 / 550.92 |

For serial compact household data, full CSV-and-index-sort CPU rises from 288.286 to 293.360 ms, about 1.8%, while sort-operation CPU changes from 46.703 to 46.289 ms. Full CSV-and-matrix CPU rises from 411.182 to 414.162 ms, while operation CPU is nearly unchanged at 167.560 and 167.880 ms. The new design does not establish an additional full-path CPU improvement on these disordered observations.

Held-heap sizes match the monotonic checkpoint. Compact matrix and optional-export workflows still retain 15.4375 MiB less malloc capacity than the earlier qualified checkpoint. Their peak RSS remains almost unchanged. These inherited capacity savings are distinct from the new nearby-swap peak-memory improvement.

[All 24 reference cases](results.md) also show the earlier qualified checkpoint. Held heap records live malloc allocation sizes, including spare capacity. Peak RSS records resident pages. A smaller retained capacity does not imply equal physical-RAM relief. Full-path and sort-only CPU differences remain separate.

## Validation and acceptance boundaries

Release, Debug, and Address Sanitizer each pass all 427 dataframe test functions without failures or skips. Three new small test functions pass before and after implementation. They cover first-disorder positions, both sides of the component-budget boundary, IEEE edges, stable permutations, public dataframe sorting, and Int64 row identifiers above 2^53. Existing tests cover valid NaNs before and after dispatch, null bitmap boundaries, and monotonic signed-zero ties. The new test type is 69 lines.

Twenty-eight eager and twenty-eight streamed reference reads pass exact type, value, null, and row-order checks. The real panel has 96 preflights and 768 measured fresh processes. The shape panel has 192 preflights and 1,536 measured fresh processes. All 2,304 measured outputs match their complete fingerprints.

Eight balanced orders put each label in each position twice and each ordered adjacent pair twice. The fourth label repeats the candidate executable. The frozen policy flags candidate/twin median CPU differences above 10%, or peak RSS differences above 5% plus 8 MiB. Flagged comparisons remain unqualified. Real-data quality is `quality_passed=true`, with flags `[]`. The separate [shape audit](shape-audit.json) preserves shape quality.

Tests, builds, and fixture preparation finish before accepted timings. AC power is checked at both ends. Independent audits verify source, input, module-import and executable hashes, balanced order, exact output equality, and recomputed medians. The machine is an Apple M4 Max with 128 GiB unified memory, using Swift 6.4 and an arm64 macOS 14 deployment target.

CPU is process user plus system time. These measurements do not establish FLOPs, energy, physical memory traffic, or cache mechanisms. Address Sanitizer does not prove universal leak freedom. Validation covers the dataframe module, not the complete MLX-dependent package. This remains a local trial. The conservative sparse admission rule, small optional monotonic CPU cost, and mixed full-path reference results prevent an unconditional efficiency claim. The next experiment should compare broader key admission using whole-sort CPU and peak memory, particularly below half occupancy.

## Evidence and reproduction

- [All real-data results](results.md) and [shape results](shape-results.md).
- [Main audit](audit.json), [shape audit](shape-audit.json), and [comparator provenance](comparator-provenance.json).
- [Frozen study definition](study.json) and [source patch](changes.patch.gz).
- [Design synthesis](architecture.md) and [independent architecture review](architecture-judgment.md).
- [Source, scripts, raw records, and receipts](experiments.tar.gz).
- [Rejected direct-index screen](rejected-direct-indices.tar.gz).
- [Artifact hashes](artifact-sha256.json).
- [Previous monotonic study](../2026-10-23-csv-monotonic-permutations/README.md).

Restore the recorded source and dependencies. Rebuild reference modules from their compiler receipts. The archive includes compiler-command-template.json for the build scripts' F/build.json input; restore it at the recorded path or update F. Update machine-specific paths and decompress the patch. Run verify.py Release with a fresh label, then validate.py, measure.py, and package.py. The implement.py codemod reproduces the candidate from the base TypedColumn.swift, and its proof file matches the final source byte for byte.

The archive contains fixture generators and contracts instead of large CSV files. It excludes executables, dependency caches, and result bundles. Source and tests stay on the local experiment branch. Reports, architecture decisions, and raw evidence stay only on codex/engineering-notes.
