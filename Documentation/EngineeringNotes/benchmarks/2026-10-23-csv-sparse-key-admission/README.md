# Sparse admission for shared sort keys

The candidate removes the 50% valid-row condition from the shared-key sorter. Source is `940353d441c5b2b1bcec69344629452b4ac65b7c` on `codex/csv-shared-keys-sparse-admission`, based on `b982028c59c89f615688882ee71be19a0eccd8f2`. This remains a local experiment. No push or PR is included.

## Whole-sort storage replaces a component-only bound

The parent compares 8*N key bytes with 16*V tuple bytes. That bound omits the parent's separate 8*(N-V) missing-row indices. The complete replaced preparation is 8*N+8*V, before allocator capacity and output storage. Removing the component bound therefore needs measurement of the complete sort, especially sparse comparison locality.

Preparation now starts at the first direction change for every column admitted by the existing 1,024-valid-row minimum and 5% sparse bypass. The radix run limit is unchanged. Removing the density condition makes the secondary scalar run-count branch and its final tuple fallback unreachable, so this patch deletes them. The source change removes 25 lines and adds 9.

Monotonic permutations, stable numeric ties, signed zeros, missing rows last, valid-NaN fallback, native Int64 identifiers, stored values, public options, and CPU parallelism retain their existing contracts. The [parent study](../2026-10-23-csv-shared-sort-keys/README.md) explains the shared representation and its earlier alternatives.

## Broad controls measure CPU and peak memory

Forty fixtures at 32,768 and 1,000,000 rows produce 80 cases across optional and compact storage. Existing controls cover ascending, descending, nearby swaps, single early/middle/late swaps, random values, late radix selection, and the former 50% admission boundary. New nearly ordered fixtures contain approximately 5.3%, 10%, 25%, or 50% valid rows. Missing rows are distributed or clustered. Each new fixture swaps two unequal valid values near the middle of its valid sequence.

Independent Python stable permutations and complete value hashes define exact results. Quoted empty CSV fields preserve missing rows. Timing uses ascending order. Correctness tests cover both directions. The input is retained throughout sort timing. CSV construction and output verification are outside sort CPU timing. Peak RSS can include the earlier CSV construction peak.

| Million-row compact layout | CPU parent / candidate, ms | Peak RSS parent / candidate, MiB | Qualified |
|---|---:|---:|---|
| ascending-1000000 | 1.440 / 1.464 | 25.234 / 25.250 | True |
| descending-1000000 | 2.554 / 2.303 | 25.219 / 25.234 | True |
| half-1000000 | 2.499 / 2.474 | 30.969 / 30.984 | True |
| half-minus-one-1000000 | 3.529 / 2.558 | 38.656 / 31.016 | True |
| half-plus-one-1000000 | 2.525 / 2.462 | 30.969 / 30.984 | True |
| late-radix-64-1000000 | 12.450 / 12.227 | 38.219 / 38.234 | True |
| nearby-swaps-1000000 | 6.785 / 6.914 | 34.188 / 34.234 | True |
| random-1000000 | 12.204 / 12.201 | 38.234 / 38.234 | True |
| single-early-1000000 | 2.975 / 2.939 | 30.562 / 30.578 | True |
| single-late-1000000 | 4.050 / 3.852 | 30.594 / 30.594 | True |
| single-middle-1000000 | 3.912 / 3.871 | 34.391 / 34.406 | True |
| sparse-1000000 | 2.260 / 2.178 | 31.047 / 31.062 | True |
| valid-10-clustered-1000000 | 3.360 / 2.035 | 32.125 / 31.000 | True |
| valid-10-distributed-1000000 | 3.213 / 2.228 | 32.141 / 31.141 | True |
| valid-19-clustered-1000000 | 3.242 / 1.938 | 31.406 / 30.891 | True |
| valid-19-distributed-1000000 | 3.068 / 2.210 | 31.422 / 30.891 | True |
| valid-2-clustered-1000000 | 4.650 / 3.087 | 38.547 / 32.539 | True |
| valid-2-distributed-1000000 | 3.843 / 3.090 | 38.656 / 32.516 | True |
| valid-4-clustered-1000000 | 3.773 / 2.449 | 34.469 / 31.578 | True |
| valid-4-distributed-1000000 | 3.533 / 2.747 | 34.438 / 31.547 | True |

## Complete observation workflows remain separate

The real-data panel covers 2,075,259 household electricity observations and 35,064 air-quality observations. Every executable receives the same complete schema, null tokens, native types, storage policy, values, and row order. Serial and native parallel CSV conversion each run index sorting, sorting followed by matrix preparation, and sorting followed by retained optional exports.

Total CPU includes CSV construction, requested operations, consumer preparation, and release. Operation CPU excludes CSV construction and release. Complete output verification is outside timing. The table gives serial household medians.

| Household serial storage and workflow | Total CPU parent / candidate, ms | Operation CPU parent / candidate, ms | Held heap parent / candidate, MiB | Peak RSS parent / candidate, MiB |
|---|---:|---:|---:|---:|
| optional / sort-indices | 309.047 / 308.954 | 53.386 / 53.560 | 300.999 / 300.999 | 421.312 / 420.625 |
| optional / sort-matrix | 436.280 / 452.313 | 197.000 / 202.331 | 395.999 / 395.999 | 737.500 / 737.492 |
| optional / sort-materialize | 436.667 / 439.899 | 186.125 / 188.218 | 285.156 / 285.156 | 626.641 / 626.656 |
| compact / sort-indices | 296.570 / 299.313 | 47.636 / 48.314 | 191.952 / 191.952 | 312.375 / 312.391 |
| compact / sort-matrix | 419.601 / 423.255 | 169.918 / 168.632 | 286.952 / 286.952 | 503.391 / 503.477 |
| compact / sort-materialize | 433.018 / 434.327 | 181.425 / 178.862 | 397.812 / 397.812 | 550.969 / 551.180 |

## The result favors broader admission, with measured limits

All eight new million-row compact sparse controls use less CPU, about 19.6% to 40.2%, and lower peak RSS. For approximately 5.3%, 10%, and 25% valid rows, CPU falls by 22.2% to 40.2%. Savings occur with distributed and clustered missing rows. This is broader evidence than the former half-occupancy boundary alone.

With one valid row below half occupancy and an early inversion, compact CPU falls from 3.529 to 2.558 ms. Peak RSS falls from 38.656 to 31.016 MiB, about 19.8%. At half occupancy, which already used prepared keys, CPU changes from 2.499 to 2.474 ms with essentially unchanged peak RSS. The old dispatch cliff is removed for these fixtures.

Other controls retain small costs. The largest observed sorting CPU increase is the optional 32,768-row half-occupancy case, 0.0625 to 0.0665 ms, about 6.4%. The compact early-inversion case at that size rises from 0.0840 to 0.0885 ms. Million-row optional nearby swaps rise from 6.689 to 6.831 ms, about 2.1%. The largest upward shape peak-RSS difference is 0.046875 MiB. These results are included without a quality waiver.

The reference datasets already qualified for shared keys in the parent. The current panel does not show an additional full-path CPU improvement. Reference total CPU ratios range from 0.989 to 1.0367. 18 of the 24 medians rise. The worst case is serial optional household sorting followed by matrix preparation, 436.280 to 452.313 ms, about 3.7%. Its operation CPU rises from 197.000 to 202.331 ms, about 2.7%.

Serial compact household index sorting rises from 296.571 to 299.313 ms total CPU, about 0.9%, with operation CPU 47.636 to 48.314 ms. Compact matrix preparation rises from 419.601 to 423.255 ms total CPU, while operation CPU falls from 169.919 to 168.633 ms. Retained heap and peak RSS are essentially unchanged for these reference paths. Their shared sorting algorithm was already selected before this edit. The measurements do not isolate a compiler-layout, constructor, or scheduling cause for the small CPU costs.

The decision is to preserve this smaller implementation as an isolated local candidate. It improves the newly admitted sparse operations in both CPU and peak memory, but it is not an unconditional production recommendation. Before combining it into a PR, investigate the common-path CPU costs without changing the frozen quality policy. The inherited minimum-size and 5% bypasses remain separate questions. No threshold was tuned from this panel.


## Verification and limits

Release, Debug, and Address Sanitizer each pass 429 dataframe test functions with zero failures or skips. The two new test functions also pass on the unchanged parent. They check early, middle, and late first disorder, clustered and distributed missing rows, both sort directions and storage choices, public dataframe sorting, stable Int64 row identities above 2^53, and valid NaNs before and after preparation. The new type is 68 lines.

Twenty-eight eager and twenty-eight streamed reference reads pass exact type, value, null, and row-order checks. The shape panel has 320 preflights and 2560 measured processes. The real-data panel has 96 preflights and 768 measured processes. All output fingerprints match.

Eight balanced orders place each label in each position twice and each ordered adjacent pair twice. Original is `91c0ff09b7810b57cabdd953f8bc67791b1008f5`. Parent is `b982028c59c89f615688882ee71be19a0eccd8f2`. Current and twin run the identical candidate executable. The frozen quality policy flags candidate/twin median CPU differences above 10%, or peak RSS differences above 5% plus 8 MiB. Flagged cases remain unqualified. Shape quality flags are `[]`. Real-data quality flags are `[]`.

Tests, builds, and fixture preparation finish before accepted timings. AC power is checked at both ends. Audits verify source, input, executable, and module-import hashes, balanced order, exact outputs, and independently recomputed medians. The machine is an Apple M4 Max with 128 GiB unified memory, Swift 6.4, and an arm64 macOS 14 deployment target. No worker caps or affinity settings change.

CPU means process user plus system time. These results do not establish energy, FLOPs, cache effects, physical memory traffic, or universal leak freedom. The validated scope is the dataframe module, not the complete MLX-dependent package.

## Evidence and reproduction

[All shape cases](shape-results.md), [all reference cases](results.md), [source and validation audit](audit.json), [shape audit](shape-audit.json), and [comparator provenance](comparator-provenance.json) retain the full results. The [experiment archive](experiments.tar.gz) contains controllers, input generators, commands, receipts, raw measurements, source snapshots, and logs. The [source patch](changes.patch.gz) applies to the recorded parent. [Artifact hashes](artifact-sha256.json) identify these files.

The archived `verify.py`, `validate.py`, `measure.py`, `analyze.py`, and `package.py` reproduce each phase. Build receipts record the compiler, dependency, and module paths. Restore their local dependencies and the recorded external dataset contracts before rerunning. Rebuild each comparator at its recorded head. Never mix a client module from one head with an object from another.
